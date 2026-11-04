import concurrent.futures, hashlib, hmac, json, time, os, uuid
import pytest
from sqlalchemy import select, update, text
from fastapi.testclient import TestClient
from cloud.config import Settings
from cloud.db import engine_for,migrate,orders,tasks,wallets,ledger,now
from cloud.auth import create_identity,new_session
from cloud.ledger import reserve,claim,settle,create_order,payment_paid,refund_confirmed,audit_wallet,BillingError
from cloud.main import create_app
from cloud.payments import verify_webhook,apply_event

PRICE={'version':'test-1','service_units':5,'input_units_per_million':1000,'output_units_per_million':2000}
@pytest.fixture(params=['sqlite','postgresql'])
def system(tmp_path,request):
    url='sqlite:///'+str(tmp_path/'db.sqlite')
    if request.param=='postgresql':
        base=os.getenv('KSTUDIO_TEST_POSTGRES_URL')
        if not base:pytest.skip('Explicit disposable PostgreSQL test URL not configured')
        schema='r2_'+uuid.uuid4().hex
        admin=engine_for(base)
        with admin.begin() as c:c.execute(text('CREATE SCHEMA '+schema))
        admin.dispose();url=base+'?options=-csearch_path%3D'+schema
    settings=Settings(database_url=url,session_secret='test-session-secret-not-for-production-123456',environment='test',prices_confirmed=True,prices={'version':'test-1','byok_task_units':5,'byok_service_enabled':True},stripe_webhook_secret='synthetic-webhook-secret')
    app=create_app(settings);engine=app.state.engine;migrate(engine)
    user=create_identity(engine,'fixture|alice','Alice');other=create_identity(engine,'fixture|bob','Bob')
    token,csrf=new_session(engine,user['id'],'browser',3600)
    client=TestClient(app);client.cookies.set('kstudio_session',token)
    client.headers.update({'X-CSRF-Token':csrf})
    yield settings,engine,user,other,client
    engine.dispose()
def credit(engine,user,units=100):
    order=create_order(engine,user,'payment-fixture','test',{'amount':100,'currency':'usd','credits':units})
    with engine.begin() as c:c.execute(update(orders).where(orders.c.id==order['id']).values(provider_session='cs_test_fixture'))
    payment_paid(engine,'evt_paid',order['id'],'pi_fixture',100,'usd','cs_test_fixture')
    return order
def test_atomic_concurrent_reservations_and_no_float(system):
    _,e,a,_,_=system;credit(e,a['id'],100)
    def run(k):
        try:return reserve(e,a['id'],k,'byok','provider',70,PRICE)['id']
        except BillingError:return None
    with concurrent.futures.ThreadPoolExecutor(2) as pool:result=list(pool.map(run,['one','two']))
    assert sum(x is not None for x in result)==1
    assert audit_wallet(e,a['id'])['consistent']
    assert audit_wallet(e,a['id'])['reserved']==70
    with pytest.raises(BillingError):reserve(e,a['id'],'float','byok','provider',1.1,PRICE)

def test_concurrent_idempotency_and_daily_cap(system):
    _,e,a,_,_=system;credit(e,a['id'],100)
    def run(_):return reserve(e,a['id'],'same-key','platform','fixture',70,PRICE)['id']
    with concurrent.futures.ThreadPoolExecutor(2) as pool:ids=list(pool.map(run,range(2)))
    assert ids[0]==ids[1] and audit_wallet(e,a['id'])['reserved']==70
    claim(e,a['id'],ids[0]);settle(e,a['id'],ids[0],50)
    with pytest.raises(BillingError):reserve(e,a['id'],'daily-limit','platform','fixture',30,PRICE,daily_limit=70)
    assert audit_wallet(e,a['id'])['reserved']==0

