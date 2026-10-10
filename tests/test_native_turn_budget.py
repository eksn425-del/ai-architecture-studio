"""Codex Native evidence-backed budget stops, retaining partial usage."""
from __future__ import annotations

import io
import json

import pytest

from app import native_agent as subject


class _FakeProcess:
    stdout = io.BytesIO()
    stdin = io.BytesIO()
    def poll(self):
        return 0


def _fixture(tmp_path, monkeypatch, events):
    monkeypatch.setattr(subject.subprocess, "Popen", lambda *a, **k: _FakeProcess())
    runtime = subject.CodexAppServerRuntime(tmp_path, codex_executable="fixture")
    monkeypatch.setattr(runtime, "_request", lambda *a: {"thread": {"id": "budget-test"}})
    iterator = iter(events)
    monkeypatch.setattr(runtime, "_next_event", lambda *a: next(iterator))
    project = tmp_path / "project"
    workspace = project / "runtime/agent_workspace"
    workspace.mkdir(parents=True)
    return runtime, project, workspace


def _run(runtime, project, workspace, **kw):
    return runtime._run_turn(
        project_dir=project, agent_workspace=workspace, thread_id=None,
        prompt="build", mcp_enabled=True, developer_instructions="safe",
        dynamic_tools=[{"name": "sketchup_run_workspace_ruby"}],
        tool_handler=lambda *a: {"success": True}, model="gpt-6-luna",
        reasoning_effort="max", reference_images=[],
        workflow_mode="image_reconstruction", **kw
    )


def test_native_token_budget_aborts_before_unbounded_builder_work(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_CODEX_MAX_TURN_INPUT_TOKENS", "250")
    events = [
        {"method": "thread/tokenUsage/updated", "params": {"tokenUsage": {
            "total": {"inputTokens": 200, "outputTokens": 50},
            "last": {"inputTokens": 101, "outputTokens": 4},
        }}},
        {"method": "thread/tokenUsage/updated", "params": {"tokenUsage": {
            "total": {"inputTokens": 400, "outputTokens": 60},
            "last": {"inputTokens": 200, "outputTokens": 10},
        }}},
    ]
    runtime, project, workspace = _fixture(tmp_path, monkeypatch, events)
    with pytest.raises(subject.NativeAgentUnavailable, match="input-token budget") as exc:
        _run(runtime, project, workspace)
    assert exc.value.partial_result.status == "interrupted"
    assert exc.value.partial_result.input_tokens == 301
    logfile = next((project / "runtime/agent_events").glob("*.jsonl"))
    assert "native_budget_exhausted" in logfile.read_text(encoding="utf8")


def test_native_tool_budget_stops_before_dispatch(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_CODEX_MAX_TURN_TOOL_CALLS", "1")
    calls = [{"method": "item/started", "params": {"item": {"type": "commandExecution"}}},
             {"id": 8, "method": "item/tool/call",
              "params": {"tool": "sketchup_run_workspace_ruby", "arguments": {}}}]
    runtime, project, workspace = _fixture(tmp_path, monkeypatch, calls)
    with pytest.raises(subject.NativeAgentUnavailable, match="tool-call budget") as exc:
        _run(runtime, project, workspace)
    assert exc.value.partial_result.tool_call_count == 1


def test_native_budget_can_be_explicitly_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_CODEX_MAX_TURN_TOOL_CALLS", "0")
    monkeypatch.setenv("ARCH_STUDIO_CODEX_MAX_TURN_INPUT_TOKENS", "0")
    runtime = subject.CodexAppServerRuntime(tmp_path, codex_executable="fixture")
    assert runtime.max_tool_calls_per_turn == 0
    assert runtime.max_input_tokens_per_turn == 0
