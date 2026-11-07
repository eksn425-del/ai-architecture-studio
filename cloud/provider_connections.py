"""Opt-in account credential vault and one-use, device-bound explicit restoration.

There is deliberately no provider probe: BYOK stays desktop-to-provider. Browser
lists and CRUD responses never expose the saved secret. A recent browser login
authorizes one particular already-paired device to redeem a short-lived grant.
"""
from __future__ import annotations

import hashlib
import secrets
import time
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from sqlalchemy import Table, Column, String, Text, BigInteger, ForeignKey, select, update, delete, func

from .db import metadata, sessions, users, now, uid
from .credential_crypto import CredentialCipher, CredentialCryptoError

connections = Table('provider_connections', metadata,
    Column('id', String(64), primary_key=True), Column('user_id', ForeignKey('users.id'), nullable=False),
    Column('label', String(80), nullable=False), Column('provider', String(40), nullable=False),
    Column('protocol', String(32), nullable=False), Column('base_url', String(2048), nullable=False),
    Column('model_id', String(160), nullable=False), Column('reasoning_effort', String(32), nullable=False),
    Column('ciphertext', Text, nullable=False), Column('nonce', String(64), nullable=False),
    Column('key_version', String(40), nullable=False), Column('secret_hint', String(16), nullable=False),
    Column('created_at', BigInteger, nullable=False), Column('updated_at', BigInteger, nullable=False),
    Column('last_verified_at', BigInteger))
sync_grants = Table('connection_sync_grants', metadata,
    Column('id', String(64), primary_key=True), Column('token_hash', String(64), unique=True, nullable=False),
    Column('user_id', ForeignKey('users.id'), nullable=False),
    Column('connection_id', ForeignKey('provider_connections.id'), nullable=False),
    Column('device_id', ForeignKey('sessions.id'), nullable=False),
    Column('connection_updated_at', BigInteger, nullable=False),
    Column('expires_at', BigInteger, nullable=False), Column('consumed_at', BigInteger))
credential_audit = Table('credential_audit', metadata,
    Column('id', String(64), primary_key=True), Column('user_id', ForeignKey('users.id'), nullable=False),
    Column('connection_id', String(64)), Column('device_id', String(64)),
    Column('action', String(40), nullable=False), Column('created_at', BigInteger, nullable=False))


def public_connection(row):
    fields = ('id', 'label', 'provider', 'protocol', 'base_url', 'model_id', 'reasoning_effort',
              'created_at', 'updated_at', 'last_verified_at')
    return {**{k: row[k] for k in fields}, 'has_secret': True, 'secret_mask': row['secret_hint'],
            'verification_status': 'not_verified' if row['last_verified_at'] is None else 'verified'}


def _audit(c, user_id, action, connection_id=None, device_id=None):
    c.execute(credential_audit.insert().values(id=uid(), user_id=user_id, action=action,
        connection_id=connection_id, device_id=device_id, created_at=now()))


def _validate(body, old=None):
    if not isinstance(body, dict) or 'user_id' in body or 'ciphertext' in body:
        raise HTTPException(400, '连接格式不正确。')
    data = {k: body.get(k, old.get(k) if old else None) for k in (
        'label', 'provider', 'protocol', 'base_url', 'model_id', 'reasoning_effort')}
    data['reasoning_effort'] = data['reasoning_effort'] or 'provider-default'
    for key, limit in (('label',80),('provider',40),('base_url',2048),('model_id',160)):
        value = data[key]
        if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c)<32 for c in value):
            raise HTTPException(400, '请填写有效的名称、服务商、API地址和模型。')
        data[key] = value.strip()
    if data['protocol'] not in ('responses', 'chat-completions'):
        raise HTTPException(400, '请选择 Responses 或 Chat Completions 协议。')
    if data['reasoning_effort'] not in ('provider-default','low','medium','high','xhigh','max'):
        raise HTTPException(400, '推理档位无效。')
    try:
        url = urlsplit(data['base_url']); _ = url.port
        if (url.scheme != 'https' or not url.hostname or url.username or url.password
                or url.query or url.fragment or data['base_url'].endswith(('/responses','/chat/completions'))):
            raise ValueError()
    except ValueError:
        raise HTTPException(400, '请填写不含凭据的 HTTPS API Base。') from None
    data['base_url'] = data['base_url'].rstrip('/')
    secret = body.get('api_key')
    if secret is not None and (not isinstance(secret,str) or not 8 <= len(secret.strip()) <= 4096
                               or any(ord(c)<32 for c in secret)):
        raise HTTPException(400, 'API Key 格式无效。')
    changed = old and any(data[k] != old[k] for k in ('protocol','base_url','model_id'))
    if (not old or changed) and not secret:
        raise HTTPException(400, '新连接或更换地址、协议、模型时需要重新输入 API Key。')
    return data, secret.strip() if secret else None


