"""Offline signed protocol fixtures; NOT production payment acceptance."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import re
import time
from types import SimpleNamespace

import httpx
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select, update

from cloud import wechat_payments as wx
from cloud.auth import create_identity
from cloud.db import engine_for, migrate, orders, wallets, payment_reconciliation
from cloud.ledger import create_order, audit_wallet, reserve, claim, settle, BillingError


@pytest.fixture
def system(tmp_path):
    merchant = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    provider = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = tmp_path/'merchant.pem'
    private.write_bytes(merchant.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    api_key = tmp_path/'apiv3.key';api_key.write_bytes(b'k'*32)
    material = tmp_path/'public.json'
    material.write_text(json.dumps({'keys': {'PUB_KEY_ID_fixture': provider.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()}}))
    settings = SimpleNamespace(payment_provider='wechat_native', prices_confirmed=True,
        wechatpay_mchid='1234567890', wechatpay_appid='wxfixture', wechatpay_merchant_serial='AABBCC',
        wechatpay_api_v3_key_file=str(api_key), wechatpay_merchant_private_key_file=str(private),
        wechatpay_verify_material_file=str(material), public_url='https://kstudio.example')
    engine=engine_for('sqlite:///'+str(tmp_path/'db.sqlite'));migrate(engine)
    alice=create_identity(engine,'fixture|wx-alice','Alice')
    bob=create_identity(engine,'fixture|wx-bob','Bob')
    order=create_order(engine,alice['id'],'new','test',{'amount':990,'currency':'cny','credits':1000})
    yield settings,engine,alice,bob,order,merchant,provider
    engine.dispose()


def signed(provider, raw, timestamp=None, serial='PUB_KEY_ID_fixture'):
    stamp=str(int(time.time()) if timestamp is None else timestamp);nonce='provider_nonce'
    sig=provider.sign(stamp.encode()+b'\n'+nonce.encode()+b'\n'+raw+b'\n',padding.PKCS1v15(),hashes.SHA256())
    return {'Wechatpay-Timestamp':stamp,'Wechatpay-Nonce':nonce,
            'Wechatpay-Serial':serial,'Wechatpay-Signature':base64.b64encode(sig).decode()}


def client_for(system, handler):
    settings,_,_,_,_,merchant,provider=system
    def mock(request):
        # Every actual request must have correct byte-exact merchant signature.
        fields=dict(re.findall(r'(\w+)="([^"]+)"',request.headers['authorization']))
        assert fields['mchid']==settings.wechatpay_mchid
        assert fields['serial_no']==settings.wechatpay_merchant_serial
        assert request.headers['Wechatpay-Serial']=='PUB_KEY_ID_fixture'
        canonical=request.method.encode()+b'\n'+request.url.raw_path+b'\n'+fields['timestamp'].encode()+b'\n'+fields['nonce_str'].encode()+b'\n'+request.content+b'\n'
        merchant.public_key().verify(base64.b64decode(fields['signature']),canonical,padding.PKCS1v15(),hashes.SHA256())
        code,data=handler(request)
        raw=b'' if data is None else json.dumps(data,separators=(',',':')).encode()
        return httpx.Response(code,content=raw,headers=signed(provider,raw))
    return wx.Client(settings,transport=httpx.MockTransport(mock))


def prepare(system):
    settings,e,_,_,order,*_=system
    client=client_for(system,lambda r:(200,{'code_url':'weixin://wxpay/bizpayurl?pr=fixture'}))
    result=wx.checkout(e,settings,order,client=client)
    assert result['provider']=='wechat_native' and result['checkout_url'] is None
    return client


def tx(system, **changes):
    settings,_,_,_,order,*_=system
    data={'appid':settings.wechatpay_appid,'mchid':settings.wechatpay_mchid,'out_trade_no':order['id'],
          'transaction_id':'WX_TRANSACTION_1','trade_state':'SUCCESS','amount':{'total':990,'currency':'CNY'},
          'payer':{'openid':'private-identity-must-not-be-stored'}}
    data.update(changes);return data


def notification(system,data,kind='TRANSACTION.SUCCESS',event_id='event-1'):
    cipher=AESGCM(b'k'*32).encrypt(b'123456789012',json.dumps(data).encode(),b'transaction')
    raw=json.dumps({'id':event_id,'event_type':kind,'resource_type':'encrypt-resource','resource':{
        'algorithm':'AEAD_AES_256_GCM','nonce':'123456789012','associated_data':'transaction',
        'ciphertext':base64.b64encode(cipher).decode()}}).encode()
    return raw,signed(system[-1],raw)


def pay(system):
    client=prepare(system);settings,e,*_=system
    raw,headers=notification(system,tx(system))
    assert wx.receive_notification(e,settings,raw,headers,client=client)=='credited'
    return client


def test_default_disabled_and_configuration_safe(system):
    settings,*_=system
    settings.payment_provider='disabled'
    assert not wx.enabled(settings)
    with pytest.raises(wx.PaymentError,match='not configured'):wx.Client(settings)
    settings.payment_provider='wechat_native';settings.prices_confirmed=False
    assert not wx.enabled(settings)


def test_checkout_signs_exact_bytes_and_records_identity_before_dispatch(system):
    settings,e,_,_,order,*_=system
    def handler(request):
        with e.connect() as c:
            row=c.execute(select(orders).where(orders.c.id==order['id'])).mappings().one()
            assert row['provider_session']=='wxnative:'+order['id']
        assert request.url.host=='api.mch.weixin.qq.com'
        body=json.loads(request.content)
        assert body['amount']=={'total':990,'currency':'CNY'}
        assert body['notify_url']=='https://kstudio.example/api/payments/wechat/notify'
        return 200,{'code_url':'weixin://wxpay/bizpayurl?pr=fixture'}
    assert wx.checkout(e,settings,order,client=client_for(system,handler))['state']=='checkout'


@pytest.mark.parametrize('attack',['body','expired','future','unknown-key','signature','nonce'])
def test_response_signature_and_freshness(system,attack):
    client=wx.Client(system[0]);raw=b'{"ok":true}';headers=signed(system[-1],raw)
    if attack=='body':raw=b'{"ok":false}'
    if attack=='expired':headers=signed(system[-1],raw,int(time.time())-301)
    if attack=='future':headers=signed(system[-1],raw,int(time.time())+301)
    if attack=='unknown-key':headers=signed(system[-1],raw,serial='PUB_KEY_ID_unknown')
    if attack=='signature':headers['Wechatpay-Signature']='bad!'
    if attack=='nonce':headers['Wechatpay-Nonce']='with\nnewline'
    with pytest.raises(wx.PaymentError):client.verify(raw,headers)


@pytest.mark.parametrize('change',[{'mchid':'another'},{'appid':'another'},
    {'amount':{'total':991,'currency':'CNY'}},{'amount':{'total':990,'currency':'USD'}},
    {'amount':{'total':990.0,'currency':'CNY'}},{'trade_state':'NOTPAY'}])
def test_signed_but_wrong_payment_identity_never_credits(system,change):
    client=prepare(system);settings,e,alice,*_=system
    raw,headers=notification(system,tx(system,**change))
    with pytest.raises(wx.PaymentError):wx.receive_notification(e,settings,raw,headers,client=client)
    assert audit_wallet(e,alice['id'])['balance']==0
    with e.connect() as c:assert not c.execute(select(wx.verified_payment_inbox)).first()


def test_duplicate_and_concurrent_callbacks_credit_once_no_payer_stored(system):
    client=prepare(system);settings,e,alice,*_=system
    raw,headers=notification(system,tx(system))
    def call(_):return wx.receive_notification(e,settings,raw,headers,client=client)
    with ThreadPoolExecutor(3) as pool:results=list(pool.map(call,range(3)))
    assert results.count('credited')==1
    wallet=audit_wallet(e,alice['id']);assert wallet['balance']==1000 and wallet['consistent']
    with e.connect() as c:
        rows=c.execute(select(wx.verified_payment_inbox)).mappings().all()
    assert len(rows)==1 and rows[0]['state']=='applied' and 'private-identity' not in rows[0]['payload']


def test_durable_inbox_survives_settlement_failure_and_replays(system,monkeypatch):
    client=prepare(system);settings,e,alice,*_=system
    raw,headers=notification(system,tx(system))
    original=wx.payment_paid
    def crash(*args):raise RuntimeError('simulated crash after durable verification')
    monkeypatch.setattr(wx,'payment_paid',crash)
    with pytest.raises(RuntimeError):wx.receive_notification(e,settings,raw,headers,client=client)
    with e.connect() as c:assert c.execute(select(wx.verified_payment_inbox.c.state)).scalar()=='pending'
    assert audit_wallet(e,alice['id'])['balance']==0
    monkeypatch.setattr(wx,'payment_paid',original)
    assert wx.recover_pending(e)[0]['result']=='credited'
    assert wx.recover_pending(e)==[]
    assert audit_wallet(e,alice['id'])['balance']==1000


def test_query_recovers_missed_notification_and_later_callback_is_duplicate(system):
    prepare(system);settings,e,alice,_,order,*_=system
    client=client_for(system,lambda r:(200,tx(system)))
    assert wx.query_order(e,settings,order['id'],client=client)['state']=='paid'
    raw,headers=notification(system,tx(system))
    assert wx.receive_notification(e,settings,raw,headers,client=client)=='duplicate'
    assert audit_wallet(e,alice['id'])['balance']==1000


def refund_data(system, refund_id, status='SUCCESS', amount=990):
    return {'out_trade_no':system[4]['id'],'transaction_id':'WX_TRANSACTION_1','out_refund_no':refund_id,
        'refund_id':'WX_REFUND_1','status':status,'amount':{'total':990,'refund':amount,'currency':'CNY'}}


def test_refund_requires_query_success_and_holds_credits_during_processing(system):
    pay(system);settings,e,alice,_,order,*_=system
    observed=[];state={'refund_id':None,'status':'PROCESSING'}
    def handler(request):
        if request.url.path.startswith('/v3/pay/'):
            return 200,tx(system)
        if request.method=='POST':
            state['refund_id']=json.loads(request.content)['out_refund_no']
            assert audit_wallet(e,alice['id'])['reserved']==1000
            observed.append('request')
            return 200,refund_data(system,state['refund_id'],'SUCCESS')
        observed.append('query')
        return 200,refund_data(system,state['refund_id'],state['status'])
    client=client_for(system,handler)
    result=wx.request_refund(e,settings,order['id'],client=client)
    assert result['completed'] is False and result['provider_state']=='PROCESSING'
    assert observed==['request','query']
    w=audit_wallet(e,alice['id']);assert w['balance']==1000 and w['reserved']==1000 and w['consistent']
    with pytest.raises(BillingError):reserve(e,alice['id'],'spend','byok','x',1,{'version':'v'})
    state['status']='SUCCESS'
    result=wx.query_refund(e,settings,state['refund_id'],client=client)
    assert result['completed'] and result['state']=='refunded'
    assert wx.query_refund(e,settings,state['refund_id'],client=client)['state']=='duplicate'
    w=audit_wallet(e,alice['id']);assert w['balance']==0 and w['reserved']==0 and w['consistent']


def test_unknown_refund_keeps_hold_and_does_not_resubmit(system):
    pay(system);settings,e,alice,_,order,*_=system
    calls=[]
    def handler(request):
        calls.append(request.method+' '+request.url.path)
        if request.url.path.startswith('/v3/pay/'):return 200,tx(system)
        raise httpx.ReadTimeout('simulated timeout',request=request)
    client=client_for(system,handler)
    first=wx.request_refund(e,settings,order['id'],client=client)
    assert first['state']=='UNKNOWN' and audit_wallet(e,alice['id'])['reserved']==1000
    with pytest.raises(wx.PaymentError):wx.request_refund(e,settings,order['id'],client=client)
    assert calls.count('POST /v3/refund/domestic/refunds')==1
    with e.connect() as c:assert len(c.execute(select(wx.wechat_refunds)).all())==1


def test_spent_credit_refund_rejected_before_any_refund_request(system):
    pay(system);settings,e,alice,_,order,*_=system
    task=reserve(e,alice['id'],'spend','byok','x',20,{'version':'v'})
    claim(e,alice['id'],task['id']);settle(e,alice['id'],task['id'],20)
    paths=[]
    def handler(request):paths.append(request.url.path);return 200,tx(system)
    with pytest.raises(wx.PaymentError,match='spent or reserved'):
        wx.request_refund(e,settings,order['id'],client=client_for(system,handler))
    assert paths==['/v3/pay/transactions/out-trade-no/'+order['id']]
    assert audit_wallet(e,alice['id'])['reserved']==0


def test_external_partial_refund_is_pending_not_fake_completion(system):
    client=pay(system);settings,e,alice,_,order,*_=system
    data=refund_data(system,'external-refund',amount=100)
    data['refund_status']=data.pop('status');data['mchid']=settings.wechatpay_mchid
    raw,headers=notification(system,data,'REFUND.SUCCESS','external-partial')
    assert wx.receive_notification(e,settings,raw,headers,client=client)=='refund_pending_reconciliation'
    assert wx.receive_notification(e,settings,raw,headers,client=client)=='refund_pending_reconciliation'
    with e.connect() as c:assert len(c.execute(select(payment_reconciliation)).all())==1
    assert audit_wallet(e,alice['id'])['balance']==1000


@pytest.mark.parametrize('state',['CLOSED','ABNORMAL'])
def test_refund_closed_releases_hold_but_abnormal_retains_it(system,state):
    pay(system);settings,e,alice,_,order,*_=system
    seen={}
    def handler(request):
        if request.url.path.startswith('/v3/pay/'):return 200,tx(system)
        if request.method=='POST':seen['id']=json.loads(request.content)['out_refund_no']
        return 200,refund_data(system,seen['id'],state)
    result=wx.request_refund(e,settings,order['id'],client=client_for(system,handler))
    assert not result['completed']
    w=audit_wallet(e,alice['id']);assert w['balance']==1000 and w['consistent']
    assert w['reserved']==(0 if state=='CLOSED' else 1000)


def test_close_requires_final_provider_query(system):
    prepare(system);settings,e,_,_,order,*_=system
    calls=[]
    def handler(request):
        calls.append(request.method)
        if request.method=='POST':return 204,None
        return 200,tx(system,trade_state='CLOSED')
    result=wx.close_order(e,settings,order['id'],client=client_for(system,handler))
    assert result['state']=='closed' and calls==['POST','GET']


def test_wrong_event_id_reuse_cannot_credit_another_transaction(system):
    client=pay(system);settings,e,alice,*_=system
    raw,headers=notification(system,tx(system,transaction_id='DIFFERENT_TRANSACTION'))
    with pytest.raises(wx.PaymentError,match='conflicts'):wx.receive_notification(e,settings,raw,headers,client=client)
    assert audit_wallet(e,alice['id'])['balance']==1000


def test_disabled_new_payments_still_accept_existing_notification(system):
    client=prepare(system);settings,e,alice,_,order,*_=system
    settings.payment_enabled=False;settings.prices_confirmed=False
    with pytest.raises(wx.PaymentError,match='disabled'):wx.checkout(e,settings,order,client=client)
    raw,headers=notification(system,tx(system))
    assert wx.receive_notification(e,settings,raw,headers)=='credited'
    assert audit_wallet(e,alice['id'])['balance']==1000


def test_official_refund_notification_without_currency_settles_held_refund_once(system):
    pay(system);settings,e,alice,_,order,*_=system
    observed={}
    def handler(request):
        if request.url.path.startswith('/v3/pay/'):return 200,tx(system)
        if request.method=='POST':observed['id']=json.loads(request.content)['out_refund_no']
        return 200,refund_data(system,observed['id'],'PROCESSING')
    client=client_for(system,handler)
    wx.request_refund(e,settings,order['id'],client=client,approved_by=alice['id'])
    data=refund_data(system,observed['id'])
    data['refund_status']=data.pop('status');data['mchid']=settings.wechatpay_mchid
    data['amount'].pop('currency')
    raw,headers=notification(system,data,'REFUND.SUCCESS','refund-success')
    def call(_):return wx.receive_notification(e,settings,raw,headers,client=client)
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(call,range(2)))
    assert results.count('refunded')==1
    w=audit_wallet(e,alice['id']);assert w['balance']==0 and w['reserved']==0 and w['consistent']
    with e.connect() as c:
        assert c.execute(select(wx.wechat_refunds.c.approved_by)).scalar()==alice['id']
