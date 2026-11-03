import json
from types import SimpleNamespace
import pytest
from app.deepseek_studio import DeepSeekStudioRuntime, BASE, ARCHITECTURE
from app.local_connections import connection_router

def test_desktop_routes_saved_key_to_official_dsh_without_codex(tmp_path,monkeypatch):
    monkeypatch.setenv('KSTUDIO_AGENT_ENGINE','deepseek-harness')
    monkeypatch.setenv('KSTUDIO_DSH_SDK_SITE',str(tmp_path/'sdk'))
    monkeypatch.setenv('KSTUDIO_DSH_BIN',str(tmp_path/'dsh.cmd'))
    native=SimpleNamespace(runtime_root=tmp_path,sketchup_mcp=None)
    app=SimpleNamespace(state=SimpleNamespace(native_agent=native,store=SimpleNamespace(root=tmp_path)))
    item={'model':'deepseek-v4.1-flash','api_base':'https://example.invalid/v1','api_key':'test-not-a-key',
          'mode':'codex-responses','reasoning_effort':'high','compatibility_acknowledged':True}
    router=connection_router(app,item)
    assert router.economy_route.provider=='deepseek-harness'
    engine=router.providers['deepseek-harness']
    assert engine.protocol=='openai-responses'
    assert engine.instructions.endswith(ARCHITECTURE)
    empty=connection_router(app,None)
    assert empty.economy_route.model==''
    monkeypatch.setenv('KSTUDIO_DSH_GUIDANCE','native')
    second=connection_router(app,{**item,'mode':'compatible'})
    assert second.providers['deepseek-harness'].instructions==BASE
    assert second.providers['deepseek-harness'].protocol=='openai-completions'

def test_old_geometry_is_not_silently_rebuilt(tmp_path,monkeypatch):
    engine=DeepSeekStudioRuntime(tmp_path,connection={'model':'deepseek-v4.1-flash',
        'api_base':'https://example.invalid/v1','api_key':'fake','mode':'codex-responses'},mcp=None)
    with pytest.raises(Exception,match='历史模型'):
        engine.respond(project_dir=tmp_path,thread_id=None,prompt='',mcp_enabled=True,
            ruby_state={'legacy':{'revision':3}})