class ConnectionService:
    def __init__(self, engine, cipher): self.engine, self.cipher = engine, cipher

    def list(self, user_id):
        with self.engine.connect() as c:
            rows=c.execute(select(connections).where(connections.c.user_id==user_id).order_by(connections.c.created_at)).mappings().all()
        return {'connections':[public_connection(x) for x in rows], 'cloud_storage':'encrypted_opt_in',
                'platform_keys_included':False}

    def save(self, user_id, body, connection_id=None):
        with self.engine.begin() as c:
            old = c.execute(select(connections).where(connections.c.id==connection_id,
                connections.c.user_id==user_id).with_for_update()).mappings().first() if connection_id else None
            if connection_id and old is None: raise HTTPException(404,'连接不存在。')
            if old is None:
                if body.get('cloud_storage_consent') is not True: raise HTTPException(400,'请明确同意加密保存到当前 K Studio 账户。')
                if c.execute(select(func.count()).select_from(connections).where(connections.c.user_id==user_id)).scalar_one() >= 100:
                    raise HTTPException(409,'当前账户最多保存100个连接。')
            data, secret = _validate(body,old)
            cid = connection_id or uid()
            stamp=max(int(time.time()*1000), (old['updated_at']+1) if old else 0)
            values={**data,'updated_at':stamp}
            if secret:
                values.update(self.cipher.encrypt(secret,user_id,cid),secret_hint='••••'+secret[-4:],last_verified_at=None)
            if old:
                c.execute(update(connections).where(connections.c.id==cid,connections.c.user_id==user_id).values(**values))
                c.execute(delete(sync_grants).where(sync_grants.c.connection_id==cid,sync_grants.c.user_id==user_id))
            else:
                c.execute(connections.insert().values(id=cid,user_id=user_id,created_at=stamp,**values))
            _audit(c,user_id,'updated' if old else 'created',cid)
            return public_connection(c.execute(select(connections).where(connections.c.id==cid)).mappings().one())

    def remove(self,user_id,connection_id):
        with self.engine.begin() as c:
            row=c.execute(select(connections.c.id).where(connections.c.id==connection_id,connections.c.user_id==user_id).with_for_update()).first()
            if row is None: raise HTTPException(404,'连接不存在。')
            c.execute(delete(sync_grants).where(sync_grants.c.connection_id==connection_id,sync_grants.c.user_id==user_id))
            c.execute(delete(connections).where(connections.c.id==connection_id,connections.c.user_id==user_id))
            _audit(c,user_id,'deleted',connection_id)
        return {'deleted':True,'device_cache_notice':'下次联网清除此连接的云同步缓存；已取得的Key不能远程彻底抹除，需要时请在供应商撤销。'}

    def issue_grant(self,user_id,connection_id,device_id):
        with self.engine.begin() as c:
            row=c.execute(select(connections).where(connections.c.id==connection_id,connections.c.user_id==user_id)).mappings().first()
            device=c.execute(select(sessions).where(sessions.c.id==device_id,sessions.c.user_id==user_id,
                sessions.c.revoked==0,sessions.c.expires>now(),sessions.c.refresh_hash.is_not(None))).mappings().first()
            if row is None or device is None: raise HTTPException(404,'连接或已授权设备不存在。')
            # Reissuing invalidates any earlier unconsumed authorization for this pair.
            c.execute(delete(sync_grants).where(sync_grants.c.connection_id==connection_id,sync_grants.c.device_id==device_id))
            token=secrets.token_urlsafe(48);expires=now()+120
            c.execute(sync_grants.insert().values(id=uid(),token_hash=hashlib.sha256(token.encode()).hexdigest(),
                user_id=user_id,connection_id=connection_id,device_id=device_id,
                connection_updated_at=row['updated_at'],expires_at=expires,consumed_at=None))
            _audit(c,user_id,'restore_authorized',connection_id,device_id)
        return {'sync_token':token,'expires_at':expires,'device_id':device_id,'connection_id':connection_id}

    def redeem(self,user_id,device_id,token):
        if not isinstance(token,str) or not 40<=len(token)<=128: raise HTTPException(400,'恢复授权无效。')
        with self.engine.begin() as c:
            device=c.execute(select(sessions).where(sessions.c.id==device_id,sessions.c.user_id==user_id,
                sessions.c.revoked==0,sessions.c.expires>now(),sessions.c.refresh_hash.is_not(None))).mappings().first()
            grant=c.execute(select(sync_grants).where(sync_grants.c.token_hash==hashlib.sha256(token.encode()).hexdigest(),
                sync_grants.c.user_id==user_id,sync_grants.c.device_id==device_id,
                sync_grants.c.expires_at>now(),sync_grants.c.consumed_at.is_(None)).with_for_update()).mappings().first()
            if device is None or grant is None: raise HTTPException(403,'恢复授权已过期、已使用或不属于此设备。')
            row=c.execute(select(connections).where(connections.c.id==grant['connection_id'],connections.c.user_id==user_id,
                connections.c.updated_at==grant['connection_updated_at']).with_for_update()).mappings().first()
            if row is None: raise HTTPException(409,'连接已修改或删除，请重新授权恢复。')
            changed=c.execute(update(sync_grants).where(sync_grants.c.id==grant['id'],sync_grants.c.consumed_at.is_(None)).values(consumed_at=now())).rowcount
            if changed!=1: raise HTTPException(409,'恢复授权已使用。')
            secret=self.cipher.decrypt(dict(row))
            _audit(c,user_id,'restored_to_device',row['id'],device_id)
            return {'connection':{**public_connection(row),'api_key':secret},'user_id':user_id,'device_id':device_id}

    def rotate_keys(self):
        count=0
        with self.engine.begin() as c:
            rows=c.execute(select(connections).where(connections.c.key_version!=self.cipher.active_version).with_for_update()).mappings().all()
            for row in rows:
                values=self.cipher.encrypt(self.cipher.decrypt(dict(row)),row['user_id'],row['id'])
                c.execute(update(connections).where(connections.c.id==row['id']).values(**values))
                _audit(c,row['user_id'],'key_rotated',row['id']);count+=1
        return {'rotated':count,'active_key_version':self.cipher.active_version}

    def export_metadata(self,user_id):
        with self.engine.connect() as c:
            user=c.execute(select(users.c.id,users.c.display_name,users.c.created).where(users.c.id==user_id)).mappings().one()
            audit=c.execute(select(credential_audit.c.action,credential_audit.c.connection_id,credential_audit.c.created_at).where(credential_audit.c.user_id==user_id).order_by(credential_audit.c.created_at)).mappings().all()
        return {'account':dict(user),**self.list(user_id),'credential_audit':[dict(x) for x in audit],
                'secrets_exported':False,'financial_data_location':'/api/account/usage and /api/account/orders',
                'local_projects':'Local projects and source files are not uploaded by this export.'}

    def delete_private_data(self,user_id):
        with self.engine.begin() as c:
            c.execute(delete(sync_grants).where(sync_grants.c.user_id==user_id))
            removed=c.execute(delete(connections).where(connections.c.user_id==user_id)).rowcount
            c.execute(update(sessions).where(sessions.c.user_id==user_id).values(revoked=1))
            c.execute(update(users).where(users.c.id==user_id).values(display_name='已清除个人资料的账户'))
            _audit(c,user_id,'private_data_deleted')
        return {'private_credentials_deleted':removed,'sessions_revoked':True,'profile_display_name_removed':True,
                'full_account_deleted':False,'retained':['stable identity mapping','orders and financial ledger','security audit'],
                'notice':'账户Key已删除、设备已撤销。为避免账户串用及处理已有订单，身份映射和财务/安全记录仍保留；这不是完整销户。设备已取得的Key无法远程彻底抹除，需要时向供应商撤销。'}


