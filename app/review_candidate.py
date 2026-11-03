"""Isolated read-only review entry; never use as a modeling release."""
from pathlib import Path
from fastapi.responses import HTMLResponse,JSONResponse
from starlette.requests import Request
from .native_execution_safety import execution_readiness


def create_review_app(base_app=None):
    if base_app is None:
        from .main import create_app
        base_app=create_app()
    class ReviewBoundary:
      def __init__(self):self.state=base_app.state
      async def __call__(self,scope,receive,send):
        if scope['type']=='websocket':
            await send({'type':'websocket.close','code':1008});return
        if scope['type']!='http':return await base_app(scope,receive,send)
        request=Request(scope)
        response=None
        if request.method not in {'GET','HEAD','OPTIONS'}:
            response=JSONResponse(status_code=409,content={'detail':'这是独立审阅候选。模型调用与建模修改暂未开放。'})
        elif request.url.path=='/api/candidate-review':
            route=base_app.state.model_router.route('economy')
            response=JSONResponse({'mode':'isolated_read_only_review','model_calls_enabled':False,
                'modeling_writes_enabled':False,'python_bridge_enabled':False,
                'configured_route':route.as_dict(),'native_execution_safety':execution_readiness(),
                'native_probes':{'dsh_bai':'verified_separately','codex_bai':'verified_separately',
                                 'ui_integration':'not_completed','building_quality':'not_verified'}})
        elif request.url.path=='/' and request.method=='GET':
            html=(Path(__file__).parent/'static/index.html').read_text(encoding='utf-8')
            banner='<aside id="candidate-review-banner" style="position:fixed;bottom:12px;left:16px;right:16px;z-index:99999;padding:12px 18px;border:1px solid #b8c8bc;border-radius:12px;background:#edf5ef;color:#193c29;font:14px sans-serif;box-shadow:0 5px 25px #0002">独立审阅候选 · 模型调用与建模修改暂未开放 · 新 Python 桥已关闭 · Windows 原生执行未通过隔离验证</aside>'
            response=HTMLResponse(html.replace('</body>',banner+'</body>'),headers={'Cache-Control':'no-store'})
        if response is not None:return await response(scope,receive,send)
        return await base_app(scope,receive,send)
    return ReviewBoundary()
