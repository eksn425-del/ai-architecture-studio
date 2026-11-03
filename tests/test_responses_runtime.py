from decimal import Decimal
from types import SimpleNamespace
import json

import pytest

from app.responses_runtime import ResponsesRuntime, ResponsesProfile, PilotBudget, responses_input
from app.native_agent import NativeAgentUnavailable


def budget(cap='10'):
    return PilotBudget(Decimal(cap), Decimal('2'), Decimal('10'), 200000, 1000, 8)


def reply(output=None, **kwargs):
    return {'id':'resp_1', 'model':'gpt-6.1-sol', 'status':'completed',
            'usage':{'input_tokens':100, 'output_tokens':25},
            'output':output or [{'type':'message','role':'assistant','content':[{'type':'output_text','text':'done'}]}], **kwargs}


def runtime(tmp_path, transport, profile=None, cap='10'):
    r=ResponsesRuntime(tmp_path, profile=profile, budget=budget(cap), transport=transport)
    r.session_api_key='not-a-real-secret'
    return r


def invoke(r, messages=None, **extra):
    return r._responses_completion(model='gpt-6.1-sol',api_key=r.session_api_key,
        messages=messages or [{'role':'user','content':'test'}],**extra)


def test_wire_images_tool_cycles_and_reasoning(tmp_path):
    sent=[]
    raw=[{'type':'reasoning','id':'rs1','encrypted_content':'opaque','summary':[]},
         {'type':'function_call','id':'fc1','call_id':'call1','name':'read','arguments':'{}'},
         {'type':'function_call','id':'fc2','call_id':'call2','name':'read','arguments':'{}'}]
    def transport(body, headers):
        sent.append((body,headers));return reply(raw) if len(sent)==1 else reply()
    r=runtime(tmp_path,transport)
    msgs=[{'role':'system','content':'Skill'}, {'role':'user','content':[
        {'type':'text','text':'source'}, {'type':'image_url','image_url':{'url':'data:image/png;base64,AA=='}}]}]
    result=invoke(r,msgs,tools=[{'type':'function','function':{'name':'read','parameters':{'type':'object'}}}],reasoning_effort='low')
    assert sent[0][0]['input'][1]['content'][1]['type']=='input_image'
    assert sent[0][0]['tools'][0]['name']=='read'
    assert sent[0][0]['store'] is False
    assert sent[0][0]['reasoning']=={'effort':'low'}
    msgs += [{'role':'assistant','responses_output':raw,'tool_calls':result.choices[0].message['tool_calls']},
             {'role':'tool','tool_call_id':'call1','content':'{"ok":true}'},
             {'role':'tool','tool_call_id':'call2','content':'{"ok":false,"error":"rejected"}'}]
    invoke(r,msgs)
    assert sent[1][0]['input'][2:5]==raw
    assert sent[1][0]['input'][-1]['call_id']=='call2'
    assert r.receipts[1]['actual_model']=='gpt-6.1-sol'


def test_tool_schema_included_in_input_envelope(tmp_path):
    sent=[]
    r=runtime(tmp_path,lambda *args:sent.append(args))
    r.budget=PilotBudget(Decimal('10'),Decimal('2'),Decimal('10'),1000,1000,8)
    with pytest.raises(NativeAgentUnavailable,match='Full request byte'):
        invoke(r,tools=[{'type':'function','function':{'name':'read',
            'description':'x'*1100,'parameters':{'type':'object'}}}])
    assert not sent and not r.receipts


@pytest.mark.parametrize('change',[
    {'model':'other'}, {'status':'incomplete'}, {'usage':None},
    {'output':[{'type':'function_call','call_id':'c','name':'bad','arguments':'[]'}]},
    {'output':[{'type':'function_call','call_id':'c','name':'bad','arguments':'{'}]},
    {'output':[{'type':'message','content':[{'type':'refusal','refusal':'no'}]}]},
    {'output':[{'type':'web_search_call'}]},
])
def test_invalid_provider_outputs_never_execute(tmp_path,change):
    r=runtime(tmp_path,lambda *_:reply(**change))
    with pytest.raises(NativeAgentUnavailable):invoke(r)
    assert len(r.receipts)==1


