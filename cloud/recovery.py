"""Crash recovery never replays a potentially billed upstream request."""
from sqlalchemy import and_, or_, select, update
from .db import tasks, now
from .gateway import MAX_UPSTREAM_TOTAL_SECONDS
from .ledger import release_undispatched

RECOVERY_GRACE_SECONDS=60


def recover_stale(engine,age_seconds=900):
    if age_seconds<300:raise ValueError('Recovery age must exceed the reservation grace period')
    stamp=now()
    cutoff=stamp-age_seconds
    platform_running_cutoff=stamp-max(age_seconds,MAX_UPSTREAM_TOTAL_SECONDS+RECOVERY_GRACE_SECONDS)
    # A maintenance restart or model-config change must not reduce a previous
    # worker's possible lifetime. A never-dispatched reservation is distinct.
    old_platform_stream=and_(tasks.c.mode=='platform',tasks.c.state=='running',tasks.c.updated<platform_running_cutoff)
    other_stale=and_(tasks.c.updated<cutoff,or_(tasks.c.state=='reserved',
                                             and_(tasks.c.mode!='platform',tasks.c.state=='running')))
    recovered=[]
    with engine.connect() as c:
        rows=c.execute(select(tasks).where(or_(old_platform_stream,other_stale))).mappings().all()
    for row in rows:
        if row['state']=='reserved':
            changed=release_undispatched(engine,row['user_id'],row['id'],row['updated'])
            outcome='released_without_dispatch'
        else:
            with engine.begin() as c:
                changed=c.execute(update(tasks).where(tasks.c.id==row['id'],tasks.c.state=='running',
                    tasks.c.updated==row['updated']).values(state='pending_reconciliation',updated=now())).rowcount
            outcome='pending_reconciliation'
        if changed:
            recovered.append({'task_id':row['id'],'outcome':outcome})
    return recovered
