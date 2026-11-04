"""Real Authlib OIDC verification + device pairing; deterministic IdP, no live login."""
import hashlib,json,time,types,os
from urllib.parse import urlparse,parse_qs
import httpx,pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,update
from authlib.jose import JsonWebKey,jwt
from cloud.config import Settings
from cloud.main import create_app
from cloud.db import migrate,users,sessions,tasks,wallets,device_authorizations
from cloud import device_auth,gateway
from cloud.auth import lookup
from app.cloud_account import CloudAccount,CloudAccountError
from test_control_plane import credit,PRICE

class MemoryEncryptedStore:
    # Test storage double only. Production CloudAccount uses the existing DPAPI.
    def __init__(self):self.value=None
    def load(self):return self.value
    def save(self,value):self.value=dict(value);return True

@pytest.mark.parametrize('configured,existing', [(False,False),(False,True),(True,False)])
def test_unused_or_absent_account_vault_is_never_decrypted(tmp_path,monkeypatch,configured,existing):
    from app.local_credentials import LocalCredentialStore
    if existing:
        path=tmp_path/'local-settings'/'cloud-account.dpapi';path.parent.mkdir();path.write_bytes(b'unrelated-old-encrypted-state')
    def forbidden(_):raise AssertionError('Unused account storage must not be decrypted')
    monkeypatch.setattr(LocalCredentialStore,'load',forbidden)
    account=CloudAccount(tmp_path,'https://cloud.example.test' if configured else '')
    assert account.state['source_mode']==('unavailable' if existing and not configured else 'byok') and not account.state['token']

@pytest.mark.parametrize('base',['','http://cloud.example.test','https://[','https://cloud.example.test:invalid'])
def test_missing_or_invalid_endpoint_with_existing_vault_never_implies_free_byok(tmp_path,monkeypatch,base):
    from app.local_credentials import LocalCredentialStore
    path=tmp_path/'local-settings'/'cloud-account.dpapi';path.parent.mkdir();original=b'preserved-unread-old-cloud-account';path.write_bytes(original)
    def forbidden(_):raise AssertionError('Missing endpoint must not decrypt account')
    monkeypatch.setattr(LocalCredentialStore,'load',forbidden)
    account=CloudAccount(tmp_path,base)
    assert account.state['source_mode']=='unavailable' and account.status()['account_restore_required']
    assert '运营地址' in account.status()['error']
    app=types.SimpleNamespace(state=types.SimpleNamespace(model_router=types.SimpleNamespace()))
    with pytest.raises(CloudAccountError,match='运营地址'):account.authorize_turn(app,'turn','project',None)
    with pytest.raises(CloudAccountError,match='运营地址'):account.select(app,{'mode':'byok'})
    assert path.read_bytes()==original

@pytest.mark.parametrize('payload', ['not-json','[]',json.dumps({'base':'https://old.example.test','source_mode':'byok'}),json.dumps({'base':'https://cloud.example.test','source_mode':'made-up'}),json.dumps({'base':'https://cloud.example.test','source_mode':'platform','model_id':'one','platform_model':{}})])
def test_corrupt_or_mismatched_saved_account_blocks_all_inference(tmp_path,payload):
    storage=MemoryEncryptedStore();storage.value={'payload':payload}
    account=CloudAccount(tmp_path,'https://cloud.example.test',storage=storage)
    assert account.state['source_mode']=='unavailable' and account.restore_error
    original=storage.value.copy()
    app=types.SimpleNamespace(state=types.SimpleNamespace(model_router=types.SimpleNamespace()))
    with pytest.raises(CloudAccountError,match='恢复'):account.authorize_turn(app,'turn','project',None)
    assert storage.value==original
    account.public_config=lambda:{'byok':{'service_enabled':False,'service_units':0}}
    result=account.select(app,{'mode':'byok'})
    assert account.state['source_mode']=='byok' and not account.restore_error
    assert result['byok']['service_units']==0

def test_native_corrupt_dpapi_is_preserved_and_never_becomes_byok(tmp_path):
    path=tmp_path/'local-settings'/'cloud-account.dpapi';path.parent.mkdir();path.write_bytes(b'not-valid-encrypted-account')
    account=CloudAccount(tmp_path,'https://cloud.example.test')
    assert account.restore_error and account.state['source_mode']=='unavailable'
    assert path.read_bytes()==b'not-valid-encrypted-account'

