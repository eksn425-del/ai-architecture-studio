"""No paid inference: actual same-user process/junction evidence and proxy tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from app.workspace_files import workspace_file_call
from app.dsh_configuration import resolve_configuration
from app.dsh_runtime import write_profile


def workspace(path):
    path.mkdir()
    for folder in ('notes','qa','scripts'):(path/folder).mkdir()
    return path


def test_unconfined_process_reaches_synthetic_credentials_and_repo(tmp_path):
    # Dummy canaries only: never inspect real user credentials.
    secret=tmp_path/'credentials-canary.txt';secret.write_text('dummy-private-canary')
    repo=tmp_path/'repo-canary.txt';repo.write_text('before')
    result=subprocess.run([sys.executable,'-c',
        'import pathlib,os,sys; p=pathlib.Path(sys.argv[1]); assert p.read_text()=="dummy-private-canary"; assert os.environ["KSTUDIO_TEST_CANARY"]=="dummy-env"; pathlib.Path(sys.argv[2]).write_text("after"); print("same_user_unconfined")',
        str(secret),str(repo)],env={**os.environ,'KSTUDIO_TEST_CANARY':'dummy-env'},text=True,capture_output=True,check=True)
    assert repo.read_text()=='after' and 'same_user_unconfined' in result.stdout


def test_proxy_persists_ruby_and_rejects_traversal(tmp_path):
    root=workspace(tmp_path/'workspace')
    content='root.entities.add_group # generated only'
    workspace_file_call(root,'workspace_write',{'relative_path':'scripts/module.rb','content':content})
    assert workspace_file_call(root,'workspace_read',{'relative_path':'scripts/module.rb'})['content']==content
    for name in ('../credentials.txt','notes/../../repo.md','C:/credentials.txt','scripts/x.rb:stream','scripts/../notes/secret.md'):
        for tool in ('workspace_read','workspace_write'):
            with pytest.raises(ValueError):workspace_file_call(root,tool,{'relative_path':name,'content':'changed'})


def test_real_link_escape_read_write_and_root_rejected(tmp_path):
    root=workspace(tmp_path/'workspace');outside=tmp_path/'outside';outside.mkdir()
    (outside/'canary.rb').write_text('unchanged')
    (root/'scripts').rmdir()
    if os.name=='nt':
        # Windows junctions need no symlink privilege. One shell, exact fixture paths.
        cmd=f"New-Item -ItemType Junction -Path '{root / 'scripts'}' -Target '{outside}' | Out-Null"
        subprocess.run(['powershell','-NoProfile','-Command',cmd],check=True,capture_output=True)
    else:(root/'scripts').symlink_to(outside,target_is_directory=True)
    for tool in ('workspace_read','workspace_write'):
        with pytest.raises(ValueError):workspace_file_call(root,tool,{'relative_path':'scripts/canary.rb','content':'changed'})
    assert (outside/'canary.rb').read_text()=='unchanged'
    assert 'scripts/canary.rb' not in workspace_file_call(root,'workspace_read',{})['files']
    with pytest.raises(ValueError):workspace_file_call(root/'scripts','workspace_read',{})


def test_production_mcp_cannot_start_and_zero_retry_is_carried(tmp_path,monkeypatch):
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY','production-file-proxy')
    cfg=resolve_configuration({'api_base':'http://127.0.0.1:1/v1','model':'fixture','request_retries':0})
    for full in (False,True):
        path=tmp_path/f'profile-{full}.json'
        write_profile(path,api_base=cfg.endpoint,model=cfg.model,full_capabilities=full,effective_configuration=cfg)
        rows=json.loads(path.read_text());policy=next(r for r in rows if r.get('id')=='llm-pi-ai')['config']['providers']['kstudio-bai']['retryPolicy']
        assert policy['maxRetries']==0
    config=tmp_path/'external.json';config.write_text(json.dumps({'second-writer':{'transport':'stdio','command':'must-not-start'}}))
    monkeypatch.setenv('KSTUDIO_DSH_MCP_CONFIG',str(config))
    with pytest.raises(ValueError,match='External MCP'):
        write_profile(tmp_path/'bad.json',api_base=cfg.endpoint,model=cfg.model,full_capabilities=True)


def test_full_production_official_inventory(tmp_path,monkeypatch):
    sdk=os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE');binary=os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:pytest.skip('Explicit installed official SDK required for zero-inference inventory test')
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY','production-file-proxy')
    monkeypatch.delenv('KSTUDIO_DSH_MCP_CONFIG',raising=False)
    from app.dsh_runtime import DSHHostSession
    cfg=resolve_configuration({'api_base':'http://127.0.0.1:1/v1','model':'fixture','capabilities_json':json.dumps({'tools':True,'streaming':True})})
    host=DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,api_key='dummy-not-real',model=cfg.model,
        specs=[],dispatch=lambda *_:{},trace_path=tmp_path/'inventory.jsonl',sdk_site=Path(sdk),dsh_bin=Path(binary),
        effective_configuration=cfg,reasoning_effort='provider-default',full_capabilities=True)
    try:
        host.start()
        assert {'subagent','subagent_fork','web_search','skill'}<=set(host.inventory)
        assert not {'pwsh','bash','read','write','edit','glob','grep','working_directory','job_output','workflow'}&set(host.inventory)
    finally:host.close()


@pytest.mark.parametrize('protocol',['openai-completions','openai-responses'])
def test_official_zero_retries_makes_one_http_request(tmp_path,protocol):
    sdk=os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE');binary=os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:pytest.skip('Explicit installed SDK required; local HTTP only')
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    from app.dsh_runtime import DSHHostSession
    from app.native_agent import NativeAgentUnavailable
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']));requests.append(self.path)
            self.send_response(503);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(b'{"error":{"message":"local fixture failure"}}')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    cfg=resolve_configuration({'api_base':f'http://127.0.0.1:{server.server_port}/v1','model':'fixture',
        'request_retries':0,'mode':'codex-responses' if protocol=='openai-responses' else 'compatible',
        'capabilities_json':json.dumps({'streaming':True})})
    host=DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,api_key='dummy',model=cfg.model,
        specs=[],dispatch=lambda *_:{},trace_path=tmp_path/'one-http.jsonl',sdk_site=Path(sdk),dsh_bin=Path(binary),
        effective_configuration=cfg,reasoning_effort='provider-default',protocol=protocol,full_capabilities=False)
    try:
        with pytest.raises(NativeAgentUnavailable):host.run(prompt='本地协议验证',images=[])
        assert len(requests)==1
    finally:host.close();server.shutdown();server.server_close()
