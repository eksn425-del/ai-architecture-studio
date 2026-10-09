import io
import json
from app import native_agent as subject


def test_native_coding_operations_are_counted_and_logged(tmp_path, monkeypatch):
    class Process:
        stdout = io.BytesIO()
        stdin = io.BytesIO()
        def poll(self):
            return 0

    monkeypatch.setattr(subject.subprocess, "Popen", lambda *args, **kwargs: Process())
    runtime = subject.CodexAppServerRuntime(tmp_path, codex_executable="fixture")
    monkeypatch.setattr(runtime, "_request", lambda *args: {"thread": {"id": "fixture-thread"}})
    events = iter([
        {"method": "item/started", "params": {"item": {"type": "commandExecution"}}},
        {"method": "item/completed", "params": {"item": {"type": "commandExecution", "status": "completed", "exitCode": 1}}},
        {"method": "item/started", "params": {"item": {"type": "fileChange"}}},
        {"method": "item/completed", "params": {"item": {"type": "fileChange", "status": "completed"}}},
        {"method": "item/completed", "params": {"item": {"type": "agentMessage", "text": "planned"}}},
        {"method": "turn/completed", "params": {"turn": {"status": "completed"}}},
    ])
    monkeypatch.setattr(runtime, "_next_event", lambda *args: next(events))
    project = tmp_path / "project"
    workspace = project / "runtime/agent_workspace"
    workspace.mkdir(parents=True)
    result = runtime._run_turn(
        project_dir=project, agent_workspace=workspace, thread_id=None,
        prompt="plan", mcp_enabled=False, developer_instructions="fixture",
        dynamic_tools=[], tool_handler=lambda *args: {}, model="gpt-6-luna",
        reasoning_effort="max", reference_images=[], workflow_mode="image_reconstruction",
    )
    assert result.tool_call_count == 2
    assert result.failed_tool_calls == 1
    log = list((project / "runtime/agent_events").glob("*.jsonl"))[0]
    recorded = [json.loads(line) for line in log.read_text(encoding="utf8").splitlines()]
    results = [event for event in recorded if event["event"] == "tool_result"]
    assert [(item["tool"], item["success"]) for item in results] == [
        ("codex_commandExecution", False), ("codex_fileChange", True)]
