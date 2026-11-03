"""Real installed Codex + product public API runtime + deterministic localhost SSE.

No paid provider, real credential, external model or native modeling quality test.
Only the model peer and dynamic read tool are synthetic. App Server owns all turns,
tool scheduling, native input images, durable history, and thread resume.
"""
import argparse
import base64
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.agent_tools import AgentToolContext
from app.codex_provider import CodexResponsesProvider
from app.native_agent import CodexAppServerRuntime


def run(output: Path, executable: str):
    if output.exists():
        raise ValueError('Use a fresh output directory; previous evidence is immutable')
    project = output / 'project'
    source = project / 'inputs/reference/synthetic.png'
    source.parent.mkdir(parents=True)
    from PIL import Image
    Image.new('RGB',(32,32),(100,130,170)).save(source)
    data_url = 'data:image/png;base64,' + base64.b64encode(source.read_bytes()).decode()
    requests, dispatches = [], []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            raw = self.rfile.read(int(self.headers['Content-Length']))
            body = json.loads(raw)
            # Inspect what the REAL official registry exposes before replying.
            # No command, file mutation or unknown tool is ever requested.
            allowed={'blender_inspect_scene','update_plan','request_user_input'}
            unexpected=[tool.get('name',tool.get('type')) for tool in body.get('tools',[])
                        if tool.get('type')!='function' or tool.get('name') not in allowed]
            if unexpected:
                requests.append(body)
                self.send_error(400,'Unexpected tool surface');return
            n = len(requests)+1
            requests.append(body)
            if self.path != '/v1/responses' or n>3 or body.get('model')!='fixture-model':
                self.send_error(400); return
            if n==1:
                item = {'id':'fc_fixture','type':'function_call','call_id':'call_fixture',
                        'name':'blender_inspect_scene','arguments':'{}','status':'completed'}
            else:
                item = {'id':f'msg_{n}','type':'message','role':'assistant','status':'completed',
                        'content':[{'type':'output_text','text':'FIXTURE_OK','annotations':[]}]}
            response = {'id':f'resp_{n}','object':'response','model':'fixture-model','status':'completed','output':[item],
                        'usage':{'input_tokens':100*n,'output_tokens':10,'total_tokens':100*n+10,
                                 'input_tokens_details':{'cached_tokens':0}}}
            events = [{'type':'response.created','response':{'id':response['id'],'status':'in_progress','output':[]}},
                      {'type':'response.output_item.added','output_index':0,'item':item},
                      {'type':'response.output_item.done','output_index':0,'item':item},
                      {'type':'response.completed','response':response}]
            data=''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode()
            self.send_response(200);self.send_header('Content-Type','text/event-stream')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    peer=threading.Thread(target=server.serve_forever,daemon=True);peer.start()
    base=f'http://127.0.0.1:{server.server_port}/v1'
    config=CodexResponsesProvider(api_base=base,api_key='synthetic-local-fixture-only',
        compatibility_acknowledged=True,allow_loopback=True)
    runtime=CodexAppServerRuntime(output/'runtime',codex_executable=executable,
        home_root=output/'codex-home',model='fixture-model',api_provider=config,timeout_seconds=60, execution_mode='host_tools')
    def dispatch(name,args):
        assert name=='blender_inspect_scene' and args=={}
        dispatches.append(name)
        return {'success':True,'contentItems':[{'type':'inputText','text':'{"source":"synthetic fixture","revision":1}'},
                                               {'type':'inputImage','imageUrl':data_url}]}
    runtime.tool_surface.prepare=lambda **kwargs: AgentToolContext(dynamic_tools=[{
        'name':'blender_inspect_scene','description':'Read a synthetic fixture and its pixels.',
        'inputSchema':{'type':'object','properties':{},'additionalProperties':False}}],
        dispatch=dispatch,quality_state={'backend':'blender'})
    summary={'paid_inference':False,'external_provider_requests':0,'model_quality_test':False,'execution_mode':'host_tools','os_isolation_test':False,
        'synthetic_components':['localhost Responses SSE peer','bounded Blender read tool with synthetic implementation'],
        'real_components':['installed upstream Codex','public CodexAppServerRuntime.respond','reference input images',
                           'dynamic image results','upstream durable session'],
        'executable':executable,'endpoint':base}
    try:
        args=dict(project_dir=project,prompt='Read the synthetic fixture, then respond FIXTURE_OK.',
            mcp_enabled=True,developer_instructions='Synthetic fixture only; call blender_inspect_scene, then reply.',
            workflow_mode='image_reconstruction',tool_profile='reconstruction_coding')
        first=runtime.respond(thread_id=None,**args)
        second=runtime.respond(thread_id=first.thread_id,**args)
        summary['turns']=[asdict(first),asdict(second)]
        summary['same_native_thread']=first.thread_id==second.thread_id
        summary['source_pixels_reached_peer']=bool(requests and 'data:image/' in json.dumps(requests[0]))
        summary['tool_pixels_reached_peer']=len(requests)>1 and 'call_fixture' in json.dumps(requests[1]) and json.dumps(requests[1]).count('data:image/')>=2
        events=[json.loads(line) for p in (project/'runtime/agent_events').glob('*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
        summary['native_receipts']=[e for e in events if e.get('event') in {'thread_model_identity','native_turn_context'}]
        summary['upstream_tool_names']=sorted({tool.get('name',tool.get('type')) for req in requests for tool in req.get('tools',[])})
        summary['no_builtin_environment_tools']=set(summary['upstream_tool_names']) <= {'blender_inspect_scene','update_plan','request_user_input'}
        summary['passed']=summary['no_builtin_environment_tools'] and all(t.reply=='FIXTURE_OK' and t.status=='completed' for t in [first,second]) and len(dispatches)==1 and summary['same_native_thread'] and summary['source_pixels_reached_peer'] and summary['tool_pixels_reached_peer']
    except Exception as e:
        summary.update(passed=False,error=f'{type(e).__name__}: {e}')
    finally:
        server.shutdown();server.server_close();peer.join(timeout=3)
        summary.update(request_count=len(requests),tool_dispatch_count=len(dispatches))
        (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        # Synthetic data only; store complete wire evidence separately from console.
        (output/'requests.json').write_text(json.dumps(requests,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if summary['passed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--codex',required=True)
    args=parser.parse_args()
    raise SystemExit(run(args.output.resolve(),args.codex))
