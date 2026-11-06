"""Crash recovery never replays a potentially billed upstream request."""
from sqlalchemy import select, update
from .db import tasks, now
from .ledger import settle

def recover_stale(engine,age_seconds=900):
    if age_seconds<300:raise ValueError('Recovery age must exceed live request timeout')
    cutoff=now()-age_seconds;recovered=[]
    with engine.connect() as c:
        rows=c.execute(select(tasks).where(tasks.c.updated<cutoff,tasks.c.state.in_(['reserved','running']))).mappings().all()
    for row in rows:
        # Claim the stale state conditionally; a concurrent active transition wins.
        with engine.begin() as c:
            changed=c.execute(update(tasks).where(tasks.c.id==row['id'],tasks.c.state==row['state'],tasks.c.updated==row['updated']).values(state='pending_reconciliation',updated=now())).rowcount
        if not changed:continue
        if row['state']=='reserved':settle(engine,row['user_id'],row['id'],0,'recovery: reserved task was never dispatched',reconcile=True)
        recovered.append({'task_id':row['id'],'outcome':'released_without_dispatch' if row['state']=='reserved' else 'pending_reconciliation'})
    return recovered
