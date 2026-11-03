import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from app.blender_backend import enabled
from app.main import create_app
from app.models import AgentSession, ModelState


class NoInference:
    available = True
    model = 'offline-only'
    reasoning_effort = 'medium'

    def respond(self, **kwargs):
        raise AssertionError('Software selection must not invoke a model')


@pytest.fixture
def selection(tmp_path):
    app = create_app(runtime_root=tmp_path, native_agent=NoInference())
    client = TestClient(app)
    pid = client.post('/api/projects', json={'project_name': 'Tool selection'}).json()['project_id']
    return app, client, pid, app.state.store.project_dir(pid)


def choose(client, pid, backend):
    return client.post(f'/api/projects/{pid}/modeling/backend', json={'backend': backend})


def test_accidental_blender_can_return_to_su_without_model_or_conversation_changes(selection):
    app, client, pid, root = selection
    context = root / 'state/project_context.json'
    before = context.read_bytes()
    assert choose(client, pid, 'blender').status_code == 200
    session = app.state.store.load_state(pid, 'agent_session.json', AgentSession)
    session.thread_id = 'blender-thread'
    session.reconstruction_state = 'planned'
    app.state.store.save_state(pid, session, 'agent_session.json')
    pending = root / 'runtime/pending_design_scope.json'
    pending.parent.mkdir(exist_ok=True)
    pending.write_text(json.dumps({'consumed': False, 'pending_plan_id': 'old-blender-plan'}))
    result = choose(client, pid, 'sketchup')
    assert result.status_code == 200, result.text
    data = result.json()
    assert data['geometry_writes'] == 0 and data['requires_plan']
    restored = data['project']['agent_session']
    assert restored['modeling_backend'] == 'sketchup'
    assert not restored['thread_id'] and restored['reconstruction_state'] not in ('planned', 'building')
    assert not enabled(root)
    assert context.read_bytes() == before
    assert json.loads(pending.read_text())['consumed']
    assert not list(root.rglob('*.skp')) and not list(root.rglob('*.blend'))


def test_each_tool_restores_its_own_model_identity_and_receipts(selection):
    app, client, pid, root = selection
    store = app.state.store
    paths = [root / 'outputs/model/owner.skp', root / 'runtime/blender/owner.blend']
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'preserved opaque native fixture')
    digests = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    su = store.load_state(pid, 'agent_session.json', AgentSession)
    su.model_path = 'outputs/model/owner.skp'
    su.model_guid = 'owned-su-guid'
    su.ruby_state = {'building': {'revision': 7}}
    su.thread_id = 'old-su-thread'
    store.save_state(pid, su, 'agent_session.json')
    assert choose(client, pid, 'blender').status_code == 200
    blender = store.load_state(pid, 'agent_session.json', AgentSession)
    assert not blender.model_path and not blender.ruby_state and not blender.model_guid
    blender.model_path = 'runtime/blender/owner.blend'
    blender.last_model_info = {'revision': 3}
    store.save_state(pid, blender, 'agent_session.json')
    model = store.load_state(pid, 'model_state.json', ModelState)
    model.model_path = blender.model_path
    store.save_state(pid, model, 'model_state.json')
    data = choose(client, pid, 'sketchup').json()['project']
    assert data['agent_session']['model_guid'] == 'owned-su-guid'
    assert data['agent_session']['ruby_state'] == su.ruby_state
    assert not data['agent_session']['thread_id']
    data = choose(client, pid, 'blender').json()['project']
    assert data['agent_session']['model_path'] == blender.model_path
    assert data['model_state']['model_path'] == blender.model_path
    assert not data['agent_session']['model_guid'] and not data['agent_session']['ruby_state']
    assert digests == [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]


def test_running_turn_blocks_switch_without_state_changes(selection):
    app, client, pid, root = selection
    before = (root / 'state/agent_session.json').read_bytes()
    with app.state.agent_lock:
        assert choose(client, pid, 'blender').status_code == 409
    assert (root / 'state/agent_session.json').read_bytes() == before
    assert not (root / 'state/modeling_backend.json').exists()


@pytest.mark.parametrize('body', [{}, {'backend': 'rhino'}, {'backend': 'blender', 'execute': True}])
def test_invalid_selection_cannot_grant_execution(selection, body):
    app, client, pid, root = selection
    assert client.post(f'/api/projects/{pid}/modeling/backend', json=body).status_code == 422
    assert not (root / 'state/modeling_backend.json').exists()


def test_reselecting_active_tool_preserves_current_plan(selection):
    app, client, pid, root = selection
    choose(client, pid, 'blender')
    session = app.state.store.load_state(pid, 'agent_session.json', AgentSession)
    session.thread_id = 'same-tool-thread'
    session.reconstruction_state = 'planned'
    app.state.store.save_state(pid, session, 'agent_session.json')
    before = (root / 'state/agent_session.json').read_bytes()
    assert not choose(client, pid, 'blender').json()['changed']
    assert (root / 'state/agent_session.json').read_bytes() == before


def test_interrupted_switch_blocks_tools_and_can_be_recovered(selection, monkeypatch):
    app, client, pid, root = selection
    original = app.state.store.save_state
    failed = False
    def fail_once(project_id, state, filename):
        nonlocal failed
        if isinstance(state, AgentSession) and state.modeling_backend == 'blender' and not failed:
            failed = True
            raise OSError('simulated disk failure')
        return original(project_id, state, filename)
    monkeypatch.setattr(app.state.store, 'save_state', fail_once)
    assert choose(client, pid, 'blender').status_code == 409
    with pytest.raises(ValueError, match='切换未完成'):
        enabled(root)
    assert choose(client, pid, 'sketchup').status_code == 200
    assert not enabled(root)
    assert app.state.store.load_state(pid, 'agent_session.json', AgentSession).modeling_backend == 'sketchup'


def test_cross_project_saved_session_is_rejected(selection):
    app, client, pid, root = selection
    foreign = AgentSession(project_id='other', modeling_backend='blender')
    (root / 'state/modeling_backend_sessions.json').write_text(json.dumps({
        'blender': {'session': foreign.model_dump(), 'model': ModelState(project_id='other').model_dump()}}))
    assert choose(client, pid, 'blender').status_code == 409
    assert not (root / 'state/modeling_backend.json').exists()


def test_switch_does_not_reuse_old_execution_approval(selection, monkeypatch):
    app, client, pid, root = selection
    monkeypatch.setattr('app.blender_backend.shutil.which', lambda _: 'fixture-only-not-executed')
    session=app.state.store.load_state(pid,'agent_session.json',AgentSession)
    session.workflow_mode='image_reconstruction'
    session.reconstruction_state='planned'
    app.state.store.save_state(pid,session,'agent_session.json')
    for backend in ('blender','sketchup'):
        assert choose(client,pid,backend).status_code==200
        result=client.post(f'/api/projects/{pid}/conversation',json={'message':'批准','agent_action':'execute'})
        assert result.status_code==409,result.text