def register_routes(app,engine,settings,identity,json_object,rate):
    configured=bool(getattr(settings,'vault_keys_file','') and getattr(settings,'vault_active_key_version',''))
    cipher=CredentialCipher.from_file(settings.vault_keys_file,settings.vault_active_key_version) if configured else None
    service=ConnectionService(engine,cipher) if cipher else None
    app.state.connection_service=service
    def current(request,*,recent=False,browser=False,device=False):
        row=identity(request)
        if service is None: raise HTTPException(503,'账户API加密保存尚未配置；本机保存仍可使用。')
        if recent and not 0 <= now()-int(row.get('authenticated_at') or 0) <= 600:
            raise HTTPException(403,'此操作需要最近10分钟内重新登录，请先重新验证身份。')
        bearer=request.headers.get('authorization','').startswith('Bearer ')
        if browser and (bearer or row.get('refresh_hash') or row.get('device_name')!='browser'): raise HTTPException(403,'请在官网重新登录后管理账户API和授权设备恢复。')
        if device and (not bearer or not row.get('refresh_hash')): raise HTTPException(403,'此接口仅允许已授权桌面设备。')
        rate('credential:'+row['user_id'],30)
        return row
    @app.get('/api/account/connections')
    async def list_connections(request:Request):
        row=current(request);return service.list(row['user_id'])
    @app.get('/api/account/export')
    async def export_metadata(request:Request):
        row=current(request,recent=True,browser=True);return service.export_metadata(row['user_id'])
    @app.delete('/api/account/private-data')
    async def delete_private_data(request:Request):
        row=current(request,recent=True,browser=True);body=await json_object(request)
        if body.get('confirm_delete_private_data') is not True:raise HTTPException(400,'请确认删除账户保存的API并撤销全部设备。')
        return service.delete_private_data(row['user_id'])
    @app.post('/api/account/connections')
    async def create_connection(request:Request):
        row=current(request,recent=True,browser=True);return service.save(row['user_id'],await json_object(request))
    @app.patch('/api/account/connections/{connection_id}')
    async def update_connection(connection_id:str,request:Request):
        row=current(request,recent=True,browser=True);return service.save(row['user_id'],await json_object(request),connection_id)
    @app.delete('/api/account/connections/{connection_id}')
    async def delete_connection(connection_id:str,request:Request):
        row=current(request,recent=True,browser=True);return service.remove(row['user_id'],connection_id)
    @app.post('/api/account/connections/{connection_id}/sync-grants')
    async def authorize_sync(connection_id:str,request:Request):
        row=current(request,recent=True,browser=True);body=await json_object(request)
        if body.get('confirm_device_restore') is not True: raise HTTPException(400,'请确认将此Key恢复到选定设备。')
        return service.issue_grant(row['user_id'],connection_id,body.get('device_id'))
    @app.post('/api/account/connections/restore')
    async def restore(request:Request):
        row=current(request,device=True);body=await json_object(request)
        try: return service.redeem(row['user_id'],row['id'],body.get('sync_token'))
        except CredentialCryptoError: raise HTTPException(503,'账户加密凭据暂不可读取；没有返回密钥，请联系支持。') from None
