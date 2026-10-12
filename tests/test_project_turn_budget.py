"""Project budget must not double-count event updates or fabricate unknown use."""
import json
import pytest
from app.project_turn_budget import read_project_builder_usage
from app import native_agent as subject
from tests.test_native_turn_budget import _fixture, _run


def _log(folder, name, events):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf8")


def test_project_budget_sums_only_terminal_builder_usage(tmp_path):
    folder = tmp_path / "events"
    _log(folder, "first.jsonl", [
        {"event": "project_budget_started", "is_builder": True},
        {"event": "token_usage", "input_tokens": 100},
        {"event": "project_budget_finished", "is_builder": True, "input_tokens": 180, "output_tokens": 8, "status": "completed"},
    ])
    _log(folder, "critic.jsonl", [
        {"event": "project_budget_started", "is_builder": False},
        {"event": "project_budget_finished", "is_builder": False, "input_tokens": 900, "output_tokens": 3, "status": "completed"},
    ])
    result = read_project_builder_usage(folder)
    assert (result.input_tokens, result.output_tokens, result.uncertain_files) == (180, 8, ())


def test_unknown_and_legacy_budget_fail_closed(tmp_path):
    folder = tmp_path / "events"
    _log(folder, "unfinished.jsonl", [{"event": "project_budget_started", "is_builder": True}])
    _log(folder, "legacy.jsonl", [{"event": "token_usage", "input_tokens": 100}])
    _log(folder, "unknown.jsonl", [
        {"event": "project_budget_started", "is_builder": True},
        {"event": "project_budget_finished", "is_builder": True, "input_tokens": None, "output_tokens": 0, "status": "interrupted"},
    ])
    assert set(read_project_builder_usage(folder).uncertain_files) == {"legacy.jsonl", "unfinished.jsonl", "unknown.jsonl"}


def test_second_builder_turn_respects_cumulative_cap(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_CODEX_MAX_TURN_INPUT_TOKENS", "0")
    monkeypatch.setenv("ARCH_STUDIO_CODEX_MAX_PROJECT_INPUT_TOKENS", "350")
    monkeypatch.setenv("ARCH_STUDIO_CODEX_PROJECT_DELIVERY_RESERVE", "50")
    first = [
        {"method": "thread/tokenUsage/updated", "params": {"tokenUsage": {
            "total": {"inputTokens": 180, "outputTokens": 8},
            "last": {"inputTokens": 180, "outputTokens": 8},
        }}},
        {"method": "turn/completed", "params": {"turn": {"status": "completed"}}},
    ]
    runtime, project, workspace = _fixture(tmp_path, monkeypatch, first)
    assert _run(runtime, project, workspace).input_tokens == 180
    second = [{"method": "thread/tokenUsage/updated", "params": {"tokenUsage": {
        "total": {"inputTokens": 150, "outputTokens": 5},
        "last": {"inputTokens": 150, "outputTokens": 5},
    }}}]
    events = iter(second)
    monkeypatch.setattr(runtime, "_next_event", lambda *a: next(events))
    with pytest.raises(subject.NativeAgentUnavailable, match="Project input-token budget exceeded") as exc:
        _run(runtime, project, workspace)
    assert exc.value.partial_result.input_tokens == 150
    result = read_project_builder_usage(project / "runtime" / "agent_events")
    assert result.input_tokens == 330 and not result.uncertain_files


def test_legacy_usage_blocks_metered_continuation(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_CODEX_MAX_PROJECT_INPUT_TOKENS", "500")
    monkeypatch.setenv("ARCH_STUDIO_CODEX_PROJECT_DELIVERY_RESERVE", "50")
    runtime, project, workspace = _fixture(tmp_path, monkeypatch, [])
    _log(project / "runtime" / "agent_events", "old.jsonl", [{"event": "tool_started"}])
    with pytest.raises(subject.NativeAgentUnavailable, match="cannot be verified"):
        _run(runtime, project, workspace)
