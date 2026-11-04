from pathlib import Path
import asyncio, collections, hmac, json, secrets, time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select, update, text, func
from authlib.integrations.starlette_client import OAuth
from .config import Settings
from .db import engine_for, users, sessions, tasks, orders, ledger, feedback, now, uid
from . import auth, payments, gateway,device_auth
from .ledger import BillingError, wallet, reserve, claim, settle, create_order
from urllib.parse import urlparse

def create_app(settings=None):
    settings=(settings or Settings.from_env()).validate()
    engine=engine_for(settings.database_url)
    app=FastAPI(title='K Studio cloud control',docs_url=None,redoc_url=None)
    app.state.settings=settings;app.state.engine=engine
    secure=settings.public_url.startswith('https:')
    app.add_middleware(SessionMiddleware,secret_key=settings.session_secret,session_cookie='kstudio_oidc',https_only=secure,same_site='lax',max_age=600)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=[urlparse(settings.public_url).hostname,'testserver'] if settings.environment=='test' else [urlparse(settings.public_url).hostname])
    oauth=OAuth()
    app.state.oauth=oauth
    oidc_ready=bool(settings.oidc_metadata_url and settings.oidc_client_id)
    if oidc_ready:
        oauth.register(name='identity',client_id=settings.oidc_client_id,client_secret=settings.oidc_client_secret,
            server_metadata_url=settings.oidc_metadata_url,client_kwargs={'scope':'openid profile email','code_challenge_method':'S256'})
    buckets=collections.defaultdict(collections.deque)
    def rate(key,limit=30):
        stamp=time.monotonic()
        if key not in buckets and len(buckets)>=10_000:
            for old in list(buckets):
                if not buckets[old] or buckets[old][-1]<stamp-60:del buckets[old]
            if len(buckets)>=10_000:raise HTTPException(429,'服务繁忙，请稍后再试。')
        q=buckets[key]
        while q and q[0]<stamp-60:q.popleft()
        if len(q)>=limit:raise HTTPException(429,'请求过于频繁，请稍后再试。',headers={'Retry-After':'60'})
        q.append(stamp)
    def identity(request,required=True):
        bearer=request.headers.get('authorization','')
        is_bearer=bearer.startswith('Bearer ')
        token=bearer[7:] if is_bearer else request.cookies.get('kstudio_session')
        row=auth.lookup(engine,token)
        if not row and required:raise HTTPException(401,'请先登录。')
        if row and request.method not in ('GET','HEAD','OPTIONS') and not is_bearer:
            origin=request.headers.get('origin')
            if origin and origin.rstrip('/')!=settings.public_url.rstrip('/'):raise HTTPException(403,'请求来源不匹配。')
            if not hmac.compare_digest(request.headers.get('x-csrf-token',''),row['csrf']):raise HTTPException(403,'会话校验失败，请刷新重试。')
        return row
    async def json_object(request):
        value=await request.json()
        if not isinstance(value,dict):raise HTTPException(400,'请求必须是JSON对象。')
        return value
    @app.exception_handler(BillingError)
    async def billing_error(request,exc):return JSONResponse({'detail':str(exc)},status_code=409)
    @app.exception_handler(json.JSONDecodeError)
    async def json_error(request,exc):return JSONResponse({'detail':'请求必须是有效JSON。'},status_code=400)
    @app.middleware('http')
    async def limits(request,call_next):
        if request.headers.get('content-length','').isdigit() and int(request.headers['content-length'])>settings.max_request_bytes:return JSONResponse({'detail':'请求过大'},status_code=413)
        if request.method in ('POST','PUT','PATCH'):
            chunks=[];size=0
            async for chunk in request.stream():
                size+=len(chunk)
                if size>settings.max_request_bytes:return JSONResponse({'detail':'请求过大'},status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        if request.url.path.startswith('/api/account') or request.url.path.startswith('/api/auth'):response.headers['Cache-Control']='no-store'
        return response
    @app.get('/health/live')
    async def live():return {'status':'alive'}
    @app.get('/health/ready')
    async def ready():
        try:
            with engine.connect() as c:assert c.execute(text('SELECT version FROM schema_version')).scalar()==2
        except Exception:return JSONResponse({'status':'database_unavailable_or_unmigrated'},status_code=503)
        return {'status':'ready','environment':settings.environment}
    @app.get('/api/public/config')
    async def public_config():
        release=settings.release
        downloadable=bool(release.get('verified') and release.get('public_distribution_authorized') and release.get('sha256') and release.get('url'))
        return {'environment':settings.environment,'auth':{'available':oidc_ready,'login_url':'/api/auth/login' if oidc_ready else None},
                'payment':{'available':bool(settings.stripe_key and settings.prices_confirmed),'provider':'stripe','sandbox':settings.environment!='production'},
                'pricing':{'confirmed':settings.prices_confirmed,'version':settings.prices.get('version'),'packages':settings.prices.get('packages',{}) if settings.prices_confirmed else {},'byok':'API费用由用户直接向供应商支付；软件服务收费默认未启用，启用后按单独确认的任务授权规则收取。'},
                'release':{**release,'download_available':downloadable,'url':release.get('url') if downloadable else None},
                'byok':{'service_enabled':bool(settings.prices_confirmed and settings.prices.get('byok_service_enabled')),'service_units':settings.prices.get('byok_task_units',0) if settings.prices_confirmed and settings.prices.get('byok_service_enabled') else 0,'price_version':settings.prices.get('version'),'data_path':'local-direct-provider'},
                'models':[{'id':k,'name':v.get('name',k),'protocol':v.get('protocol'),'enabled':bool(v.get('enabled') and settings.prices_confirmed),'verified':v.get('verified',False),'capabilities':v.get('capabilities',{})} for k,v in settings.models.items()]}
    @app.get('/api/status')
    async def status():
        state=await ready()
        return {'environment':settings.environment,'database':state if isinstance(state,dict) else {'status':'unavailable'},'model_service':'configured_unverified' if settings.models else 'not_configured','payment_service':'configured_unverified' if settings.stripe_key else 'not_configured','known_issues':['跨电脑与多版本SketchUp尚未完成验收','真实支付与供应商调用按配置和独立验收记录开放']}
    @app.get('/api/auth/me')
    async def me(request:Request):
        row=identity(request,False)
        return {'authenticated':False} if not row else {'authenticated':True,'user':{'id':row['user_id'],'display_name':row['display_name']},'csrf_token':row['csrf'],'expires':row['expires']}
    @app.get('/api/auth/login')
    async def login(request:Request):
        if not oidc_ready:raise HTTPException(503,'身份服务尚未配置；本地模式仍可使用。')
        rate('login:'+request.client.host,10)
        destination=request.query_params.get('return_to',request.query_params.get('next','/account/usage'))
        parsed=urlparse(destination)
        if parsed.scheme or parsed.netloc or parsed.path not in ('/account/device','/account/usage') or '\\' in destination:raise HTTPException(400,'登录返回地址不正确。')
        request.session['return_to']=destination
        return await oauth.identity.authorize_redirect(request,settings.public_url+'/auth/callback',code_verifier=secrets.token_urlsafe(48))
    @app.get('/auth/callback')
    async def callback(request:Request):
        if not oidc_ready:raise HTTPException(503,'身份服务尚未配置。')
        try:
            token=await oauth.identity.authorize_access_token(request)
            info=token['userinfo'];subject=str(info['iss'])+'|'+str(info['sub'])
            user=auth.create_identity(engine,subject,str(info.get('name') or 'K Studio 用户'))
            value,csrf=auth.new_session(engine,user['id'],'browser',settings.session_seconds)
        except Exception:raise HTTPException(401,'登录验证失败或已过期，请重新登录。') from None
        destination=request.session.get('return_to','/account/usage')
        request.session.clear()
        response=RedirectResponse(destination,303)
        response.set_cookie('kstudio_session',value,max_age=settings.session_seconds,httponly=True,secure=secure,samesite='lax')
        return response
    @app.post('/api/auth/logout')
    async def logout(request:Request):
        row=identity(request);auth.revoke(engine,row['user_id'],row['id'])
        response=JSONResponse({'logged_out':True});response.delete_cookie('kstudio_session');return response
    @app.post('/api/auth/device/start')
    async def device_start(request:Request):
        if not oidc_ready:raise HTTPException(503,'身份服务尚未配置；自带API本地模式仍可使用。')
        rate('device-start:'+request.client.host,10);body=await json_object(request)
        value=device_auth.start(engine,body.get('device_name'),body.get('code_challenge'))
        return {**value,'verification_uri':settings.public_url+'/account/device','verification_uri_complete':settings.public_url+'/account/device?user_code='+value['user_code']}
    @app.get('/api/auth/device/details')
    async def device_details(request:Request,user_code:str):
        row=identity(request);rate('device-details:'+row['user_id'],20)
        return device_auth.details(engine,user_code)
    @app.post('/api/auth/device/approve')
    async def device_approve(request:Request):
        row=identity(request);rate('device-approve:'+row['user_id'],10);body=await json_object(request)
        return device_auth.approve(engine,row['user_id'],body.get('user_code'))
    @app.post('/api/auth/device/poll')
    async def device_poll(request:Request):
        rate('device-poll:'+request.client.host,20);body=await json_object(request)
        return device_auth.poll(engine,body.get('device_code'),body.get('code_verifier'),settings.session_seconds)
    @app.post('/api/auth/refresh')
    async def refresh_session(request:Request):
        row=identity(request)
        if not request.headers.get('authorization','').startswith('Bearer '):raise HTTPException(400,'设备会话刷新需要设备授权。')
        return device_auth.rotate(engine,row,settings.session_seconds)
    @app.post('/api/auth/device/refresh')
    async def device_refresh(request:Request):
        rate('device-refresh:'+request.client.host,20);body=await json_object(request)
        return device_auth.refresh_device(engine,body.get('refresh_token'),settings.session_seconds)
    @app.get('/api/account/devices')
    async def devices(request:Request):
        row=identity(request)
        with engine.connect() as c:items=c.execute(select(sessions.c.id,sessions.c.device_name,sessions.c.expires,sessions.c.revoked).where(sessions.c.user_id==row['user_id'])).mappings().all()
        return {'devices':[dict(x) for x in items]}
    @app.delete('/api/account/devices/{device_id}')
    async def revoke_device(device_id:str,request:Request):
        row=identity(request)
        if not auth.revoke(engine,row['user_id'],device_id):raise HTTPException(404,'设备不存在')
        return {'revoked':True}
    @app.get('/api/account/usage')
    async def usage(request:Request):
        row=identity(request);user=row['user_id']
        with engine.connect() as c:
            w=wallet(c,user)
            events=c.execute(select(ledger).where(ledger.c.user_id==user).order_by(ledger.c.created.desc()).limit(100)).mappings().all()
            jobs=c.execute(select(tasks).where(tasks.c.user_id==user).order_by(tasks.c.created.desc()).limit(100)).mappings().all()
            pending=c.execute(select(func.coalesce(func.sum(tasks.c.reserve),0)).where(tasks.c.user_id==user,tasks.c.state=='pending_reconciliation')).scalar_one()
        public_jobs=[]
        for job in jobs:
            item={k:v for k,v in job.items() if k not in ('price_json','key')}
            charged=job['charged'];service=None if charged is None else min(charged,json.loads(job['price_json'])['service_units'])
            item.update(service_units=service,model_units=None if charged is None else charged-service)
            public_jobs.append(item)
        return {'balance':{**w,'pending':pending,'currency':'credits','price_version':settings.prices.get('version')},'events':[dict(x) for x in events],'tasks':public_jobs}
    @app.get('/api/account/orders')
    async def list_orders(request:Request):
        row=identity(request)
        with engine.connect() as c:items=c.execute(select(orders).where(orders.c.user_id==row['user_id']).order_by(orders.c.created.desc()).limit(100)).mappings().all()
        return {'orders':[dict(x) for x in items]}
    @app.post('/api/account/orders')
    async def order(request:Request):
        row=identity(request);rate('orders:'+row['user_id'],10)
        if not settings.prices_confirmed or not settings.stripe_key:raise HTTPException(503,'正式价格或支付渠道尚未开放。')
        body=await json_object(request);package=body.get('package_id')
        if not isinstance(package,str):raise HTTPException(400,'充值方案不正确。')
        config=settings.prices.get('packages',{}).get(package)
        if not config:raise HTTPException(400,'请选择已公布的充值方案。')
        key=body.get('idempotency_key','')
        if not isinstance(key,str) or not 8<=len(key)<=128:raise HTTPException(400,'缺少有效订单请求标识。')
        order=create_order(engine,row['user_id'],key,package,config)
        if order.get('checkout_url'):return {'order_id':order['id'],'checkout_url':order['checkout_url'],'state':order['state']}
        return await asyncio.to_thread(payments.checkout,engine,settings,order)
    @app.post('/api/payments/stripe/webhook')
    async def webhook(request:Request):
        raw=await request.body()
        if len(raw)>1_000_000:raise HTTPException(413,'Webhook too large')
        try:event=payments.verify_webhook(settings,raw,request.headers.get('stripe-signature',''))
        except Exception:raise HTTPException(400,'Invalid payment signature') from None
        return {'result':payments.apply_event(engine,event)}
    @app.post('/api/feedback')
    async def send_feedback(request:Request):
        rate('feedback:'+request.client.host,5);row=identity(request,False);body=await json_object(request)
        message=body.get('message','');email=body.get('email','')
        if not isinstance(message,str) or not 5<=len(message)<=4000 or not isinstance(email,str) or len(email)>256:raise HTTPException(400,'请填写5–4000字的问题描述。')
        if any(word in message.lower() for word in ('sk-','bearer ','api_key=')):raise HTTPException(400,'请移除密钥后再提交。')
        id=uid()
        with engine.begin() as c:c.execute(feedback.insert().values(id=id,user_id=row['user_id'] if row else None,message=message,email=email or None,created=now()))
        return {'received':True,'receipt_id':id,'status':'stored_for_operator_review'}
    @app.post('/api/tasks/byok')
    async def byok_lease(request:Request):
        row=identity(request);body=await json_object(request)
        if not settings.prices_confirmed or not settings.prices.get('byok_service_enabled'):
            return {'authorized':True,'service_enabled':False,'service_units':0,'upstream_charge_by_kstudio':0,'rule':'BYOK software service charging is not enabled'}
        if body.get('price_version')!=settings.prices.get('version'):raise HTTPException(409,'服务费规则已更新，请重新确认。')
        fee=settings.prices.get('byok_task_units')
        if type(fee) is not int:raise HTTPException(503,'BYOK授权规则尚未配置。')
        price={'version':settings.prices['version'],'service_units':fee,'input_units_per_million':0,'output_units_per_million':0}
        task=reserve(engine,row['user_id'],body.get('idempotency_key',''),'byok','direct-provider',fee,price)
        if task['state']=='reserved':
            claim(engine,row['user_id'],task['id']);settle(engine,row['user_id'],task['id'],fee,'BYOK task authorization service fee; upstream billed separately')
        return {'task_id':task['id'],'authorized_until':task['created']+3600,'service_units':fee,'upstream_charge_by_kstudio':0,'rule':'one server-authorized task lease; not local tool metering'}
    @app.post('/api/gateway/{model_id}')
    async def model_request(model_id:str,request:Request):
        row=identity(request);rate('model:'+row['user_id'],10)
        model=settings.models.get(model_id)
        if not model or not model.get('enabled') or not settings.prices_confirmed:raise HTTPException(503,'平台模型暂未开放。')
        body=await request.body()
        if len(body)>settings.max_request_bytes:raise HTTPException(413,'请求过大')
        payload=getattr(request.state,'gateway_payload',None) or json.loads(body);key=getattr(request.state,'gateway_key',None) or request.headers.get('idempotency-key','')
        if not isinstance(payload,dict):raise HTTPException(400,'请求必须是JSON对象。')
        client_stream=payload.pop('stream',True);payload.pop('stream_options',None)
        if type(client_stream) is not bool:raise HTTPException(400,'stream参数不正确。')
        allowed={'messages','input','instructions','tools','tool_choice','max_output_tokens','max_tokens','max_completion_tokens','reasoning','reasoning_effort','temperature','top_p','parallel_tool_calls','response_format','stop','presence_penalty','frequency_penalty','thinking','store','include'}
        if set(payload)-allowed:raise HTTPException(400,'请求包含不支持的字段。')
        if payload.get('store') not in (None,False):raise HTTPException(400,'平台接口不开放供应商持久存储。')
        if 'include' in payload and payload['include']!=['reasoning.encrypted_content']:raise HTTPException(400,'不支持所选返回字段。')
        with engine.connect() as c:
            running=c.execute(select(tasks.c.id).where(tasks.c.user_id==row['user_id'],tasks.c.state.in_(['running','pending_reconciliation']))).first()
        if running:raise HTTPException(409,'已有任务运行或等待对账。')
        max_tokens=payload.get('max_output_tokens',payload.get('max_completion_tokens',payload.get('max_tokens',model['max_output_tokens'])))
        if type(max_tokens) is not int or not 1<=max_tokens<=model['max_output_tokens']:raise HTTPException(400,'输出上限不支持。')
        for field in ('max_output_tokens','max_completion_tokens','max_tokens'):payload.pop(field,None)
        payload['max_output_tokens' if model['protocol']=='responses' else 'max_tokens']=max_tokens
        task=reserve(engine,row['user_id'],key,'platform',model_id,model['reservation_units'],model['price'],daily_limit=model.get('daily_units',10_000))
        if task['state']!='reserved':raise HTTPException(409,'此请求已经执行，请查看任务状态，勿重放。')
        claim(engine,row['user_id'],task['id'])
        stream=gateway.stream(engine,row['user_id'],task,payload,model,already_claimed=True)
        if not client_stream:
            return JSONResponse(await gateway.collect(stream,model['protocol']),headers={'X-KStudio-Task':task['id'],'Cache-Control':'no-store'})
        return StreamingResponse(stream,media_type='text/event-stream',headers={'X-KStudio-Task':task['id'],'Cache-Control':'no-store'})
    @app.post('/api/platform/v1/chat/completions')
    @app.post('/api/platform/v1/responses')
    async def platform_compatible(request:Request):
        payload=await json_object(request);model_id=payload.pop('model',None)
        if not isinstance(model_id,str) or model_id not in settings.models:raise HTTPException(400,'请选择平台已公布的模型。')
        expected='responses' if request.url.path.endswith('/responses') else 'chat-completions'
        if settings.models[model_id].get('protocol')!=expected:raise HTTPException(409,'此平台模型不支持所选协议。')
        request.state.gateway_payload=payload
        # SDKs may omit a task id. Each HTTP attempt still gets a unique server
        # reservation; the desktop disables SDK retry to avoid duplicate spend.
        if not request.headers.get('idempotency-key'):
            request.state.gateway_key=uid()
        return await model_request(model_id,request)
    @app.post('/api/admin/tasks/{task_id}/reconcile')
    async def reconcile(task_id:str,request:Request):
        row=identity(request)
        if row['subject'] not in settings.admin_subjects:raise HTTPException(403,'需要对账权限。')
        body=await json_object(request)
        if not isinstance(body.get('reason'),str) or len(body['reason'])<10:raise HTTPException(400,'请填写供应商账单来源与原因。')
        with engine.connect() as c:task=c.execute(select(tasks).where(tasks.c.id==task_id)).mappings().first()
        if not task:raise HTTPException(404,'任务不存在。')
        return settle(engine,task['user_id'],task_id,body.get('actual_units'),body['reason'][:256]+' actor:'+row['user_id'],reconcile=True)
    website=Path(settings.website_dir).resolve()
    @app.get('/{path:path}')
    async def site(path:str):
        if path.startswith(('api/','health/')):raise HTTPException(404)
        target=(website/path).resolve()
        if not target.is_relative_to(website):raise HTTPException(404)
        if target.is_file():return FileResponse(target)
        if (website/'index.html').is_file():return FileResponse(website/'index.html')
        raise HTTPException(503,'官网工件未安装。')
    return app
