import concurrent.futures
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import connector_instances as ci
from app import public_connector as bridge
from app.models import AgentSession, ProjectContext
from app.store import ProjectStore


@pytest.fixture
def paired(tmp_path, monkeypatch):
    root = tmp_path / 'pairing'
    root.mkdir()
    for name in ('requests', 'responses', 'journal', 'generated_scripts', 'instances', 'instance-receipts'):
        (root / name).mkdir()
    bridge.atomic_write(root / 'pairing.json', {'token': 'test-only', 'enabled': True,
        'script_root': str(root / 'generated_scripts')})
    monkeypatch.setenv('KSTUDIO_PUBLIC_CONNECTOR_ROOT', str(root))
    return root


def heartbeat(root, n, path, guid=None, **changes):
    iid = f'{n}-' + str(n) * 24
    value = {'instance_id': iid, 'pid': n, 'title': path.name, 'model_name': path.name,
             'model_path': str(path), 'model_guid': guid or f'guid{n}', 'sketchup_version': '24.0',
             'last_seen': time.time(), 'state': 'running', 'active_context': False, 'main_thread': True}
    value.update(changes)
    bridge.atomic_write(root / 'instances' / (iid + '.json'), bridge.signed(value, 'test-only'))
    return value


def project(tmp_path, name='one'):
    store = ProjectStore(tmp_path / 'runtime')
    context = store.create_project(ProjectContext(project_id=name, project_name=name))
    directory = store.project_dir(context.project_id)
    path = directory / 'outputs/model/blank-disposable-instance.skp'
    path.write_bytes(b'test fixture, not a native model')
    return store, directory, path


def test_unique_fallback_ambiguity_stale_restart_and_no_downgrade(paired, tmp_path):
    store, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    assert ci.target_for_request(paired, directory)['instance_id'] == one['instance_id']
    two = heartbeat(paired, 2, path)
    with pytest.raises(ValueError, match='明确选择'):
        ci.target_for_request(paired, directory)
    ci.write_selection(paired, directory, one)
    assert ci.target_for_request(paired, directory)['instance_id'] == one['instance_id']
    heartbeat(paired, 1, path, last_seen=time.time() - 20)
    with pytest.raises(ValueError, match='退出、过期或重启'):
        ci.target_for_request(paired, directory)
    # Another healthy process cannot take over a stale pin, including PID reuse.
    ci.write_selection(paired, directory, {**two, 'instance_id': '2-' + 'a' * 24})
    with pytest.raises(ValueError):
        ci.target_for_request(paired, directory)
    assert ci.describe(paired, directory)['selection_status'] == 'stale'


def test_changed_document_only_fixed_identity_read_allowed(paired, tmp_path):
    _, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    ci.write_selection(paired, directory, one)
    heartbeat(paired, 1, path, guid='new')
    before = ci.selection_file(paired, directory).read_bytes()
    assert ci.target_for_request(paired, directory, identity_only=True)['model_guid'] == 'guid1'
    with pytest.raises(ValueError, match='GUID'):
        ci.target_for_request(paired, directory)
    assert ci.selection_file(paired, directory).read_bytes() == before
    assert ci.describe(paired, directory)['selection_status'] == 'document_changed'


def test_session_connection_error_with_live_sketchup_does_not_launch_another(paired, tmp_path):
    from app.main import create_app
    from app.sketchup_mcp import MCPCallError
    from tests.conftest import FakeBrain, FakeSketchUp
    from tests.test_demo import FakeNativeAgent

    class BusySketchUp(FakeSketchUp):
        client = SimpleNamespace(requires_document_binding=True)

        def ping(self):
            raise MCPCallError('SketchUp is waiting for the desktop')

    app = create_app(tmp_path / 'runtime', brain=FakeBrain(), sketchup=BusySketchUp(),
                     native_agent=FakeNativeAgent(), disposable_model_launcher=lambda *_: pytest.fail('duplicate launch'))
    client = TestClient(app)
    project_id = client.post('/api/projects', json={'project_name': 'Connection recovery'}).json()['project_id']
    heartbeat(paired, 1, tmp_path / 'original.skp')
    result = client.post(f'/api/projects/{project_id}/agent/session', json={'confirm_disposable_model': True})
    assert result.status_code == 409
    assert '现有窗口' in result.json()['detail']


