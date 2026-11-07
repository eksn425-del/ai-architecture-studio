"""Single maintenance worker; PostgreSQL advisory lock prevents overlapping replicas."""
import json, logging, signal, threading
from sqlalchemy import text,select
from .config import Settings
from .db import engine_for,users
from .recovery import recover_stale
from .ledger import audit_wallet

def cycle(engine,age_seconds=960):
    with engine.connect() as lock:
        postgres=engine.dialect.name=='postgresql'
        if postgres and not lock.execute(text('SELECT pg_try_advisory_lock(827341925)')).scalar():return {'status':'another_worker_active'}
        try:
            recovered=recover_stale(engine,age_seconds=age_seconds)
            from .wechat_payments import recover_pending
            payments=recover_pending(engine)
            with engine.connect() as c:ids=c.execute(select(users.c.id)).scalars().all()
            consistent=all(audit_wallet(engine,u)['consistent'] for u in ids)
            return {'status':'ok' if consistent else 'audit_failed','accounts':len(ids),'recovery':recovered,'payment_recovery':payments,'consistent':consistent}
        finally:
            if postgres:lock.execute(text('SELECT pg_advisory_unlock(827341925)'))

def main():
    settings=Settings.from_env();engine=engine_for(settings.database_url);stop=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
    try:
        while not stop.is_set():
            try:
                report=cycle(engine,max([900]+[int(m.get('timeouts',{}).get('total',900)) for m in settings.models.values()])+60)
                # Recovery contains only task counts; no prompt, account secret or source data.
                print(json.dumps(report),flush=True)
            except Exception as exc:logging.error('Maintenance failed: %s',type(exc).__name__)
            stop.wait(60)
    finally:engine.dispose()
if __name__=='__main__':main()
