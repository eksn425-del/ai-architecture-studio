"""R3 gateway admission, bounded tool-loop spending and honest usage receipts."""
import asyncio
import concurrent.futures
import json

import httpx
import pytest
from sqlalchemy import select

from cloud import gateway
from cloud.db import tasks
from cloud.ledger import BillingError, reserve, claim, settle, audit_wallet
from test_control_plane import system, credit, PRICE


def turn_reserve(engine,user,key,**overrides):
    options=dict(turn_id='visible-turn-001',turn_ceiling=60,max_turn_requests=90,max_concurrent=4)
    options.update(overrides)
    return reserve(engine,user,key,'platform','fixture',50,PRICE,**options)


def finish(engine,user,task,actual=8):
    claim(engine,user,task['id'])
    return settle(engine,user,task['id'],actual)


def test_shared_turn_budget_survives_new_request_ids_and_restart(system):
    _,engine,user,_,_=system;uid=user['id'];credit(engine,uid,500)
    first=turn_reserve(engine,uid,'request-one');finish(engine,uid,first)
    second=turn_reserve(engine,uid,'request-two');finish(engine,uid,second)
    # A third HTTP attempt cannot reset the visible turn budget. It must reserve
    # 50 on top of 16 already spent, even though the wallet still has ample funds.
    with pytest.raises(BillingError,match='turn budget'):turn_reserve(engine,uid,'request-three')
    assert audit_wallet(engine,uid)['balance']==484
    assert audit_wallet(engine,uid)['reserved']==0
    with engine.connect() as c:
        rows=c.execute(select(tasks).where(tasks.c.user_id==uid)).mappings().all()
        assert {json.loads(r['price_json'])['_turn']['id'] for r in rows}=={'visible-turn-001'}
    # Reconstructing the engine/process cannot lose a budget kept in the ledger.
    from cloud.db import engine_for
    second_engine=engine_for(engine.url.render_as_string(hide_password=False))
    try:
        with pytest.raises(BillingError,match='turn budget'):turn_reserve(second_engine,uid,'after-restart')
    finally:second_engine.dispose()


def test_turn_idempotency_precedes_budget_admission_and_cannot_change_turn(system):
    _,e,u,_,_=system;uid=u['id'];credit(e,uid)
    first=turn_reserve(e,uid,'same-request');finish(e,uid,first)
    assert turn_reserve(e,uid,'same-request')['id']==first['id']
    with pytest.raises(BillingError,match='another modeling turn'):
        turn_reserve(e,uid,'same-request',turn_id='different-turn')
    assert audit_wallet(e,uid)['balance']==92


def test_turn_request_count_and_original_limit_cannot_be_increased(system):
    _,e,u,_,_=system;uid=u['id'];credit(e,uid,500)
    first=turn_reserve(e,uid,'first',turn_ceiling=60,max_turn_requests=1);finish(e,uid,first,0)
    with pytest.raises(BillingError,match='request limit'):
        turn_reserve(e,uid,'second',turn_ceiling=500,max_turn_requests=90)
    assert audit_wallet(e,uid)['balance']==500


def test_turn_prices_and_model_are_frozen(system):
    _,e,u,_,_=system;uid=u['id'];credit(e,uid,500)
    first=turn_reserve(e,uid,'first');finish(e,uid,first,0)
    for model,price in [('another',PRICE),('fixture',{**PRICE,'version':'changed'})]:
        with pytest.raises(BillingError,match='model or price changed'):
            reserve(e,uid,'new-'+model+price['version'],'platform',model,50,price,turn_id='visible-turn-001',turn_ceiling=500)


def test_expired_turn_does_not_silently_renew(system,monkeypatch):
    import cloud.ledger as billing
    _,e,u,_,_=system;uid=u['id'];credit(e,uid,500)
    first=turn_reserve(e,uid,'first',turn_seconds=60);finish(e,uid,first,0)
    stamp=billing.now();monkeypatch.setattr(billing,'now',lambda:stamp+61)
    with pytest.raises(BillingError,match='expired'):turn_reserve(e,uid,'second')


def test_global_capacity_is_account_independent_and_released_on_settle(system):
    _,e,u,other,_=system;uid=u['id'];credit(e,uid)
    first=turn_reserve(e,uid,'first',max_concurrent=1)
    with pytest.raises(BillingError,match='capacity'):
        turn_reserve(e,other['id'],'second',max_concurrent=1)
    finish(e,uid,first)
    with pytest.raises(BillingError,match='Insufficient'):
        turn_reserve(e,other['id'],'second',max_concurrent=1)
    assert audit_wallet(e,uid)['consistent']


