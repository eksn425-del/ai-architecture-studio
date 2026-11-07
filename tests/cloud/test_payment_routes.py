"""Authenticated web surface fixtures; no live merchant or payment is used."""
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import update

from cloud.config import Settings
from cloud.main import create_app
from cloud.db import migrate, orders, sessions, now
from cloud.auth import create_identity, new_session
from cloud.ledger import create_order
from cloud import wechat_payments as wx


@pytest.fixture
def surface(tmp_path):
    settings=Settings(database_url='sqlite:///'+str(tmp_path/'db.sqlite'),session_secret='test-session-secret-12345678901234567890',
                      environment='test',payment_provider='wechat_native',admin_subjects=('fixture|admin',))
    app=create_app(settings);engine=app.state.engine;migrate(engine)
    assert any(r.path=='/api/payments/wechat/notify' for r in app.routes), 'Root must register payment_routes'
    alice=create_identity(engine,'fixture|alice','Alice');bob=create_identity(engine,'fixture|bob','Bob')
    admin=create_identity(engine,'fixture|admin','Admin')
    order=create_order(engine,alice['id'],'fixture-order','fixture',{'amount':990,'currency':'cny','credits':1000})
    with engine.begin() as c:c.execute(update(orders).where(orders.c.id==order['id']).values(
        state='checkout',provider_session='wxnative:'+order['id'],checkout_url='weixin://wxpay/bizpayurl?pr=fixture'))
    def client(user):
        token,csrf=new_session(engine,user['id'],'browser',3600)
        c=TestClient(app);c.cookies.set('kstudio_session',token);c.headers['X-CSRF-Token']=csrf
        return c
    yield settings,engine,order,client(alice),client(bob),client(admin),alice,admin
    engine.dispose()


def test_qr_is_owned_no_store_and_no_provider_get(surface,monkeypatch):
    _,_,order,alice,bob,*_=surface
    def no_request(*args,**kwargs):raise AssertionError('GET must not call payment provider')
    monkeypatch.setattr(wx.Client,'request',no_request)
    url='/api/account/orders/'+order['id']+'/payment'
    assert bob.get(url).status_code==404
    response=alice.get(url)
    assert response.status_code==200 and response.headers['content-type'].startswith('image/svg+xml')
    assert response.headers['cache-control']=='no-store' and '<svg' in response.text


def test_query_close_ownership_and_csrf_before_dispatch(surface,monkeypatch):
    _,_,order,alice,bob,*_=surface;calls=[]
    def fake(*args):calls.append(args[-1]);return {'state':'checkout'}
    monkeypatch.setattr(wx,'query_order',fake);monkeypatch.setattr(wx,'close_order',fake)
    for action in ('query','close'):
        url='/api/account/orders/'+order['id']+'/'+action
        assert bob.post(url,json={}).status_code==404
        assert alice.post(url,json={},headers={'X-CSRF-Token':''}).status_code==403
        assert alice.post(url,json={}).status_code==200
    assert calls==[order['id'],order['id']]


def test_refund_admin_recent_auth_explicit_confirmation(surface,monkeypatch):
    _,engine,order,alice,_,admin,_,admin_user=surface;calls=[]
    def fake(*args,**kwargs):calls.append(kwargs);return {'state':'PROCESSING','completed':False}
    monkeypatch.setattr(wx,'request_refund',fake)
    url='/api/admin/orders/'+order['id']+'/refund'
    body={'confirm_order_id':order['id'],'reason':'Author explicitly approved this test refund'}
    assert alice.post(url,json=body).status_code==403
    assert admin.post(url,json={'reason':body['reason']}).status_code==400
    assert admin.post(url,json=body).status_code==200
    assert calls[0]['approved_by']==admin_user['id']
    with engine.begin() as c:c.execute(update(sessions).where(sessions.c.user_id==admin_user['id']).values(authenticated_at=now()-301))
    assert admin.post(url,json=body).status_code==403


def test_notify_never_acknowledges_unverified_or_unpersisted(surface,monkeypatch):
    _,_,_,alice,*_=surface
    def fail(*args):raise wx.PaymentError('fake signature')
    monkeypatch.setattr(wx,'receive_notification',fail)
    response=alice.post('/api/payments/wechat/notify',content=b'{}')
    assert response.status_code==400 and response.json()['code']=='FAIL'
    monkeypatch.setattr(wx,'receive_notification',lambda *args:'credited')
    response=alice.post('/api/payments/wechat/notify',content=b'{}')
    assert response.status_code==204 and not response.content
