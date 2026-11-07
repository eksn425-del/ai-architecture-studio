"""Real route/session proof: refresh is never a fresh browser authentication."""
import base64
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from cloud import auth, device_auth, wechat_payments
from cloud.config import Settings
from cloud.db import migrate, now, sessions
from cloud.main import create_app
from cloud.ledger import BillingError


BODY={'label':'Fixture','provider':'fixture','protocol':'responses',
      'base_url':'https://api.example.invalid/v1','model_id':'model',
      'api_key':'fixture-secret-not-a-real-key','cloud_storage_consent':True}


@pytest.fixture
def system(tmp_path,monkeypatch):
    keys=tmp_path/'private-fixture-keys.json'
    keys.write_text(json.dumps({'v1':base64.b64encode(b'k'*32).decode()}))
    app=create_app(Settings(database_url='sqlite:///'+str(tmp_path/'db.sqlite'),
        session_secret='fixture-session-secret'+'x'*32,environment='test',
        vault_active_key_version='v1',vault_keys_file=str(keys),admin_subjects=('fixture|admin',)))
    engine=app.state.engine;migrate(engine);user=auth.create_identity(engine,'fixture|admin','Fixture')
    token,csrf=auth.new_session(engine,user['id'],'browser',3600,authenticated_at=now()-1200)
    browser=TestClient(app);browser.cookies.set('kstudio_session',token);browser.headers['X-CSRF-Token']=csrf
    calls=[]
    monkeypatch.setattr(wechat_payments,'request_refund',lambda *a,**k:calls.append(True) or {'fixture':True})
    yield app,engine,user,token,browser,calls
    browser.close();engine.dispose()


def approved_device(system):
    app,engine,_,_,browser,_=system
    proof='p'*48;pending=device_auth.start(engine,'browser',device_auth.challenge(proof))
    # An old but still signed-in browser can approve a device. Approval must
    # not turn its old IdP authentication into a recent sensitive-operation grant.
    assert browser.post('/api/auth/device/approve',json={'user_code':pending['user_code']}).status_code==200
    result=browser.post('/api/auth/device/poll',json={'device_code':pending['device_code'],'code_verifier':proof})
    assert result.status_code==200
    value=result.json();device=TestClient(app);device.headers['Authorization']='Bearer '+value['access_token']
    return value,device


def test_stale_browser_cannot_refresh_into_recent_payment_or_vault_authority(system):
    app,engine,_,token,browser,calls=system
    refund={'confirm_order_id':'fixture-order','reason':'Fixture authorization only'}
    assert browser.post('/api/admin/orders/fixture-order/refund',json=refund).status_code==403
    assert browser.post('/api/account/connections',json=BODY).status_code==403
    with TestClient(app) as bearer:
        bearer.headers['Authorization']='Bearer '+token
        assert bearer.post('/api/auth/refresh',json={}).status_code==400
        assert bearer.post('/api/admin/orders/fixture-order/refund',json=refund).status_code==403
        assert bearer.post('/api/account/connections',json=BODY).status_code==403
    assert now()-auth.lookup(engine,token)['authenticated_at']>=1200
    assert calls==[]


def test_device_rotation_preserves_identity_and_cannot_replay_or_create_browser(system):
    _,engine,_,_,_,_=system
    value,device=approved_device(system)
    original=auth.lookup(engine,value['access_token'])
    assert original['authenticated_at']==0 and original['refresh_hash']
    refreshed=device.post('/api/auth/refresh',json={})
    assert refreshed.status_code==200
    current=auth.lookup(engine,refreshed.json()['access_token'])
    for field in ('id','authenticated_at','refresh_hash','refresh_expires','device_name','csrf'):
        assert current[field]==original[field]
    assert auth.lookup(engine,value['access_token']) is None
    with pytest.raises(BillingError):device_auth.rotate(engine,original,3600)
    # The actual refresh secret still works and preserves auth_time/device ID.
    later=device.post('/api/auth/device/refresh',json={'refresh_token':value['refresh_token']})
    assert later.status_code==200
    last=auth.lookup(engine,later.json()['access_token'])
    assert last['id']==original['id'] and last['authenticated_at']==0 and last['refresh_hash']
    device.close()


def test_even_legacy_recent_device_cannot_manage_vault_or_refunds_using_cookie(system):
    app,engine,_,_,_,calls=system
    value,device=approved_device(system);row=auth.lookup(engine,value['access_token'])
    # Older device sessions may predate this fix; browser-only checks must hold
    # even if their auth_time is recent or their user-supplied name is 'browser'.
    with engine.begin() as c:c.execute(update(sessions).where(sessions.c.id==row['id']).values(authenticated_at=now()))
    for client in (device,TestClient(app)):
        if client is not device:
            client.cookies.set('kstudio_session',value['access_token']);client.headers['X-CSRF-Token']=row['csrf']
        assert client.post('/api/account/connections',json=BODY).status_code==403
        assert client.patch('/api/account/connections/anything',json={'label':'changed'}).status_code==403
        assert client.delete('/api/account/connections/anything').status_code==403
        assert client.get('/api/account/export').status_code==403
        assert client.post('/api/account/connections/anything/sync-grants',json={}).status_code==403
        assert client.post('/api/admin/orders/fixture-order/refund',json={}).status_code==403
        client.close()
    assert calls==[]


def test_fresh_browser_authorizes_same_device_restore_after_access_rotation(system):
    _,engine,user,_,browser,_=system
    value,device=approved_device(system)
    rotated=device.post('/api/auth/refresh',json={}).json()['access_token']
    device.headers['Authorization']='Bearer '+rotated;row=auth.lookup(engine,rotated)
    # Simulate only the already-tested verified IdP issuance boundary, not a
    # token refresh. Real IdP access is outside this offline security test.
    fresh,csrf=auth.new_session(engine,user['id'],'browser',3600,authenticated_at=now())
    browser.cookies.set('kstudio_session',fresh);browser.headers['X-CSRF-Token']=csrf
    saved=browser.post('/api/account/connections',json=BODY)
    assert saved.status_code==200
    grant=browser.post('/api/account/connections/'+saved.json()['id']+'/sync-grants',
        json={'device_id':row['id'],'confirm_device_restore':True})
    assert grant.status_code==200
    body={'sync_token':grant.json()['sync_token']}
    restored=device.post('/api/account/connections/restore',json=body)
    assert restored.status_code==200 and restored.json()['connection']['api_key']==BODY['api_key']
    assert device.post('/api/account/connections/restore',json=body).status_code==403
    device.close()