def test_concurrent_turn_request_only_one_reserves(system):
    _,e,u,_,_=system;uid=u['id'];credit(e,uid,500)
    def run(k):
        try:return turn_reserve(e,uid,k)['id']
        except BillingError:return None
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        rows=list(pool.map(run,['one','two']))
    assert sum(x is not None for x in rows)==1
    assert audit_wallet(e,uid)['reserved']==50
    assert audit_wallet(e,uid)['consistent']


def model_config():
    return {'enabled':True,'verified':True,'protocol':'responses','upstream_model':'fixture',
            'base_url':'https://fixture.invalid/v1','key_env':'R3_FIXTURE_KEY','max_output_tokens':4096,
            'reservation_units':50,'turn_budget_units':60,'max_turn_requests':2,'reasoning_effort':'low','price':PRICE}


@pytest.mark.parametrize('unverified',[False,None,'true',1])
def test_unverified_model_rejected_before_reservation_or_dispatch(system,unverified):
    s,e,u,_,client=system;credit(e,u['id']);s.models['public-model']={**model_config(),'verified':unverified}
    r=client.post('/api/platform/v1/responses',json={'model':'public-model','input':'test'},headers={'X-KStudio-Turn-ID':'visible-turn-001'})
    assert r.status_code==503
    with e.connect() as c:assert c.execute(select(tasks)).first() is None


def test_missing_turn_and_unconfirmed_prices_rejected(system):
    s,e,u,_,client=system;credit(e,u['id']);s.models['public-model']=model_config()
    assert client.post('/api/platform/v1/responses',json={'model':'public-model','input':'test'}).status_code==400
    s.prices_confirmed=False
    assert client.post('/api/platform/v1/responses',json={'model':'public-model','input':'test'},headers={'X-KStudio-Turn-ID':'visible-turn-001'}).status_code==503
    assert audit_wallet(e,u['id'])['reserved']==0


def test_actual_route_groups_sdk_tool_loop_and_bounds_cost(system,monkeypatch):
    s,e,u,_,client=system;uid=u['id'];credit(e,uid,500);s.models['public-model']=model_config()
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url);monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    original=httpx.AsyncClient;seen=[]
    def response(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200,text='data: {"type":"response.completed","response":{"model":"fixture","status":"completed","output":[],"usage":{"input_tokens":1000,"output_tokens":1000}}}\n\n')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(response),**kw))
    body={'model':'public-model','input':'test','stream':False,'reasoning':{'effort':'low'}}
    for key in ('one','two'):
        result=client.post('/api/platform/v1/responses',json=body,headers={'X-KStudio-Turn-ID':'visible-turn-001','Idempotency-Key':key})
        assert result.status_code==200 and result.headers['x-kstudio-turn']=='visible-turn-001'
    third=client.post('/api/platform/v1/responses',json=body,headers={'X-KStudio-Turn-ID':'visible-turn-001','Idempotency-Key':'three'})
    assert third.status_code==409 and len(seen)==2
    assert all(payload['model']=='fixture' and payload['reasoning']['effort']=='low' for payload in seen)
    assert audit_wallet(e,uid)['balance']==484


@pytest.mark.parametrize('timeouts',[{'total':0},{'connect':False},{'read':601},{'total':1801},{'total':10,'read':20},{'unknown':20}])
def test_operator_timeouts_are_bounded(timeouts):
    with pytest.raises(BillingError):gateway.timeout_policy({'timeouts':timeouts})


@pytest.mark.parametrize('status,category',[(401,'authentication'),(403,'authentication'),(402,'balance'),(429,'rate_limit'),(503,'provider_failure')])
def test_upstream_failure_distinctions_do_not_retry_or_fabricate_free_usage(system,monkeypatch,status,category):
    _,e,u,_,_=system;uid=u['id'];credit(e,uid);original=httpx.AsyncClient;seen=[]
    def response(request):seen.append(1);return httpx.Response(status,text='private upstream diagnostic not echoed')
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url);monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(response),**kw))
    task=turn_reserve(e,uid,'failure')
    async def run():return ''.join([x async for x in gateway.stream(e,uid,task,{},model_config())])
    output=asyncio.run(run())
    assert category in output and 'private upstream' not in output and len(seen)==1
    with e.connect() as c:
        receipt=c.execute(select(tasks).where(tasks.c.id==task['id'])).mappings().one()
        assert receipt['charged'] is None and receipt['state']=='pending_reconciliation'


