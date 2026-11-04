"""Official full SDK transport plus a loopback host-tool plugin, no custom agent loop."""
from __future__ import annotations
import hmac
import json
import os
import secrets
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .native_agent import AgentTurnResult, NativeAgentUnavailable
from .codex_provider import redact
from .harness_task_anchor import task_anchor, runtime_failure_detail

def reported_usage(events):
    messages=[e.get('data',{}) for e in events if e.get('type')=='assistant/message']
    rows=[m.get('usage') for m in messages]
    # A length/transport failure can still have billed reasoning. The official
    # SDK stores its usage in assistant/attempt rather than assistant/message.
    for event in events:
        data=event.get('data',{})
        # Official agent-loop settles each request as either attempt OR message.
        # A later successful message at the same step is a separate billed retry.
        if event.get('type')!='assistant/attempt':continue
        chunks=[s.get('chunk',{}) for s in data.get('stream',[]) if isinstance(s,dict)]
        usage=[c.get('usage') for c in chunks if c.get('type')=='usage']
        rows.append(usage[-1] if usage else None)
    if not rows or any(not isinstance(r,dict) for r in rows):return None,None
    inputs=outputs=0
    for row in rows:
        incoming,outgoing=row.get('inputTokens'),row.get('outputTokens')
        if type(incoming) is not int or type(outgoing) is not int:return None,None
        total=row.get('totalTokens')
        inputs += total-outgoing if type(total) is int and total>=incoming+outgoing else incoming
        outputs += outgoing
    return inputs,outputs

DISABLED = "tool-plugin-manager plugin-manager config-editor settings remote-access typert-gateway deepseek-account llm-deepseek-account session-title-llm session-telemetry-otel tool-working-directory tool-bash tool-pwsh tool-jobs tool-fs tool-fs-search agent-instructions skill-filesystem tool-skill tool-subagent-control tool-subagent-list-agents tool-subagent tool-subagent-fork tool-workflow tool-goal tool-web tool-todo plan-mode workspace-dependencies skill-office".split()


def write_profile(path, *, api_base, model, protocol="openai-responses", max_tokens=None, full_capabilities=None, effective_configuration=None):
    from .dsh_full_profile import enabled, full_rows, provider_retry_policy
    if effective_configuration is None:
        from .dsh_configuration import resolve_configuration
        effective_configuration = resolve_configuration({'api_base':api_base, 'model':model, 'mode':'codex-responses' if protocol=='openai-responses' else 'compatible', 'reasoning_effort':'provider-default'})
    if enabled() if full_capabilities is None else full_capabilities:
        rows=full_rows(api_base=api_base, model=model, protocol=protocol, max_tokens=max_tokens,
                       host_plugin=Path(__file__).parent/'dsh_host_tools.mjs', effective_configuration=effective_configuration)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        return
    rows=[{"id":name,"disabled":True} for name in DISABLED]
    rows += [
        {"id":"llm-pi-ai","config":{"providers":{"kstudio-bai":{"apiKeyEnv":"KSTUDIO_DSH_API_KEY","api":protocol,"baseURL":api_base,
            "models":[effective_configuration.model_descriptor()],"retryPolicy":provider_retry_policy(effective_configuration.request_retries)}}}},
        {"id":"system-prompt","config":{"personaPrefix":"You are K Studio's architectural modeling assistant. Use only the provided protected SketchUp tools. Do not execute code or claim an unverified model is complete."}},
        {"id":"compaction-basic","config":effective_configuration.compaction()},
        {"insert":[{"id":"kstudio-host-tools","name":(Path(__file__).parent/"dsh_host_tools.mjs").as_posix()}]},
    ]
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")