def test_schema_one_to_two_keeps_existing_session_and_balance(system):
    from cloud.db import schema_version
    _,e,a,_,c=system;credit(e,a['id'])
    with e.begin() as conn:
        conn.execute(text('DROP INDEX ix_sessions_refresh'))
        conn.execute(text('ALTER TABLE sessions DROP COLUMN refresh_hash'))
        conn.execute(text('ALTER TABLE sessions DROP COLUMN refresh_expires'))
        conn.execute(update(schema_version).values(version=1))
    migrate(e)
    assert c.get('/api/auth/me').json()['user']['id']==a['id']
    assert c.get('/api/account/usage').json()['balance']['balance']==100
    with e.connect() as conn:assert conn.execute(select(schema_version.c.version)).scalar()==2
def test_task_idempotency_claim_unknown_and_reconcile(system):
    _,e,a,_,_=system;credit(e,a['id'])
    t=reserve(e,a['id'],'one','platform','model',60,PRICE)
    assert reserve(e,a['id'],'one','platform','model',60,{**PRICE,'version':'changed'})['price_version']=='test-1'
    claim(e,a['id'],t['id'])
    with pytest.raises(BillingError):claim(e,a['id'],t['id'])
    settle(e,a['id'],t['id'],None)
    assert audit_wallet(e,a['id'])['reserved']==60
    with pytest.raises(BillingError):settle(e,a['id'],t['id'],25)
    settle(e,a['id'],t['id'],25,'provider invoice fixture',reconcile=True)
    settle(e,a['id'],t['id'],25)
    w=audit_wallet(e,a['id']);assert w['consistent'] and w['balance']==75 and w['reserved']==0
def test_payments_duplicate_mismatch_rollback_and_refund(system):
    _,e,a,_,_=system;order=credit(e,a['id'])
    assert payment_paid(e,'evt_paid',order['id'],'pi_fixture',100,'usd','cs_test_fixture')=='duplicate'
    assert payment_paid(e,'evt_other',order['id'],'pi_fixture',100,'usd','cs_test_fixture')=='duplicate'
    with pytest.raises(BillingError):payment_paid(e,'evt_bad',order['id'],'pi_other',100,'usd','cs_test_fixture')
    with pytest.raises(BillingError):payment_paid(e,'evt_wrong',order['id'],'pi_fixture',101,'usd','cs_test_fixture')
    assert audit_wallet(e,a['id'])['balance']==100
    refund_confirmed(e,order['id'],'refund_1',100)
    assert refund_confirmed(e,order['id'],'refund_1',100)=='duplicate'
    assert audit_wallet(e,a['id'])['consistent'] and audit_wallet(e,a['id'])['balance']==0

def test_spent_credit_refund_is_durably_pending(system):
    from cloud.db import payment_reconciliation
    _,e,a,_,c=system;order=credit(e,a['id'])
    task=reserve(e,a['id'],'spent','byok','fixture',20,PRICE);claim(e,a['id'],task['id']);settle(e,a['id'],task['id'],20)
    event={'id':'evt_refund_spent','type':'charge.refunded','data':{'object':{'payment_intent':'pi_fixture','refunded':True,'amount':100,'amount_refunded':100}}}
    assert apply_event(e,event)=='refund_pending_reconciliation'
    assert apply_event(e,event)=='refund_pending_reconciliation'
    with e.connect() as conn:
        assert len(conn.execute(select(payment_reconciliation)).all())==1
    assert c.get('/api/account/orders').json()['orders'][0]['state']=='refund_pending_reconciliation'
    assert audit_wallet(e,a['id'])['balance']==80
def signed(raw,secret,t=None):
    stamp=int(t or time.time());sig=hmac.new(secret.encode(),str(stamp).encode()+b'.'+raw,hashlib.sha256).hexdigest();return f't={stamp},v1={sig}'