def test_error_event_then_done_does_not_settle_as_success(system,monkeypatch):
    _,e,u,_,_=system;uid=u['id'];credit(e,uid);original=httpx.AsyncClient
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url);monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    payload='data: {"error":{"code":"provider_failed"},"usage":{"input_tokens":1,"output_tokens":1}}\n\ndata: [DONE]\n\n'
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(lambda request:httpx.Response(200,text=payload)),**kw))
    task=turn_reserve(e,uid,'failed-event')
    async def run():return [x async for x in gateway.stream(e,uid,task,{},model_config())]
    asyncio.run(run())
    with e.connect() as c:assert c.execute(select(tasks.c.state).where(tasks.c.id==task['id'])).scalar()=='pending_reconciliation'


def test_total_timeout_remains_bounded_with_stream_keepalives(system,monkeypatch):
    _,e,u,_,_=system;uid=u['id'];credit(e,uid);original=httpx.AsyncClient
    class KeepAlive(httpx.AsyncByteStream):
        async def __aiter__(self):
            while True:
                yield b': keepalive\n\n'
                await asyncio.sleep(.1)
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url);monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(lambda request:httpx.Response(200,stream=KeepAlive())),**kw))
    task=turn_reserve(e,uid,'deadline')
    async def run():return ''.join([x async for x in gateway.stream(e,uid,task,{}, {**model_config(),'timeouts':{'connect':1,'read':1,'total':1}})])
    output=asyncio.run(run())
    assert 'timeout' in output
    with e.connect() as c:assert c.execute(select(tasks.c.state).where(tasks.c.id==task['id'])).scalar()=='pending_reconciliation'


@pytest.mark.parametrize('payload',[{'reasoning':{'effort':'high'}},{'reasoning_effort':'high'},{'reasoning':{'effort':'low'},'reasoning_effort':'high'},{'thinking':{'type':'disabled'}},{'reasoning':{'budget_tokens':1}}])
def test_verified_effort_cannot_be_changed_before_reservation(system,payload):
    s,e,u,_,client=system;credit(e,u['id']);s.models['public-model']=model_config()
    result=client.post('/api/platform/v1/responses',json={'model':'public-model','input':'test',**payload},headers={'X-KStudio-Turn-ID':'effort-turn-001'})
    assert result.status_code==409
    with e.connect() as c:assert c.execute(select(tasks)).first() is None
    assert audit_wallet(e,u['id'])['balance']==100


def test_operator_switch_is_enforced_in_public_metadata_and_real_route(system):
    s,e,u,_,client=system;credit(e,u['id']);s.models['public-model']=model_config();s.platform_enabled=False
    assert client.get('/api/public/config').json()['models'][0]['enabled'] is False
    result=client.post('/api/platform/v1/responses',json={'model':'public-model','input':'test'},headers={'X-KStudio-Turn-ID':'switch-turn-001'})
    assert result.status_code==503
    with e.connect() as c:assert c.execute(select(tasks)).first() is None


def test_provider_default_never_becomes_low_and_explicit_config_is_applied():
    for protocol in ('responses','chat-completions'):
        value=gateway.apply_reasoning_policy({}, {'protocol':protocol,'reasoning_effort':'provider-default'})
        assert 'reasoning_effort' not in value and 'reasoning' not in value
        with pytest.raises(BillingError):gateway.apply_reasoning_policy({'reasoning_effort':'low'}, {'protocol':protocol,'reasoning_effort':'provider-default'})
        value=gateway.apply_reasoning_policy({}, {'protocol':protocol,'reasoning_effort':'high'})
        assert (value.get('reasoning',{}).get('effort') if protocol=='responses' else value.get('reasoning_effort'))=='high'


@pytest.mark.parametrize('full',[False,True])
def test_dsh_profile_retains_turn_header_in_both_profiles(tmp_path,full):
    from app.dsh_runtime import write_profile
    path=tmp_path/'profile.json'
    write_profile(path,api_base='https://gateway.fixture/api/platform/v1',model='public-model',full_capabilities=full,request_headers={'X-KStudio-Turn-ID':'visible-turn-001'})
    rows=json.loads(path.read_text(encoding='utf8'))
    provider=next(r for r in rows if r.get('id')=='llm-pi-ai')['config']['providers']['kstudio-bai']
    assert provider['headers']=={'X-KStudio-Turn-ID':'visible-turn-001'}
    with pytest.raises(ValueError):write_profile(path,api_base='https://gateway.fixture/v1',model='public-model',request_headers={'Authorization':'Bearer injected'})

