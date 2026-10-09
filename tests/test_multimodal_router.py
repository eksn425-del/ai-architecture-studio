from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

from app.litellm_runtime import LiteLLMRuntime
from app.model_router import DeterministicModelRouter
from app.native_agent import CodexAppServerRuntime, _app_server_turn_input


class FakeCodex:
    available = True
    runtime_root = None
    model = "gpt-6-luna"


def test_native_timeout_accommodates_real_reconstruction_turns(tmp_path: Path):
    runtime = CodexAppServerRuntime(tmp_path, home_root=tmp_path / "home")
    assert runtime.timeout_seconds == 900
    bounded = CodexAppServerRuntime(tmp_path, home_root=tmp_path / "home", timeout_seconds=60)
    assert bounded.timeout_seconds == 60


def test_native_timeout_can_bound_high_reasoning_benchmarks(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setenv("ARCH_STUDIO_CODEX_TIMEOUT_SECONDS", "1800")
    assert CodexAppServerRuntime(tmp_path).timeout_seconds == 1800
    assert CodexAppServerRuntime(tmp_path, timeout_seconds=60).timeout_seconds == 60
    monkeypatch.setenv("ARCH_STUDIO_CODEX_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValueError, match="between 30 and 3600"):
        CodexAppServerRuntime(tmp_path)


def test_codex_app_server_turn_input_uses_local_image_wire_variant(tmp_path: Path):
    first = tmp_path / "reference-01.png"
    second = tmp_path / "reference-02.png"

    turn_input = _app_server_turn_input("Describe both images.", [first, second])

    assert [item["type"] for item in turn_input] == ["text", "text", "localImage", "text", "localImage"]
    assert [item["path"] for item in turn_input if item["type"] == "localImage"] == [str(first), str(second)]
    assert first.name in turn_input[1]["text"] and second.name in turn_input[3]["text"]


def test_router_allows_explicit_benchmark_reasoning_overrides(tmp_path, monkeypatch):
    monkeypatch.delenv("ARCH_STUDIO_ECONOMY_PROVIDER", raising=False)
    monkeypatch.setenv("ARCH_STUDIO_ECONOMY_MODEL", "gpt-6-luna")
    monkeypatch.setenv("ARCH_STUDIO_ECONOMY_REASONING_EFFORT", "max")
    monkeypatch.setenv("ARCH_STUDIO_PREMIUM_REASONING_EFFORT", "low")

    router = DeterministicModelRouter(FakeCodex(), runtime_root=tmp_path)

    assert router.route("economy").model == "gpt-6-luna"
    assert router.route("economy").reasoning_effort == "max"
    assert router.route("premium").model == "gpt-6-astra"
    assert router.route("premium").reasoning_effort == "low"


def test_litellm_first_user_turn_contains_project_reference_image(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-only-key")
    image = tmp_path / "inputs" / "reference" / "jinshan-plan.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"reference-image-bytes")
    seen = []

    def completion(**kwargs):
        seen.append(kwargs)
        user = next(item for item in kwargs["messages"] if item.get("role") == "user")
        assert isinstance(user["content"], list)
        assert user["content"][0]["type"] == "text"
        assert "jinshan-plan.png" in user["content"][0]["text"]
        image_parts = [part for part in user["content"] if part.get("type") == "image_url"]
        assert len(image_parts) == 1
        assert image_parts[0]["image_url"]["url"].startswith("data:image/png;base64,")
        return SimpleNamespace(
            choices=[SimpleNamespace(message={"content": "已读取参考图。", "tool_calls": None})],
            usage={"prompt_tokens": 10, "completion_tokens": 4},
        )

    litellm_module = ModuleType("litellm")
    litellm_module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", litellm_module)

    runtime = LiteLLMRuntime(tmp_path)
    result = runtime.respond(
        project_dir=tmp_path,
        thread_id=None,
        prompt="先阅读参考图再设计。",
        mcp_enabled=False,
        developer_instructions="architecture agent",
    )

    assert seen
    assert result.reply == "已读取参考图。"