class DSHHostSession:
    def __init__(self, *, home, workspace, api_base, api_key, model, specs, dispatch, trace_path,
                 sdk_site, dsh_bin, progress=None, protocol="openai-responses", instructions=None, max_tokens=None, reasoning_effort='high', full_capabilities=None, effective_configuration=None, source_manifest=None):
        if effective_configuration is None:
            from .dsh_configuration import resolve_configuration
            effective_configuration=resolve_configuration({'api_base':api_base,'model':model,'mode':'codex-responses' if protocol=='openai-responses' else 'compatible','reasoning_effort':reasoning_effort})
        if reasoning_effort != effective_configuration.requested_effort:
            raise ValueError('Reasoning effort differs from effective connection configuration')
        if max_tokens is not None and max_tokens!=effective_configuration.max_output_tokens:
            raise ValueError('Output limit differs from effective connection configuration')
        from .dsh_test_budget import TestBatchBudget
        self.test_budget=TestBatchBudget.configured(effective_configuration,workspace)
        self.source_manifest=source_manifest or []
        self.effective_configuration=effective_configuration
        max_tokens=effective_configuration.max_output_tokens
        self.reasoning_effort=reasoning_effort
        self.home,self.workspace=Path(home),Path(workspace)
        self.specs,self.dispatch,self.progress=specs,dispatch,progress
        self.api_key,self.model=api_key,model
        self.events=[];self.calls=[];self.inventory=None;self.cancelled=False
        from .dsh_interactions import Interactions
        self.interactions=Interactions()
        self.native_call_ids=set()
        self.task_anchor = ''
        from .dsh_full_profile import enabled
        self.full_capabilities = enabled() if full_capabilities is None else full_capabilities
        self.architecture_instructions = instructions if self.full_capabilities else None
        self.inventory_ready=threading.Event()
        self.dispatch_lock=threading.Lock()
        self.trace_path=Path(trace_path);self.trace_path.parent.mkdir(parents=True,exist_ok=True)
        self.token=secrets.token_urlsafe(32)
        parent=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_): pass
            def reply(self,data,status=200):
                body=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
                self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def authorized(self):
                return hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+parent.token)
            def do_GET(self):
                if not self.authorized(): return self.reply({},403)
                if self.path=='/control':
                    if parent.cancelled:parent.interactions.cancel()
                    return self.reply({'cancelled':parent.cancelled})
                if self.path.startswith('/interaction/'):
                    try:return self.reply(parent.interactions.get(self.path.rsplit('/',1)[-1]))
                    except ValueError:return self.reply({},404)
                if self.path=='/task': return self.reply({'text':parent.task_anchor,'instructions':parent.architecture_instructions,'test_budget_enabled':parent.test_budget is not None})
                if self.path!='/tools': return self.reply({},404)
                self.reply(parent.specs)
            def do_POST(self):
                if not self.authorized(): return self.reply({},403)
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=2_000_000:return self.reply({},413)
                try:
                    data=json.loads(self.rfile.read(size))
                    if self.path.startswith('/test-budget/'):
                        if parent.test_budget is None:raise ValueError('Finite test budget not enabled')
                        if self.path=='/test-budget/reserve':return self.reply(parent.test_budget.reserve(data))
                        if self.path=='/test-budget/settle':return self.reply(parent.test_budget.settle(data))
                        return self.reply({},404)
                    if self.path=='/interaction':
                        if parent.cancelled:raise ValueError('Turn cancelled')
                        row=parent.interactions.create(data)
                        parent.emit_progress({'event':'interaction_pending','kind':row['kind']})
                        return self.reply(row)
                    if self.path=='/interaction/cancel':
                        parent.interactions.cancel(data.get('id'));return self.reply({'ok':True})
                    if self.path=='/native-event':
                        if not parent.full_capabilities:raise ValueError('Native event requires full profile')
                        name=data['tool'];key=data['call_id']
                        if data['event']=='tool_result' and name not in {s['name'] for s in parent.specs} and key not in parent.native_call_ids:
                            parent.native_call_ids.add(key)
                            parent.calls.append({'name':name,'success':data.get('success') is True,'elapsed_ms':data.get('elapsed_ms')})
                        if name not in {s['name'] for s in parent.specs}:parent.emit_progress(data)
                        return self.reply({'ok':True})
                    if self.path=='/inventory':
                        from .dsh_full_profile import enabled
                        expected={s['name'] for s in parent.specs}
                        actual=set(data['names'])
                        if (not expected.issubset(actual) if parent.full_capabilities else expected!=actual):
                            raise ValueError('Required host tools missing or protected inventory differs')
                        parent.inventory=data['names'];parent.inventory_ready.set();return self.reply({'ok':True})
                    if self.path!='/call':return self.reply({},404)
                    if parent.cancelled:raise ValueError('Turn cancelled; no new tool started')
                    name=data['name']
                    if name not in {s['name'] for s in parent.specs}:raise ValueError('Unknown tool')
                    start=time.monotonic()
                    try:
                        with parent.dispatch_lock:
                            if parent.cancelled:raise ValueError('Turn cancelled; no new tool started')
                            parent.emit_progress({'event':'tool_started','tool':name})
                            result=parent.dispatch(name,data['arguments'])
                    except Exception as error:
                        result={'success':False,'error':redact(str(error),(parent.api_key,parent.token))}
                    event={'event':'host_tool_result','name':name,'success':result.get('success') is not False,'elapsed_ms':round((time.monotonic()-start)*1000)}
                    parent.calls.append(event);parent.record(event)
                    parent.emit_progress({'event':'tool_result','tool':name,'success':event['success'],'elapsed_ms':event['elapsed_ms']})
                    self.reply(result)
                except (ValueError,KeyError,TypeError) as error:
                    self.reply({'error':str(error)},400)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True);self.worker.start()
        patch=self.home/'kstudio.patch.yml'
        write_profile(patch,api_base=api_base,model=model,protocol=protocol,max_tokens=max_tokens,full_capabilities=self.full_capabilities,effective_configuration=self.effective_configuration)
        if instructions and not self.full_capabilities:
            rows=json.loads(patch.read_text(encoding='utf-8'))
            next(r for r in rows if r.get('id')=='system-prompt')['config']['personaPrefix']=instructions
            patch.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
        if str(sdk_site) not in sys.path:sys.path.insert(0,str(sdk_site))
        from deepseek_harness import DeepSeekHarness
        self.harness=DeepSeekHarness(provider='kstudio-bai',model=model,reasoning_effort=self.effective_configuration.sdk_effort,max_tokens=max_tokens,
            profile='sdk',patches=(str(patch),),dsh_home=str(self.home),cwd=str(self.workspace),dsh_bin=str(dsh_bin),
            env={'KSTUDIO_DSH_CAPABILITIES':'full' if self.full_capabilities else 'protected','KSTUDIO_DSH_EXECUTION_POLICY':__import__('app.dsh_security',fromlist=['execution_policy']).execution_policy(),'KSTUDIO_DSH_API_KEY':api_key,'KSTUDIO_TOOLS_TOKEN':self.token,'KSTUDIO_TOOLS_URL':f'http://127.0.0.1:{self.server.server_port}',
                 'DEEPSEEK_API_KEY':'','OPENAI_API_KEY':'','BAI_API_KEY':'','DSH_TELEMETRY_MODE':'DISABLED','DSH_MAX_TOKENS_AS_SUCCESS':'false'},
            initialize_timeout_seconds=40,request_timeout_seconds=90)

    def record(self,event):
        safe=redact(event,(self.api_key,self.token))
        with self.trace_path.open('a',encoding='utf-8') as f:f.write(json.dumps(safe,ensure_ascii=False,default=str)+'\n')

    def emit_progress(self,event):
        # The product reader consumes standard events; keep raw SDK receipts too.
        self.record(event)
        if self.progress:
            public=dict(event)
            if public['event']=='tool_result':public['event']='tool_completed'
            try:self.progress(public)
            except Exception:
                # A progress subscriber must never turn a committed write into a retry.
                self.record({'event':'progress_subscriber_failed'})

    def start(self):
        try:
            self.harness.start()
            self.inventory_ready.wait(5)
            if self.inventory is None:
                detail='\n'.join(getattr(self.harness.client,'_stderr_lines',[]))[-2500:]
                raise NativeAgentUnavailable('Full SDK did not register verified host tools: '+redact(detail,(self.api_key,self.token)))
        except BaseException:
            self.close()
            raise
        from .dsh_security import evidence
        self.record({'event':'runtime_initialized','engine':'deepseek-harness-sdk','profile':'sdk','tools':self.inventory,'execution_security':evidence()})

    def run(self, *, prompt, images, session_id=None):
        self.task_anchor = task_anchor(prompt)
        from .dsh_images import image_block
        if images and not self.effective_configuration.vision:
            raise NativeAgentUnavailable('当前连接尚未声明图像能力；请先在连接设置确认供应商能力，未发送图片。')
        if (self.specs or self.full_capabilities) and not self.effective_configuration.tools:
            raise NativeAgentUnavailable('当前连接尚未声明工具调用能力；未启动建模。')
        if not self.effective_configuration.streaming:
            raise NativeAgentUnavailable('当前连接尚未声明流式响应能力；DeepSeek Harness 需要供应商支持流式响应。')
        blocks=[{'type':'text','text':prompt}]
        for index,path in enumerate(images):
            block,receipt=image_block(path)
            blocks.append(block)
            self.record({'event':'source_image_prepared','order':index,'source_id':f'source_{index+1}',
                         'source_role':self.source_manifest[index].get('role','unknown') if index<len(self.source_manifest) else 'unknown',**receipt})
        self.record({'event':'effective_configuration',**self.effective_configuration.evidence()})
        self.start()
        session=self.harness.resume_session(session_id) if session_id else self.harness.start_session()
        def notify(note):
            if note.method=='session.event':
                event=note.payload.get('event',{})
                self.events.append(event);self.record(event)
                if event.get('type')=='assistant/message':
                    self.emit_progress({'event':'provider_response'})
                if self.progress:self.emit_progress({'event':'dsh_activity','type':event.get('type')})
        start=time.monotonic()
        self.record({'event':'session_bound','session_id':session.id,'resumed':bool(session_id)})
        self.emit_progress({'event':'provider_started'})
        try:
            result=session.run(blocks,on_notification=notify)
        except Exception as error:
            failure=NativeAgentUnavailable(redact(str(error),(self.api_key,self.token)))
            incoming,outgoing=reported_usage(self.events)
            failure.partial_result=AgentTurnResult(thread_id=session.id,reply='',status='failed',provider_name='deepseek-harness',model_name=self.model,
                reasoning_effort=self.reasoning_effort,region='user-configured (unverified)',latency_ms=round((time.monotonic()-start)*1000),
                tool_call_count=len(self.calls),failed_tool_calls=sum(not c['success'] for c in self.calls),
                input_tokens=incoming,output_tokens=outgoing,
                tool_calls=[{'tool':c['name'],'status':'completed' if c['success'] else 'failed'} for c in self.calls])
            self.record({'event':'turn_failed','error':str(failure),'elapsed_ms':failure.partial_result.latency_ms,
                'tool_call_count':len(self.calls),'input_tokens':incoming,'output_tokens':outgoing})
            raise failure from error
        incoming,outgoing=reported_usage(result.events)
        turn=AgentTurnResult(thread_id=result.session_id,reply=result.final_response,provider_name='deepseek-harness',model_name=self.model,
            reasoning_effort=self.reasoning_effort,region='user-configured (unverified)',latency_ms=round((time.monotonic()-start)*1000),tool_call_count=len(self.calls),
            input_tokens=incoming,output_tokens=outgoing,tool_calls=[{'tool':c['name'],'status':'completed' if c['success'] else 'failed'} for c in self.calls],
            status='interrupted' if self.cancelled else 'completed',cancellation_requested=self.cancelled,
            failed_tool_calls=sum(not c['success'] for c in self.calls))
        if result.finish_reason not in {'completed'}:
            turn.status='interrupted' if self.cancelled else 'failed'
            detail=redact(runtime_failure_detail(result.events),(self.api_key,self.token))
            failure=NativeAgentUnavailable(f'Official DeepSeek Harness ended with {result.finish_reason}; {detail}; committed model work is preserved.')
            failure.partial_result=turn
            self.record({'event':'turn_failed','error':str(failure),'elapsed_ms':turn.latency_ms,
                'tool_call_count':len(self.calls),'input_tokens':incoming,'output_tokens':outgoing})
            raise failure
        return turn

    def close(self):
        self.interactions.cancel()
        try:self.harness.close()
        finally:
            self.server.shutdown();self.server.server_close();self.worker.join(3)
            if self.test_budget is not None:self.test_budget.close()
