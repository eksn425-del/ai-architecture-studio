"""WeChat Native v3, pinned public keys, durable verified inbox and refund holds.

Only the fixed official API origin is contacted. Production credentials are read
from private mounted files. No response/request bodies are logged. Routes must
authenticate/CSRF-check account operations and run this synchronous adapter in a
threadpool. Notifications are authenticated here, before durable acceptance.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import secrets
import time
from urllib.parse import quote, urlencode

import httpx
from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import Table, Column, String, Text, BigInteger, ForeignKey, func, select, update
from sqlalchemy.exc import IntegrityError

from .db import metadata, orders, wallets, payment_reconciliation, now, uid
from .ledger import BillingError, payment_paid, event as ledger_event

API_ORIGIN = 'https://api.mch.weixin.qq.com'
MAX_RESPONSE_BYTES = 1_000_000
MIN_ORDER_EXPIRY_MARGIN_SECONDS = 65
verified_payment_inbox = Table(
    'verified_payment_inbox', metadata,
    Column('id', String(160), primary_key=True),
    Column('order_id', ForeignKey('orders.id'), nullable=False),
    Column('kind', String(40), nullable=False),
    Column('payload', Text, nullable=False),
    Column('digest', String(64), nullable=False),
    Column('state', String(32), nullable=False),
    Column('created', BigInteger, nullable=False),
    Column('updated', BigInteger, nullable=False),
)
wechat_refunds = Table(
    'wechat_refunds', metadata,
    Column('id', String(64), primary_key=True),
    Column('order_id', ForeignKey('orders.id'), unique=True, nullable=False),
    Column('user_id', ForeignKey('users.id'), nullable=False),
    Column('amount', BigInteger, nullable=False),
    Column('credits', BigInteger, nullable=False),
    Column('held', BigInteger, nullable=False),
    Column('provider_id', String(128)),
    Column('approved_by', String(64)),
    Column('reason', String(200), nullable=False),
    Column('state', String(32), nullable=False),
    Column('created', BigInteger, nullable=False),
    Column('updated', BigInteger, nullable=False),
)


class PaymentError(BillingError):
    """Safe error message; never interpolates a provider body or credentials."""


def configuration_status(settings):
    names = ('wechatpay_mchid', 'wechatpay_appid', 'wechatpay_merchant_serial',
             'wechatpay_api_v3_key_file', 'wechatpay_merchant_private_key_file',
             'wechatpay_verify_material_file')
    missing = [name for name in names if not getattr(settings, name, '')]
    return {'configured': not missing, 'missing': missing,
            'enabled': getattr(settings, 'payment_provider', '') == 'wechat_native'
            and not missing and bool(settings.prices_confirmed)
            and bool(getattr(settings, 'payment_enabled', True))}


def enabled(settings):
    return configuration_status(settings)['enabled']


def _identifier(value, maximum=64):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_*-]{1,'+str(maximum)+'}', value):
        raise PaymentError('Invalid payment identifier')
    return value


def _json(raw):
    if len(raw) > MAX_RESPONSE_BYTES:
        raise PaymentError('Payment payload too large')
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError):
        raise PaymentError('Invalid payment JSON') from None
    if not isinstance(result, dict):
        raise PaymentError('Invalid payment object')
    return result


class Client:
    """Strict public-key mode. Injected httpx transport is only for offline tests."""
    def __init__(self, settings, *, transport=None, clock=time.time):
        # Closing new payments must not block verification/settlement of already
        # accepted orders or administrator refund recovery.
        if not configuration_status(settings)['configured'] or getattr(settings, 'payment_provider', '') != 'wechat_native':
            raise PaymentError('WeChat payment is not configured and enabled')
        self.settings = settings
        self.clock = clock
        self.transport = transport
        try:
            self.private_key = serialization.load_pem_private_key(
                Path(settings.wechatpay_merchant_private_key_file).read_bytes(), password=None)
            if not isinstance(self.private_key, rsa.RSAPrivateKey) or self.private_key.key_size < 2048:
                raise ValueError('merchant key')
            self.api_key = Path(settings.wechatpay_api_v3_key_file).read_bytes().rstrip(b'\r\n')
            if len(self.api_key) != 32:
                raise ValueError('APIv3 key')
            material = _json(Path(settings.wechatpay_verify_material_file).read_bytes())
            self.public_keys = {}
            for key_id, pem in material['keys'].items():
                if not re.fullmatch(r'PUB_KEY_ID_[A-Za-z0-9_]{1,120}', key_id):
                    raise ValueError('public key id')
                key = serialization.load_pem_public_key(pem.encode('ascii'))
                if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
                    raise ValueError('public key')
                self.public_keys[key_id] = key
            if not self.public_keys:
                raise ValueError('empty key ring')
            self.active_public_key = material.get('active_key_id')
            if not self.active_public_key and len(self.public_keys) == 1:
                self.active_public_key = next(iter(self.public_keys))
            if self.active_public_key not in self.public_keys:
                raise ValueError('active public key id')
            _identifier(settings.wechatpay_mchid, 32)
            _identifier(settings.wechatpay_appid, 32)
            _identifier(settings.wechatpay_merchant_serial, 128)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise PaymentError('Invalid private WeChat payment configuration') from None

    def verify(self, raw, headers):
        if len(raw) > MAX_RESPONSE_BYTES:
            raise PaymentError('Payment response too large')
        headers = {str(k).lower(): str(v) for k, v in headers.items()}
        try:
            stamp = headers['wechatpay-timestamp']
            nonce = headers['wechatpay-nonce']
            serial = headers['wechatpay-serial']
            if headers.get('wechatpay-signature-type', 'WECHATPAY2-SHA256-RSA2048') != 'WECHATPAY2-SHA256-RSA2048':
                raise ValueError('signature type')
            if not re.fullmatch(r'[0-9]{1,12}', stamp) or abs(int(self.clock())-int(stamp)) > 300:
                raise ValueError('timestamp')
            if not nonce or len(nonce) > 256 or '\n' in nonce or '\r' in nonce:
                raise ValueError('nonce')
            key = self.public_keys[serial]
            signature = base64.b64decode(headers['wechatpay-signature'], validate=True)
            key.verify(signature, stamp.encode()+b'\n'+nonce.encode()+b'\n'+raw+b'\n',
                       padding.PKCS1v15(), hashes.SHA256())
        except (KeyError, ValueError, InvalidSignature):
            raise PaymentError('WeChat response signature or freshness verification failed') from None

    def request(self, method, path, payload=None):
        if not path.startswith('/v3/') or '\n' in path or '\r' in path:
            raise PaymentError('Invalid payment API path')
        body = b'' if payload is None else json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf8')
        stamp = str(int(self.clock()))
        nonce = secrets.token_hex(16)
        canonical = method.upper().encode()+b'\n'+path.encode()+b'\n'+stamp.encode()+b'\n'+nonce.encode()+b'\n'+body+b'\n'
        signature = base64.b64encode(self.private_key.sign(canonical, padding.PKCS1v15(), hashes.SHA256())).decode()
        authorization = ('WECHATPAY2-SHA256-RSA2048 mchid="'+self.settings.wechatpay_mchid+
                         '",nonce_str="'+nonce+'",timestamp="'+stamp+'",serial_no="'+
                         self.settings.wechatpay_merchant_serial+'",signature="'+signature+'"')
        try:
            with httpx.Client(transport=self.transport, timeout=httpx.Timeout(20, connect=5),
                              follow_redirects=False, trust_env=False) as client:
                with client.stream(method, API_ORIGIN+path, content=body, headers={
                        'Authorization': authorization, 'Accept': 'application/json',
                        'Content-Type': 'application/json', 'User-Agent': 'KStudio-R3/1',
                        'Wechatpay-Serial': self.active_public_key}) as response:
                    chunks = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_RESPONSE_BYTES:
                            raise PaymentError('Payment response too large')
                        chunks.append(chunk)
                    raw = b''.join(chunks)
                    self.verify(raw, response.headers)
                    if not 200 <= response.status_code < 300:
                        # A verified error can still describe an unknown remote commit.
                        # Callers must query the original order/refund, never create a new ID.
                        raise PaymentError('WeChat rejected the request; query the original operation before retry')
                    return {} if response.status_code == 204 and not raw else _json(raw)
        except httpx.HTTPError:
            raise PaymentError('WeChat request outcome unknown; query the original operation') from None

    def notification(self, raw, headers):
        self.verify(raw, headers)
        envelope = _json(raw)
        resource = envelope.get('resource', {})
        try:
            if envelope.get('resource_type') != 'encrypt-resource' or resource['algorithm'] != 'AEAD_AES_256_GCM':
                raise ValueError('algorithm')
            nonce = resource['nonce'].encode()
            if len(nonce) != 12:
                raise ValueError('nonce')
            plaintext = AESGCM(self.api_key).decrypt(nonce, base64.b64decode(resource['ciphertext'], validate=True),
                                                  resource.get('associated_data', '').encode())
            data = _json(plaintext)
            event_id = _identifier(envelope['id'], 128)
            kind = envelope['event_type']
        except (KeyError, ValueError, TypeError, AttributeError, InvalidTag):
            raise PaymentError('Invalid encrypted payment notification') from None
        if kind not in ('TRANSACTION.SUCCESS', 'REFUND.SUCCESS', 'REFUND.CLOSED', 'REFUND.ABNORMAL'):
            raise PaymentError('Unsupported WeChat event type')
        return 'wx:'+event_id, kind, data


def _order(engine, order_id):
    _identifier(order_id, 32)
    with engine.connect() as c:
        row = c.execute(select(orders).where(orders.c.id == order_id)).mappings().first()
    if not row:
        raise PaymentError('Payment order not found')
    return dict(row)


def _session(order):
    return 'wxnative:'+order['id']


def checkout(engine, settings, order, *, client=None):
    if not enabled(settings):
        raise PaymentError('New WeChat payments are disabled')
    client = client or Client(settings)
    order = _order(engine, order['id'])
    if str(order['currency']).upper() != 'CNY':
        raise PaymentError('WeChat Native requires CNY')
    if order['state'] not in ('created', 'checkout'):
        return {'order_id': order['id'], 'state': order['state']}
    if order['provider_session'] not in (None, _session(order)):
        raise PaymentError('Order already belongs to another payment provider')
    from datetime import datetime, timezone
    expires = int(order['created'])+1800
    if expires <= now():
        raise PaymentError('Payment window expired; close and create a new order')
    if order['provider_session'] == _session(order):
        return checkout_snapshot(order,expires)
    if expires-now() < MIN_ORDER_EXPIRY_MARGIN_SECONDS:
        raise PaymentError('Payment window expired; close and create a new order')
    # Claim the original merchant order once before dispatch. Concurrent callers
    # and ambiguous transport outcomes follow the existing order's query path.
    with engine.begin() as c:
        changed = c.execute(update(orders).where(orders.c.id == order['id'],
            orders.c.state=='created',orders.c.provider_session.is_(None))
            .values(state='checkout', provider_session=_session(order))).rowcount
    if changed != 1:
        return checkout_snapshot(_order(engine,order['id']),expires)
    try:
        result = client.request('POST', '/v3/pay/transactions/native', {
            'appid': settings.wechatpay_appid, 'mchid': settings.wechatpay_mchid,
            'description': 'K Studio credits '+str(order['package'])[:64],
            'out_trade_no': order['id'], 'notify_url': settings.public_url.rstrip('/')+'/api/payments/wechat/notify',
            'time_expire': datetime.fromtimestamp(expires, timezone.utc).isoformat(),
            'amount': {'total': order['amount'], 'currency': 'CNY'}})
    except PaymentError:
        return checkout_snapshot(_order(engine,order['id']),expires)
    code = result.get('code_url', '')
    if isinstance(code,str) and code.startswith('weixin://wxpay/') and len(code)<=2048:
        with engine.begin() as c:
            c.execute(update(orders).where(orders.c.id == order['id'],orders.c.state=='checkout')
                      .values(checkout_url=code))
    return checkout_snapshot(_order(engine,order['id']),expires)


def checkout_snapshot(order,expires):
    code=order['checkout_url'] if order['state']=='checkout' else None
    return {'order_id':order['id'],'state':order['state'],'provider':'wechat_native',
            'code_url':code,'expires':expires,'checkout_url':None,
            'query_required':order['state']=='checkout' and not code}


def _transaction_payload(settings, order, data):
    money = data.get('amount', {})
    if not isinstance(money, dict):
        raise PaymentError('Invalid payment amount object')
    if (data.get('mchid') != settings.wechatpay_mchid or data.get('appid') != settings.wechatpay_appid
            or data.get('out_trade_no') != order['id'] or order['provider_session'] != _session(order)
            or money.get('total') != order['amount'] or type(money.get('total')) is not int
            or money.get('currency') != 'CNY' or str(order['currency']).upper() != 'CNY'):
        raise PaymentError('Payment merchant, app, order or amount mismatch')
    if data.get('trade_state') != 'SUCCESS':
        raise PaymentError('Payment has not succeeded')
    tx = _identifier(data.get('transaction_id'), 128)
    return {'mchid': data['mchid'], 'appid': data['appid'], 'out_trade_no': order['id'],
            'transaction_id': tx, 'trade_state': 'SUCCESS',
            'amount': {'total': order['amount'], 'currency': 'CNY'}}


def _store_inbox(engine, event_id, kind, order, payload):
    packed = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(packed.encode()).hexdigest()
    try:
        with engine.begin() as c:
            c.execute(verified_payment_inbox.insert().values(id=event_id, order_id=order['id'], kind=kind,
                payload=packed, digest=digest, state='pending', created=now(), updated=now()))
    except IntegrityError:
        with engine.connect() as c:
            old = c.execute(select(verified_payment_inbox).where(verified_payment_inbox.c.id == event_id)).mappings().one()
        if old['digest'] != digest or old['order_id'] != order['id'] or old['kind'] != kind:
            raise PaymentError('Verified event identifier conflicts with prior receipt')


def replay_inbox(engine, event_id):
    """Safe recovery of already verified, minimized receipts; no raw PII/key stored."""
    with engine.connect() as c:
        row = c.execute(select(verified_payment_inbox).where(verified_payment_inbox.c.id == event_id)).mappings().one()
    data = json.loads(row['payload'])
    if hashlib.sha256(row['payload'].encode()).hexdigest() != row['digest']:
        raise PaymentError('Stored payment receipt integrity mismatch')
    order = _order(engine, row['order_id'])
    if row['kind'] == 'TRANSACTION.SUCCESS':
        result = payment_paid(engine, event_id, order['id'], data['transaction_id'], data['amount']['total'],
                              order['currency'], _session(order))
    else:
        result = _apply_refund(engine, order, data)
    with engine.begin() as c:
        c.execute(update(verified_payment_inbox).where(verified_payment_inbox.c.id == event_id)
                  .values(state='applied', updated=now()))
    return result


def receive_notification(engine, settings, raw, headers, *, client=None):
    client = client or Client(settings)
    event_id, kind, data = client.notification(raw, headers)
    order = _order(engine, data.get('out_trade_no'))
    if kind == 'TRANSACTION.SUCCESS':
        payload = _transaction_payload(settings, order, data)
    else:
        if data.get('mchid') != settings.wechatpay_mchid:
            raise PaymentError('Refund merchant mismatch')
        expected = kind.split('.', 1)[1]
        if data.get('refund_status') != expected:
            raise PaymentError('Refund event status mismatch')
        payload = _refund_payload(order, data, notification=True)
    _store_inbox(engine, event_id, kind, order, payload)
    return replay_inbox(engine, event_id)


def query_order(engine, settings, order_id, *, client=None):
    client = client or Client(settings)
    order = _order(engine, order_id)
    if order['provider_session'] != _session(order):
        raise PaymentError('Order is not a WeChat Native order')
    result = client.request('GET', '/v3/pay/transactions/out-trade-no/'+quote(order_id, safe='')+
                            '?'+urlencode({'mchid': settings.wechatpay_mchid}))
    if result.get('out_trade_no') != order_id or result.get('mchid') != settings.wechatpay_mchid or result.get('appid') != settings.wechatpay_appid:
        raise PaymentError('Queried payment identity mismatch')
    state = result.get('trade_state')
    if state == 'SUCCESS':
        payload = _transaction_payload(settings, order, result)
        event_id = 'wxquery:'+payload['transaction_id']
        _store_inbox(engine, event_id, 'TRANSACTION.SUCCESS', order, payload)
        replay_inbox(engine, event_id)
    elif state == 'CLOSED':
        with engine.begin() as c:
            c.execute(update(orders).where(orders.c.id == order_id, orders.c.state.in_(['created', 'checkout']))
                      .values(state='closed'))
    elif state not in ('NOTPAY', 'USERPAYING', 'REFUND', 'REVOKED', 'PAYERROR'):
        raise PaymentError('Unknown WeChat order state')
    return {'order_id': order_id, 'provider_state': state, 'state': _order(engine, order_id)['state']}


def close_order(engine, settings, order_id, *, client=None):
    client = client or Client(settings)
    order = _order(engine, order_id)
    if order['provider_session'] != _session(order) or order['state'] not in ('created', 'checkout', 'closed'):
        raise PaymentError('Only unpaid WeChat orders can be closed')
    if order['state'] != 'closed':
        client.request('POST', '/v3/pay/transactions/out-trade-no/'+quote(order_id, safe='')+'/close',
                       {'mchid': settings.wechatpay_mchid})
    # A signed 204 acknowledgement is not substituted for final order readback.
    return query_order(engine, settings, order_id, client=client)


def _refund_payload(order, data, notification=False):
    money = data.get('amount', {})
    if not isinstance(money, dict):
        raise PaymentError('Invalid refund amount object')
    state = data.get('refund_status') if notification else data.get('status')
    # Official Native refund notifications omit currency. They are bound to an
    # already verified CNY order; queries explicitly return the currency.
    currency = money.get('currency', 'CNY' if notification else None)
    if (data.get('out_trade_no') != order['id'] or data.get('transaction_id') != order['payment_id']
            or order['provider_session'] != _session(order) or money.get('total') != order['amount']
            or type(money.get('total')) is not int or type(money.get('refund')) is not int
            or not 0 < money['refund'] <= order['amount'] or currency != 'CNY'
            or str(order['currency']).upper() != 'CNY'
            or state not in ('SUCCESS', 'PROCESSING', 'CLOSED', 'ABNORMAL')):
        raise PaymentError('Refund payment identity, amount or state mismatch')
    return {'out_trade_no': order['id'], 'transaction_id': order['payment_id'],
            'out_refund_no': _identifier(data.get('out_refund_no'), 64),
            'refund_id': _identifier(data.get('refund_id'), 128), 'status': state,
            'amount': {'total': money['total'], 'refund': money['refund'], 'currency': 'CNY'}}


def _manual_refund(c, order, data):
    key = 'wxrefund:'+data['refund_id']
    old = c.execute(select(payment_reconciliation).where(payment_reconciliation.c.event_id == key)).first()
    if not old:
        c.execute(payment_reconciliation.insert().values(event_id=key, order_id=order['id'],
            amount=data['amount']['refund'], reason='External/partial refund requires reviewed credit reconciliation',
            state='pending', created=now()))
    c.execute(update(orders).where(orders.c.id == order['id'], orders.c.state == 'paid')
              .values(state='refund_pending_reconciliation'))
    return 'refund_pending_reconciliation'


def _apply_refund(engine, order, data):
    with engine.begin() as c:
        # Order lock and conditional row transitions serialize even differently
        # identified query/callback notifications. Never debit twice.
        c.execute(update(orders).where(orders.c.id == order['id']).values(state=orders.c.state))
        row = c.execute(select(wechat_refunds).where(wechat_refunds.c.id == data['out_refund_no'],
                        wechat_refunds.c.order_id == order['id']).with_for_update()).mappings().first()
        if not row:
            return _manual_refund(c, order, data)
        if row['amount'] != data['amount']['refund'] or row['amount'] != order['amount']:
            raise PaymentError('Refund amount differs from approved hold')
        if row['provider_id'] and row['provider_id'] != data['refund_id']:
            raise PaymentError('Refund provider identity changed')
        state = data['status']
        if row['state'] in ('SUCCESS', 'CLOSED'):
            if row['state'] != state:
                # Old PROCESSING delivery after terminal status is harmless.
                if state in ('PROCESSING', 'ABNORMAL'):
                    return row['state'].lower()
                raise PaymentError('Conflicting terminal refund state')
            return 'duplicate'
        if state == 'SUCCESS':
            changed = c.execute(update(wallets).where(wallets.c.user_id == row['user_id'],
                wallets.c.reserved >= row['held'], wallets.c.balance >= row['credits'])
                .values(balance=wallets.c.balance-row['credits'], reserved=wallets.c.reserved-row['held'])).rowcount
            if changed != 1:
                raise PaymentError('Refund hold invariant failed; manual reconciliation required')
            ledger_event(c, row['user_id'], 'refund', -row['credits'], -row['held'], order['id'],
                         'wxrefund-settle:'+row['id'], 'package:'+order['package'], 'WeChat confirmed full refund')
            c.execute(update(orders).where(orders.c.id == order['id']).values(state='refunded'))
        elif state == 'CLOSED':
            c.execute(update(wallets).where(wallets.c.user_id == row['user_id'])
                      .values(reserved=wallets.c.reserved-row['held']))
            ledger_event(c, row['user_id'], 'refund_release', 0, -row['held'], order['id'],
                         'wxrefund-release:'+row['id'], 'package:'+order['package'], 'WeChat closed refund')
        c.execute(update(wechat_refunds).where(wechat_refunds.c.id == row['id'])
                  .values(state=state, provider_id=data['refund_id'], held=0 if state in ('SUCCESS','CLOSED') else row['held'], updated=now()))
        return 'refunded' if state == 'SUCCESS' else 'refund_'+state.lower()


def request_refund(engine, settings, order_id, reason='Owner-authorized refund', *, client=None, approved_by=None):
    """Administrator-only route. Full, unspent/unreserved credit refund only.

    Existing requests are queried, never silently resubmitted with another ID.
    Unknown remote state retains its hold and requires subsequent official query.
    """
    client = client or Client(settings)
    with engine.connect() as c:
        existing=c.execute(select(wechat_refunds.c.id).where(wechat_refunds.c.order_id==order_id)).scalar_one_or_none()
    if existing is not None:
        return query_refund(engine,settings,existing,client=client)
    verification = query_order(engine, settings, order_id, client=client)
    with engine.begin() as c:
        c.execute(update(orders).where(orders.c.id == order_id).values(state=orders.c.state))
        order = c.execute(select(orders).where(orders.c.id == order_id)).mappings().one()
        old = c.execute(select(wechat_refunds).where(wechat_refunds.c.order_id == order_id)).mappings().first()
        if old:
            refund_id = old['id']
            newly_created = False
        else:
            if order['state'] != 'paid' or verification['provider_state'] != 'SUCCESS':
                raise PaymentError('Refund requires a currently verified paid order')
            changed = c.execute(update(wallets).where(wallets.c.user_id == order['user_id'],
                wallets.c.balance-wallets.c.reserved >= order['credits'])
                .values(reserved=wallets.c.reserved+order['credits'])).rowcount
            if changed != 1:
                raise PaymentError('Refund needs manual review: credits are spent or reserved')
            refund_id = uid()
            c.execute(wechat_refunds.insert().values(id=refund_id, order_id=order_id, user_id=order['user_id'],
                amount=order['amount'], credits=order['credits'], held=order['credits'],
                approved_by=approved_by, reason=str(reason)[:200], state='REQUEST_PENDING', created=now(), updated=now()))
            ledger_event(c, order['user_id'], 'refund_reserve', 0, order['credits'], order_id,
                         'wxrefund-reserve:'+refund_id, 'package:'+order['package'], 'Pending WeChat refund hold')
            newly_created = True
    if not newly_created:
        return query_refund(engine, settings, refund_id, client=client)
    try:
        client.request('POST', '/v3/refund/domestic/refunds', {
            'transaction_id': order['payment_id'], 'out_refund_no': refund_id,
            'reason': str(reason)[:80], 'notify_url': settings.public_url.rstrip('/')+'/api/payments/wechat/notify',
            'amount': {'refund': order['amount'], 'total': order['amount'], 'currency': 'CNY'}})
    except PaymentError:
        with engine.begin() as c:
            c.execute(update(wechat_refunds).where(wechat_refunds.c.id == refund_id,
                wechat_refunds.c.state == 'REQUEST_PENDING').values(state='UNKNOWN', updated=now()))
        return {'refund_id': refund_id, 'order_id': order_id, 'state': 'UNKNOWN', 'requires_query': True}
    # Request acceptance, even if it says SUCCESS, is not our completion proof.
    return query_refund(engine, settings, refund_id, client=client)


def query_refund(engine, settings, refund_id, *, client=None):
    client = client or Client(settings)
    _identifier(refund_id, 64)
    with engine.connect() as c:
        row = c.execute(select(wechat_refunds).where(wechat_refunds.c.id == refund_id)).mappings().first()
    if not row:
        raise PaymentError('Refund request not found')
    order = _order(engine, row['order_id'])
    result = client.request('GET', '/v3/refund/domestic/refunds/'+quote(refund_id, safe=''))
    payload = _refund_payload(order, result)
    if payload['out_refund_no'] != refund_id:
        raise PaymentError('Queried refund identity mismatch')
    # Refund query responses do not include mchid/appid. Fixed merchant-signed
    # request + pinned WeChat signature + local payment binding supplies identity.
    event_id = 'wxrefundquery:'+refund_id+':'+payload['status']
    _store_inbox(engine, event_id, 'REFUND.'+payload['status'], order, payload)
    state = replay_inbox(engine, event_id)
    return {'refund_id': refund_id, 'order_id': order['id'], 'state': state,
            'provider_state': payload['status'], 'completed': payload['status'] == 'SUCCESS'}


def recover_pending(engine, limit=100):
    """No outbound requests: replay durable, previously verified receipts."""
    with engine.connect() as c:
        ids = c.execute(select(verified_payment_inbox.c.id).where(verified_payment_inbox.c.state == 'pending')
                        .order_by(verified_payment_inbox.c.created).limit(min(max(int(limit),1),1000))).scalars().all()
    results = []
    for event_id in ids:
        try:
            result = replay_inbox(engine, event_id)
        except BillingError:
            # Keep an irreconcilable verified receipt separate so it cannot
            # repeatedly prevent later good receipts from reaching settlement.
            with engine.begin() as c:
                c.execute(update(verified_payment_inbox).where(verified_payment_inbox.c.id == event_id,
                            verified_payment_inbox.c.state == 'pending').values(state='review_required', updated=now()))
            result = 'review_required'
        results.append({'event_id': event_id, 'result': result})
    return results


def pending_review_count(engine):
    with engine.connect() as c:
        inbox = c.execute(select(func.count()).select_from(verified_payment_inbox).where(
            verified_payment_inbox.c.state == 'review_required')).scalar_one()
        external = c.execute(select(func.count()).select_from(payment_reconciliation).where(
            payment_reconciliation.c.state == 'pending')).scalar_one()
    return {'verified_inbox': inbox, 'external_refunds': external}
