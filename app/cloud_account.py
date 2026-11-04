"""Desktop account bridge. Keys stay in local BYOK vault; cloud tokens use DPAPI.

The website authenticates through Authlib/OIDC. This client only starts a short-lived
device request and polls outbound HTTPS after the user approves it in that website.
No token enters browser JavaScript or a callback URL. No remote writer is exposed.
"""
from __future__ import annotations
import asyncio,base64,copy,hashlib,json,math,os,secrets,threading,time,uuid
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from fastapi import HTTPException,Request
from .local_credentials import LocalCredentialStore

class CloudAccountError(RuntimeError):pass

def valid_base(value):
    p=urlsplit(value)
    return bool(p.scheme=='https' and p.hostname and not p.username and not p.password and p.path in ('','/') and not p.query and not p.fragment)

class CloudAccount:
    def __init__(self,root,base_url,*,transport=None,storage=None):
        self.base=base_url.rstrip('/') if valid_base(base_url) else ''
        self.transport=transport;self.storage=storage or LocalCredentialStore(Path(root))
        if storage is None:self.storage.path=Path(root)/'local-settings'/'cloud-account.dpapi'
        self.lock=threading.RLock();self.pending=None;self.config=None;self.byok_router=None;self.restore_error=''
        self.state={'base':self.base,'token':'','refresh_token':'','expires':0,'source_mode':'byok','model_id':None,'service_ack_version':None}
        # An unconfigured standalone/BYOK installation must never touch account
        # credentials. Even a configured fresh install has nothing to decrypt.
        # Explicit injected stores support controlled tests without filesystem IO.
        if not self.base or (storage is None and not self.storage.path.is_file()):return
        try:
            saved=self.storage.load()
            if saved:
                value=json.loads(saved['payload'])
                if not isinstance(value,dict) or value.get('base')!=self.base:raise ValueError('Account destination changed')
                if value.get('source_mode') not in ('byok','platform','unavailable'):raise ValueError('Unknown account source')
                if not all(isinstance(value.get(k,''),str) for k in ('token','refresh_token')):raise ValueError('Invalid account token')
                expiry=value.get('expires',0)
                if isinstance(expiry,bool) or not isinstance(expiry,(int,float)) or not math.isfinite(expiry):raise ValueError('Invalid account expiry')
                if value.get('model_id') is not None and not isinstance(value['model_id'],str):raise ValueError('Invalid model ID')
                if value.get('service_ack_version') is not None and not isinstance(value['service_ack_version'],str):raise ValueError('Invalid policy version')
                if value.get('source_mode')=='platform':
                    model=value.get('platform_model')
                    if not isinstance(model,dict) or model.get('id')!=value.get('model_id') or model.get('protocol') not in ('chat-completions','responses'):raise ValueError('Invalid platform model')
                self.state.update(value)
                if value['source_mode']=='unavailable':self._restore_failed()
            elif storage is None:raise ValueError('Existing account vault cannot be read')
        except (ValueError,OSError,KeyError,TypeError,AttributeError):self._restore_failed()

    def _restore_failed(self):
        # Preserve the encrypted file and block all inference until a deliberate
        # source selection. A broken/mismatched vault cannot imply free BYOK.
        self.state.update(source_mode='unavailable',token='',refresh_token='',expires=0)
        self.restore_error='云账户配置无法恢复；原文件已保留。请重新登录并明确选择模型方式，或明确选择自带API；尚未调用任何模型。'

    def save(self):
        if not self.storage.save({'payload':json.dumps(self.state)}):raise CloudAccountError('当前系统不能安全保存云账户；未保存明文令牌。')

    def request(self,path,*,method='GET',payload=None,authenticated=False):
        if not self.base:raise CloudAccountError('云账户尚未配置；自带API仍在本机直连使用。')
        headers={}
        request_token=None
        if authenticated:
            if not self.state.get('token'):raise CloudAccountError('请先登录 K Studio 账户。')
            request_token=self.state['token'];headers['Authorization']='Bearer '+request_token
        try:
            with httpx.Client(base_url=self.base,timeout=20,follow_redirects=False,trust_env=False,transport=self.transport) as client:
                response=client.request(method,path,json=payload,headers=headers)
            if response.status_code==401:
                if self.state.get('token')==request_token:self.state['token']='';self.state['refresh_token']='';self.state['expires']=0;self.save()
                raise CloudAccountError('设备会话已过期或撤销，请重新登录；本机模型和API配置仍保留。')
            if response.status_code>=400:
                try:detail=response.json().get('detail')
                except ValueError:detail=None
                raise CloudAccountError(str(detail or '云服务暂不可用，未切换到其他模型。')[:300])
            return response.json()
        except (httpx.HTTPError,ValueError) as exc:
            if isinstance(exc,CloudAccountError):raise
            raise CloudAccountError('无法连接云服务；已保留本机模型，请联网后重试。') from None

    def public_config(self):
        self.config=self.request('/api/public/config')
        return self.config

    def ensure_session(self):
        with self.lock:
            if not self.state.get('token'):raise CloudAccountError('请先登录 K Studio 账户。')
            if self.state.get('expires',0)<time.time()+120:
                value=self.request('/api/auth/device/refresh',method='POST',payload={'refresh_token':self.state.get('refresh_token','')})
                self.state.update(token=value['access_token'],refresh_token=value['refresh_token'],expires=value['expires']);self.save()
            return self.request('/api/auth/me',authenticated=True)

    def status(self):
        result={'configured':bool(self.base),'available':bool(self.base),'url':self.base or None,'authenticated':False,
                'source_mode':self.state['source_mode'],'selected_model':self.state.get('model_id'),'models':[],
                'byok':{'service_enabled':False,'service_units':0,'data_path':'local-direct-provider'},'credential_storage':'windows-dpapi','platform_key_on_desktop':False}
        if not self.base:return result
        try:
            config=self.public_config();result['models']=config.get('models',[]);result['byok']=config.get('byok',result['byok'])
            if self.state.get('token'):
                info=self.ensure_session();result.update(authenticated=info['authenticated'],user=info.get('user'),expires=info.get('expires'))
                result['balance']=self.request('/api/account/usage',authenticated=True)['balance']
        except CloudAccountError as exc:result['error']=str(exc)
        if self.restore_error:result.update(error=self.restore_error,account_restore_required=True)
        return result

    def start(self):
        with self.lock:
            verifier=secrets.token_urlsafe(48)
            digest=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
            value=self.request('/api/auth/device/start',method='POST',payload={'device_name':'K Studio · Windows','code_challenge':digest})
            uri=value['verification_uri_complete']
            if not uri.startswith(self.base+'/account/device?'):raise CloudAccountError('设备授权地址与账户服务器不一致。')
            self.pending={'device_code':value['device_code'],'verifier':verifier,'expires':time.time()+value['expires_in']}
            return {'verification_uri':uri,'user_code':value['user_code'],'expires_in':value['expires_in'],'interval':value['interval']}

    def poll(self):
        with self.lock:
            if not self.pending or self.pending['expires']<=time.time():self.pending=None;return {'status':'expired_token'}
            value=self.request('/api/auth/device/poll',method='POST',payload={'device_code':self.pending['device_code'],'code_verifier':self.pending['verifier']})
            if value['status']=='authorized':
                self.state.update(token=value['access_token'],refresh_token=value['refresh_token'],expires=value['expires']);self.save();self.pending=None
                return {'status':'authorized','account':self.status()}
            return {k:v for k,v in value.items() if k not in ('access_token','refresh_token','device_code')}

    def logout(self):
        # A network error must not pretend the remote session was revoked.
        if self.state.get('token'):self.request('/api/auth/logout',method='POST',authenticated=True)
        self.state.update(token='',refresh_token='',expires=0);self.save();return {'logged_out':True,'local_models_preserved':True}

    def platform_connection(self,config):
        model=next((x for x in config.get('models',[]) if x['id']==self.state.get('model_id') and x.get('enabled')),None)
        if not model:raise CloudAccountError('所选平台模型当前未开放，未自动替换其他供应商。')
        requested=model['id'] if os.getenv('KSTUDIO_AGENT_ENGINE')=='deepseek-harness' or model['protocol']=='responses' else 'openai/'+model['id']
        return {'id':'cloud-platform','name':model.get('name',model['id']),'mode':'codex-responses' if model['protocol']=='responses' else 'compatible',
                'model':requested,'api_base':self.base+'/api/platform/v1','api_key':self.state['token'],'reasoning_effort':'provider-default',
                'capabilities_json':json.dumps(model.get('capabilities',{})),'request_retries':0,'credential_kind':'cloud-device','compatibility_acknowledged':True}

    def apply_platform(self,app,config):
        from .local_connections import connection_router
        connection=self.platform_connection(config)
        self.state['platform_model']=next(x for x in config['models'] if x['id']==self.state['model_id'])
        router=connection_router(app,connection);router.cloud_model_id=self.state['model_id'];router.cloud_token_fingerprint=hashlib.sha256(connection['api_key'].encode()).hexdigest()
        app.state.model_router=router

    def select(self,app,payload):
        previous=copy.deepcopy(self.state);previous_router=app.state.model_router;previous_byok=self.byok_router;previous_error=self.restore_error
        try:return self._select(app,payload)
        except Exception:
            # Keep freshly rotated/revoked tokens, but never leave a failed
            # source application active after persistence/runtime failure.
            auth={k:self.state[k] for k in ('token','refresh_token','expires')}
            self.state=previous;self.state.update(auth);self.restore_error=previous_error
            app.state.model_router=previous_router;self.byok_router=previous_byok
            raise

    def _select(self,app,payload):
        mode=payload.get('mode')
        if mode not in ('byok','platform'):raise CloudAccountError('请选择自带API或平台模型。')
        try:config=self.public_config() if self.base else {'byok':{'service_enabled':False,'service_units':0}}
        except CloudAccountError:
            if mode!='byok' or self.state.get('service_ack_version') or self.restore_error:raise
            config={'byok':{'service_enabled':False,'service_units':0}}
        fee=config.get('byok',{})
        if mode=='byok' and fee.get('service_enabled') and fee.get('service_units',0)>0:
            if payload.get('service_fee_acknowledged') is not True:raise CloudAccountError('请先确认已公布的每任务 K Studio 服务费；供应商API费用另计。')
            self.ensure_session();self.state['service_ack_version']=fee['price_version']
        if mode=='platform':
            self.ensure_session();previous=dict(self.state);self.state['model_id']=payload.get('model_id')
            try:
                self.platform_connection(config)
                if not getattr(app.state.model_router,'cloud_model_id',None):self.byok_router=app.state.model_router
                self.apply_platform(app,config)
            except Exception:self.state=previous;raise
        elif getattr(app.state.model_router,'cloud_model_id',None):
            if self.byok_router:app.state.model_router=self.byok_router
            else:
                from .local_connections import connection_router
                vault=getattr(app.state,'connection_vault',None);saved=vault.load() if vault else {'connections':[],'active_id':None}
                active=next((x for x in saved['connections'] if x['id']==saved['active_id']),None)
                app.state.model_router=connection_router(app,active)
        self.state['source_mode']=mode;self.save();self.restore_error='';return self.status()

    def authorize_turn(self,app,turn_id,project_id,route):
        """Gate BEFORE consuming native approval or sending provider inference."""
        if self.restore_error or self.state['source_mode']=='unavailable':raise CloudAccountError(self.restore_error or '请先明确选择模型方式。')
        platform=getattr(app.state.model_router,'cloud_model_id',None)
        if platform:
            if route is not None and (getattr(route,'tier','economy')!='economy' or route.model.removeprefix('openai/').removeprefix('deepseek/')!=platform):raise CloudAccountError('当前已选择平台模型，请在账户面板明确更换；未使用其他模型或本机API。')
            if route is not None:
                provider=app.state.model_router.providers.get(route.provider)
                destination=getattr(getattr(provider,'api_provider',None),'api_base',None) or getattr(provider,'api_base',None)
                if destination!=self.base+'/api/platform/v1':raise CloudAccountError('平台推理地址已变化，请重新应用平台模型；未绕过云账本调用其他地址。')
            self.ensure_session();config=self.public_config();self.platform_connection(config)
            fingerprint=hashlib.sha256(self.state['token'].encode()).hexdigest()
            selected=next(x for x in config['models'] if x['id']==platform)
            if getattr(app.state.model_router,'cloud_token_fingerprint','')!=fingerprint or self.state.get('platform_model')!=selected:
                try:self.apply_platform(app,config)
                except (ValueError,OSError,RuntimeError):raise CloudAccountError('平台模型运行配置尚未就绪，未调用供应商或本机替代模型。') from None
            return {'mode':'platform','billing_authority':'cloud-ledger','upstream_key_on_desktop':False}
        if self.state['source_mode']=='platform':
            # A deliberately activated local saved connection supersedes platform.
            # On restart a previously selected platform must first be restored.
            raise CloudAccountError('平台连接尚未恢复；请在账户面板重新应用平台模型，或明确选择自带API。')
        if not self.base:return {'mode':'byok','service_units':0,'service_enabled':False,'data_path':'local-direct-provider'}
        # No prior paid policy => BYOK remains free/offline. Once a user accepted
        # a paid service rule, a network failure cannot bypass its authorization.
        try:config=self.public_config()
        except CloudAccountError:
            if self.state.get('service_ack_version'):raise
            return {'mode':'byok','service_units':0,'service_enabled':False,'data_path':'local-direct-provider','cloud_status':'offline_no_paid_policy'}
        fee=config.get('byok',{})
        if not fee.get('service_enabled') or fee.get('service_units',0)==0:return {'mode':'byok','service_units':0,'service_enabled':False,'data_path':'local-direct-provider'}
        if self.state.get('service_ack_version')!=fee.get('price_version'):raise CloudAccountError('K Studio服务费规则需要确认，请在账户面板选择自带API并确认；尚未调用模型。')
        self.ensure_session()
        key=hashlib.sha256((project_id+':'+turn_id).encode()).hexdigest()
        result=self.request('/api/tasks/byok',method='POST',authenticated=True,payload={'idempotency_key':key,'price_version':fee['price_version']})
        if result.get('service_units',0)>0 and result.get('authorized_until',0)<=time.time():raise CloudAccountError('本次任务服务授权已过期，请发起新任务；原模型和账单保留，未自动重复收费。')
        return result

