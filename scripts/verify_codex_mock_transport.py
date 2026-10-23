"""Local-only real Codex transport smoke; NOT a provider/quality/cost benchmark.

Public respond() cannot retain custom provider config: this deliberately tests
_run_turn with isolated config, and records that integration limitation separately.
No real auth is read; all model replies and usage are deterministic fixtures.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.native_agent import CodexAppServerRuntime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codex', default='/opt/codex/bin/codex')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    out.chmod(0o700)
    home, codex_home, project = out/'home', out/'codex_home', out/'project'
    workspace = project/'runtime'/'agent_workspace'
    for d in (home, codex_home, workspace):
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o700)
    assert not (codex_home/'auth.json').exists(), 'Must use an unauthenticated isolated home'
    requests, dispatches, readiness = [], [], []
    verified_endpoint = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            requests.append({'method':'GET','path':self.path})
            self.send_error(404)
        def do_POST(self):
            raw = self.rfile.read(int(self.headers['Content-Length']))
            body = json.loads(raw)
            n = sum(r.get('method') == 'POST' for r in requests) + 1
            requests.append({'method':'POST','path':self.path,'body_bytes':len(raw),'body':body,
                             'authorization_present':bool(self.headers.get('Authorization'))})
            if self.path != '/v1/responses' or n > 3:
                self.send_error(400); return
            if n == 1:
                item = {'id':'fc_fixture','type':'function_call','call_id':'call_fixture',
                        'name':'fixture_read','arguments':'{}','status':'completed'}
            else:
                item = {'id':'msg_fixture','type':'message','role':'assistant','status':'completed',
                        'content':[{'type':'output_text','text':'FIXTURE_OK','annotations':[]}]}
            response = {'id':f'resp_fixture_{n}','object':'response','status':'completed','output':[item],
                        'usage':{'input_tokens':100*n,'output_tokens':10,'total_tokens':100*n+10,
                                 'input_tokens_details':{'cached_tokens':0}}}
            events = [ {'type':'response.created','response':{'id':response['id'],'status':'in_progress','output':[]}},
                       {'type':'response.output_item.added','output_index':0,'item':item},
                       {'type':'response.output_item.done','output_index':0,'item':item},
                       {'type':'response.completed','response':response} ]
            data = ''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode()
            self.send_response(200); self.send_header('Content-Type','text/event-stream')
            self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    endpoint = f'http://127.0.0.1:{server.server_port}/v1'
    config = f'''model = "fixture-model"
model_provider = "local_fixture"
approval_policy = "never"
sandbox_mode = "workspace-write"
project_root_markers = [".kstudio-agent-root"]
[features]
plugins = false
apps = false
remote_plugin = false
[analytics]
enabled = false
[model_providers.local_fixture]
name = "Local deterministic fixture"
base_url = "{endpoint}"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
[sandbox_workspace_write]
network_access = false
writable_roots = [{json.dumps(str(workspace))}]
'''
    (codex_home/'config.toml').write_text(config)
    (workspace/'.kstudio-agent-root').write_text('fixture boundary\n')
    env = {'HOME':str(home),'CODEX_HOME':str(codex_home),'PATH':'/usr/bin:/bin',
           'XDG_RUNTIME_DIR':str(home),'TMPDIR':str(out),'NO_PROXY':'127.0.0.1,localhost','RUST_LOG':'warn'}

    class VerifiedRuntime(CodexAppServerRuntime):
        def _request(self, process, events, request_id, method, params, buffered):
            if method == 'thread/start':
                observed = super()._request(process, events, 90001, 'config/read', {'includeLayers':False}, buffered)
                readiness.append(observed)
                effective = observed['config']
                assert effective['model_provider'] == 'local_fixture', effective
                assert effective['model_providers']['local_fixture']['base_url'] == endpoint, effective
                assert effective['model_providers']['local_fixture'].get('requires_openai_auth') is False
                verified_endpoint.append(endpoint)
            return super()._request(process, events, request_id, method, params, buffered)

    def dispatch(name, arguments):
        dispatches.append({'name':name,'arguments':arguments})
        assert name == 'fixture_read' and arguments == {}
        return {'success':True,'value':'fixture'}

    summary = {'simulation':True,'model_quality_test':False,'paid_inference':False,
               'usage_is_fixture_not_billing':True,'endpoint':endpoint,
               'boundary':'real CodexAppServerRuntime._run_turn, not public respond()',
               'public_respond_limitation':'_prepare_home requires auth.json and discards custom model_provider/model_providers config',
               'official_config_reference':'https://developers.openai.com/codex/config-reference/'}
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        with patch.dict(os.environ, env, clear=True):
            summary['version'] = subprocess.check_output([args.codex,'--version'],env=env,text=True).strip()
            runtime = VerifiedRuntime(out/'runtime',codex_executable=args.codex,home_root=codex_home,model='fixture-model',timeout_seconds=30)
            result = runtime._run_turn(project_dir=project,agent_workspace=workspace,thread_id=None,
                prompt='Call fixture_read once, then reply FIXTURE_OK.',mcp_enabled=True,
                developer_instructions='Controlled transport fixture. Do not invoke any other tools.',
                dynamic_tools=[{'name':'fixture_read','description':'Read a fixed test value.',
                                'inputSchema':{'type':'object','properties':{},'additionalProperties':False}}],
                tool_handler=dispatch,model='fixture-model',reasoning_effort='low',reference_images=[])
            summary['result'] = asdict(result)
            summary['passed'] = result.reply == 'FIXTURE_OK' and len(dispatches) == 1
    except Exception as exc:
        summary.update(passed=False,error=f'{type(exc).__name__}: {exc}')
    finally:
        server.shutdown(); server.server_close(); thread.join()
        summary.update(request_count=sum(r['method']=='POST' for r in requests),
                       total_request_body_bytes=sum(r.get('body_bytes',0) for r in requests),
                       tool_dispatch_count=len(dispatches),endpoint_verified_before_turn=bool(verified_endpoint))
        for name, value in [('summary',summary),('requests',requests),('dispatches',dispatches),('readiness',readiness)]:
            (out/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if summary['passed'] else 1

if __name__ == '__main__': raise SystemExit(main())
