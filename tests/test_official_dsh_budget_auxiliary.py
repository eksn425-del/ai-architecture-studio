"""Actual pinned SDK/official subagents and summarizer, loopback synthetic SSE."""
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import urlopen
import pytest
from app.dsh_configuration import resolve_configuration
from app.dsh_runtime import DSHHostSession
from app.native_agent import NativeAgentUnavailable
from tests.test_official_dsh_local import enable_budget


@pytest.mark.parametrize('scenario',['subagents','compaction','retry','cancel'])
def test_official_auxiliary_calls_share_finite_budget(tmp_path,monkeypatch,scenario):
    sdk=os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE');binary=os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:pytest.skip('Explicit official SDK paths required; no real provider')
    requests=[];lock=threading.Lock();release_stream=threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with lock:requests.append(body);n=len(requests)
            if scenario=='retry':
                self.send_response(503);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"error":{"message":"local fixture"}}');return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            def send(row):self.wfile.write(('data: '+json.dumps(row)+'\n\n').encode());self.wfile.flush()
            if scenario=='cancel':
                send({'id':str(n),'object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':{'role':'assistant','content':'partial'},'finish_reason':None}]})
                release_stream.wait(20);return
            spawn=scenario=='subagents' and n==1
            delta={'role':'assistant','content':'Local synthetic summary.'}
            if spawn:delta={'role':'assistant','tool_calls':[{'index':i,'id':f'child{i}','type':'function','function':{'name':'subagent','arguments':json.dumps({'description':f'local child {i}','prompt':f'Reply once: child fixture {i}'})}} for i in range(2)]}
            if scenario=='subagents' and not spawn:time.sleep(.3)
            send({'id':str(n),'object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':delta,'finish_reason':None}]})
            send({'id':str(n),'object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':{},'finish_reason':'tool_calls' if spawn else 'stop'}],'usage':{'prompt_tokens':30,'completion_tokens':10,'total_tokens':40}})
            self.wfile.write(b'data: [DONE]\n\n')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    cfg=resolve_configuration({'api_base':f'http://127.0.0.1:{server.server_port}/v1','model':'fixture-model','request_retries':2,
        'capabilities_json':json.dumps({'tools':True,'streaming':True,'context_window':65536,'max_output_tokens':4096})})
    limit=3 if scenario=='subagents' else 2
    enable_budget(monkeypatch,tmp_path,cfg,limit)
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY','production-file-proxy')
    monkeypatch.delenv('KSTUDIO_DSH_MCP_CONFIG',raising=False)
    host=DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,api_key='dummy',model=cfg.model,
        specs=[],dispatch=lambda *_:{},trace_path=tmp_path/'events.jsonl',sdk_site=Path(sdk),dsh_bin=Path(binary),
        effective_configuration=cfg,reasoning_effort='provider-default',protocol=cfg.protocol,full_capabilities=True)
    if scenario=='compaction':
        patch=tmp_path/'home/kstudio.patch.yml';rows=json.loads(patch.read_text(encoding='utf-8'))
        rows.append({'insert':[{'id':'budget-auxiliary-fixture','name':(Path(__file__).parent/'fixtures/dsh_budget_auxiliary.mjs').resolve().as_posix(),'config':{'receipt':str(tmp_path/'aux.json')}}]})
        patch.write_text(json.dumps(rows),encoding='utf-8')
    try:
        if scenario=='cancel':
            outcomes=[]
            def run_cancelled():
                try:outcomes.append(host.run(prompt='Run cancellation fixture.',images=[]))
                except NativeAgentUnavailable as error:outcomes.append(error.partial_result)
            runner=threading.Thread(target=run_cancelled);runner.start()
            for _ in range(150):
                if requests:break
                time.sleep(.1)
            assert len(requests)==1
            host.cancelled=True;runner.join(15)
            assert not runner.is_alive() and outcomes[0].status=='interrupted'
        elif scenario=='compaction':
            result=host.run(prompt='Reply once.',images=[]);assert result.status=='completed'
            port=json.loads((tmp_path/'aux.json').read_text())['port']
            with urlopen(f'http://127.0.0.1:{port}/',timeout=15) as response:assert response.status==200
            assert len(requests)==2
        else:
            with pytest.raises(NativeAgentUnavailable):host.run(prompt='Run the local fixture.',images=[])
        with sqlite3.connect(tmp_path/'dsh-test-batches.sqlite3') as db:
            rows=db.execute('SELECT session,status,usage_json FROM attempts').fetchall()
        if scenario=='cancel':
            assert len(requests)==1 and len(rows)==1 and rows[0][1]=='unknown'
        elif scenario=='retry':
            assert len(requests)==1 and len(rows)==1 and rows[0][1]=='unknown'
            # Official retry event may occur; its adapter dispatch is denied.
            assert any(e.get('type')=='llm/retry' for e in host.events)
        elif scenario=='subagents':
            assert len(requests)<=3 and len(rows)==3
            assert len({r[0] for r in rows})>=2  # real child session(s), not only parent
        else:assert any(json.loads(r[2]).get('request_purpose')=='compaction' for r in rows)
        (tmp_path/'auxiliary-receipt.json').write_text(json.dumps({'scenario':scenario,'http_requests':len(requests),'rows':rows,'paid_calls':0},indent=2),encoding='utf-8')
    finally:release_stream.set();host.close();server.shutdown();server.server_close()
