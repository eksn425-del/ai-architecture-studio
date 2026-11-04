import hashlib
import json
import subprocess
import sys
import threading
import time

import pytest

from app import public_connector as bridge


@pytest.fixture
def paired(tmp_path):
    for name in ('requests', 'responses', 'journal', 'generated_scripts'):
        (tmp_path / name).mkdir()
    (tmp_path / 'pairing.json').write_text(json.dumps({'token': 'test-only', 'enabled': True,
        'script_root': str(tmp_path / 'generated_scripts')}), encoding='utf-8')
    return tmp_path


def test_hmac_tampering_and_revocation(paired):
    signed = bridge.signed({'a': 1}, 'test-only')
    assert bridge.verified(signed, 'test-only') == {'a': 1}
    signed['body'] = '{"a":2}'
    with pytest.raises(ValueError, match='signature'):
        bridge.verified(signed, 'test-only')
    (paired / 'pairing.json').write_text('{"enabled":false}')
    with pytest.raises(ValueError, match='disabled'):
        bridge.call('sketchup_health', root=paired)


def test_pairing_adds_explicit_profile_without_rotating_secret_or_erasing_old_roots(paired):
    first = paired / 'runtime-one'
    second = paired / 'runtime-two'
    first.mkdir()
    second.mkdir()
    for workspace in (first, second, second):
        bridge.authorize_workspace(paired, workspace)
    config = json.loads((paired / 'pairing.json').read_text())
    assert config['token'] == 'test-only'
    assert config['workspace_roots'] == [str(first.resolve()), str(second.resolve())]
    with pytest.raises(ValueError, match='runtime directory'):
        bridge.authorize_workspace(paired, first.anchor)
    config['enabled'] = False
    bridge.atomic_write(paired / 'pairing.json', config)
    with pytest.raises(ValueError, match='disabled'):
        bridge.authorize_workspace(paired, second)


def test_frozen_update_resolves_current_connector_without_rewriting_pairing(tmp_path, monkeypatch):
    from app import sketchup_mcp
    current = tmp_path / 'current'
    current.mkdir()
    (current / 'KStudioConnector.exe').touch()
    config = tmp_path / 'bridge.json'
    payload = json.dumps({'command': str(tmp_path / 'retired' / 'KStudioConnector.exe'),
        'args': [], 'cwd': str(tmp_path / 'retired'),
        'env': {'KSTUDIO_PUBLIC_CONNECTOR_ROOT': str(tmp_path / 'pairing')}})
    config.write_text(payload)
    monkeypatch.setenv('ARCH_STUDIO_MCP_CONFIG', str(config))
    monkeypatch.setattr(sketchup_mcp.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sketchup_mcp.sys, 'executable', str(current / 'KStudio.exe'))
    command, env, cwd = sketchup_mcp._resolve_server()
    assert command == [str(current / 'KStudioConnector.exe')]
    assert cwd == str(current)
    assert env['KSTUDIO_PUBLIC_CONNECTOR_ROOT'] == str(tmp_path / 'pairing')
    assert config.read_text() == payload


def test_request_receipt_and_timeout_never_replays(paired):
    script = paired / 'generated_scripts' / 'fixture.rb'
    script.write_text('# ARCHFLOW_GENERATED_SCRIPT\n{ok: true}', encoding='utf-8')
    calls = []
    def native_fixture():
        for _ in range(100):
            requests = list((paired / 'requests').glob('*.json'))
            if requests:
                request = bridge.verified(json.loads(requests[0].read_text()), 'test-only')
                calls.append(request)
                bridge.atomic_write(paired / 'responses' / requests[0].name,
                    bridge.signed({'operation_id': request['operation_id'],
                        'request_digest': request['request_digest'], 'result': {'fixture': True}}, 'test-only'))
                return
            time.sleep(.01)
    worker = threading.Thread(target=native_fixture)
    worker.start()
    args = {'script_path': str(script)}
    assert bridge.call('sketchup_eval_project_file', args, root=paired, timeout=2) == {'fixture': True}
    worker.join()
    assert bridge.call('sketchup_eval_project_file', args, root=paired, timeout=.1) == {'fixture': True}
    assert len(calls) == 1
    assert calls[0]['arguments']['script_sha256'] == hashlib.sha256(script.read_bytes()).hexdigest()
    script.write_text('# ARCHFLOW_GENERATED_SCRIPT\n{new: true}', encoding='utf-8')
    with pytest.raises(TimeoutError, match='unknown'):
        bridge.call('sketchup_eval_project_file', args, root=paired, timeout=.02)
    count = len(list((paired / 'requests').glob('*.json')))
    with pytest.raises(TimeoutError):
        bridge.call('sketchup_eval_project_file', args, root=paired, timeout=.02)
    assert len(list((paired / 'requests').glob('*.json'))) == count