def test_bad_signature_future_heartbeat_and_stopped_cannot_route(paired, tmp_path):
    _, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path, last_seen=time.time() + 30)
    heartbeat(paired, 2, path, state='stopped')
    assert [x['status'] for x in ci.instances(paired)] == ['stale', 'stopped']
    bad = paired / 'instances' / (one['instance_id'] + '.json')
    bad.write_text(json.dumps(bridge.signed(one, 'wrong-token')))
    assert len(ci.instances(paired)) == 1
    with pytest.raises(ValueError, match='未发现'):
        ci.target_for_request(paired, directory)


def test_profiles_with_same_project_id_have_distinct_pins(paired, tmp_path):
    _, one, path = project(tmp_path / 'a')
    _, two, path2 = project(tmp_path / 'b')
    first, second = heartbeat(paired, 1, path), heartbeat(paired, 2, path2)
    ci.write_selection(paired, one, first)
    ci.write_selection(paired, two, second)
    assert ci.target_for_request(paired, one)['instance_id'] == first['instance_id']
    assert ci.target_for_request(paired, two)['instance_id'] == second['instance_id']


def test_parallel_project_requests_are_targeted_and_wrong_reply_refused(paired, tmp_path):
    _, one, path1 = project(tmp_path, 'one')
    _, two, path2 = project(tmp_path, 'two')
    a, b = heartbeat(paired, 1, path1), heartbeat(paired, 2, path2)
    ci.write_selection(paired, one, a)
    ci.write_selection(paired, two, b)
    observed = []
    def consumer():
        deadline = time.monotonic() + 4
        seen = set()
        while time.monotonic() < deadline and len(seen) < 2:
            for file in (paired / 'instance-requests').glob('*/*.json'):
                if file.name in seen:
                    continue
                value = bridge.verified(json.loads(file.read_text()), 'test-only')
                seen.add(file.name)
                observed.append(value)
                target = value['target']
                bridge.atomic_write(paired / 'responses' / file.name, bridge.signed({
                    'operation_id': value['operation_id'], 'request_digest': value['request_digest'],
                    'instance_id': target['instance_id'], 'result': {'path': target['model_path']}}, 'test-only'))
            time.sleep(.005)
    worker = threading.Thread(target=consumer)
    worker.start()
    def request(directory):
        with ci.project_scope(directory):
            return bridge.call('sketchup_health', {'_kstudio_project': ci.current_project()}, root=paired, timeout=3)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        results = list(pool.map(request, (one, two)))
    worker.join()
    assert [r['path'] for r in results] == [str(path1), str(path2)]
    assert len({r['target']['instance_id'] for r in observed}) == 2
    assert not list((paired/'requests').iterdir())  # legacy plugins cannot consume modern requests
    assert ci.current_project() == ''
    # A signed reply from the other process is still invalid for this request.
    original = observed[0]
    original['target']['instance_id'] = b['instance_id'] if original['target']['instance_id'] == a['instance_id'] else a['instance_id']
    # Receipt mismatch is separately checked by call; signed does not mean matching.
    def wrong_consumer():
        while True:
            fresh = [f for f in (paired/'instance-requests').glob('*/*.json') if f.stem not in {r['operation_id'] for r in observed}]
            if fresh:
                v = bridge.verified(json.loads(fresh[0].read_text()), 'test-only')
                bridge.atomic_write(paired/'responses'/fresh[0].name, bridge.signed({'operation_id':v['operation_id'],
                    'request_digest':v['request_digest'], 'instance_id':b['instance_id'], 'result':{}}, 'test-only'))
                return
            time.sleep(.005)
    worker = threading.Thread(target=wrong_consumer, daemon=True)
    worker.start()
    with pytest.raises(ValueError, match='different SketchUp instance'):
        bridge.call('sketchup_health', {'_kstudio_project':str(one)}, root=paired, timeout=2)
    worker.join(2)


def proof(root, one, old, new, **changes):
    value = {'instance_id': one['instance_id'], 'completed': True, 'error': None,
             'at': time.time(),
             'identity_before': {'model_path':one['model_path'], 'model_guid':old},
             'identity_after': {'model_path':one['model_path'], 'model_guid':new}}
    value.update(changes)
    bridge.atomic_write(root/'instance-receipts'/(one['instance_id']+'.json'), bridge.signed(value, 'test-only'))


