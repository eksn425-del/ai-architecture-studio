"""Real installed LiteLLM serialization, intercepted locally; no live provider claim."""
import json

import pytest

from app.litellm_runtime import LiteLLMRuntime
from tests.test_model_router import ToolClient


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
        monkeypatch.setattr(litellm, "completion", lambda **kw: original(**kw, client=handler))
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