def test_no_script_path_escape(paired):
    outside = paired / 'private.rb'
    outside.write_text('# private')
    with pytest.raises(ValueError, match='outside'):
        bridge.call('sketchup_eval_project_file', {'script_path': str(outside)}, root=paired)
    assert not list((paired / 'requests').iterdir())


def test_mcp_both_framing_modes_and_catalog():
    from app.sketchup_mcp import _frame, _read_frames
    requests = [{'jsonrpc':'2.0', 'id': 1, 'method':'initialize'},
                {'jsonrpc':'2.0', 'id': 2, 'method':'tools/list'}]
    for framed in (True, False):
        data = b''.join(_frame(r) if framed else json.dumps(r).encode() + b'\n' for r in requests)
        result = subprocess.run([sys.executable, '-m', 'app.public_connector'], input=data,
            capture_output=True, timeout=10)
        assert result.returncode == 0, result.stderr.decode()
        answers = _read_frames(result.stdout) if framed else [json.loads(line) for line in result.stdout.splitlines()]
        assert answers[0]['result']['serverInfo']['name'] == 'kstudio-public-sketchup'
        assert set(t['name'] for t in answers[1]['result']['tools']) == set(bridge.TOOL_NAMES)


@pytest.mark.parametrize('tool',['sketchup_set_camera','sketchup_export_view_image'])
def test_camera_requests_require_explicit_document_binding_before_enqueue(paired,tool):
    with pytest.raises(ValueError,match='document path and GUID'):
        bridge.call(tool,{},root=paired)
    assert list((paired/'requests').iterdir())==[]
    assert set(bridge.DOCUMENT_BINDING).issubset(bridge.TOOL_PROPERTIES[tool])


def test_public_adapter_reads_identity_before_camera_and_capture(tmp_path,monkeypatch):
    from app.sketchup_mcp import SketchUpAdapter
    calls=[]
    class Client:
        requires_document_binding=True
        def call(self,name,args):calls.append((name,args));return {'fixture':True}
    adapter=SketchUpAdapter(Client())
    identities=[]
    def identity():
        identities.append(True)
        return {'model_path':str(tmp_path/'owned.skp'),'model_guid':'owner-guid'}
    monkeypatch.setattr(adapter,'get_active_model_identity',identity)
    adapter.set_camera([1,2,3],[0,0,0])
    adapter.capture_view(tmp_path/'view.png')
    assert len(identities)==2
    for name,args in calls:
        assert args['expected_model_guid']=='owner-guid'
        assert args['expected_model_path']==str(tmp_path/'owned.skp')


def test_unknown_owned_write_blocks_different_next_operation_without_dispatch(tmp_path):
    from app.project_ruby import ProjectRubyExecutor
    from app.sketchup_mcp import MCPCallError
    class Client:
        def call(self,*_):pytest.fail('No native operation may run while prior geometry outcome is unknown')
    executor=ProjectRubyExecutor(tmp_path,'fixture',expected_model_path=tmp_path/'projects/fixture/outputs/model/blank-disposable-test.skp',
        expected_model_guid='owner-guid',mcp=Client(),ruby_state={'old':{'durability_status':'unconfirmed','write_in_flight':True}})
    with pytest.raises(MCPCallError,match='checkpoint is unconfirmed'):
        executor.run({'script_id':'different_new_operation','ruby_source':'raise "must never execute"'})