def test_guid_pin_cas_requires_matching_completed_native_receipt(paired, tmp_path):
    _, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    ci.write_selection(paired, directory, one)
    for changes in ({'completed':False}, {'error':'unknown'}, {'instance_id':'2-'+'2'*24}, {'at':0},
                    {'identity_after':{'model_path':str(path.parent/'other.skp'), 'model_guid':'new'}}):
        proof(paired, one, 'guid1', 'new', **changes)
        with pytest.raises(ValueError, match='回执'):
            ci.advance_document_pin(directory, path, 'guid1', 'new', root=paired)
        assert ci.read_selection(paired, directory)['model_guid'] == 'guid1'
    proof(paired, one, 'guid1', 'new')
    assert ci.advance_document_pin(directory, path, 'guid1', 'new', root=paired)
    assert ci.read_selection(paired, directory)['model_guid'] == 'new'
    with pytest.raises(ValueError, match='绑定已变化'):
        ci.advance_document_pin(directory, path, 'guid1', 'later', root=paired)


def test_checkpoint_cas_requires_exact_operation_root_revision(paired, tmp_path):
    _, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    ci.write_selection(paired, directory, one)
    fields = {'operation_id':'save-123', 'instance_id':one['instance_id'], 'root_pid':77, 'revision':3}
    proof(paired, one, 'guid1', 'new', **fields)
    for key, bad in [('operation_id','old'), ('root_pid',78), ('revision',2), ('instance_id','2-'+'2'*24)]:
        with pytest.raises(ValueError, match='原生版本不匹配'):
            ci.advance_document_pin(directory, path, 'guid1', 'new', root=paired, checkpoint={**fields,key:bad})
    assert ci.advance_document_pin(directory, path, 'guid1', 'new', root=paired, checkpoint=fields)


def test_same_write_does_not_get_new_operation_on_guid_change(paired, tmp_path):
    _, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    script = paired/'generated_scripts/repeated.rb'
    script.write_text('# ARCHFLOW_GENERATED_SCRIPT\n{}')
    args = {'script_path':str(script), '_kstudio_project':str(directory)}
    with pytest.raises(TimeoutError):
        bridge.call('sketchup_eval_project_file', args, root=paired, timeout=.01)
    first = list((paired/'instance-requests').glob('*/*.json'))
    assert len(first) == 1
    heartbeat(paired, 1, path, guid='new')
    with pytest.raises(TimeoutError):
        bridge.call('sketchup_eval_project_file', args, root=paired, timeout=.01)
    assert list((paired/'instance-requests').glob('*/*.json')) == first


def test_route_select_native_readback_ready_and_pending_write_protection(paired, tmp_path):
    store, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    other = heartbeat(paired, 2, tmp_path/'original.skp')
    app = FastAPI()
    calls = []
    def native_read():
        calls.append(ci.current_project())
        return {**one, 'main_thread':True}
    app.state.sketchup = SimpleNamespace(get_active_model_identity=native_read)
    ci.register_routes(app, store, threading.Lock())
    client = TestClient(app)
    rows = client.get('/api/connectors/sketchup/instances?project_id=one').json()['instances']
    assert [r['selectable'] for r in rows] == [True, False]
    body = {'instance_id':one['instance_id'], 'expected_model_path':str(path), 'expected_model_guid':'guid1'}
    result = client.post('/api/projects/one/connector/instance', json=body)
    assert result.status_code == 200, result.text
    assert result.json()['session']['status'] == 'ready'
    assert calls == [str(directory.resolve())]
    assert ci.current_project() == ''
    session = store.load_state('one', 'agent_session.json', AgentSession)
    session.ruby_state = {'old':{'durability_status':'unconfirmed', 'write_in_flight':True}}
    session.error = 'original unknown error'
    store.save_state('one', session, 'agent_session.json')
    before = (directory/'state/agent_session.json').read_bytes()
    rejected = client.post('/api/projects/one/connector/instance', json=body)
    assert rejected.status_code == 409
    assert (directory/'state/agent_session.json').read_bytes() == before
    assert ci.describe(paired, directory, session)['selection_status'] == 'unknown'


def test_configured_client_context_hidden_from_agent_schema(paired, tmp_path, monkeypatch):
    from app import sketchup_mcp
    monkeypatch.setattr(sketchup_mcp, '_resolve_server', lambda: (['python','-m','app.public_connector'], {}, None))
    client = sketchup_mcp.ConfiguredSketchUpMCP()
    seen = []
    monkeypatch.setattr(client, '_request', lambda request, _: seen.append(request[-1]) or {})
    with ci.project_scope(tmp_path):
        client.call_raw('sketchup_health')
    assert seen[0]['params']['arguments']['_kstudio_project'] == str(tmp_path.resolve())
    assert all('_kstudio_project' not in props for props in bridge.TOOL_PROPERTIES.values())


