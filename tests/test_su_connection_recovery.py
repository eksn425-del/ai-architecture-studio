import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import AgentSession
from app.sketchup_mcp import MCPCallError, ConnectorUnavailable, _bridge_script_arguments


class NoModel:
    available = True
    model = 'offline-connection-test'
    reasoning_effort = 'medium'
    def respond(self, **kwargs):
        raise AssertionError('Connection recovery cannot invoke a builder')


@pytest.fixture
def connection(tmp_path, monkeypatch):
    app = create_app(runtime_root=tmp_path, native_agent=NoModel())
    client = TestClient(app)
    pid = client.post('/api/projects', json={'project_name': 'Connection recovery'}).json()['project_id']
    store = app.state.store
    root = store.project_dir(pid)
    model = root / 'outputs/model/blank-disposable-owned.skp'
    model.write_bytes(b'opaque path identity fixture, not a native SKP')
    session = store.load_state(pid, 'agent_session.json', AgentSession)
    session.reconstruction_state = 'planned'
    session.workflow_mode = 'image_reconstruction'
    store.save_state(pid, session, 'agent_session.json')
    monkeypatch.setattr('app.contextual_turn.resolve_host_action', lambda *a, **kw:
        ('execute', {'user_message_id': 'fixture-turn', 'execution_granted': True}))
    return app, client, pid, root, model


def test_unbound_start_returns_connection_action_without_launching_or_inference(connection):
    app, client, pid, root, model = connection
    before = (root / 'state/agent_session.json').read_bytes()
    result = client.post(f'/api/projects/{pid}/conversation', json={
        'message': '开始建模', 'workflow_mode': 'image_reconstruction'})
    assert result.status_code == 409
    assert result.json()['detail']['code'] == 'SKETCHUP_CONNECTION_REQUIRED'
    assert (root / 'state/agent_session.json').read_bytes() == before


def test_recover_route_resumes_journal_even_if_ruby_state_was_already_persisted(connection,monkeypatch):
    app,client,pid,root,model=connection
    session=app.state.store.load_state(pid,'agent_session.json',AgentSession)
    session.model_path=model.relative_to(root).as_posix()
    app.state.store.save_state(pid,session,'agent_session.json')
    pending=root/'runtime/native-recovery/pending.json';pending.parent.mkdir(parents=True)
    pending.write_text('{}')
    state=root/'runtime/project_ruby_state.json'
    state.write_text(json.dumps({'model_path':str(model),'scripts':{'harness_building':{'durability_status':'recovered_verified_checkpoint'}}}))
    before=state.read_bytes();called=[]
    def resume(*args,**kwargs):
        called.append(True);raise ValueError('activation-resume-selected')
    monkeypatch.setattr('app.native_checkpoint_recovery.recover_saved_checkpoint',resume)
    response=client.post(f'/api/projects/{pid}/agent/recover')
    assert response.status_code==409 and 'activation-resume-selected' in response.json()['detail']
    assert called==[True] and state.read_bytes()==before and pending.exists()


def test_intent_failure_survives_refresh_without_forging_conversation(connection, monkeypatch):
    from app.native_agent import NativeAgentUnavailable
    app, client, pid, root, model = connection
    before = (root / 'state/project_context.json').read_bytes()
    def fail(*args, **kwargs):
        raise NativeAgentUnavailable('TIMEOUT: Request timed out.')
    monkeypatch.setattr('app.contextual_turn.resolve_host_action', fail)
    result = client.post(f'/api/projects/{pid}/conversation', json={
        'message':'请调整木饰面，其他不变', 'workflow_mode':'image_reconstruction'})
    assert result.status_code == 409
    assert 'TIMEOUT' in client.get(f'/api/projects/{pid}').json()['agent_session']['error']
    assert (root / 'state/project_context.json').read_bytes() == before


