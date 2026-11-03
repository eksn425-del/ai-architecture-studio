"""Isolated browser/read-only HTTP smoke; synthetic data, no model provider or SU."""
from __future__ import annotations
import asyncio
import json
import socket
import threading
import time
from pathlib import Path

import httpx
import uvicorn
from playwright.sync_api import sync_playwright

from app.main import create_app
from app.models import ProjectContext
from app.store import utc_now
from app.native_agent import CodexAppServerRuntime


def main():
    output = Path('runtime/release-audit').resolve()
    runtime = output/'browser-synthetic-runtime'
    class NoNativeAccess:
        def __getattr__(self, name):
            raise AssertionError('Native model access forbidden in this UI/HTTP fixture: '+name)

    app = create_app(runtime, sketchup=NoNativeAccess(),
                     native_agent=CodexAppServerRuntime(runtime, codex_executable='NO_PROVIDER_CALLS_ALLOWED'))
    store = app.state.store
    context = ProjectContext(project_id='release-ui-fixture', project_name='界面回归 · 合成资料')
    context.conversation = [
        {'role': 'user' if i % 2 == 0 else 'assistant', 'phase':'agent',
         'content': ('请检查这一轮局部修改，并保留其他构件。' if i % 2 == 0 else '这是一条用于界面回归的合成记录。\n\n用于检查长对话、进度回看与阅读位置。')*3,
         'created_at':utc_now(), 'metadata':{'activity_id':f'fixture-{i}'}}
        for i in range(28)
    ]
    context = store.create_project(context)
    pid = context.project_id
    folder = store.project_dir(pid)/'runtime/public_activity'
    folder.mkdir(parents=True)
    for i in range(0, 28, 2):
        run = {'id':f'fixture-{i}', 'anchor':f'fixture-{i}', 'started':time.time()+i,
               'finished':True, 'events':[{'id':f'e-{i}', 'text':'合成执行记录：已核对资料，模型质量未验收', 'status':'done'}]}
        (folder/f'fixture-{i}.json').write_text(json.dumps(run,ensure_ascii=False),'utf-8')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'))
    thread = threading.Thread(target=server.run,daemon=True);thread.start()
    deadline = time.monotonic()+15
    while not server.started and time.monotonic()<deadline:time.sleep(.05)
    if not server.started:raise RuntimeError('Isolated test service did not start')
    base = f'http://127.0.0.1:{port}'
    errors=[];checks=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            page=browser.new_page(viewport={'width':1920,'height':1080})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(base,wait_until='networkidle')
            page.wait_for_selector('.activity-message')
            assert page.locator('.activity-message').count()==14
            assert page.locator('#reference-role').count()==0
            assert page.locator('#live-activity').evaluate('(e)=>e.parentElement.id')=='conversation-history'
            page.locator('#conversation-history').evaluate('(e)=>e.scrollTop=200')
            before=page.locator('#conversation-history').evaluate('(e)=>e.scrollTop')
            page.evaluate('renderConversation()')
            after=page.locator('#conversation-history').evaluate('(e)=>e.scrollTop')
            assert abs(before-after)<2,(before,after)
            assert page.locator('.activity-message').count()==14
            page.screenshot(path=str(output/'ui-desktop.png'))
            checks.append({'viewport':'1920x1080','persistent_records':14,'before_scroll':before,'after_rerender_scroll':after})
            page.reload(wait_until='networkidle')
            assert page.locator('.activity-message').count()==14
            page.set_viewport_size({'width':390,'height':844})
            page.locator('#conversation-history').evaluate('(e)=>e.scrollTop=0')
            bounds=page.locator('#conversation-history').bounding_box()
            assert bounds['height']>100,bounds
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(output/'ui-mobile.png'))
            checks.append({'viewport':'390x844','history_height':bounds['height'],'horizontal_overflow':False})
            page.set_viewport_size({'width':1920,'height':1080})
            page.evaluate("renderTurnControls({running:true, request_id:'synthetic-run', cancel_supported:true, stage:'正在核对资料（合成回归）', elapsed_seconds:12, tool_calls:2, committed_revisions:[]})")
            page.locator('#conversation-history').evaluate('(e)=>e.scrollTop=e.scrollHeight')
            page.screenshot(path=str(output/'ui-live.png'))
            assert page.locator('#live-activity').is_visible()
            browser.close()
        assert not errors,errors

        async def smoke():
            semaphore=asyncio.Semaphore(20);latencies=[];statuses=[]
            async with httpx.AsyncClient(base_url=base,timeout=10,trust_env=False) as client:
                async def virtual_client():
                    async with semaphore:
                        for path in ['/api/release-readiness','/api/projects']:
                            start=time.perf_counter();r=await client.get(path)
                            latencies.append((time.perf_counter()-start)*1000);statuses.append(r.status_code)
                start=time.perf_counter()
                await asyncio.gather(*(virtual_client() for _ in range(500)))
            latencies.sort()
            return {'synthetic_virtual_clients':500,'concurrency':20,'requests':len(statuses),
                    'errors':sum(s!=200 for s in statuses),'wall_seconds':time.perf_counter()-start,
                    'p95_ms':latencies[int(len(latencies)*.95)-1],
                    'scope':'local read-only HTTP only; no registered users, auth, database, cloud, paid inference or native modeling load'}
        load=asyncio.run(smoke());assert load['errors']==0,load
        result={'browser_checks':checks,'javascript_errors':errors,'read_only_http_smoke':load,'provider_calls':0,'native_model_calls':0}
        (output/'browser-and-http-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
        print(json.dumps(result,ensure_ascii=True))
    finally:
        server.should_exit=True;thread.join(timeout=10)


if __name__=='__main__':main()
