from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.litellm_runtime import LiteLLMRuntime
from app.model_router import DeterministicModelRouter
from app.native_agent import NativeAgentUnavailable


class ToolClient:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [{
            "name": "sketchup_health",
            "description": "Read SketchUp bridge health.",
            "inputSchema": {"type": "object", "properties": {}},
        }]

    def call_for_agent(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "success": True,
            "contentItems": [{"type": "inputImage", "imageUrl": "data:image/png;base64,AAAA"}],
        }


class FakeCodex:
    available = True
    runtime_root = None
    model = "gpt-6-luna"


def test_router_is_economy_by_default_and_premium_is_explicit(tmp_path, monkeypatch):
    monkeypatch.delenv("ARCH_STUDIO_ECONOMY_PROVIDER", raising=False)
    monkeypatch.delenv("ARCH_STUDIO_ECONOMY_MODEL", raising=False)
    router = DeterministicModelRouter(FakeCodex(), runtime_root=tmp_path)

    assert router.route("economy").model == "gpt-6-luna"
    assert router.route("economy").tier == "economy"
    assert router.route("premium").model == "gpt-6-astra"
    assert router.route("premium").reasoning_effort == "low"


def test_economy_route_rejects_astra_model(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_ECONOMY_MODEL", "gpt-6-astra")
    with pytest.raises(ValueError, match="Economy cannot use an Astra model"):
        DeterministicModelRouter(FakeCodex(), runtime_root=tmp_path)


def test_litellm_economy_route_reports_its_own_availability(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_ECONOMY_PROVIDER", "litellm")
    monkeypatch.setenv("ARCH_STUDIO_CHINA_MODEL", "dashscope/qwen3-vl-flash")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    status = DeterministicModelRouter(FakeCodex(), runtime_root=tmp_path).status()

    assert status["economy"]["provider"] == "litellm"
    assert status["economy"]["model"] == "dashscope/qwen3-vl-flash"
    assert status["providers"]["litellm"]["available"] is False
    assert status["premium"]["model"] == "gpt-6-astra"


def test_litellm_adapter_does_not_send_without_local_dashscope_credential(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    runtime = LiteLLMRuntime(tmp_path)
    assert runtime.available is False
    with pytest.raises(NativeAgentUnavailable, match="DASHSCOPE_API_KEY is not set"):
        runtime.respond(
            project_dir=tmp_path, thread_id=None, prompt="test", mcp_enabled=False,
            developer_instructions="test",
        )


def test_litellm_adapter_reuses_sketchup_tools_and_passes_tool_images(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-only-key")
    client = ToolClient()
    runtime = LiteLLMRuntime(tmp_path, sketchup_mcp=client, region="beijing")
    seen = []

    def completion(**kwargs):
        seen.append(kwargs)
        if len(seen) == 1:
            message = {
                "content": None,
                "tool_calls": [{
                    "id": "call-health",
                    "function": {"name": "sketchup_health", "arguments": "{}"},
                }],
            }
        else:
            assert any(
                part.get("type") == "image_url"
                for item in kwargs["messages"] if item.get("role") == "user"
                for part in (item.get("content") if isinstance(item.get("content"), list) else [])
            )
            message = {"content": "SketchUp 状态正常，视口已检查。", "tool_calls": None}
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)],
            usage={"prompt_tokens": 123, "completion_tokens": 45},
        )

    litellm_module = ModuleType("litellm")
    litellm_module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", litellm_module)
    result = runtime.respond(
        project_dir=tmp_path, thread_id=None, prompt="检查当前模型。",
        mcp_enabled=True, developer_instructions="same architecture agent rules",
        ruby_enabled=False,
    )

    assert client.calls == [("sketchup_health", {})]
    assert seen[0]["tools"][0]["function"]["name"] == "sketchup_health"
    assert seen[0]["api_base"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert result.reply == "SketchUp 状态正常，视口已检查。"
    assert result.provider_name == "litellm"
    assert result.region == "beijing"
    assert (result.input_tokens, result.output_tokens) == (123, 45)
    assert result.tool_call_count == 1
    assert result.failed_tool_calls == 0
