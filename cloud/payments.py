"""Stripe official SDK adapter; no unsigned payment-success endpoint."""
import stripe
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from .db import orders,payment_reconciliation,now
from .ledger import BillingError, payment_paid, refund_confirmed

def checkout(engine,settings,order):
    if not settings.stripe_key:raise BillingError('Payment merchant not configured')
    # Idempotency lives both in our order and at provider, including network retry.
    client=stripe.StripeClient(settings.stripe_key)
    session=client.v1.checkout.sessions.create(params={
        'mode':'payment','client_reference_id':order['id'],
        'metadata':{'kstudio_order':order['id']},
        'payment_intent_data':{'metadata':{'kstudio_order':order['id']}},
        'line_items':[{'price_data':{'currency':order['currency'],'unit_amount':order['amount'],'product_data':{'name':'K Studio credits '+order['package']}},'quantity':1}],
        'success_url':settings.public_url+'/account/orders?payment=returned',
        'cancel_url':settings.public_url+'/account/orders?payment=cancelled'},
        options={'idempotency_key':'kstudio-checkout-'+order['id']})
    with engine.begin() as c:
        c.execute(update(orders).where(orders.c.id==order['id'],orders.c.state=='created').values(state='checkout',provider_session=session.id,checkout_url=session.url))
    return {'order_id':order['id'],'checkout_url':session.url,'state':'checkout'}

def verify_webhook(settings,raw,signature):
    if not settings.stripe_webhook_secret:raise BillingError('Payment webhook disabled')
    event=stripe.Webhook.construct_event(raw,signature,settings.stripe_webhook_secret,tolerance=300)
    expected_live=settings.environment=='production'
    if bool(event.get('livemode'))!=expected_live:raise BillingError('Payment environment mismatch')
    return event

def apply_event(engine,event):
    data=event['data']['object'];kind=event['type']
    if kind in ('checkout.session.completed','checkout.session.async_payment_succeeded'):
        if data.get('payment_status')!='paid':return 'awaiting_payment'
        order=data.get('metadata',{}).get('kstudio_order')
        if not order or data.get('client_reference_id')!=order:raise BillingError('Missing order identity')
        return payment_paid(engine,event['id'],order,data['payment_intent'],data['amount_total'],data['currency'],data['id'])
    if kind=='charge.refunded':
        with engine.connect() as c:
            row=c.execute(select(orders).where(orders.c.payment_id==data.get('payment_intent'))).mappings().first()
        if not row:raise BillingError('Refund order not found')
        reason='Partial refund requires reviewed proportional credit reversal'
        if data.get('refunded') and data.get('amount_refunded')==data.get('amount'):
            try:return refund_confirmed(engine,row['id'],event['id'],data['amount_refunded'])
            except BillingError as exc:reason=str(exc)
        try:
            with engine.begin() as c:
                c.execute(payment_reconciliation.insert().values(event_id=event['id'],order_id=row['id'],amount=data['amount_refunded'],reason=reason,state='pending',created=now()))
                c.execute(update(orders).where(orders.c.id==row['id'],orders.c.state=='paid').values(state='refund_pending_reconciliation'))
        except IntegrityError:pass
        return 'refund_pending_reconciliation'
    return 'ignored'
