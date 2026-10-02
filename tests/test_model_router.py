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
    monkeypatch.delenv("ARCH_STUDIO_ECONOMY_REASONING_EFFORT", raising=False)
    router = DeterministicModelRouter(FakeCodex(), runtime_root=tmp_path)

    assert router.route("economy").model == "gpt-6.1-sol"
    assert router.route("economy").reasoning_effort == "low"
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
        assert kwargs["max_retries"] == 0
        assert kwargs["num_retries"] == 0
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
    assert (result.input_tokens, result.output_tokens) == (246, 90)
    assert result.tool_call_count == 1
    assert result.failed_tool_calls == 0


def test_deepseek_preserves_thinking_through_tools_and_next_turn(tmp_path, monkeypatch):
    runtime = LiteLLMRuntime(tmp_path, sketchup_mcp=ToolClient(), model="deepseek/deepseek-flash")
    runtime.session_api_key = "test-only-key"
    runtime.custom_api_base = "https://api.deepseek.com"
    seen = []

    def completion(**kwargs):
        import copy
        seen.append(copy.deepcopy(kwargs))
        assert kwargs["reasoning_effort"] == "low"
        assert kwargs["extra_body"]["reasoning_effort"] == "low"
        assert kwargs["model"] == "deepseek/deepseek-flash"
        if len(seen) == 1:
            message = {"content": None, "reasoning_content": "tool-thought", "tool_calls": [
                {"id": "health", "function": {"name": "sketchup_health", "arguments": "{}"}}]}
        else:
            previous = [m for m in kwargs["messages"] if m["role"] == "assistant"]
            assert previous[0]["reasoning_content"] == "tool-thought"
            if len(seen) == 3:
                assert previous[-1]["reasoning_content"] == "final-thought"
            message = {"content": "checked", "reasoning_content": "final-thought"}
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage={})

    module = ModuleType("litellm")
    module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", module)
    result = runtime.respond(project_dir=tmp_path, thread_id=None, prompt="check", mcp_enabled=True,
                             developer_instructions="test", ruby_enabled=False, reasoning_effort="low")
    runtime.respond(project_dir=tmp_path, thread_id=result.thread_id, prompt="again", mcp_enabled=True,
                    developer_instructions="test", ruby_enabled=False, reasoning_effort="low")
    assert len(seen) == 3


def test_litellm_stops_repeated_modeling_failures_and_checkpoints_history(tmp_path, monkeypatch):
    import json
    runtime = LiteLLMRuntime(tmp_path, sketchup_mcp=ToolClient())
    runtime.session_api_key = "test-only-key"
    tool = {"name": "sketchup_run_workspace_ruby", "inputSchema": {"type": "object"}}
    monkeypatch.setattr(runtime.tool_surface, "prepare", lambda **kw: SimpleNamespace(
        dynamic_tools=[tool], dispatch=lambda *args: {"success": False, "text": "blocked script"}))
    seen = []
    def completion(**kw):
        seen.append(kw)
        return SimpleNamespace(choices=[SimpleNamespace(message={"content": None, "tool_calls": [
            {"id": str(len(seen)), "function": {"name": tool["name"], "arguments": "{}"}}]})], usage={})
    module = ModuleType("litellm")
    module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", module)
    with pytest.raises(NativeAgentUnavailable, match="连续 3 次"):
        runtime.respond(project_dir=tmp_path, thread_id="litellm-test", prompt="build", mcp_enabled=True,
                        developer_instructions="test")
    assert len(seen) == 3
    saved = json.loads((tmp_path / "runtime/provider_sessions/litellm-test.json").read_text(encoding="utf-8"))
    assert sum(m["role"] == "tool" for m in saved["messages"]) == 3
    events = next((tmp_path / "runtime/agent_events").glob("*.jsonl")).read_text(encoding="utf-8")
    assert "retry_budget_exhausted" in events and "blocked script" in events


def test_litellm_skill_is_once_in_current_system_not_repeated_history(tmp_path, monkeypatch):
    import json
    runtime = LiteLLMRuntime(tmp_path, sketchup_mcp=ToolClient())
    runtime.session_api_key = "test-only-key"
    seen = []
    def completion(**kw):
        seen.append(json.loads(json.dumps(kw["messages"])))
        return SimpleNamespace(choices=[SimpleNamespace(message={"content": "ok"})], usage={})
    module = ModuleType("litellm")
    module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", module)
    result = runtime.respond(project_dir=tmp_path, thread_id=None, prompt="first", mcp_enabled=False,
                             developer_instructions="test", architecture_skill_context="UNIQUE_SKILL")
    runtime.respond(project_dir=tmp_path, thread_id=result.thread_id, prompt="second", mcp_enabled=False,
                    developer_instructions="test", architecture_skill_context="UNIQUE_SKILL")
    assert sum(json.dumps(m).count("UNIQUE_SKILL") for m in seen[-1]) == 1
    assert "UNIQUE_SKILL" in seen[-1][0]["content"]
    assert any(m.get("content") == "first" for m in seen[-1])

@pytest.mark.parametrize('mode', ['limit', 'provider_error'])
def test_interrupted_litellm_turn_reports_current_usage_and_checkpoint(tmp_path, monkeypatch, mode):
    import json
    runtime = LiteLLMRuntime(tmp_path, sketchup_mcp=ToolClient())
    runtime.session_api_key = 'test-only-key'
    runtime.max_tool_calls = 1
    calls = []
    def completion(**kw):
        calls.append(kw)
        if len(calls) == 2 and mode == 'provider_error':
            raise RuntimeError('fixture unavailable')
        return SimpleNamespace(choices=[SimpleNamespace(message={'content':None,'tool_calls':[
            {'id':str(len(calls)), 'function':{'name':'sketchup_health','arguments':'{}'}}]})],
            usage={'prompt_tokens':100, 'completion_tokens':10})
    module = ModuleType('litellm')
    module.completion = completion
    monkeypatch.setitem(sys.modules, 'litellm', module)
    with pytest.raises(NativeAgentUnavailable) as captured:
        runtime.respond(project_dir=tmp_path, thread_id='litellm-checkpoint', prompt='inspect',
                        mcp_enabled=True, ruby_enabled=False, developer_instructions='test')
    result = captured.value.partial_result
    assert result.tool_call_count == 1 and result.failed_tool_calls == 0
    assert result.input_tokens == (200 if mode == 'limit' else 100)
    assert result.output_tokens == (20 if mode == 'limit' else 10)
    assert result.thread_id == 'litellm-checkpoint'
    history = json.loads((tmp_path / 'runtime/provider_sessions/litellm-checkpoint.json').read_text())
    assert len([m for m in history['messages'] if m['role']=='tool']) == 1
