"""Short-lived device authorization, backed by an existing OIDC browser session.

The desktop polls outbound HTTPS. No callback or remote model-control port opens.
PKCE binds redemption to the desktop's verifier. Identity remains Authlib/OIDC.
"""
import base64,hashlib,hmac,re,secrets
from sqlalchemy import select,update
from .db import device_authorizations as devices,now,uid,sessions
from .auth import digest,issue_session
from .ledger import BillingError

def normalized_code(value):return str(value).replace('-','').replace(' ','').upper()
def challenge(verifier):return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()

def start(engine,device_name,code_challenge):
    if not isinstance(code_challenge,str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}',code_challenge):raise BillingError('PKCE S256 challenge required')
    if not isinstance(device_name,str) or not 1<=len(device_name)<=80:raise BillingError('Invalid device name')
    code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(10));token=secrets.token_urlsafe(48)
    with engine.begin() as c:c.execute(devices.insert().values(id=uid(),device_hash=digest(token),user_code_hash=digest(code),challenge=code_challenge,device_name=device_name,state='pending',user_id=None,expires=now()+600,last_poll=0))
    return {'device_code':token,'user_code':code[:5]+'-'+code[5:],'expires_in':600,'interval':5}

def details(engine,code):
    with engine.connect() as c:row=c.execute(select(devices).where(devices.c.user_code_hash==digest(normalized_code(code)),devices.c.expires>now())).mappings().first()
    if not row:raise BillingError('设备登录码无效或已过期。')
    return {'device_name':row['device_name'],'expires':row['expires'],'state':row['state']}

def approve(engine,user,code):
    with engine.begin() as c:
        changed=c.execute(update(devices).where(devices.c.user_code_hash==digest(normalized_code(code)),devices.c.expires>now(),devices.c.state=='pending').values(state='approved',user_id=user)).rowcount
        if changed!=1:raise BillingError('设备登录码已使用或过期，请在桌面重新登录。')
    return {'approved':True}

def poll(engine,device_code,verifier,seconds):
    if not isinstance(device_code,str) or not isinstance(verifier,str) or not re.fullmatch(r'[A-Za-z0-9._~-]{43,128}',verifier):raise BillingError('Invalid device proof')
    with engine.begin() as c:
        row=c.execute(select(devices).where(devices.c.device_hash==digest(device_code)).with_for_update()).mappings().first()
        if not row or row['expires']<=now() or row['state']=='consumed':return {'status':'expired_token'}
        if not hmac.compare_digest(row['challenge'],challenge(verifier)):raise BillingError('Device PKCE proof mismatch')
        if row['last_poll']>now()-5:return {'status':'slow_down','interval':5}
        if row['state']=='pending':
            c.execute(update(devices).where(devices.c.id==row['id']).values(last_poll=now()))
            return {'status':'authorization_pending','interval':5}
        changed=c.execute(update(devices).where(devices.c.id==row['id'],devices.c.state=='approved').values(state='consumed',last_poll=now())).rowcount
        if changed!=1:return {'status':'expired_token'}
        # Device approval is not a fresh IdP authentication. The token must not
        # acquire recent-browser privileges merely because it was issued now.
        token,_=issue_session(c,row['user_id'],row['device_name'],seconds,authenticated_at=0)
        refresh=secrets.token_urlsafe(48)
        c.execute(update(sessions).where(sessions.c.token_hash==digest(token)).values(refresh_hash=digest(refresh),refresh_expires=now()+30*86400))
        return {'status':'authorized','access_token':token,'refresh_token':refresh,'token_type':'Bearer','expires':now()+seconds}

def rotate(engine,row,seconds):
    if not row.get('refresh_hash') or int(row.get('refresh_expires') or 0)<=now():
        raise BillingError('此刷新接口仅允许有效桌面设备，浏览器需要重新登录。')
    with engine.begin() as c:
        token=secrets.token_urlsafe(48)
        changed=c.execute(update(sessions).where(sessions.c.id==row['id'],sessions.c.revoked==0,
            sessions.c.expires>now(),sessions.c.token_hash==row['token_hash'],
            sessions.c.refresh_hash==row['refresh_hash'],sessions.c.refresh_expires>now())
            .values(token_hash=digest(token),expires=now()+seconds)).rowcount
        if changed!=1:raise BillingError('设备会话已撤销或过期，请重新登录。')
        # Keep device identity, refresh proof and original authenticated_at.
        # A second rotation of the same access proof fails the old-hash guard.
        return {'access_token':token,'token_type':'Bearer','expires':now()+seconds}

def refresh_device(engine,refresh_token,seconds):
    if not isinstance(refresh_token,str) or not 40<=len(refresh_token)<=128:raise BillingError('设备刷新凭据无效，请重新登录。')
    hashed=digest(refresh_token)
    with engine.begin() as c:
        row=c.execute(select(sessions).where(sessions.c.refresh_hash==hashed,sessions.c.refresh_expires>now(),sessions.c.revoked==0).with_for_update()).mappings().first()
        if not row:raise BillingError('设备已撤销、刷新凭据已使用或已过期，请重新登录。')
        token=secrets.token_urlsafe(48);refresh=secrets.token_urlsafe(48)
        changed=c.execute(update(sessions).where(sessions.c.id==row['id'],sessions.c.refresh_hash==hashed,sessions.c.revoked==0).values(token_hash=digest(token),refresh_hash=digest(refresh),expires=now()+seconds)).rowcount
        if changed!=1:raise BillingError('设备会话已更新，请重新登录。')
        return {'access_token':token,'refresh_token':refresh,'token_type':'Bearer','expires':now()+seconds}
