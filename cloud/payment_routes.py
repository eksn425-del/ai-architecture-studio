"""Account-owned WeChat operations; no browser return is payment proof."""
import asyncio
from io import BytesIO

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .db import orders, now
from . import wechat_payments as wx


def register_routes(app, engine, settings, identity, json_object, rate):
    def own_order(request, order_id):
        user = identity(request)
        with engine.connect() as c:
            item = c.execute(select(orders).where(orders.c.id == order_id,
                             orders.c.user_id == user['user_id'])).mappings().first()
        if item is None:
            raise HTTPException(404, '订单不存在。')
        if item['provider_session'] != 'wxnative:'+item['id']:
            raise HTTPException(409, '此订单不是微信支付订单。')
        return user, dict(item)

    def administrator(request):
        user = identity(request)
        if request.headers.get('authorization','').startswith('Bearer ') or user.get('refresh_hash') or user.get('device_name')!='browser':
            raise HTTPException(403, '请在官网重新登录后进行支付管理。')
        if user['subject'] not in settings.admin_subjects:
            raise HTTPException(403, '需要支付管理权限。')
        if not 0 <= now()-int(user.get('authenticated_at', 0)) <= 300:
            raise HTTPException(403, '请重新登录后执行敏感支付操作。')
        rate('wechat-admin:'+user['user_id'], 10)
        return user

    @app.get('/api/account/orders/{order_id}/payment')
    async def payment_code(order_id: str, request: Request):
        user, item = own_order(request, order_id)
        rate('wechat-code:'+user['user_id'], 30)
        # Stored provider result only: GET never creates/retries a payment.
        code = item.get('checkout_url') or ''
        if (item['state'] != 'checkout' or not code.startswith('weixin://wxpay/')
                or len(code) > 2048 or item['created']+1800 <= now()):
            raise HTTPException(409, '付款码已失效或订单已结束，请刷新订单状态。')
        import qrcode
        import qrcode.image.svg
        output = BytesIO()
        qrcode.make(code, image_factory=qrcode.image.svg.SvgPathImage, border=4).save(output)
        return Response(output.getvalue(), media_type='image/svg+xml', headers={
            'Cache-Control': 'no-store', 'Content-Security-Policy': "default-src 'none'"})

    @app.post('/api/account/orders/{order_id}/query')
    async def query_payment(order_id: str, request: Request):
        user, _ = own_order(request, order_id)
        rate('wechat-query:'+user['user_id'], 10)
        return await asyncio.to_thread(wx.query_order, engine, settings, order_id)

    @app.post('/api/account/orders/{order_id}/close')
    async def close_payment(order_id: str, request: Request):
        user, _ = own_order(request, order_id)
        rate('wechat-close:'+user['user_id'], 5)
        return await asyncio.to_thread(wx.close_order, engine, settings, order_id)

    @app.post('/api/payments/wechat/notify')
    async def notification(request: Request):
        raw = await request.body()
        if len(raw) > wx.MAX_RESPONSE_BYTES:
            return JSONResponse({'code': 'FAIL', 'message': '通知过大'}, status_code=413)
        try:
            # Validation → durable minimized inbox → idempotent application.
            # If application fails, no acknowledgement; recovery replays inbox.
            await asyncio.to_thread(wx.receive_notification, engine, settings, raw, dict(request.headers))
        except wx.PaymentError:
            return JSONResponse({'code': 'FAIL', 'message': '通知验证失败'}, status_code=400)
        except SQLAlchemyError:
            return JSONResponse({'code': 'FAIL', 'message': '通知保存暂不可用'}, status_code=503)
        return Response(status_code=204)

    @app.post('/api/admin/orders/{order_id}/refund')
    async def request_refund(order_id: str, request: Request):
        user = administrator(request)
        body = await json_object(request)
        reason = body.get('reason')
        if body.get('confirm_order_id') != order_id or not isinstance(reason, str) or not 10 <= len(reason) <= 200:
            raise HTTPException(400, '请确认订单编号并填写退款授权与原因。')
        # Administrator entitlement and explicit order confirmation are both
        # required; ordinary user refund requests go through support review.
        return await asyncio.to_thread(wx.request_refund, engine, settings, order_id,
                                       reason, approved_by=user['user_id'])

    @app.post('/api/admin/refunds/{refund_id}/query')
    async def query_refund(refund_id: str, request: Request):
        administrator(request)
        return await asyncio.to_thread(wx.query_refund, engine, settings, refund_id)

    @app.post('/api/admin/payments/wechat/recover')
    async def recover(request: Request):
        administrator(request)
        return {'results': await asyncio.to_thread(wx.recover_pending, engine, 100)}
