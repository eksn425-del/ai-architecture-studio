"""Opt-in pinned official SDK, local SSE fixture, real loop/tool/retry/resume.

No paid provider, GUI, SketchUp or geometry is called. Run with the two explicit
KSTUDIO_TEST_DSH_* dependency paths; absence is a named environment prerequisite.
"""
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import threading
import pytest

from app.dsh_configuration import resolve_configuration
from app.dsh_runtime import DSHHostSession


@pytest.mark.parametrize('protocol',['openai-completions','openai-responses'])
def test_official_loop_retries_request_not_tool_and_resumes(tmp_path,protocol):
    sdk=os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE');binary=os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:pytest.skip('Requires explicit installed official DSH SDK and binary paths; no provider credentials required')
    requests=[];tools=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body);n=len(requests)
            if n==2:
                self.send_response(503);self.send_header('Content-Type','application/json');self.end_headers()
                self.wfile.write(b'{"error":{"message":"fixture temporary server error"}}');return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            def send(row):self.wfile.write(('data: '+json.dumps(row)+'\n\n').encode());self.wfile.flush()
            if protocol=='openai-completions':
                delta=({'role':'assistant','tool_calls':[{'index':0,'id':'probe1','type':'function','function':{'name':'readonly_probe','arguments':'{}'}}]}
                       if n==1 else {'role':'assistant','content':'本地协议验证完成。'})
                send({'id':f'fixture{n}','object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':delta,'finish_reason':None}]})
                send({'id':f'fixture{n}','object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':{},'finish_reason':'tool_calls' if n==1 else 'stop'}],
                      'usage':{'prompt_tokens':20,'completion_tokens':5,'total_tokens':25}})
                self.wfile.write(b'data: [DONE]\n\n')
            else:
                send({'type':'response.created','response':{'id':f'fixture{n}','model':'fixture-model','status':'in_progress','output':[]}})
                if n==1:
                    item={'id':'fc1','type':'function_call','call_id':'probe1','name':'readonly_probe','arguments':'','status':'in_progress'}
                    send({'type':'response.output_item.added','output_index':0,'item':item})
                    send({'type':'response.function_call_arguments.delta','item_id':'fc1','output_index':0,'delta':'{}'})
                    item={**item,'arguments':'{}','status':'completed'}
                else:
                    item={'id':f'm{n}','type':'message','role':'assistant','status':'in_progress','content':[]}
                    send({'type':'response.output_item.added','output_index':0,'item':item})
                    send({'type':'response.content_part.added','item_id':item['id'],'output_index':0,'content_index':0,'part':{'type':'output_text','text':'','annotations':[]}})
                    send({'type':'response.output_text.delta','item_id':item['id'],'output_index':0,'content_index':0,'delta':'本地协议验证完成。'})
                    item={**item,'status':'completed','content':[{'type':'output_text','text':'本地协议验证完成。','annotations':[]}]}
                send({'type':'response.output_item.done','output_index':0,'item':item})
                send({'type':'response.completed','response':{'id':f'fixture{n}','model':'fixture-model','status':'completed','output':[item],
                      'usage':{'input_tokens':20,'output_tokens':5,'total_tokens':25}}})
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    cfg=resolve_configuration({'api_base':f'http://127.0.0.1:{server.server_port}/v1','model':'fixture-model',
        'mode':'codex-responses' if protocol=='openai-responses' else 'compatible','reasoning_effort':'provider-default',
        'capabilities_json':json.dumps({'context_window':65536,'max_output_tokens':4096,'tools':True,'streaming':True})})
    def transport(index):
        return DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,api_key='local-only-no-real-key',model=cfg.model,
            specs=[{'name':'readonly_probe','description':'Local read probe','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}],
            dispatch=lambda name,args:(tools.append(name) or {'success':True,'fixture':'durable-readback'}),
            trace_path=tmp_path/f'trace-{index}.jsonl',sdk_site=Path(sdk),dsh_bin=Path(binary),protocol=protocol,
            reasoning_effort=cfg.requested_effort,effective_configuration=cfg,full_capabilities=False)
    try:
        first=transport(1)
        try:result=first.run(prompt='检查一次然后回复。',images=[])
        finally:first.close()
        assert result.status=='completed' and tools==['readonly_probe']
        assert len(requests)==3  # one committed tool, one failed request, one retry
        text=json.dumps(requests[-1],ensure_ascii=False)
        assert 'durable-readback' in text and 'readonly_probe' in text
        second=transport(2)
        try:resumed=second.run(prompt='保留刚才结果，继续对话。',images=[],session_id=result.thread_id)
        finally:second.close()
        assert resumed.thread_id==result.thread_id and len(tools)==1 and len(requests)==4
        assert 'durable-readback' in json.dumps(requests[-1],ensure_ascii=False)
        assert any(json.loads(row).get('type')=='llm/retry' for row in (tmp_path/'trace-1.jsonl').read_text(encoding='utf-8').splitlines())
    finally:server.shutdown();server.server_close()


@pytest.mark.parametrize('protocol',['openai-completions','openai-responses'])
def test_official_stream_drop_preserves_completed_tool_and_rejects_partial(tmp_path,protocol):
    sdk=os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE');binary=os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:pytest.skip('Requires explicit installed official DSH SDK and binary paths; no provider credentials required')
    requests=[];tools=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body);n=len(requests)
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            def send(row):self.wfile.write(('data: '+json.dumps(row)+'\n\n').encode());self.wfile.flush()
            if n==2:
                # A valid SSE event contains only the beginning of tool arguments.
                # Then FIN closes the socket before any terminal completion event.
                if protocol=='openai-completions':
                    send({'id':'dropped','object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':{'role':'assistant','tool_calls':[{'index':0,'id':'partial2','type':'function','function':{'name':'readonly_probe','arguments':'{"unfinished":'}}]},'finish_reason':None}]})
                else:
                    send({'type':'response.created','response':{'id':'dropped','model':'fixture-model','status':'in_progress','output':[]}})
                    send({'type':'response.output_item.added','output_index':0,'item':{'id':'partial2','type':'function_call','call_id':'partial2','name':'readonly_probe','arguments':'','status':'in_progress'}})
                    send({'type':'response.function_call_arguments.delta','item_id':'partial2','output_index':0,'delta':'{"unfinished":'})
                import socket
                self.connection.shutdown(socket.SHUT_WR)
                self.close_connection=True
                return
            if protocol=='openai-completions':
                delta=({'role':'assistant','tool_calls':[{'index':0,'id':'probe1','type':'function','function':{'name':'readonly_probe','arguments':'{}'}}]}
                       if n==1 else {'role':'assistant','content':'本地协议验证完成。'})
                send({'id':f'fixture{n}','object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':delta,'finish_reason':None}]})
                send({'id':f'fixture{n}','object':'chat.completion.chunk','model':'fixture-model','choices':[{'index':0,'delta':{},'finish_reason':'tool_calls' if n==1 else 'stop'}],
                      'usage':{'prompt_tokens':20,'completion_tokens':5,'total_tokens':25}})
                self.wfile.write(b'data: [DONE]\n\n')
            else:
                send({'type':'response.created','response':{'id':f'fixture{n}','model':'fixture-model','status':'in_progress','output':[]}})
                if n==1:
                    item={'id':'fc1','type':'function_call','call_id':'probe1','name':'readonly_probe','arguments':'','status':'in_progress'}
                    send({'type':'response.output_item.added','output_index':0,'item':item})
                    send({'type':'response.function_call_arguments.delta','item_id':'fc1','output_index':0,'delta':'{}'})
                    item={**item,'arguments':'{}','status':'completed'}
                else:
                    item={'id':f'm{n}','type':'message','role':'assistant','status':'in_progress','content':[]}
                    send({'type':'response.output_item.added','output_index':0,'item':item})
                    send({'type':'response.content_part.added','item_id':item['id'],'output_index':0,'content_index':0,'part':{'type':'output_text','text':'','annotations':[]}})
                    send({'type':'response.output_text.delta','item_id':item['id'],'output_index':0,'content_index':0,'delta':'本地协议验证完成。'})
                    item={**item,'status':'completed','content':[{'type':'output_text','text':'本地协议验证完成。','annotations':[]}]}
                send({'type':'response.output_item.done','output_index':0,'item':item})
                send({'type':'response.completed','response':{'id':f'fixture{n}','model':'fixture-model','status':'completed','output':[item],
                      'usage':{'input_tokens':20,'output_tokens':5,'total_tokens':25}}})
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    cfg=resolve_configuration({'api_base':f'http://127.0.0.1:{server.server_port}/v1','model':'fixture-model',
        'mode':'codex-responses' if protocol=='openai-responses' else 'compatible','reasoning_effort':'provider-default','request_retries':0,
        'capabilities_json':json.dumps({'context_window':65536,'max_output_tokens':4096,'tools':True,'streaming':True})})
    def transport(index):
        return DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,api_key='local-only-no-real-key',model=cfg.model,
            specs=[{'name':'readonly_probe','description':'Local read probe','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}],
            dispatch=lambda name,args:(tools.append(name) or {'success':True,'fixture':'durable-readback'}),
            trace_path=tmp_path/f'trace-{index}.jsonl',sdk_site=Path(sdk),dsh_bin=Path(binary),protocol=protocol,
            reasoning_effort=cfg.requested_effort,effective_configuration=cfg,full_capabilities=False)
    try:
        first=transport(1)
        from app.native_agent import NativeAgentUnavailable
        try:
            with pytest.raises(NativeAgentUnavailable) as failure:
                first.run(prompt='检查一次然后回复。',images=[])
        finally:first.close()
        partial=failure.value.partial_result
        assert partial.status=='failed'
        assert partial.tool_call_count==1 and tools==['readonly_probe']
        assert len(requests)==2
        assert 'durable-readback' in json.dumps(requests[1],ensure_ascii=False)
        assert partial.tool_calls==[{'tool':'readonly_probe','status':'completed'}]
        events=[json.loads(row) for row in (tmp_path/'trace-1.jsonl').read_text(encoding='utf-8').splitlines()]
        assert any(row.get('event')=='turn_failed' for row in events)
        assert not any(row.get('type')=='llm/retry' for row in events)
        (tmp_path/'streamdrop-receipt.json').write_text(json.dumps({'protocol':protocol,'paid_calls':0,'http_requests':len(requests),'completed_tools':tools,'partial_status':partial.status,'partial_tool_executed':False},indent=2),encoding='utf-8')
    finally:server.shutdown();server.server_close()