def test_offline_bridge_does_not_consume_approval(connection):
    app, client, pid, root, model = connection
    from app.design_scope_approval import capture_pending_design_plan
    card = root / 'runtime/agent_workspace/notes/reconstruction_card.md'
    card.parent.mkdir(parents=True)
    card.write_text('Explicit fixture plan', encoding='utf-8')
    pending = capture_pending_design_plan(root, card.read_text(), is_followup=False)
    session = app.state.store.load_state(pid, 'agent_session.json', AgentSession)
    session.status = 'ready'
    session.model_path = model.relative_to(root).as_posix()
    app.state.store.save_state(pid, session, 'agent_session.json')
    class Offline:
        def ping(self): raise MCPCallError('bridge closed')
    app.state.sketchup = Offline()
    result = client.post(f'/api/projects/{pid}/conversation', json={
        'message': '开始建模', 'workflow_mode': 'image_reconstruction',
        'approved_pending_plan_id': pending['pending_plan_id']})
    assert result.status_code == 409, result.text
    assert result.json()['detail']['code'] == 'SKETCHUP_CONNECTION_REQUIRED'
    assert not json.loads((root / 'runtime/pending_design_scope.json').read_text())['consumed']


@pytest.mark.parametrize('ready,own_model,guid,bound', [
    (False, True, 'fixture-guid', False), (True, True, 'fixture-guid', True),
    (True, False, 'fixture-guid', False), (True, True, 'changed-guid', False),
    (True, True, '', False),
])
def test_probe_distinguishes_bridge_from_project_binding(connection, ready, own_model, guid, bound):
    app, client, pid, root, model = connection
    session = app.state.store.load_state(pid, 'agent_session.json', AgentSession)
    session.status = 'ready' if ready else 'conversation'
    session.model_path = model.relative_to(root).as_posix() if ready else ''
    session.model_guid = guid
    app.state.store.save_state(pid, session, 'agent_session.json')
    class Adapter:
        def ping(self): return {'success': True}
        def get_model_info(self): return {'entity_count': 0}
        def get_active_model_identity(self): return {
            'model_path': str(model if own_model else root.parent / 'another.skp'),
            'model_name': 'test-copy', 'model_guid': 'fixture-guid',
            'main_thread': True, 'active_context': False}
    app.state.sketchup = Adapter()
    result = client.get(f'/api/projects/{pid}/connector').json()
    assert result['reachable']
    assert result['project_bound'] is bound
    assert result['project_copy_open'] is own_model


def test_script_compatibility_alias_requires_same_physical_root(tmp_path, monkeypatch):
    root = tmp_path / 'generated'; root.mkdir()
    script = root / 'read.rb'; script.write_text('# ARCHFLOW_GENERATED_SCRIPT')
    monkeypatch.setenv('ARCHFLOW_GENERATED_SCRIPT_DIR', str(root))
    monkeypatch.setenv('ARCHFLOW_BRIDGE_SCRIPT_ROOT', str(root))
    args = {'script_path': str(script), 'operation_name': 'read only'}
    assert _bridge_script_arguments('sketchup_eval_project_file', args) == args
    monkeypatch.setenv('ARCHFLOW_BRIDGE_SCRIPT_ROOT', str(tmp_path))
    with pytest.raises(ConnectorUnavailable, match='no script was dispatched'):
        _bridge_script_arguments('sketchup_eval_project_file', args)


def test_script_compatibility_alias_rejects_outside_file(tmp_path, monkeypatch):
    root = tmp_path / 'generated'; root.mkdir()
    outside = tmp_path / 'outside.rb'; outside.write_text('# ARCHFLOW_GENERATED_SCRIPT')
    monkeypatch.setenv('ARCHFLOW_GENERATED_SCRIPT_DIR', str(root))
    monkeypatch.setenv('ARCHFLOW_BRIDGE_SCRIPT_ROOT', str(root))
    with pytest.raises(ConnectorUnavailable):
        _bridge_script_arguments('sketchup_eval_project_file', {'script_path': str(outside)})
    assert _bridge_script_arguments('sketchup_health', {}) == {}


def test_compatibility_alias_can_come_from_existing_connector_configuration(tmp_path, monkeypatch):
    script=tmp_path/'read.rb';script.write_text('# ARCHFLOW_GENERATED_SCRIPT')
    monkeypatch.delenv('ARCHFLOW_BRIDGE_SCRIPT_ROOT',raising=False)
    monkeypatch.setenv('ARCHFLOW_GENERATED_SCRIPT_DIR',str(tmp_path))
    monkeypatch.setattr('app.sketchup_mcp._resolve_server',lambda:(['fixture'],{'ARCHFLOW_BRIDGE_SCRIPT_ROOT':str(tmp_path)},None))
    result=_bridge_script_arguments('sketchup_eval_project_file',{'script_path':str(script)})
    assert result['script_path']==str(script)