@pytest.mark.parametrize('error',[TimeoutError('timeout'),RuntimeError('HTTP 429'),RuntimeError('HTTP 500')])
def test_errors_no_retry_unknown_usage_breaker(tmp_path,error):
    calls=[]
    def transport(*_):calls.append(1);raise error
    r=runtime(tmp_path,transport)
    with pytest.raises(NativeAgentUnavailable):invoke(r)
    with pytest.raises(NativeAgentUnavailable):invoke(r)
    assert len(calls)==1 and r.unknown_usage


def test_budget_cancel_images_and_key_fail_closed(tmp_path):
    calls=[];r=runtime(tmp_path,lambda *_:calls.append(1),cap='0.01')
    with pytest.raises(NativeAgentUnavailable):invoke(r)
    assert not calls
    r=runtime(tmp_path,lambda *_:reply());r.cancelled.set()
    with pytest.raises(NativeAgentUnavailable):invoke(r)
    r.cancelled.clear();r.session_api_key=''
    with pytest.raises(NativeAgentUnavailable):invoke(r)
    r=runtime(tmp_path,lambda *_:reply(),ResponsesProfile(images=False))
    with pytest.raises(ValueError):invoke(r,[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/png;base64,AA=='}}]}])


def test_live_consent_not_implied_by_key(tmp_path,monkeypatch):
    monkeypatch.delenv('K_STUDIO_OPERATOR_LIVE_CONSENT',raising=False)
    r=runtime(tmp_path,None)
    assert not r.available
    with pytest.raises(NativeAgentUnavailable):invoke(r)
    assert not r.receipts


def test_full_shared_harness_tool_error_resume_and_project_context(tmp_path):
    calls=[]
    def transport(body,headers):
        calls.append(body)
        if len(calls)==1:return reply([{'type':'function_call','id':'fc','call_id':'c1','name':'probe','arguments':'{}'}])
        return reply()
    r=runtime(tmp_path,transport)
    executed=[]
    def dispatch(name,args):executed.append(name);raise ValueError('guarded tool failure')
    r.tool_surface=SimpleNamespace(prepare=lambda **_:SimpleNamespace(dynamic_tools=[{
        'name':'probe','description':'readonly','inputSchema':{'type':'object','properties':{}}}],quality_state={},dispatch=dispatch))
    p=tmp_path/'project';p.mkdir()
    kwargs=dict(project_dir=p,thread_id=None,prompt='source reconstruction',mcp_enabled=False,
                developer_instructions='Core Skill',architecture_skill_context='wall/opening Skill',workflow_mode='image_reconstruction')
    result=r.respond(**kwargs)
    assert result.tool_call_count==1 and result.failed_tool_calls==1
    assert executed==['probe']
    assert any(i.get('type')=='function_call_output' and i['call_id']=='c1' for i in calls[1]['input'])
    result2=r.respond(**{**kwargs,'thread_id':result.thread_id,'prompt':'modify same project'})
    assert result2.thread_id==result.thread_id
    assert 'source reconstruction' in json.dumps(calls[-1]) and 'Core Skill' in json.dumps(calls[-1])
    receipt=next((p/'runtime/responses_receipts').glob('*.json')).read_text()
    assert 'not-a-real-secret' not in receipt


def test_opaque_output_survives_history_roundtrip():
    raw=[{'type':'reasoning','encrypted_content':'opaque','summary':[]}, {'type':'function_call','call_id':'c','name':'x','arguments':'{}'}]
    msgs=[{'role':'assistant','responses_output':raw},{'role':'tool','tool_call_id':'c','content':'ok'}]
    assert responses_input(json.loads(json.dumps(msgs)),images=True)[0]==raw[0]
    with pytest.raises(ValueError):responses_input([{'role':'tool','tool_call_id':'orphan','content':'ok'}],images=True)


def test_dedicated_critic_has_images_and_no_writer_tools(tmp_path,monkeypatch):
    import app.litellm_runtime as harness
    from PIL import Image
    img=tmp_path/'inputs/reference/source.png';img.parent.mkdir(parents=True)
    Image.new('RGB',(8,8)).save(img)
    (tmp_path/'state').mkdir(exist_ok=True)
    (tmp_path/'state/project_context.json').write_text(json.dumps({'references': [{
        'type': 'image', 'source': 'inputs/reference/source.png', 'evidence_role': 'target_building'}]}))
    monkeypatch.setattr(harness,'discover_project_reference_images',lambda *_,**kw:[img])
    monkeypatch.setattr(harness,'validate_visual_review_views',lambda *_:({'scene':1},None,{v:img for v in harness.CANONICAL_REVIEW_VIEWS}))
    monkeypatch.setattr(harness,'validate_source_matched_pairs',lambda *_:[])
    requests=[];dispatches=[]
    def transport(body,headers):
        requests.append(body)
        if len(requests)==1:
            return reply([{'type':'function_call','call_id':'review1','name':'sketchup_submit_visual_review','arguments':'{"views":{}}'}])
        if len(requests)==2:
            return reply([{'type':'message','content':[{'type':'output_text','text':'NEEDS_FIX: NO\n<assessment>Mock view match</assessment>\n<keep>roof</keep><review_requirements>[]</review_requirements>'}]}])
        return reply()
    r=runtime(tmp_path,transport)
    def dispatch(name,args):dispatches.append(args);return {'success':True}
    r.tool_surface=SimpleNamespace(prepare=lambda **_:SimpleNamespace(dynamic_tools=[{'name':'sketchup_submit_visual_review','description':'review','inputSchema':{'type':'object'}}],quality_state={},dispatch=dispatch))
    result=r.respond(project_dir=tmp_path,thread_id=None,prompt='source',mcp_enabled=False,
        developer_instructions='Core',workflow_mode='image_reconstruction',tool_profile='reconstruction_coding',ruby_state={'scene':{'revision':1}})
    assert result.failed_tool_calls==0
    assert 'tools' not in requests[1]
    assert sum(b['type']=='input_image' for i in requests[1]['input'] for b in i.get('content',[]) if isinstance(b,dict))==7
    assert dispatches[0]['_reviewer']['mode']=='host_dedicated_read_only'


def test_cancellation_after_network_blocks_tool_output(tmp_path):
    r=None
    def transport(*_):r.cancelled.set();return reply([{'type':'function_call','call_id':'c','name':'write','arguments':'{}'}])
    r=runtime(tmp_path,transport)
    with pytest.raises(NativeAgentUnavailable,match='cancelled'):invoke(r)
    assert len(r.receipts)==1


def test_operator_router_no_codex_fallback(tmp_path,monkeypatch):
    from app.model_router import DeterministicModelRouter
    monkeypatch.setenv('ARCH_STUDIO_ECONOMY_PROVIDER','responses');monkeypatch.setenv('ARCH_STUDIO_STANDALONE','1')
    monkeypatch.delenv('K_STUDIO_OPERATOR_MAX_USD',raising=False)
    router=DeterministicModelRouter(SimpleNamespace(available=True,runtime_root=tmp_path))
    assert router.route('economy').provider=='managed-responses'
    assert not router.available
    with pytest.raises(NativeAgentUnavailable):router.respond(tier='economy',project_dir=tmp_path)


def test_receipt_write_failure_releases_turn_lock(tmp_path,monkeypatch):
    import app.litellm_runtime as harness
    r=runtime(tmp_path,lambda *_:reply())
    monkeypatch.setattr(harness.LiteLLMRuntime,'respond',lambda *_args,**_kwargs:None)
    def fail(_):raise OSError('disk unavailable')
    monkeypatch.setattr(r,'_persist_receipts',fail)
    with pytest.raises(OSError):r.respond(project_dir=tmp_path)
    assert r._run_lock.acquire(blocking=False)
    r._run_lock.release()
