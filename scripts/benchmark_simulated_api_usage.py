#!/usr/bin/env python3
"""Local HTTP simulation, not an LLM, provider invoice, or intelligence benchmark.

Run with --repo /path/to/checkout --output /path/to/new/results. The same script
can import an untouched baseline checkout. No app monkeypatches are used.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ESTIMATOR = 'ceil(UTF-8 bytes / 4), per JSON text payload; not a tokenizer or vision estimate'

def text_payload(value):
    if isinstance(value, dict):
        return {k: text_payload(v) for k, v in value.items() if k != 'image_url'}
    if isinstance(value, list):
        return [text_payload(v) for v in value if not isinstance(v, dict) or v.get('type') != 'image_url']
    return value

def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def tool_message(name, arguments, call_id):
    return {'role': 'assistant', 'content': None, 'tool_calls': [{'id': call_id, 'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(arguments, ensure_ascii=False)}}]}

class ScriptedServer:
    """Loopback-only queued assistant messages; HTTP errors are explicit fixtures."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.seen_messages = set()
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                raw = self.rfile.read(int(self.headers['Content-Length']))
                body = json.loads(raw)
                index = len(owner.requests)
                images = [b['image_url']['url'] for m in body.get('messages', [])
                          if isinstance(m.get('content'), list) for b in m['content'] if b.get('type') == 'image_url']
                repeated = 0
                for message in body.get('messages', []):
                    blob = encoded(text_payload(message))
                    digest = hashlib.sha256(blob).hexdigest()
                    if digest in owner.seen_messages:
                        repeated += len(blob)
                    owner.seen_messages.add(digest)
                text_bytes = len(encoded(text_payload(body)))
                measurement = {'request_index': index, 'path': self.path, 'body': body,
                    'wire_body_bytes': len(raw), 'text_json_bytes': text_bytes,
                    'estimated_text_tokens': math.ceil(text_bytes / 4),
                    'repeated_exact_message_text_bytes': repeated,
                    'image_attachment_count': len(images),
                    'image_decoded_bytes': sum(len(base64.b64decode(url.split(',', 1)[1])) for url in images if url.startswith('data:'))}
                owner.requests.append(measurement)
                reply = owner.responses[index] if index < len(owner.responses) else {'http_error': 500}
                if callable(reply):
                    reply = reply(body)
                if 'http_error' in reply:
                    payload = encoded({'error': {'message': 'scripted local failure', 'type': 'server_error'}})
                    self.send_response(reply['http_error'])
                    self.send_header('Content-Type', 'application/json')
                else:
                    usage = {'prompt_tokens': math.ceil(text_bytes / 4), 'completion_tokens': max(1, math.ceil(len(encoded(reply))/4))}
                    finish = 'tool_calls' if reply.get('tool_calls') else 'stop'
                    envelope = {'id': 'chatcmpl-local-'+str(index), 'object': 'chat.completion', 'created': 1,
                                'model': body['model'], 'choices': [{'index': 0, 'message': reply, 'finish_reason': finish}], 'usage': {**usage, 'total_tokens': sum(usage.values())}}
                    if body.get('stream'):
                        delta = dict(reply)
                        if delta.get('tool_calls'):
                            delta['tool_calls'] = [dict(t, index=i) for i,t in enumerate(delta['tool_calls'])]
                        chunk = {k: envelope[k] for k in ('id','created','model')}
                        chunk['object'] = 'chat.completion.chunk'
                        frames = [dict(chunk, choices=[{'index':0,'delta':delta,'finish_reason':None}]),
                                  dict(chunk, choices=[{'index':0,'delta':{},'finish_reason':finish}]),
                                  dict(chunk, choices=[], usage=envelope['usage'])]
                        payload = (''.join('data: '+json.dumps(f)+'\n\n' for f in frames)+'data: [DONE]\n\n').encode()
                    else:
                        payload = encoded(envelope)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream' if body.get('stream') else 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.base_url = f'http://127.0.0.1:{self.server.server_port}/v1'
    def __enter__(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self
    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

def file_reply(directory, timeout_seconds=300):
    """Opt-in assistant-mediated relay, NOT an autonomous model API.

    Each call writes request-NNN.json and waits for response-NNN.json containing
    one assistant message. The caller owns reasoning and validates its action.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    counter = 0
    def reply(body):
        nonlocal counter
        number = counter
        counter += 1
        (directory/f'request-{number:03}.json').write_text(json.dumps(body, ensure_ascii=False, indent=2))
        response = directory/f'response-{number:03}.json'
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if response.is_file():
                try:
                    message = json.loads(response.read_text())
                except json.JSONDecodeError:
                    time.sleep(0.1)
                    continue
                if message.get('role') != 'assistant':
                    raise ValueError('Relay response must be an assistant message')
                return message
            time.sleep(0.1)
        return {'http_error': 504}
    return reply

def summarize(requests):
    names = ['wire_body_bytes','text_json_bytes','estimated_text_tokens','repeated_exact_message_text_bytes','image_attachment_count','image_decoded_bytes']
    return {'http_requests':len(requests), **{name:sum(r[name] for r in requests) for name in names},
            'peak_wire_body_bytes':max((r['wire_body_bytes'] for r in requests),default=0)}

def run_case(root, name, chain=24):
    from app.litellm_runtime import LiteLLMRuntime
    from PIL import Image
    project = root/name/'project'
    source = project/'inputs/reference/source.png'
    source.parent.mkdir(parents=True)
    Image.new('RGB',(64,64),(30,80,140)).save(source)
    runtime = LiteLLMRuntime(root/name/'runtime', model='openai/local-scripted-model', max_tool_calls=64)
    runtime.session_api_key = 'local-fixture-not-a-credential'
    runtime.tool_surface.prepare(project_dir=project,mcp_enabled=False,model_path=None,model_guid='',ruby_enabled=False,ruby_state=None,tool_profile='reconstruction_coding',workspace_tools_enabled=True)
    notes = project/'runtime/agent_workspace/notes'
    (notes/'long.md').write_text('Observed fixture feature: wall unchanged, preserve baseline.\n'*400)
    if name == 'long_chain_checkpoint':
        path=notes/'construction_strategy.json'
        data=json.loads(path.read_text());data['current_stage']='primary_form';path.write_text(json.dumps(data))
    if name.startswith('long_chain'):
        replies=[tool_message('workspace_read',{'relative_path':'notes/long.md'},'read-'+str(i)) for i in range(chain)]
        replies += [{'role':'assistant','content':'Scripted chain complete; no model geometry was created.'}]
    elif name == 'tool_error_recovery':
        replies=[tool_message('workspace_read',{'relative_path':'../../forbidden'},'bad'),tool_message('workspace_read',{'relative_path':'notes/long.md'},'good'),{'role':'assistant','content':'Scripted correction complete.'}]
    elif name == 'http_503_no_retry':
        replies=[{'http_error':503}]
    else:
        replies=[{'role':'assistant','content':'First instruction recorded.'},{'role':'assistant','content':'Changed instruction recorded.'}]
    results=[]
    with ScriptedServer(replies) as server:
        runtime.custom_api_base=server.base_url
        thread=None
        prompts=['Only inspect the main building. KEEP wall unchanged.']
        if name == 'changed_instruction': prompts+=['NEW USER: only inspect roof now; do not add roads.']
        for prompt in prompts:
            try:
                result=runtime.respond(project_dir=project,thread_id=thread,prompt=prompt,mcp_enabled=False,ruby_enabled=False,developer_instructions='Deterministic local contract fixture. No geometry writes.',workflow_mode='image_reconstruction',tool_profile='reconstruction_coding')
                thread=result.thread_id
                results.append({'status':result.status,'tool_calls':result.tool_call_count,'failed_tool_calls':result.failed_tool_calls,'mock_reported_input_tokens':result.input_tokens})
            except Exception as error:
                partial=getattr(error,'partial_result',None)
                results.append({'status':'interrupted','error_type':type(error).__name__,'tool_calls':getattr(partial,'tool_call_count',0),'failed_tool_calls':getattr(partial,'failed_tool_calls',0)})
        requests=server.requests
    events=[json.loads(line) for p in (project/'runtime/agent_events').glob('*.jsonl') for line in p.read_text().splitlines()]
    report={'case':name,**summarize(requests),'results':results,'compacted_requests':sum(bool(e.get('context_compacted')) for e in events),
            'requests':requests,'events':events}
    (root/name/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return {k:v for k,v in report.items() if k not in {'requests','events'}}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--chain',type=int,default=24);parser.add_argument('--source-revision',help='Explicit archive provenance when .git is absent')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    os.environ['HOME']=str(args.output/'isolated-home');Path(os.environ['HOME']).mkdir(exist_ok=True)
    os.environ['LITELLM_LOCAL_MODEL_COST_MAP']='True'
    os.environ['NO_PROXY']='127.0.0.1,localhost'
    os.environ['KSTUDIO_EXECUTION_LIMITS']='on'
    sys.path.insert(0,str(args.repo.resolve()))
    cases=[run_case(args.output,name,args.chain) for name in ['long_chain_checkpoint','long_chain_no_checkpoint','tool_error_recovery','http_503_no_retry','changed_instruction']]
    report={'kind':'local deterministic HTTP simulation, not LLM reasoning or bill','estimator':ESTIMATOR,'vision_tokens':'NOT_ESTIMATED','actual_provider_cost':'NOT_RUN','repo_commit':args.source_revision or subprocess.check_output(['git','-C',str(args.repo),'rev-parse','HEAD'],text=True).strip(),'cases':cases}
    (args.output/'summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