def test_first_connection_and_explicit_recovery_pin_same_instance_only(paired, tmp_path):
    _, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    assert ci.lifecycle_pin(directory) is None
    assert ci.bind_verified_lifecycle(directory, one, None, path)
    previous = ci.lifecycle_pin(directory)
    target = path.parent/'blank-disposable-recovery.skp'
    target.write_bytes(b'fixture')
    changed = heartbeat(paired, 1, target, guid='recovered')
    heartbeat(paired, 2, path)
    assert ci.bind_verified_lifecycle(directory, changed, previous, target)
    saved = ci.lifecycle_pin(directory)
    assert saved['instance_id'] == one['instance_id']
    assert saved['model_guid'] == 'recovered'
    with pytest.raises(ValueError, match='期间会话连接绑定已变化'):
        ci.bind_verified_lifecycle(directory, changed, previous, target)
    other = heartbeat(paired, 2, target)
    with pytest.raises(ValueError, match='另一个'):
        ci.bind_verified_lifecycle(directory, other, saved, target)
    assert ci.lifecycle_pin(directory) == saved


def test_first_connection_cannot_auto_choose_with_multiple_windows(paired, tmp_path):
    _, directory, path = project(tmp_path)
    one = heartbeat(paired, 1, path)
    heartbeat(paired, 2, path)
    with pytest.raises(ValueError, match='多个'):
        ci.bind_verified_lifecycle(directory, one, None, path)
    assert ci.lifecycle_pin(directory) is None
    with pytest.raises(ValueError, match='安全副本'):
        ci.bind_verified_lifecycle(directory, {**one,'active_context':True}, None, path)


def test_official_turn_dispatch_enters_project_scope_inside_real_http_worker(tmp_path, monkeypatch):
    import sys
    import urllib.request
    from app.harness_comparison import ComparisonRuntime
    from app.dsh_runtime import DSHHostSession
    from app.dsh_configuration import resolve_configuration
    # Local transport test, zero inference. Use the actual SDK host HTTP worker
    # to prove a web-request ContextVar is not incorrectly relied upon.
    monkeypatch.setitem(sys.modules, 'deepseek_harness', SimpleNamespace(DeepSeekHarness=lambda **_:SimpleNamespace(close=lambda:None)))
    project = tmp_path/'projects/worker'
    project.mkdir(parents=True)
    runtime = ComparisonRuntime.__new__(ComparisonRuntime)
    runtime.arm = 'B'
    runtime.model = 'deepseek-v4.1-flash'
    runtime.home = tmp_path/'home'
    runtime.session_identity = 'local-fixture'
    runtime.platform_turn_id = None
    runtime._dsh_active = {}
    runtime.api_provider = SimpleNamespace(api_base='https://fixture.invalid/v1', api_key='test-only')
    runtime.effective_configuration = resolve_configuration({'model':runtime.model, 'api_base':runtime.api_provider.api_base, 'reasoning_effort':'high'})
    monkeypatch.setattr(runtime, '_assert_execution_ready', lambda:None)
    monkeypatch.setattr(runtime, '_dsh_paths', lambda:(tmp_path, 'not-launched'))
    observed = []
    def dispatch(name, args):
        observed.append((ci.current_project(), threading.current_thread().name))
        return {'success':True}
    def run(host, **_):
        request = urllib.request.Request(f'http://127.0.0.1:{host.server.server_port}/call',
            data=json.dumps({'name':'fixture_read', 'arguments':{}}).encode(),
            headers={'Authorization':'Bearer '+host.token, 'Content-Type':'application/json'})
        with urllib.request.urlopen(request) as response:
            assert json.load(response)['success']
        return SimpleNamespace(thread_id='fixture')
    monkeypatch.setattr(DSHHostSession, 'run', run)
    runtime._official_turn(project=project, thread_id=None, prompt='fixture', specs=[{'name':'fixture_read'}],
                           dispatch=dispatch, instructions='fixture', images=[])
    assert observed[0][0] == str(project.resolve())
    assert observed[0][1] != threading.current_thread().name
    assert ci.current_project() == ''