def test_official_stripe_signature_replay_window_and_environment(system):
    s,e,a,_,_=system;order=create_order(e,a['id'],'stripe-key','test',{'amount':100,'currency':'usd','credits':100})
    with e.begin() as c:c.execute(update(orders).where(orders.c.id==order['id']).values(provider_session='cs_test_fixture'))
    payload={'id':'evt_signed','object':'event','type':'checkout.session.completed','livemode':False,'data':{'object':{'id':'cs_test_fixture','payment_status':'paid','payment_intent':'pi_fixture','amount_total':100,'currency':'usd','metadata':{'kstudio_order':order['id']},'client_reference_id':order['id']}}}
    raw=json.dumps(payload).encode();evt=verify_webhook(s,raw,signed(raw,s.stripe_webhook_secret));assert apply_event(e,evt)=='credited';assert apply_event(e,evt)=='duplicate'
    with pytest.raises(Exception):verify_webhook(s,raw+b' ',signed(raw,s.stripe_webhook_secret))
    with pytest.raises(Exception):verify_webhook(s,raw,signed(raw,s.stripe_webhook_secret,time.time()-600))
    payload['livemode']=True;raw=json.dumps(payload).encode()
    with pytest.raises(BillingError):verify_webhook(s,raw,signed(raw,s.stripe_webhook_secret))
def test_tenant_csrf_revocation_and_no_key_disclosure(system):
    _,e,a,b,c=system;credit(e,a['id'])
    bt,bc=new_session(e,b['id'],'second',3600)
    other=TestClient(c.app);other.cookies.set('kstudio_session',bt);other.headers['X-CSRF-Token']=bc
    assert other.get('/api/account/usage').json()['balance']['balance']==0
    assert other.get('/api/account/orders').json()['orders']==[]
    device=c.get('/api/account/devices').json()['devices'][0]['id']
    assert other.delete('/api/account/devices/'+device).status_code==404
    assert c.post('/api/auth/logout',headers={'X-CSRF-Token':'wrong'}).status_code==403
    assert c.post('/api/auth/logout',headers={'Origin':'https://attacker.invalid'}).status_code==403
    assert c.post('/api/auth/logout').status_code==200
    assert c.get('/api/account/usage').status_code==401
    assert 'synthetic-webhook-secret' not in other.get('/api/public/config').text
def test_byok_service_fee_only_and_restart_persistence(system):
    s,e,a,_,c=system;credit(e,a['id'])
    r=c.post('/api/tasks/byok',json={'idempotency_key':'test-task-1','price_version':'test-1'});assert r.status_code==200
    assert r.json()['upstream_charge_by_kstudio']==0
    assert c.post('/api/tasks/byok',json={'idempotency_key':'test-task-1','price_version':'test-1'}).json()['task_id']==r.json()['task_id']
    another=engine_for(s.database_url)
    assert audit_wallet(another,a['id'])['balance']==95
    assert audit_wallet(another,a['id'])['consistent'];another.dispose()
def test_rollback_of_financial_event(system):
    _,e,a,_,_=system;credit(e,a['id'])
    with pytest.raises(RuntimeError):
        with e.begin() as c:
            c.execute(update(wallets).where(wallets.c.user_id==a['id']).values(balance=999))
            raise RuntimeError('crash before commit')
    assert audit_wallet(e,a['id'])['balance']==100
def test_platform_only_one_active_reservation(system):
    _,e,a,_,_=system;credit(e,a['id'])
    reserve(e,a['id'],'one','platform','model',20,PRICE)
    with pytest.raises(BillingError):reserve(e,a['id'],'two','platform','model',20,PRICE)
    assert audit_wallet(e,a['id'])['reserved']==20
def test_config_blocks_public_sqlite_live_key_and_fake_login(system):
    s,e,a,_,c=system
    assert c.get('/api/auth/login').status_code==503
    assert c.get('/api/public/config').json()['release']['download_available'] is False
    with pytest.raises(ValueError):Settings(database_url='sqlite:///forbidden.sqlite',session_secret=s.session_secret,environment='production',public_url='https://test.invalid').validate()
    assert c.post('/api/feedback',json={'message':'实际问题反馈'}).status_code==200
