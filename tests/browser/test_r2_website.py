"""Opt-in real Edge + control-plane UI smoke, with isolated synthetic identities.

KSTUDIO_RUN_BROWSER_TESTS=1 python -m pytest tests/browser/test_r2_website.py
No upstream model, identity provider, or payment service is contacted.
"""
import os
import socket
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip('sqlalchemy')
pytest.importorskip('authlib')
playwright = pytest.importorskip('playwright.sync_api')
from cloud.auth import create_identity, new_session
from cloud.config import Settings
from cloud.db import migrate
from cloud.main import create_app
import uvicorn

pytestmark = pytest.mark.skipif(os.getenv('KSTUDIO_RUN_BROWSER_TESTS') != '1', reason='Explicit local browser acceptance only')


def test_r2_public_routes_and_real_local_account(tmp_path):
    browser_exe = Path(os.getenv('KSTUDIO_TEST_BROWSER', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'))
    if not browser_exe.is_file():
        pytest.skip('Installed test browser unavailable; no automatic browser download')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    root = Path(__file__).resolve().parents[2]
    settings = Settings(database_url='sqlite:///' + str(tmp_path / 'website.sqlite'),
                        session_secret='browser-fixture-secret-never-production-20261104',
                        environment='test', public_url=base, website_dir=str(root / 'website'))
    app = create_app(settings)
    migrate(app.state.engine)
    user = create_identity(app.state.engine, 'fixture|r2-browser', '本地验收 fixture（非真实用户）')
    token, _ = new_session(app.state.engine, user['id'], 'Browser fixture', 3600)
    new_session(app.state.engine, user['id'], 'Revocation fixture', 3600)
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(.05)
        assert server.started
        with playwright.sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=str(browser_exe), headless=True)
            try:
                context = browser.new_context(viewport={'width': 1440, 'height': 960})
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                routes = ['/', '/download', '/docs/start', '/docs/connect', '/pricing',
                          '/auth/login', '/auth/register', '/auth/recover', '/account/usage',
                          '/account/orders', '/account/payment-return', '/status', '/feedback',
                          '/privacy', '/terms', '/licenses']
                for width in (1440, 900, 390):
                    page.set_viewport_size({'width': width, 'height': 960})
                    for route in routes:
                        page.goto(base + route)
                        page.wait_for_function('document.querySelector("main h1") !== null')
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (route, width)
                    if width == 390:
                        page.locator('#menu-toggle').click()
                        assert page.locator('#main-nav').is_visible()
                        page.keyboard.press('Escape')
                        assert not page.locator('#main-nav').is_visible()
                page.goto(base + '/download')
                page.get_by_role('button', name='公开下载尚未开放').wait_for()
                assert page.get_by_role('button', name='公开下载尚未开放').is_disabled()
                page.goto(base + '/auth/login')
                page.get_by_role('button', name='账户服务尚未开放').wait_for()
                assert page.get_by_role('button', name='账户服务尚未开放').is_disabled()
                page.goto(base + '/feedback')
                page.locator('#feedback-message').fill('本地浏览器验收：检查真实反馈提交与服务端回执。')
                page.locator('#feedback-form button').click()
                page.wait_for_function('document.querySelector("#form-status").textContent.includes("反馈已接收，编号")')
                context.add_cookies([{'name':'kstudio_session', 'value':token, 'domain':'127.0.0.1',
                                     'path':'/', 'httpOnly':True, 'sameSite':'Lax'}])
                for route in ('/account/usage', '/account/orders', '/account/payment-return', '/account/devices'):
                    page.goto(base + route)
                    page.locator('#logout').wait_for()
                    assert '本地验收 fixture' in page.locator('main').inner_text()
                row = page.get_by_role('row').filter(has_text='Revocation fixture')
                row.get_by_role('button', name='撤销设备').click()
                page.wait_for_function('Array.from(document.querySelectorAll("tr")).some(r => r.textContent.includes("Revocation fixture") && r.textContent.includes("已撤销"))')
                assert page.get_by_role('row').filter(has_text='Revocation fixture').get_by_role('button').is_disabled()
                page.locator('#logout').click()
                page.wait_for_url('**/auth/login')
                assert page.request.get(base + '/api/auth/me').json() == {'authenticated': False}
                assert not errors
            finally:
                browser.close()
    finally:
        server.should_exit = True
        thread.join(5)
        app.state.engine.dispose()
