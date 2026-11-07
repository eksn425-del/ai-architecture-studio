"""Actual browser/HTTP/QR UI, synthetic provider query; not a real payment."""
import os
from pathlib import Path
import socket
import threading
import time

import pytest

pw=pytest.importorskip('playwright.sync_api')
import uvicorn
from sqlalchemy import update
from cloud.config import Settings
from cloud.db import migrate, orders
from cloud.auth import create_identity,new_session
from cloud.ledger import create_order,payment_paid,audit_wallet
from cloud.main import create_app
from cloud import wechat_payments as wx

pytestmark=pytest.mark.skipif(os.getenv('KSTUDIO_RUN_BROWSER_TESTS')!='1',reason='Explicit browser fixture only')


def test_wechat_qr_query_close_and_disabled_new_orders(tmp_path,monkeypatch):
    executable=Path(os.getenv('KSTUDIO_TEST_BROWSER',r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'))
    if not executable.is_file():pytest.skip('Installed browser absent')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base='http://127.0.0.1:'+str(port)
    settings=Settings(database_url='sqlite:///'+str(tmp_path/'cloud.sqlite'),
        session_secret='isolated-browser-payment-secret-not-production',environment='test',public_url=base,
        website_dir=str(Path(__file__).resolve().parents[2]/'website'),payment_provider='wechat_native',
        payment_enabled=False,prices_confirmed=True,
        operator={'name':'Fixture <script>unsafe</script>','support_url':'javascript:alert(1)',
                  'privacy_contact':'fixture privacy channel','refund_policy':'fixture refund rule'},
        prices={'version':'fixture','packages':{'one':{'name':'Fixture only','amount':990,'currency':'cny','credits':1000}}})
    app=create_app(settings);engine=app.state.engine;migrate(engine)
    user=create_identity(engine,'fixture|payment-browser','Payment browser fixture')
    token,_=new_session(engine,user['id'],'browser',3600)
    def make_order(key):
        order=create_order(engine,user['id'],key,'one',settings.prices['packages']['one'])
        with engine.begin() as c:c.execute(update(orders).where(orders.c.id==order['id']).values(
            state='checkout',provider_session='wxnative:'+order['id'],checkout_url='weixin://wxpay/bizpayurl?pr=fixture'))
        return order
    first=make_order('first-ui');second=make_order('second-ui');calls=[]
    def query(e,s,order_id):
        calls.append(('query',order_id))
        payment_paid(e,'fixture-event',order_id,'fixture-tx',990,'cny','wxnative:'+order_id)
        return {'state':'paid','provider_state':'SUCCESS','order_id':order_id}
    def close(e,s,order_id):
        calls.append(('close',order_id))
        with e.begin() as c:c.execute(update(orders).where(orders.c.id==order_id).values(state='closed'))
        return {'state':'closed','provider_state':'CLOSED','order_id':order_id}
    monkeypatch.setattr(wx,'query_order',query);monkeypatch.setattr(wx,'close_order',close)
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    try:
        for _ in range(100):
            if server.started:break
            time.sleep(.05)
        assert server.started
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=str(executable),headless=True)
            context=browser.new_context(viewport={'width':1440,'height':1000})
            context.add_cookies([{'name':'kstudio_session','value':token,'url':base}])
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+'/account/orders/'+first['id'])
            page.locator('img[data-payment-qr]').wait_for()
            page.wait_for_function('document.querySelector("img[data-payment-qr]").naturalWidth > 0')
            assert page.get_by_role('button',name='充值尚未开放').is_disabled()
            assert '¥9.90' in page.locator('main').inner_text()
            assert not calls
            page.screenshot(path=str(tmp_path/'qr-fixture.png'),full_page=True)
            page.get_by_role('button',name='查询微信支付结果').click()
            page.wait_for_function('document.querySelector("main").textContent.includes("已支付")')
            assert page.locator('img[data-payment-qr]').count()==0
            assert audit_wallet(engine,user['id'])['balance']==1000
            page.goto(base+'/account/orders/'+second['id'])
            page.locator('img[data-payment-qr]').wait_for()
            page.get_by_role('button',name='关闭未支付订单').click()
            page.wait_for_function('document.querySelector("main").textContent.includes("已关闭")')
            assert page.locator('img[data-payment-qr]').count()==0
            assert calls==[('query',first['id']),('close',second['id'])]
            page.goto(base+'/privacy')
            page.get_by_role('heading',name='运营信息').wait_for()
            assert 'Fixture <script>unsafe</script>' in page.locator('main').inner_text()
            assert 'fixture privacy channel' in page.locator('main').inner_text()
            assert page.locator('main script').count()==0
            assert page.locator('a[href^="javascript:"]').count()==0
            page.goto(base+'/account/privacy')
            assert page.get_by_role('link',name='重新验证身份').get_attribute('href').endswith('return_to=%2Faccount%2Fprivacy')
            page.goto(base+'/account/connections')
            page.get_by_role('heading',name='账户配置暂不可用。').wait_for()
            assert page.get_by_role('link',name='返回账户').is_visible()
            assert page.get_by_role('button',name='重试读取配置').is_visible()
            assert not errors
            browser.close()
    finally:
        server.should_exit=True;thread.join(10);engine.dispose()
