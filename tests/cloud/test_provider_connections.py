"""Deterministic account-vault acceptance; no external IdP, provider or payment."""
import base64
import concurrent.futures
import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from cloud import auth
from cloud.db import engine_for, metadata, sessions, now
from cloud.credential_crypto import CredentialCipher, CredentialCryptoError
from cloud.provider_connections import ConnectionService, connections, sync_grants, register_routes


SECRET='fixture-only-provider-key-123456789'
BODY={'label':'My BAI','provider':'BAI','protocol':'responses','base_url':'https://api.b.ai/v1',
      'model_id':'deepseek-v4.1-flash','reasoning_effort':'low','api_key':SECRET,'cloud_storage_consent':True}


@pytest.fixture
def vault(tmp_path):
    engine=engine_for('sqlite:///'+str(tmp_path/'vault.sqlite'))
    metadata.create_all(engine)
    a=auth.create_identity(engine,'fixture|a','Alice');b=auth.create_identity(engine,'fixture|b','Bob')
    cipher=CredentialCipher({'one':b'1'*32},'one');service=ConnectionService(engine,cipher)
    device_token,_=auth.new_session(engine,a['id'],'Windows A',3600)
    second_token,_=auth.new_session(engine,a['id'],'Windows B',3600)
    for token in (device_token,second_token):
        with engine.begin() as c:c.execute(update(sessions).where(sessions.c.token_hash==auth.digest(token)).values(refresh_hash=auth.digest(token+'refresh')))
    d=auth.lookup(engine,device_token);d2=auth.lookup(engine,second_token)
    yield engine,service,a,b,d,d2,tmp_path
    engine.dispose()


def test_cipher_aad_random_nonce_and_version_rotation(vault):
    e,s,a,b,d,_,_=vault
    one=s.save(a['id'],BODY);two=s.save(a['id'],BODY)
    with e.connect() as c:rows=[dict(x) for x in c.execute(select(connections)).mappings()]
    assert rows[0]['ciphertext']!=rows[1]['ciphertext'] and rows[0]['nonce']!=rows[1]['nonce']
    assert SECRET not in json.dumps(rows)
    row=rows[0]
    assert s.cipher.decrypt(row)==SECRET
    for change in ({'user_id':b['id']},{'id':two['id']},{'key_version':'unknown'}):
        with pytest.raises(CredentialCryptoError):s.cipher.decrypt({**row,**change})
    s.cipher=CredentialCipher({'one':b'1'*32,'two':b'2'*32},'two')
    assert s.rotate_keys()['rotated']==2
    with e.connect() as c:new=dict(c.execute(select(connections).where(connections.c.id==one['id'])).mappings().one())
    assert new['key_version']=='two' and s.cipher.decrypt(new)==SECRET


def test_key_file_invalid_fails_without_leaking_values(tmp_path):
    f=tmp_path/'keys.json';f.write_text(json.dumps({'v1':'bad-secret-file-content'}))
    with pytest.raises(CredentialCryptoError,match='unavailable or invalid') as exc:CredentialCipher.from_file(str(f),'v1')
    assert 'bad-secret' not in str(exc.value)
    f.write_text(json.dumps({'v1':base64.b64encode(b'K'*32).decode()}))
    assert CredentialCipher.from_file(str(f),'v1').active_version=='v1'


def test_opt_in_cross_account_no_secret_list_and_destination_change(vault):
    e,s,a,b,d,_,_=vault
    with pytest.raises(HTTPException):s.save(a['id'],{**BODY,'cloud_storage_consent':False})
    item=s.save(a['id'],BODY)
    assert SECRET not in json.dumps(item) and item['secret_mask'].endswith('6789')
    assert s.list(b['id'])['connections']==[]
    with pytest.raises(HTTPException) as denied:s.save(b['id'],{'label':'stolen'},item['id'])
    assert denied.value.status_code==404
    with pytest.raises(HTTPException):s.remove(b['id'],item['id'])
    with pytest.raises(HTTPException):s.save(a['id'],{'base_url':'https://other.example/v1'},item['id'])
    assert s.save(a['id'],{'label':'Renamed'},item['id'])['label']=='Renamed'
    assert SECRET not in json.dumps(s.export_metadata(a['id']))


def test_sync_is_one_use_and_bound_to_account_device_and_connection_version(vault):
    e,s,a,b,d,d2,_=vault
    item=s.save(a['id'],BODY);grant=s.issue_grant(a['id'],item['id'],d['id'])
    for user,device in ((b['id'],d['id']),(a['id'],d2['id'])):
        with pytest.raises(HTTPException):s.redeem(user,device,grant['sync_token'])
    result=s.redeem(a['id'],d['id'],grant['sync_token'])
    assert result['connection']['api_key']==SECRET
    with pytest.raises(HTTPException):s.redeem(a['id'],d['id'],grant['sync_token'])
    old=s.issue_grant(a['id'],item['id'],d['id'])
    s.save(a['id'],{'label':'Changed'},item['id'])
    with pytest.raises(HTTPException):s.redeem(a['id'],d['id'],old['sync_token'])


