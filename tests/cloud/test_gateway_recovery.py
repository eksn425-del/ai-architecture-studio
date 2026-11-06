import asyncio,json,socket
import httpx,pytest
from sqlalchemy import update,select
from cloud import gateway
from cloud.db import tasks,now
from cloud.ledger import reserve,claim,audit_wallet,BillingError
from cloud.recovery import recover_stale
from test_control_plane import system,credit,PRICE

def test_gateway_known_and_unknown_usage(system,monkeypatch):
    _,engine,user,_,_=system;credit(engine,user['id'],100)
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url)
    monkeypatch.setenv('KSTUDIO_TEST_UPSTREAM','synthetic-key')
    model={'base_url':'https://unit.invalid/v1','key_env':'KSTUDIO_TEST_UPSTREAM','protocol':'chat-completions','upstream_model':'fixture'}
    original=httpx.AsyncClient
    async def response(request):
        assert request.headers['authorization']=='Bearer synthetic-key'
        assert json.loads(request.content)['model']=='fixture'
        return httpx.Response(200,text='data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: {"usage":{"prompt_tokens":1000,"completion_tokens":1000}}\n\ndata: [DONE]\n\n')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(response),**kw))
    async def run(task):return ''.join([x async for x in gateway.stream(engine,user['id'],task,{'messages':[]},model)])
    task=reserve(engine,user['id'],'known','platform','fixture',50,PRICE)
    assert 'ok' in asyncio.run(run(task))
    assert audit_wallet(engine,user['id'])['balance']==92
    async def interrupted(request):raise httpx.ReadTimeout('ambiguous upstream timeout')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(interrupted),**kw))
    task=reserve(engine,user['id'],'unknown','platform','fixture',50,PRICE)
    assert 'UPSTREAM_UNAVAILABLE' in asyncio.run(run(task))
    assert audit_wallet(engine,user['id'])['reserved']==50
    with engine.connect() as c:assert c.execute(select(tasks.c.state).where(tasks.c.id==task['id'])).scalar()=='pending_reconciliation'

def test_gateway_does_not_retry_429(system,monkeypatch):
    _,e,u,_,_=system;credit(e,u['id']);calls=[]
    original=httpx.AsyncClient
    def rejected(request):calls.append(1);return httpx.Response(429,headers={'Retry-After':'60'})
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(rejected),**kw))
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url);monkeypatch.setenv('KSTUDIO_TEST_UPSTREAM','fixture')
    t=reserve(e,u['id'],'rate-limit','platform','fixture',50,PRICE)
    async def run():return ''.join([x async for x in gateway.stream(e,u['id'],t,{}, {'base_url':'https://fixture.invalid','key_env':'KSTUDIO_TEST_UPSTREAM','protocol':'responses','upstream_model':'fixture'})])
    assert 'UPSTREAM_429' in asyncio.run(run()) and len(calls)==1
    assert audit_wallet(e,u['id'])['reserved']==50

def test_ssrf_and_usage_validation(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))])
    for url in ('https://private.invalid/v1','http://public.invalid','https://user:secret@public.invalid'):
        with pytest.raises(BillingError):gateway.validate_upstream(url)
    assert gateway.cost(PRICE,{'input_tokens':1.5,'output_tokens':1}) is None
    assert gateway.cost(PRICE,None) is None

def test_csrf_unrecognized_authorization_not_bypass_and_body_limit(system):
    config,_,_,_,client=system
    client.headers.pop('X-CSRF-Token')
    assert client.post('/api/auth/logout',headers={'Authorization':'Basic invalid'}).status_code==403
    config.max_request_bytes=20
    assert client.post('/api/feedback',content=(b'x'*10 for _ in range(3))).status_code==413

def test_crash_recovery_releases_only_undispatched(system):
    _,e,u,_,_=system;credit(e,u['id'])
    first=reserve(e,u['id'],'stale-reserved','byok','fixture',20,PRICE)
    second=reserve(e,u['id'],'stale-running','byok','fixture',30,PRICE);claim(e,u['id'],second['id'])
    with e.begin() as c:c.execute(update(tasks).values(updated=now()-1000))
    result=recover_stale(e)
    assert {x['outcome'] for x in result}=={'released_without_dispatch','pending_reconciliation'}
    assert audit_wallet(e,u['id'])['reserved']==30
    assert recover_stale(e)==[]

def test_authlib_pkce_uses_s256():
    from authlib.integrations.httpx_client import OAuth2Client
    from urllib.parse import urlparse,parse_qs
    client=OAuth2Client('fixture',code_challenge_method='S256')
    url,state=client.create_authorization_url('https://id.example/authorize',code_verifier='a'*64)
    params=parse_qs(urlparse(url).query)
    assert params['code_challenge_method']==['S256'] and params['code_challenge']!=['a'*64] and state

def test_cancelled_stream_never_fabricates_zero_usage(system,monkeypatch):
    _,e,u,_,_=system;credit(e,u['id']);original=httpx.AsyncClient
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url);monkeypatch.setenv('KSTUDIO_TEST_UPSTREAM','fixture')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(lambda req:httpx.Response(200,text='data: {"choices":[{"delta":{"content":"partial"}}]}\n\ndata: [DONE]\n\n')),**kw))
    task=reserve(e,u['id'],'cancelled','platform','fixture',50,PRICE)
    async def run():
        stream=gateway.stream(e,u['id'],task,{}, {'base_url':'https://fixture.invalid','key_env':'KSTUDIO_TEST_UPSTREAM','protocol':'chat-completions','upstream_model':'fixture'})
        assert 'partial' in await anext(stream)
        await stream.aclose()
    asyncio.run(run())
    with e.connect() as c:
        row=c.execute(select(tasks).where(tasks.c.id==task['id'])).mappings().one()
        assert row['charged'] is None and row['state']=='pending_reconciliation'
    assert audit_wallet(e,u['id'])['reserved']==50

@pytest.mark.parametrize('chunk',['event: error\ndata: {"code":"UPSTREAM_429"}\n\n','data: {"choices":[{"delta":{"content":"incomplete"}}]}\n\n'])
def test_nonstream_error_or_interruption_is_not_false_success(chunk):
    async def source():yield chunk
    with pytest.raises(BillingError):asyncio.run(gateway.collect(source(),'chat-completions'))
