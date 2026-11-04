"""Opt-in real client/website UI + real Authlib PKCE/RS256 + isolated DPAPI.

Only the IdP and HTTPS transport are controlled fixtures, never production login
routes. No upstream inference, payments, SketchUp, or public TLS is exercised.
"""
import html
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import pytest

pytest.importorskip('authlib')
pytest.importorskip('sqlalchemy')
pw = pytest.importorskip('playwright.sync_api')
import httpx
import uvicorn
from authlib.jose import JsonWebKey, jwt
from cloud.config import Settings
from cloud.db import migrate
from cloud.main import create_app as create_cloud
from cloud.device_auth import challenge

pytestmark = pytest.mark.skipif(os.getenv('KSTUDIO_RUN_BROWSER_TESTS') != '1', reason='Explicit local browser acceptance only')


def serve(app):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            return server, thread, f'http://127.0.0.1:{port}'
        time.sleep(.05)
    raise AssertionError('Local fixture server failed to start')


def test_desktop_website_device_oidc_persistence_and_modes(tmp_path, monkeypatch):
    browser_exe = Path(os.getenv('KSTUDIO_TEST_BROWSER', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'))
    if not browser_exe.is_file():
        pytest.skip('Installed browser unavailable')
    if os.getenv('KSTUDIO_TEST_APP_SITE'):
        monkeypatch.syspath_prepend(os.environ['KSTUDIO_TEST_APP_SITE'])
    for key in list(os.environ):
        if key.endswith('API_KEY'):
            monkeypatch.delenv(key)
    for key, value in {
        'ARCH_STUDIO_RUNTIME_DIR': str(tmp_path/'desktop'),
        'KSTUDIO_CONNECTIONS_DIR': str(tmp_path/'connections'),
        'KSTUDIO_PERSONAL_DESKTOP':'1', 'KSTUDIO_AGENT_ENGINE':'deepseek-harness',
        'ARCH_STUDIO_STANDALONE':'1', 'ARCH_STUDIO_ECONOMY_PROVIDER':'litellm',
        'LITELLM_LOCAL_MODEL_COST_MAP':'True',
        'ARCH_STUDIO_MCP_CONFIG':str(tmp_path/'no-native-bridge.json'),
        'KSTUDIO_CLOUD_PUBLIC_URL':'https://cloud.fixture.test',
    }.items():
        monkeypatch.setenv(key, value)
    root = Path(__file__).resolve().parents[2]
    settings = Settings(database_url='sqlite:///'+str(tmp_path/'cloud.sqlite'),
        session_secret='real-browser-fixture-secret-never-production-20261104',
        public_url='https://cloud.fixture.test', environment='test',
        website_dir=str(root/'website'), oidc_metadata_url='https://id.fixture/.well-known/openid-configuration',
        oidc_client_id='browser-fixture', oidc_client_secret='fixture-secret',
        prices_confirmed=True, prices={'version':'fixture-1','byok_service_enabled':False,'byok_task_units':5},
        models={'fixture-model':{'enabled':True,'name':'验收模型（不会调用）','protocol':'chat-completions',
          'upstream_model':'fixture-model','base_url':'https://provider.invalid/v1','key_env':'UNSET_FIXTURE_PROVIDER',
          'capabilities':{'tools':True,'vision':True,'streaming':True,'context_window':16384,'max_output_tokens':4096}}})
    cloud = create_cloud(settings)
    migrate(cloud.state.engine)
    rsa = JsonWebKey.generate_key('RSA',2048,is_private=True,options={'kid':'browser-fixture'})
    authorization = {}
    def idp(request):
        if request.url.path == '/.well-known/openid-configuration':
            return httpx.Response(200,json={'issuer':'https://id.fixture','authorization_endpoint':'https://id.fixture/authorize',
                'token_endpoint':'https://id.fixture/token','jwks_uri':'https://id.fixture/jwks',
                'response_types_supported':['code'],'subject_types_supported':['public'],'id_token_signing_alg_values_supported':['RS256']})
        if request.url.path == '/jwks':
            return httpx.Response(200,json={'keys':[rsa.as_dict(is_private=False)]})
        if request.url.path == '/token':
            data = parse_qs(request.content.decode())
            assert challenge(data['code_verifier'][0]) == authorization['code_challenge'][0]
            token = jwt.encode({'alg':'RS256','kid':'browser-fixture'},
                {'iss':'https://id.fixture','sub':'browser-user','aud':'browser-fixture','exp':int(time.time())+600,
                 'iat':int(time.time()),'nonce':authorization['nonce'][0],'name':'真实 OIDC 流程 fixture'},rsa).decode()
            return httpx.Response(200,json={'access_token':'fixture-idp-token','token_type':'Bearer','expires_in':600,'id_token':token})
        raise AssertionError(str(request.url))
    cloud.state.oauth.identity.client_kwargs['transport'] = httpx.MockTransport(idp)
    cloud_server, cloud_thread, cloud_base = serve(cloud)
    client_server = None
    try:
        from app.main import create_app
        from app.cloud_account import CloudAccount
        app = create_app(tmp_path/'desktop')
        account = app.state.cloud_account
        def cloud_transport(request):
            return httpx.request(request.method, cloud_base+request.url.raw_path.decode(),
                headers=dict(request.headers), content=request.content, follow_redirects=False, trust_env=False)
        account.transport = httpx.MockTransport(cloud_transport)
        client_server, client_thread, client_base = serve(app)
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(browser_exe),headless=True)
            context = browser.new_context(viewport={'width':1440,'height':960})
            errors = []
            context.on('page',lambda page:page.on('pageerror',lambda e:errors.append(str(e))))
            def proxy(route):
                request=route.request
                response=httpx.request(request.method,cloud_base+urlparse(request.url).path+('?' + urlparse(request.url).query if urlparse(request.url).query else ''),
                    headers={**{k:v for k,v in request.all_headers().items() if k not in ('host','content-length')},'Host':'cloud.fixture.test'},
                    content=request.post_data_buffer,follow_redirects=False,trust_env=False)
                headers={k:v for k,v in response.headers.items() if k not in ('content-encoding','transfer-encoding','content-length')}
                route.fulfill(status=response.status_code,headers=headers,body=response.content)
            context.route('https://cloud.fixture.test/**',proxy)
            def consent(route):
                authorization.update(parse_qs(urlparse(route.request.url).query))
                assert authorization['code_challenge_method']==['S256']
                callback=authorization['redirect_uri'][0]+'?'+urlencode({'code':'fixture-code','state':authorization['state'][0]})
                route.fulfill(content_type='text/html',body='<h1>Isolated identity fixture</h1><p>No real identity provider contacted.</p><a id="fixture-consent" href="'+html.escape(callback,quote=True)+'">Confirm fixture identity</a>')
            context.route('https://id.fixture/authorize**',consent)
            page=context.new_page()
            page.goto(client_base)
            page.locator('#cloud-account-open').click()
            page.locator('#cloud-account-device-start').wait_for(state='visible')
            page.locator('#cloud-account-device-start').click()
            page.locator('#cloud-account-verify').wait_for(state='visible')
            code=page.locator('#cloud-account-user-code').inner_text()
            assert code and not account.state['token']
            with page.expect_popup() as popup:
                page.locator('#cloud-account-verify').click()
            site=popup.value
            site.wait_for_load_state('domcontentloaded')
            site.get_by_role('link',name='安全登录').click()
            site.locator('#fixture-consent').click()
            site.locator('#approve-device').wait_for()
            assert code in site.locator('main').inner_text()
            assert not account.state['token'], 'A website login must not auto-authorize desktop'
            site.locator('#approve-device').click()
            site.wait_for_function('document.querySelector("#device-approval-status").textContent.includes("已确认")')
            page.locator('#cloud-account-details').wait_for(state='visible',timeout=20000)
            assert '真实 OIDC' in page.locator('#cloud-account-user').inner_text()
            assert not page.locator('#cloud-account-fee-label').is_visible()
            assert not page.locator('#cloud-account-model').is_visible()
            assert account.state['token'] and account.state['token'].encode() not in account.storage.path.read_bytes()
            restored=CloudAccount(tmp_path/'desktop',settings.public_url,transport=account.transport)
            assert restored.status()['authenticated']
            assert 'access_token' not in page.content() and 'refresh_token' not in page.content()
            page.locator('#cloud-account-mode').select_option('platform')
            page.locator('#cloud-account-model').select_option('fixture-model')
            page.locator('#cloud-account-apply').click()
            page.wait_for_function('document.querySelector("#cloud-account-status").textContent.includes("模型方式已保存")')
            assert account.state['source_mode']=='platform'
            assert app.state.model_router.cloud_model_id=='fixture-model'
            page.locator('#cloud-account-close').click()
            page.locator('.model-controls > summary').click()
            page.locator('#model-settings-toggle').click()
            page.locator('#connection-name').fill('Must not replace platform')
            page.locator('#connection-base').fill('https://example.invalid/v1')
            page.locator('#connection-model').fill('fixture-only')
            page.locator('#connection-key').fill('fixture-not-a-real-key')
            page.locator('#connection-form button[type=submit]').click()
            page.wait_for_function('document.querySelector("#connection-status").textContent.includes("未更改连接或模型")')
            assert app.state.model_router.cloud_model_id=='fixture-model'
            assert app.state.connection_vault.load()['connections']==[]
            page.locator('#connection-close').click()
            page.locator('#cloud-account-open').click()
            page.locator('#cloud-account-details').wait_for(state='visible')
            settings.prices['byok_service_enabled']=True
            page.locator('#cloud-account-refresh').click()
            page.locator('#cloud-account-mode').select_option('byok')
            page.locator('#cloud-account-fee-label').wait_for(state='visible')
            page.locator('#cloud-account-apply').click()
            page.wait_for_function('document.querySelector("#cloud-account-status").textContent.includes("请先确认")')
            assert account.state['source_mode']=='platform'
            page.locator('#cloud-account-fee-ack').check()
            page.locator('#cloud-account-apply').click()
            page.wait_for_function('document.querySelector("#cloud-account-status").textContent.includes("模型方式已保存")')
            assert account.state['source_mode']=='byok' and account.state['service_ack_version']=='fixture-1'
            assert not getattr(app.state.model_router,'cloud_model_id',None)
            evidence=os.getenv('KSTUDIO_BROWSER_EVIDENCE_DIR')
            if evidence:
                out=Path(evidence);out.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(out/'client-account-authorized-fixture.png'))
                site.screenshot(path=str(out/'website-device-approved-fixture.png'))
            for width,height in ((800,600),(390,844)):
                page.set_viewport_size({'width':width,'height':height})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                assert page.locator('#cloud-account-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
                page.locator('#cloud-account-refresh').scroll_into_view_if_needed()
                assert page.locator('#cloud-account-refresh').is_visible()
            page.set_viewport_size({'width':1440,'height':960})
            site.goto(settings.public_url+'/account/devices')
            row=site.get_by_role('row').filter(has_text='K Studio · Windows')
            row.get_by_role('button',name='撤销设备').click()
            page.locator('#cloud-account-refresh').click()
            page.locator('#cloud-account-device-start').wait_for(state='visible')
            assert not account.state['token']
            settings.prices['byok_service_enabled']=False
            account._restore_failed()
            page.locator('#cloud-account-close').click()
            if not page.locator('.model-controls').evaluate('(e)=>e.open'):
                page.locator('.model-controls > summary').click()
            page.locator('#model-settings-toggle').click()
            page.locator('#connection-name').fill('Must not bypass unavailable')
            page.locator('#connection-base').fill('https://example.invalid/v1')
            page.locator('#connection-model').fill('fixture-only')
            page.locator('#connection-key').fill('fixture-not-a-real-key')
            page.locator('#connection-form button[type=submit]').click()
            page.wait_for_function('document.querySelector("#connection-status").textContent.includes("云账户配置需要恢复")')
            assert account.state['source_mode']=='unavailable'
            assert app.state.connection_vault.load()['connections']==[]
            page.locator('#connection-close').click()
            page.locator('#cloud-account-open').click()
            page.wait_for_function('document.querySelector("#cloud-account-status").textContent.includes("云账户配置无法恢复")')
            assert page.locator('#cloud-account-details').is_visible()
            assert '尚未重新授权' in page.locator('#cloud-account-user').inner_text()
            page.locator('#cloud-account-mode').select_option('byok')
            page.locator('#cloud-account-apply').click()
            page.wait_for_function('document.querySelector("#cloud-account-status").textContent.includes("模型方式已保存")')
            assert account.state['source_mode']=='byok' and not account.restore_error
            account.base=''
            page.locator('#cloud-account-close').click()
            page.locator('#cloud-account-open').click()
            page.wait_for_function('document.querySelector("#cloud-account-status").textContent.includes("尚未配置")')
            assert not page.locator('#cloud-account-device-start').is_visible()
            assert not page.locator('#cloud-account-details').is_visible()
            assert not errors, errors
            if evidence:
                (out/'device-account-ui.json').write_text(json.dumps({'status':'PASS','identity':'Authlib RS256/PKCE fixture',
                    'transport':'controlled HTTPS-to-local HTTP fixture, not public TLS','real_client_ui':True,
                    'explicit_device_consent':True,'dpapi_persistence':True,'platform_byok_switch':True,
                    'paid_byok_confirmation':True,'revocation':True,'javascript_errors':errors,
                    'paid_inference':False,'real_oidc_provider':False},ensure_ascii=False,indent=2),encoding='utf-8')
            browser.close()
    finally:
        if client_server:
            client_server.should_exit=True;client_thread.join(5)
        cloud_server.should_exit=True;cloud_thread.join(5)
        cloud.state.engine.dispose()