def test_failed_source_persistence_restores_router_and_source(pair,monkeypatch):
    _,_,browser,account,_=pair;authorize(browser,account)
    original_router=types.SimpleNamespace(cloud_model_id='old-platform')
    app=types.SimpleNamespace(state=types.SimpleNamespace(model_router=original_router))
    byok=types.SimpleNamespace();account.byok_router=byok
    account.state['source_mode']='platform'
    monkeypatch.setattr(account.storage,'save',lambda value:False)
    with pytest.raises(CloudAccountError,match='保存'):account.select(app,{'mode':'byok'})
    assert app.state.model_router is original_router and account.state['source_mode']=='platform'
    assert account.byok_router is byok

@pytest.fixture
def pair(tmp_path):
    settings=Settings(database_url='sqlite:///'+str(tmp_path/'cloud.sqlite'),session_secret='fixture-secret-long-enough-for-signed-cookies',public_url='https://cloud.example.test',environment='test',oidc_metadata_url='https://id.fixture/.well-known/openid-configuration',oidc_client_id='desktop-fixture',oidc_client_secret='idp-fixture-secret',prices_confirmed=True,prices={'version':'test-1','byok_service_enabled':False,'byok_task_units':5})
    cloud=create_app(settings);migrate(cloud.state.engine)
    rsa=JsonWebKey.generate_key('RSA',2048,is_private=True,options={'kid':'fixture'});authorization={}
    def idp(req):
        if req.url.path=='/.well-known/openid-configuration':return httpx.Response(200,json={'issuer':'https://id.fixture','authorization_endpoint':'https://id.fixture/authorize','token_endpoint':'https://id.fixture/token','jwks_uri':'https://id.fixture/jwks','response_types_supported':['code'],'subject_types_supported':['public'],'id_token_signing_alg_values_supported':['RS256']})
        if req.url.path=='/jwks':return httpx.Response(200,json={'keys':[rsa.as_dict(is_private=False)]})
        if req.url.path=='/token':
            data=parse_qs(req.content.decode());assert device_auth.challenge(data['code_verifier'][0])==authorization['code_challenge'][0]
            token=jwt.encode({'alg':'RS256','kid':'fixture'},{'iss':'https://id.fixture','sub':'fixture-user','aud':'desktop-fixture','exp':int(time.time())+600,'iat':int(time.time()),'nonce':authorization['nonce'][0],'name':'本地身份服务测试账户'},rsa).decode()
            return httpx.Response(200,json={'access_token':'idp-fixture-only','token_type':'Bearer','expires_in':600,'id_token':token})
        raise AssertionError(req.url)
    cloud.state.oauth.identity.client_kwargs['transport']=httpx.MockTransport(idp)
    browser=TestClient(cloud,base_url=settings.public_url)
    response=browser.get('/api/auth/login?return_to=/account/device',follow_redirects=False)
    authorization.update(parse_qs(urlparse(response.headers['location']).query))
    assert authorization['code_challenge_method']==['S256']
    response=browser.get('/auth/callback',params={'code':'fixture-auth-code','state':authorization['state'][0]},follow_redirects=False)
    assert response.status_code==303 and response.headers['location']=='/account/device'
    me=browser.get('/api/auth/me').json();assert me['authenticated'];browser.headers['X-CSRF-Token']=me['csrf_token']
    anonymous=TestClient(cloud,base_url=settings.public_url)
    def control(req):
        # Desktop receives only its own Bearer identity, never browser cookies.
        response=anonymous.request(req.method,req.url.path,params=req.url.query.decode(),content=req.content,headers=dict(req.headers))
        return httpx.Response(response.status_code,content=response.content,headers=dict(response.headers))
    desktop=CloudAccount(tmp_path/'desktop',settings.public_url,transport=httpx.MockTransport(control),storage=None if os.name=='nt' else MemoryEncryptedStore())
    yield settings,cloud,browser,desktop,me['user']
    cloud.state.engine.dispose()

def authorize(browser,desktop):
    public=desktop.start();assert 'device_code' not in public and 'access_token' not in public
    details=browser.get('/api/auth/device/details',params={'user_code':public['user_code']});assert details.status_code==200
    assert browser.post('/api/auth/device/approve',json={'user_code':public['user_code']}).status_code==200
    value=desktop.poll();assert value['status']=='authorized'
    assert 'access_token' not in json.dumps(value)
    return public

