"""Real official SDK and loopback provider: uncertain native tool stops inference."""
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import pytest
from app.dsh_configuration import resolve_configuration
from app.dsh_runtime import DSHHostSession
from app.native_agent import NativeAgentUnavailable


@pytest.mark.parametrize('tool', ['sketchup_run_workspace_ruby', 'sketchup_apply_parts'])
def test_native_uncertainty_stops_before_another_provider_request(tmp_path,monkeypatch,tool):
    sdk=os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE');binary=os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:pytest.skip('Pinned official SDK paths required; no real provider')
    monkeypatch.delenv('KSTUDIO_TEST_BATCH_CONFIG',raising=False)
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY','production-file-proxy')
    requests=[];calls=[]
    class Provider(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            delta={'role':'assistant','tool_calls':[{'index':0,'id':'write1','type':'function',
                'function':{'name':tool,'arguments':'{}'}}]}
            for payload in [{'choices':[{'index':0,'delta':delta,'finish_reason':None}]},
                {'choices':[{'index':0,'delta':{},'finish_reason':'tool_calls'}],
                 'usage':{'prompt_tokens':20,'completion_tokens':5,'total_tokens':25}}]:
                self.wfile.write(('data: '+json.dumps({'id':'fixture','object':'chat.completion.chunk','model':'fixture-model',**payload})+'\n\n').encode());self.wfile.flush()
            self.wfile.write(b'data: [DONE]\n\n')
    server=ThreadingHTTPServer(('127.0.0.1',0),Provider)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    cfg=resolve_configuration({'api_base':f'http://127.0.0.1:{server.server_port}/v1','model':'fixture-model',
        'capabilities_json':json.dumps({'tools':True,'streaming':True,'context_window':65536,'max_output_tokens':4096})})
    def dispatch(name,args):
        calls.append(name)
        return {'success':False,'error':'The native write may have committed, but its outcome or disk checkpoint is unconfirmed.'}
    host=DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,api_key='offline-fixture',model=cfg.model,
        specs=[{'name':tool,'description':'Synthetic tool, no native call','inputSchema':{'type':'object','properties':{}}}],
        dispatch=dispatch,trace_path=tmp_path/'events.jsonl',sdk_site=Path(sdk),dsh_bin=Path(binary),
        effective_configuration=cfg,reasoning_effort=cfg.requested_effort,protocol=cfg.protocol,full_capabilities=True)
    try:
        with pytest.raises(NativeAgentUnavailable,match='NATIVE_RECOVERY_REQUIRED'):host.run(prompt='Run fixture once.',images=[])
        assert len(requests)==1 and calls==[tool]
        assert host.native_recovery_required is True
        (tmp_path/'native-stop-receipt.json').write_text(json.dumps({'provider_http_requests':1,'paid_calls':0,'native_writes':0,'blocked_after_uncertain_tool':True}))
    finally:host.close();server.shutdown();server.server_close()