def test_expired_deleted_and_revoked_device_grants_fail(vault):
    e,s,a,b,d,d2,_=vault
    item=s.save(a['id'],BODY);g=s.issue_grant(a['id'],item['id'],d['id'])
    with e.begin() as c:c.execute(update(sync_grants).values(expires_at=now()-1))
    with pytest.raises(HTTPException):s.redeem(a['id'],d['id'],g['sync_token'])
    g=s.issue_grant(a['id'],item['id'],d['id']);auth.revoke(e,a['id'],d['id'])
    with pytest.raises(HTTPException):s.redeem(a['id'],d['id'],g['sync_token'])
    g=s.issue_grant(a['id'],item['id'],d2['id']);s.remove(a['id'],item['id'])
    with pytest.raises(HTTPException):s.redeem(a['id'],d2['id'],g['sync_token'])


def test_concurrent_redemption_returns_secret_once(vault):
    e,s,a,b,d,_,_=vault
    item=s.save(a['id'],BODY);g=s.issue_grant(a['id'],item['id'],d['id'])
    def redeem(_):
        try:return s.redeem(a['id'],d['id'],g['sync_token'])
        except HTTPException:return None
    with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(redeem,range(2)))
    assert sum(x is not None for x in results)==1


def test_private_data_clear_is_precise_not_fake_full_account_deletion(vault):
    e,s,a,b,d,_,_=vault
    item=s.save(a['id'],BODY);s.issue_grant(a['id'],item['id'],d['id'])
    result=s.delete_private_data(a['id'])
    assert result['private_credentials_deleted']==1 and result['full_account_deleted'] is False
    assert s.list(a['id'])['connections']==[]
    with e.connect() as c:assert c.execute(select(sessions.c.revoked).where(sessions.c.id==d['id'])).scalar_one()==1


def test_http_recent_browser_authorizes_device_only_and_no_store(vault):
    e,s,a,b,d,_,tmp=vault
    keyfile=tmp/'keys.json';keyfile.write_text(json.dumps({'one':base64.b64encode(b'1'*32).decode()}))
    app=FastAPI()
    def identity(request):
        row=auth.lookup(e,request.headers.get('authorization','').removeprefix('Bearer ') or request.cookies.get('session'))
        if not row:raise HTTPException(401,'login required')
        return row
    async def body(request):return await request.json()
    register_routes(app,e,SimpleNamespace(vault_keys_file=str(keyfile),vault_active_key_version='one'),identity,body,lambda *args:None)
    browser=TestClient(app);token,_=auth.new_session(e,a['id'],'browser',3600);browser.cookies.set('session',token)
    item=browser.post('/api/account/connections',json=BODY).json()
    issued=browser.post('/api/account/connections/'+item['id']+'/sync-grants',json={'device_id':d['id'],'confirm_device_restore':True})
    assert issued.status_code==200
    # A browser cannot redeem even its own authorization.
    assert browser.post('/api/account/connections/restore',json=issued.json()).status_code==403
    with e.begin() as c:c.execute(update(sessions).where(sessions.c.token_hash==auth.digest(token)).values(authenticated_at=now()-601))
    assert browser.patch('/api/account/connections/'+item['id'],json={'label':'No'}).status_code==403
    assert browser.get('/api/account/connections').status_code==200


def test_integrated_routes_csrf_device_restore_and_cache_control(vault):
    from cloud.config import Settings
    from cloud.main import create_app
    e,s,a,b,d,_,tmp=vault
    keyfile=tmp/'integrated-keys.json';keyfile.write_text(json.dumps({'one':base64.b64encode(b'1'*32).decode()}))
    settings=Settings(database_url=str(e.url),session_secret='fixture-long-session-secret-value-12345',
        environment='test',vault_active_key_version='one',vault_keys_file=str(keyfile))
    app=create_app(settings);browser=TestClient(app)
    token,csrf=auth.new_session(e,a['id'],'browser',3600);browser.cookies.set('kstudio_session',token)
    assert browser.post('/api/account/connections',json=BODY).status_code==403
    browser.headers['X-CSRF-Token']=csrf
    created=browser.post('/api/account/connections',json=BODY)
    assert created.status_code==200 and created.headers['cache-control']=='no-store'
    assert SECRET not in created.text
    dt,_=auth.new_session(e,a['id'],'Desktop',3600)
    with e.begin() as c:c.execute(update(sessions).where(sessions.c.token_hash==auth.digest(dt)).values(refresh_hash=auth.digest('fixture-refresh')))
    device=auth.lookup(e,dt);desktop=TestClient(app,headers={'Authorization':'Bearer '+dt})
    grant=browser.post('/api/account/connections/'+created.json()['id']+'/sync-grants',json={'confirm_device_restore':True,'device_id':device['id']})
    assert grant.status_code==200
    restored=desktop.post('/api/account/connections/restore',json={'sync_token':grant.json()['sync_token']})
    assert restored.status_code==200 and restored.json()['connection']['api_key']==SECRET
    assert restored.headers['cache-control']=='no-store'
    assert SECRET not in browser.get('/api/account/export').text
    assert desktop.post('/api/account/connections/restore',json={'sync_token':grant.json()['sync_token']}).status_code==403
    app.state.engine.dispose()