def test_real_authlib_oidc_device_pkce_persistence_revoke(pair,tmp_path):
    _,cloud,browser,desktop,user=pair
    public=desktop.start();pending=dict(desktop.pending)
    with pytest.raises(Exception):device_auth.poll(cloud.state.engine,pending['device_code'],'wrong-proof'*8,3600)
    assert browser.post('/api/auth/device/approve',json={'user_code':public['user_code']}).status_code==200
    assert desktop.poll()['status']=='authorized'
    if os.name=='nt':assert desktop.state['token'].encode() not in desktop.storage.path.read_bytes()
    assert device_auth.poll(cloud.state.engine,pending['device_code'],pending['verifier'],3600)['status']=='expired_token'
    restored=CloudAccount(tmp_path/'desktop',desktop.base,storage=desktop.storage,transport=desktop.transport)
    assert restored.status()['authenticated'] and restored.status()['user']['id']==user['id']
    token=restored.state['token'];row=lookup(cloud.state.engine,token)
    assert browser.delete('/api/account/devices/'+row['id']).status_code==200
    assert restored.status()['authenticated'] is False
    assert restored.state['token']==''

def test_byok_free_and_paid_server_authority(pair):
    config,cloud,browser,desktop,user=pair;authorize(browser,desktop)
    app=types.SimpleNamespace(state=types.SimpleNamespace(model_router=types.SimpleNamespace()))
    result=desktop.authorize_turn(app,'turn-free','project',None)
    assert result['service_units']==0 and result['data_path']=='local-direct-provider'
    with cloud.state.engine.connect() as c:assert len(c.execute(select(tasks)).all())==0
    config.prices['byok_service_enabled']=True
    with pytest.raises(CloudAccountError,match='确认'):desktop.authorize_turn(app,'turn-paid','project',None)
    credit(cloud.state.engine,user['id'])
    desktop.state['service_ack_version']='test-1'
    result=desktop.authorize_turn(app,'turn-paid','project',None)
    assert result['upstream_charge_by_kstudio']==0 and result['service_units']==5
    desktop.authorize_turn(app,'turn-paid','project',None)
    bill=desktop.request('/api/account/usage',authenticated=True)
    assert bill['balance']['balance']==95 and bill['tasks'][0]['model_units']==0 and bill['tasks'][0]['service_units']==5

def test_device_rotation_invalidates_old_token_and_no_identity_substitution(pair):
    _,cloud,browser,desktop,user=pair;authorize(browser,desktop)
    old=desktop.state['token'];old_refresh=desktop.state['refresh_token'];desktop.state['expires']=0
    with cloud.state.engine.begin() as c:c.execute(update(sessions).where(sessions.c.token_hash==hashlib.sha256(old.encode()).hexdigest()).values(expires=0))
    assert desktop.ensure_session()['user']['id']==user['id']
    assert desktop.state['token']!=old and lookup(cloud.state.engine,old) is None
    with pytest.raises(Exception):device_auth.refresh_device(cloud.state.engine,old_refresh,3600)
    desktop.logout();assert lookup(cloud.state.engine,desktop.state.get('token','')) is None

def test_gateway_compatible_route_uses_server_model_and_ledger(pair,monkeypatch):
    config,cloud,browser,desktop,user=pair;authorize(browser,desktop);credit(cloud.state.engine,user['id'])
    config.models['public-model']={'enabled':True,'protocol':'chat-completions','upstream_model':'real-server-model','base_url':'https://provider.fixture/v1','key_env':'FIXTURE_PLATFORM_SECRET','max_output_tokens':4096,'reservation_units':50,'daily_units':100,'price':PRICE}
    monkeypatch.setenv('FIXTURE_PLATFORM_SECRET','server-only-fixture')
    monkeypatch.setattr(gateway,'validate_upstream',lambda url:url);original=httpx.AsyncClient
    def provider(req):
        assert req.headers['Authorization']=='Bearer server-only-fixture'
        assert json.loads(req.content)['model']=='real-server-model'
        return httpx.Response(200,text='data: {"model":"real-server-model","choices":[{"delta":{"content":"fixture reply"},"finish_reason":"stop"}]}\n\ndata: {"usage":{"prompt_tokens":1000,"completion_tokens":1000}}\n\ndata: [DONE]\n\n')
    monkeypatch.setattr(gateway.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(provider),**kw))
    value=desktop.request('/api/platform/v1/chat/completions',method='POST',authenticated=True,payload={'model':'public-model','messages':[{'role':'user','content':'test'}],'stream':False,'max_tokens':100})
    assert value['choices'][0]['message']['content']=='fixture reply'
    bill=desktop.request('/api/account/usage',authenticated=True)
    assert bill['balance']['balance']==92 and bill['tasks'][0]['service_units']==5 and bill['tasks'][0]['model_units']==3
    assert 'server-only-fixture' not in json.dumps(desktop.status())
    with pytest.raises(CloudAccountError):desktop.request('/api/platform/v1/chat/completions',method='POST',authenticated=True,payload={'model':'not-whitelisted','messages':[]})
