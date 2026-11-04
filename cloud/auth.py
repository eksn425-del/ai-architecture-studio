import hashlib, secrets
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from .db import users, wallets, sessions, now, uid

def digest(token):return hashlib.sha256(token.encode()).hexdigest()
def create_identity(engine,subject,name):
    try:
        with engine.begin() as c:
            row=c.execute(select(users).where(users.c.subject==subject)).mappings().first()
            if row:return dict(row)
            row=dict(id=uid(),subject=subject,display_name=name[:128],created=now())
            c.execute(users.insert().values(**row));c.execute(wallets.insert().values(user_id=row['id'],balance=0,reserved=0));return row
    except IntegrityError:
        with engine.connect() as c:return dict(c.execute(select(users).where(users.c.subject==subject)).mappings().one())
def new_session(engine,user,device_name,seconds):
    with engine.begin() as c:
        token,csrf=issue_session(c,user,device_name,seconds)
    return token,csrf

def issue_session(c,user,device_name,seconds):
    token=secrets.token_urlsafe(48);csrf=secrets.token_urlsafe(32)
    c.execute(sessions.insert().values(id=uid(),user_id=user,token_hash=digest(token),csrf=csrf,device_name=device_name[:128],expires=now()+seconds,revoked=0))
    return token,csrf
def lookup(engine,token):
    if not token:return None
    with engine.connect() as c:
        row=c.execute(select(sessions,users.c.display_name,users.c.subject).join(users,sessions.c.user_id==users.c.id).where(sessions.c.token_hash==digest(token),sessions.c.revoked==0,sessions.c.expires>now())).mappings().first()
        return dict(row) if row else None
def revoke(engine,user,session_id):
    with engine.begin() as c:return c.execute(update(sessions).where(sessions.c.id==session_id,sessions.c.user_id==user).values(revoked=1)).rowcount