def test_sdk_retry_without_request_key_is_one_charge_across_app_restart(system,monkeypatch):
    s,e,u,_,client=system
    credit(e,u['id'],500)
    s.models['public-model']=model_config()
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url)
    monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    original=httpx.AsyncClient
    calls=[]
    def response(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,text='data: {"type":"response.completed","response":{"id":"resp_fixture","model":"fixture","status":"completed","output":[],"usage":{"input_tokens":1000,"output_tokens":1000}}}\n\n')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(response),**kw))
    url='/api/platform/v1/responses'
    headers={'X-KStudio-Turn-ID':'sdk-retry-turn-001'}
    first=client.post(url,json={'model':'public-model','input':'same prompt','stream':False},headers=headers)
    assert first.status_code==200 and calls[0]['store'] is False

    from cloud.main import create_app
    from fastapi.testclient import TestClient
    s.session_secret='synthetic-key-rotation-for-existing-accounts'
    restarted=create_app(s)
    try:
        with TestClient(restarted,cookies=client.cookies,headers=dict(client.headers)) as next_client:
            duplicate=next_client.post(url,json={'stream':True,'input':'same prompt','model':'public-model'},headers=headers)
            assert duplicate.status_code==409
            assert duplicate.headers['x-kstudio-task']==first.headers['x-kstudio-task']
            assert len(calls)==1
            tool_loop=next_client.post(url,json={'model':'public-model','input':'later tool result','stream':False},headers=headers)
            assert tool_loop.status_code==200
            assert tool_loop.headers['x-kstudio-task']!=first.headers['x-kstudio-task']
            assert len(calls)==2
    finally:
        restarted.state.engine.dispose()
    assert audit_wallet(e,u['id'])['balance']==484


def test_request_key_cannot_alias_a_different_payload(system,monkeypatch):
    s,e,u,_,client=system
    credit(e,u['id'],500)
    s.models['public-model']=model_config()
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url)
    monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    original=httpx.AsyncClient
    seen=[]
    def response(request):
        seen.append(request)
        return httpx.Response(429)
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(response),**kw))
    headers={'X-KStudio-Turn-ID':'explicit-key-turn-001','Idempotency-Key':'fixed-key'}
    url='/api/platform/v1/responses'
    first=client.post(url,json={'model':'public-model','input':'one','stream':False},headers=headers)
    assert first.status_code==409
    duplicate=client.post(url,json={'model':'public-model','input':'one','stream':False},headers=headers)
    assert duplicate.status_code==409 and duplicate.headers['x-kstudio-task']==first.headers['x-kstudio-task']
    conflict=client.post(url,json={'model':'public-model','input':'two','stream':False},headers=headers)
    assert conflict.status_code==409 and 'different or unverified request' in conflict.json()['detail']
    assert len(seen)==1 and audit_wallet(e,u['id'])['reserved']==50


@pytest.mark.parametrize('content',[
    'data: {"type":"response.created","response":{"model":"fixture","usage":{"input_tokens":1,"output_tokens":1}}}\n\ndata: {"type":"response.completed","response":{"model":"fixture"}}\n\n',
    'data: {"type":"response.completed","response":{"model":"unexpected","usage":{"input_tokens":1,"output_tokens":1}}}\n\n',
    'data: {"type":"response.completed","response":{"model":"fixture","status":"completed","usage":{"input_tokens":1,"output_tokens":1}}}\n',
    'data: [DONE]\n\n',
    'data: {"type":"response.completed","response":{"model":"fixture","usage":{"input_tokens":1,"output_tokens":1}}}\n\n',
    'event: error\ndata: {"message":"private diagnostic"}\n\n',
    'data: {"type":"response.completed","response":{"model":"fixture","status":"completed","usage":{"input_tokens":50000,"output_tokens":50000}}}\n\n',
    'data: {"type":"response.completed","response":{"model":"fixture","status":"failed","usage":{"input_tokens":1,"output_tokens":1}}}\n\n',
])
def test_unverified_terminal_wire_contract_retains_hold_and_reports_error(system,monkeypatch,content):
    _,e,u,_,_=system
    uid=u['id'];credit(e,uid)
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url)
    monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    original=httpx.AsyncClient
    response=httpx.Response(200,text=content,headers={'x-request-id':'fixture-provider-request'})
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(lambda _:response),**kw))
    task=turn_reserve(e,uid,'unverified-terminal')
    async def run():return ''.join([frame async for frame in gateway.stream(e,uid,task,{},model_config())])
    result=asyncio.run(run())
    assert 'event: error' in result and 'private diagnostic' not in result
    assert 'response.completed' not in result and '[DONE]' not in result
    with e.connect() as c:
        row=c.execute(select(tasks).where(tasks.c.id==task['id'])).mappings().one()
        assert row['state']=='pending_reconciliation' and row['charged'] is None
        assert json.loads(row['price_json'])['_provider_receipt']['provider_request_id']=='fixture-provider-request'
    assert audit_wallet(e,uid)['reserved']==50


