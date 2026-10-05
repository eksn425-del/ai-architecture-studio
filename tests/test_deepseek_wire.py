"""Real installed LiteLLM serialization, intercepted locally; no live provider claim."""
import json
from types import SimpleNamespace

import pytest

from app.litellm_runtime import LiteLLMRuntime
from tests.test_model_router import ToolClient


@pytest.mark.parametrize("setting,expected", [("1", True), ("true", True), ("0", False), ("false", False), (None, True)])
def test_deepseek_transport_respects_cloud_proxy_setting(tmp_path, monkeypatch, setting, expected):
    litellm = pytest.importorskip("litellm")
    import os
    if setting is None:
        monkeypatch.delenv("ARCH_STUDIO_API_TRUST_ENV", raising=False)
        expected = os.name != "nt"
    else:
        monkeypatch.setenv("ARCH_STUDIO_API_TRUST_ENV", setting)
    def completion(**kwargs):
        assert kwargs["client"].client._trust_env is expected
        return SimpleNamespace(choices=[SimpleNamespace(message={"content": "checked"})], usage={})
    monkeypatch.setattr(litellm, "completion", completion)
    runtime = LiteLLMRuntime(tmp_path, model="deepseek/deepseek-flash")
    runtime.session_api_key = "test-only-placeholder"
    runtime.custom_api_base = "https://api.deepseek.com"
    result = runtime.respond(project_dir=tmp_path, thread_id=None, prompt="test", mcp_enabled=False,
                             developer_instructions="test", ruby_enabled=False)
    assert result.reply == "checked"


@pytest.mark.parametrize("model,base,host,effort", [
    ("deepseek/deepseek-flash", "https://api.deepseek.com", "api.deepseek.com", "low"),
    ("zai/glm-5.3-flash", "https://open.bigmodel.cn/api/paas/v4", "open.bigmodel.cn", "low"),
    ("zai/glm-5.3-flash", "https://api.z.ai/api/paas/v4", "api.z.ai", "low"),
    ("zai/glm-5.3-flash", "https://open.bigmodel.cn/api/paas/v4", "open.bigmodel.cn", "high"),
    ("zai/glm-5.3-flash", "https://open.bigmodel.cn/api/paas/v4", "open.bigmodel.cn", "max"),
])
def test_api_wire_keeps_images_low_effort_and_reasoning(tmp_path, monkeypatch, model, base, host, effort):
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    litellm = pytest.importorskip("litellm")
    import httpx
    from litellm.llms.custom_httpx.http_handler import HTTPHandler
    seen = []

    def intercept(request):
        body = json.loads(request.content)
        seen.append(body)
        assert request.url.host == host
        assert body["model"] == model.split("/", 1)[1]
        assert body["reasoning_effort"] == effort
        assert any(p["type"] == "image_url" for m in body["messages"] if isinstance(m.get("content"), list)
                   for p in m["content"])
        image_urls = [p["image_url"]["url"] for m in body["messages"] if isinstance(m.get("content"), list) for p in m["content"] if p["type"] == "image_url"]
        assert len(image_urls) == len(set(image_urls))
        if len(seen) == 1:
            message = {"role":"assistant", "content":None, "reasoning_content":"tool reasoning",
                       "tool_calls":[{"id":"h", "type":"function", "function":{"name":"sketchup_health","arguments":"{}"}}]}
        else:
            assistants = [m for m in body["messages"] if m["role"] == "assistant"]
            assert assistants[0]["reasoning_content"] == "tool reasoning"
            if len(seen) == 3:
                assert assistants[-1]["reasoning_content"] == "final reasoning"
            message = {"role":"assistant", "content":"checked", "reasoning_content":"final reasoning"}
        return httpx.Response(200, json={"id":"local-contract", "object":"chat.completion", "created":0,
                             "model":model.split("/", 1)[1], "choices":[{"index":0,"message":message,"finish_reason":"stop"}],
                             "usage":{"prompt_tokens":10,"completion_tokens":5}}, request=request)

    original = litellm.completion
    with httpx.Client(transport=httpx.MockTransport(intercept)) as client:
        if model.startswith("zai/"):
            from openai import OpenAI
            handler = OpenAI(api_key="test-only-placeholder", base_url=base, http_client=client)
        else:
            handler = HTTPHandler(client=client)
        def local_completion(**kw):
            kw["client"] = handler
            return original(**kw)
        monkeypatch.setattr(litellm, "completion", local_completion)
        image = tmp_path / "inputs/reference/test.png"
        image.parent.mkdir(parents=True)
        from PIL import Image
        Image.new("RGB", (8,8), "white").save(image)
        runtime = LiteLLMRuntime(tmp_path, sketchup_mcp=ToolClient(), model=model)
        runtime.session_api_key = "test-only-placeholder"
        runtime.custom_api_base = base
        result = runtime.respond(project_dir=tmp_path, thread_id=None, prompt="check", mcp_enabled=True,
                                 developer_instructions="test", ruby_enabled=False, reasoning_effort=effort)
        runtime.respond(project_dir=tmp_path, thread_id=result.thread_id, prompt="again", mcp_enabled=True,
                        developer_instructions="test", ruby_enabled=False, reasoning_effort=effort)
    assert len(seen) == 3


def test_glm_server_failure_is_not_silently_retried(tmp_path, monkeypatch):
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    litellm = pytest.importorskip("litellm")
    import httpx
    from openai import OpenAI
    from app.native_agent import NativeAgentUnavailable
    requests = []
    def fail(request):
        requests.append(request.url.host)
        return httpx.Response(503, json={"error": {"message": "local unavailable", "type": "server_error"}}, request=request)
    original = litellm.completion
    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        handler = OpenAI(api_key="test-only-placeholder", base_url="https://open.bigmodel.cn/api/paas/v4", http_client=client)
        def local_completion(**kw):
            assert kw["max_retries"] == 0
            kw["client"] = handler
            return original(**kw)
        monkeypatch.setattr(litellm, "completion", local_completion)
        runtime = LiteLLMRuntime(tmp_path, sketchup_mcp=ToolClient(), model="zai/glm-5.3-flash")
        runtime.session_api_key = "test-only-placeholder"
        runtime.custom_api_base = "https://open.bigmodel.cn/api/paas/v4"
        with pytest.raises(NativeAgentUnavailable):
            runtime.respond(project_dir=tmp_path, thread_id=None, prompt="test", mcp_enabled=False, developer_instructions="test", ruby_enabled=False, reasoning_effort="high")
    assert requests == ["open.bigmodel.cn"]