def register_routes(app,root):
    service=CloudAccount(root,os.getenv('KSTUDIO_CLOUD_PUBLIC_URL',''));app.state.cloud_account=service
    if service.state['source_mode']=='platform' and service.state.get('platform_model') and service.state.get('token'):
        try:
            service.byok_router=app.state.model_router
            service.apply_platform(app,{'models':[service.state['platform_model']]})
        except (ValueError,OSError,RuntimeError):pass # authorization gate remains closed, never silent BYOK
    def exclusive(action,*args):
        if not app.state.agent_lock.acquire(blocking=False):raise HTTPException(409,'请等当前建模回合结束后再更换账户或模型方式。')
        try:return action(*args)
        except CloudAccountError as exc:raise HTTPException(409,str(exc)) from None
        except (ValueError,OSError,RuntimeError):raise HTTPException(409,'此账户或模型运行环境暂不可用，原本机文件已保留，未改用其他供应商。') from None
        finally:app.state.agent_lock.release()
    @app.get('/api/cloud-account-config')
    def config():return {'available':bool(service.base),'url':service.base or None,'source_mode':service.state['source_mode'],'selected_model':service.state.get('model_id')}
    @app.get('/api/cloud-account')
    def status():return service.status()
    @app.post('/api/cloud-account/device/start')
    def start():return exclusive(service.start)
    @app.post('/api/cloud-account/device/poll')
    def poll():return exclusive(service.poll)
    @app.post('/api/cloud-account/logout')
    def logout():return exclusive(service.logout)
    @app.post('/api/cloud-account/source')
    async def source(request:Request):
        payload=await request.json()
        if not isinstance(payload,dict):raise HTTPException(400,'请求格式不正确。')
        return await asyncio.to_thread(exclusive,service.select,app,payload)
    @app.get('/api/cloud-account/usage')
    def usage():
        try:service.ensure_session();return service.request('/api/account/usage',authenticated=True)
        except CloudAccountError as exc:raise HTTPException(409,str(exc)) from None
