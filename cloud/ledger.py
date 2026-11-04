"""Atomic financial transitions. Unknown upstream cost stays reserved for reconciliation."""
import json
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from .db import wallets, ledger, tasks, orders, payment_events, outbox, now, uid

class BillingError(ValueError): pass
def amount(value):
    if type(value) is not int or not 0 <= value <= 10**12:raise BillingError('Invalid integer amount')
    return value
def event(c,user,kind,delta,reservation,ref,key,version,reason):
    c.execute(ledger.insert().values(id=uid(),user_id=user,kind=kind,amount=delta,reservation_delta=reservation,reference=ref,idempotency_key=key,price_version=version,reason=reason,created=now()))
def wallet(c,user):
    row=c.execute(select(wallets).where(wallets.c.user_id==user)).mappings().one()
    return {'available':row['balance']-row['reserved'],'balance':row['balance'],'reserved':row['reserved']}
def existing_task(c,user,key):
    return c.execute(select(tasks).where(tasks.c.user_id==user,tasks.c.key==key)).mappings().first()
def reserve(engine,user,key,mode,model,ceiling,price,daily_limit=None):
    amount(ceiling)
    if not isinstance(key,str) or not key or len(key)>128 or mode not in ('platform','byok'):raise BillingError('Invalid task request')
    def check(row):
        if row['mode']!=mode or row['model']!=model or row['reserve']!=ceiling:raise BillingError('Idempotency key reused for different request')
        return dict(row)
    try:
        with engine.begin() as c:
            old=existing_task(c,user,key)
            if old:return check(old)
            # Lock before the second idempotency read, including on SQLite.
            # A retry waiting behind its first request must return that request.
            c.execute(update(wallets).where(wallets.c.user_id==user).values(reserved=wallets.c.reserved))
            old=existing_task(c,user,key)
            if old:return check(old)
            # Atomic conditional debit serializes concurrent reservations on wallet.
            changed=c.execute(update(wallets).where(wallets.c.user_id==user,wallets.c.balance-wallets.c.reserved>=ceiling).values(reserved=wallets.c.reserved+ceiling)).rowcount
            if changed!=1:raise BillingError('Insufficient available credits')
            if daily_limit is not None:
                amount(daily_limit)
                today=(now()//86400)*86400
                rows=c.execute(select(tasks.c.charged,tasks.c.reserve).where(tasks.c.user_id==user,tasks.c.mode==mode,tasks.c.created>=today)).all()
                if sum(r.charged if r.charged is not None else r.reserve for r in rows)+ceiling>daily_limit:raise BillingError('Daily service usage limit reached')
            if mode=='platform' and c.execute(select(tasks.c.id).where(tasks.c.user_id==user,tasks.c.mode=='platform',tasks.c.state.in_(['reserved','running','pending_reconciliation']))).first():
                raise BillingError('Another platform task is active or awaiting reconciliation')
            row=dict(id=uid(),user_id=user,key=key,mode=mode,model=model,state='reserved',reserve=ceiling,charged=None,price_version=price['version'],price_json=json.dumps(price),created=now(),updated=now())
            c.execute(tasks.insert().values(**row))
            event(c,user,'reserve',0,ceiling,row['id'],'reserve:'+row['id'],price['version'],'task reservation')
            c.execute(outbox.insert().values(id=uid(),topic='task_reserved',reference=row['id'],state='pending',created=now()))
            return row
    except IntegrityError:
        with engine.connect() as c:
            old=existing_task(c,user,key)
            if old:return check(old)
        raise
def claim(engine,user,task_id):
    with engine.begin() as c:
        changed=c.execute(update(tasks).where(tasks.c.id==task_id,tasks.c.user_id==user,tasks.c.state=='reserved').values(state='running',updated=now())).rowcount
        if changed!=1:raise BillingError('Task already dispatched; do not replay upstream request')
def settle(engine,user,task_id,actual=None,reason='provider usage',reconcile=False):
    if actual is not None:amount(actual)
    with engine.begin() as c:
        row=c.execute(select(tasks).where(tasks.c.id==task_id,tasks.c.user_id==user).with_for_update()).mappings().first()
        if row is None:raise BillingError('Task not found')
        if row['state']=='settled':
            if actual!=row['charged']:raise BillingError('Conflicting duplicate settlement')
            return dict(row)
        if row['state']=='pending_reconciliation' and not reconcile:
            if actual is None:return dict(row)
            raise BillingError('Administrative reconciliation required')
        if actual is None or actual>row['reserve']:
            c.execute(update(tasks).where(tasks.c.id==task_id).values(state='pending_reconciliation',updated=now()))
            return {**row,'state':'pending_reconciliation'}
        changed=c.execute(update(tasks).where(tasks.c.id==task_id,tasks.c.state==row['state']).values(state='settled',charged=actual,updated=now())).rowcount
        if changed!=1:raise BillingError('Concurrent settlement conflict')
        c.execute(update(wallets).where(wallets.c.user_id==user).values(balance=wallets.c.balance-actual,reserved=wallets.c.reserved-row['reserve']))
        event(c,user,'settle',-actual,-row['reserve'],task_id,'settle:'+task_id,row['price_version'],reason)
        return {**row,'state':'settled','charged':actual}
def create_order(engine,user,key,package,config):
    amount(config['amount']);amount(config['credits'])
    if config['amount']<=0 or config['credits']<=0:raise BillingError('Invalid package')
    try:
        with engine.begin() as c:
            row=c.execute(select(orders).where(orders.c.user_id==user,orders.c.key==key)).mappings().first()
            if row:
                if row['package']!=package:raise BillingError('Idempotency key conflicts')
                return dict(row)
            row=dict(id=uid(),user_id=user,key=key,package=package,amount=config['amount'],currency=config['currency'],credits=config['credits'],state='created',created=now())
            c.execute(orders.insert().values(**row));return row
    except IntegrityError:
        with engine.connect() as c:
            row=c.execute(select(orders).where(orders.c.user_id==user,orders.c.key==key)).mappings().one()
            if row['package']!=package:raise BillingError('Idempotency key conflicts')
            return dict(row)
def payment_paid(engine,event_id,order_id,payment_id,paid_amount,currency,provider_session):
    try:
        with engine.begin() as c:
            row=c.execute(select(orders).where(orders.c.id==order_id).with_for_update()).mappings().first()
            if row is None:raise BillingError('Unknown order')
            if row['amount']!=paid_amount or row['currency']!=currency or row['provider_session']!=provider_session:raise BillingError('Payment identity/amount mismatch')
            seen=c.execute(select(payment_events).where(payment_events.c.id==event_id)).first()
            if seen:
                if seen.order_id!=order_id:raise BillingError('Payment event belongs to another order')
                return 'duplicate'
            c.execute(payment_events.insert().values(id=event_id,order_id=order_id,created=now()))
            if row['state'] in ('paid','refunded','refund_pending_reconciliation'):
                if row['payment_id']!=payment_id:raise BillingError('Order already has another payment')
                return 'duplicate'
            changed=c.execute(update(orders).where(orders.c.id==order_id,orders.c.state.in_(['created','checkout'])).values(state='paid',payment_id=payment_id)).rowcount
            if changed!=1:raise BillingError('Invalid payment state')
            c.execute(update(wallets).where(wallets.c.user_id==row['user_id']).values(balance=wallets.c.balance+row['credits']))
            event(c,row['user_id'],'recharge',row['credits'],0,order_id,'payment:'+payment_id,'package:'+row['package'],'verified payment')
            c.execute(outbox.insert().values(id=uid(),topic='payment_credited',reference=order_id,state='pending',created=now()))
            return 'credited'
    except IntegrityError:
        with engine.connect() as c:
            seen=c.execute(select(payment_events).where(payment_events.c.id==event_id,payment_events.c.order_id==order_id)).first()
            if seen:return 'duplicate'
        raise BillingError('Payment identifier already consumed')
def refund_confirmed(engine,order_id,refund_id,paid_amount):
    with engine.begin() as c:
        row=c.execute(select(orders).where(orders.c.id==order_id).with_for_update()).mappings().one()
        if paid_amount!=row['amount']:raise BillingError('Only full order refunds supported')
        if row['state']=='refunded':return 'duplicate'
        if row['state'] not in ('paid','refund_pending_reconciliation'):raise BillingError('Refund requires paid order')
        changed=c.execute(update(wallets).where(wallets.c.user_id==row['user_id'],wallets.c.balance-wallets.c.reserved>=row['credits']).values(balance=wallets.c.balance-row['credits'])).rowcount
        if changed!=1:raise BillingError('Refund needs manual reconciliation: credits spent or reserved')
        changed=c.execute(update(orders).where(orders.c.id==order_id,orders.c.state.in_(['paid','refund_pending_reconciliation'])).values(state='refunded')).rowcount
        if changed!=1:raise BillingError('Concurrent refund conflict')
        event(c,row['user_id'],'refund',-row['credits'],0,order_id,'refund:'+refund_id,'package:'+row['package'],'provider confirmed full refund')
        return 'refunded'
def audit_wallet(engine,user):
    with engine.connect() as c:
        w=wallet(c,user)
        sums=c.execute(select(func.coalesce(func.sum(ledger.c.amount),0),func.coalesce(func.sum(ledger.c.reservation_delta),0)).where(ledger.c.user_id==user)).one()
        return {**w,'event_balance':sums[0],'event_reserved':sums[1],'consistent':w['balance']==sums[0] and w['reserved']==sums[1]}