def test_framed_terminal_is_published_only_after_durable_metering(system,monkeypatch):
    _,e,u,_,_=system
    uid=u['id'];credit(e,uid)
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url)
    monkeypatch.setenv('R3_FIXTURE_KEY','fixture-not-secret')
    original=httpx.AsyncClient
    body=('event: response.completed\n'
          'data: {"type":"response.completed","response":\n'
          'data: {"id":"resp_fixture","model":"fixture","status":"completed","output":[],'
          '"usage":{"input_tokens":1000,"output_tokens":1000,"input_tokens_details":{"cached_tokens":137}}}}\n\n')
    response=httpx.Response(200,text=body,headers={'x-request-id':'provider-trace-001'})
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(lambda _:response),**kw))
    task=turn_reserve(e,uid,'verified-terminal')
    async def run():
        generator=gateway.stream(e,uid,task,{},model_config())
        terminal=await anext(generator)
        assert 'response.completed' in terminal
        with e.connect() as c:
            row=c.execute(select(tasks).where(tasks.c.id==task['id'])).mappings().one()
            assert row['state']=='settled' and row['charged']==8
            receipt=json.loads(row['price_json'])['_provider_receipt']
            assert receipt=={'provider_request_id':'provider-trace-001','provider_response_id':'resp_fixture',
                             'reported_model':'fixture','input_tokens':1000,'output_tokens':1000,'cached_input_tokens':137}
        await generator.aclose()
    asyncio.run(run())
    assert audit_wallet(e,uid)['reserved']==0


def test_reconcile_requires_recent_browser_admin_and_pending_status(system):
    s,e,u,other,client=system
    uid=u['id'];credit(e,uid)
    party=other['id']
    s.admin_subjects=(u['subject'],)
    task=turn_reserve(e,uid,'manual-reconcile')
    claim(e,uid,task['id'])
    url='/api/admin/tasks/'+task['id']+'/reconcile'
    payload={'actual_units':8,'reason':'Fixture upstream invoice reference'}
    assert client.post(url,json=payload).status_code==409  # active work may not be altered
    detail_url='/api/admin/tasks/'+task['id']+'/reconciliation'
    from cloud.ledger import remember_provider_receipt
    remember_provider_receipt(e,uid,task['id'],{'provider_request_id':'fixture-correlation'})
    settle(e,uid,task['id'],None)
    details=client.get(detail_url)
    assert details.status_code==200 and details.headers['cache-control']=='no-store'
    assert details.json()['provider_receipt']=={'provider_request_id':'fixture-correlation'}
    assert 'price_json' not in details.json() and 'user_id' not in details.json()
    from cloud.auth import new_session
    from cloud.db import now,sessions
    from fastapi.testclient import TestClient
    remote,csrf=new_session(e,party,'browser',3600)
    nonadmin=TestClient(client.app,cookies={'kstudio_session':remote},headers={'X-CSRF-Token':csrf})
    assert nonadmin.post(url,json=payload).status_code==403
    assert nonadmin.get(detail_url).status_code==403
    assert client.get(detail_url,headers={'Authorization':'Bearer '+client.cookies.get('kstudio_session')}).status_code==403
    assert client.post(url,json=payload,headers={'Authorization':'Bearer '+client.cookies.get('kstudio_session')}).status_code==403
    assert client.post(url,json={**payload,'actual_units':None}).status_code==400
    assert client.post(url,json={**payload,'actual_units':51}).status_code==409
    with e.begin() as c:c.execute(sessions.update().where(sessions.c.user_id==uid).values(authenticated_at=now()-301))
    assert client.post(url,json=payload).status_code==403
    token,csrf=new_session(e,uid,'browser',3600)
    reviewer=TestClient(client.app,cookies={'kstudio_session':token},headers={'X-CSRF-Token':csrf})
    for _ in range(2):
        result=reviewer.post(url,json=payload)
        assert result.status_code==200 and result.json()['charged']==8
        assert 'price_json' not in result.json()
    assert audit_wallet(e,uid)['balance']==92


def test_upstream_hosted_tools_are_outside_the_metered_route(system):
    s,e,u,_,client=system
    credit(e,u['id'])
    s.models['public-model']=model_config()
    result=client.post('/api/platform/v1/responses',json={'model':'public-model','input':'test','tools':[{'type':'web_search'}]},
                       headers={'X-KStudio-Turn-ID':'metered-tools-001'})
    assert result.status_code==400
    assert audit_wallet(e,u['id'])['reserved']==0
