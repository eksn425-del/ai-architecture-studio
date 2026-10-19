"""Mock-only App Server protocol checks. No executable, model, or credential use."""
from __future__ import annotations

import json
import queue
import threading

import pytest

from app import native_agent as subject
from app.native_turn_control import NativeTurnControl, NativeTurnRegistry, native_progress_event


class FakeStdout:
    def __init__(self):
        self.lines = queue.Queue()

    def readline(self):
        return self.lines.get(timeout=5)


class FakeStdin:
    def __init__(self, process):
        self.process = process

    def write(self, raw):
        message = json.loads(raw)
        self.process.sent.append(message)
        self.process.on_write(message)

    def flush(self):
        pass


class FakeProcess:
    def __init__(self, start=None, interrupt=None):
        self.stdout = FakeStdout()
        self.stdin = FakeStdin(self)
        self.sent = []
        self.stopped = False
        self.start = start
        self.interrupt = interrupt

    def feed(self, message):
        self.stdout.lines.put((json.dumps(message) + "\n").encode())

    def complete(self, status="completed", turn_id="actual-turn"):
        self.feed({"method": "turn/completed", "params": {
            "threadId": "actual-thread", "turn": {"id": turn_id, "status": status}}})

    def on_write(self, message):
        method = message.get("method")
        if method == "initialize":
            self.feed({"id": message["id"], "result": {}})
        elif method == "thread/start":
            self.feed({"id": message["id"], "result": {"thread": {"id": "actual-thread"}, "model": "fixture-model"}})
        elif method == "turn/start":
            if self.start:
                self.start(self, message)
            else:
                self.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn", "status": "inProgress"}}})
                self.complete()
        elif method == "turn/interrupt":
            if self.interrupt:
                self.interrupt(self, message)
            else:
                self.feed({"id": message["id"], "result": {}})
                self.complete("interrupted")

    def poll(self):
        return 0 if self.stopped else None

    def terminate(self):
        self.stopped = True
        self.stdout.lines.put(b"")

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminate()


def fixture(tmp_path, monkeypatch, *, process=None):
    process = process or FakeProcess()
    monkeypatch.setattr(subject.subprocess, "Popen", lambda *a, **k: process)
    runtime = subject.CodexAppServerRuntime(tmp_path, codex_executable="MOCK-NOT-EXECUTED")
    project = tmp_path / "project"
    workspace = project / "runtime/agent_workspace"
    workspace.mkdir(parents=True)
    return runtime, project, workspace, process


def run(runtime, project, workspace, **extra):
    options = dict(project_dir=project, agent_workspace=workspace, thread_id=None,
                   prompt="mock protocol", mcp_enabled=True, developer_instructions="fixture",
                   dynamic_tools=[{"name": "safe_tool", "inputSchema": {"type": "object", "properties": {}}}], tool_handler=lambda *_: {"success": True},
                   model="fixture-model", reasoning_effort="low", reference_images=[])
    options.update(extra)
    return runtime._run_turn(**options)


def launch(function):
    result = {}

    def target():
        try:
            result["value"] = function()
        except Exception as error:
            result["error"] = error

    thread = threading.Thread(target=target)
    thread.start()
    return thread, result


def tool_request(request_id=20, turn_id="actual-turn"):
    return {"id": request_id, "method": "item/tool/call", "params": {
        "threadId": "actual-thread", "turnId": turn_id,
        "tool": "safe_tool", "arguments": {"private": "must-not-be-progress"}}}


def test_actual_start_identity_and_pre_response_events_are_preserved(tmp_path, monkeypatch):
    def start(process, message):
        process.feed({"method": "turn/started", "params": {
            "threadId": "actual-thread", "turn": {"id": "actual-turn", "status": "inProgress"}}})
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn", "status": "inProgress"}}})
        process.feed({"method": "turn/plan/updated", "params": {
            "threadId": "actual-thread", "turnId": "actual-turn", "plan": [{"step": "Inspect model", "status": "inProgress"}]}})
        process.feed({"method": "item/reasoning/textDelta", "params": {"delta": "PRIVATE_REASONING"}})
        process.feed({"method": "item/agentMessage/delta", "params": {"itemId": "answer", "delta": "Working"}})
        process.feed({"method": "item/completed", "params": {"item": {"type": "agentMessage", "text": "Done"}}})
        process.complete()

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start=start))
    progress = []
    result = run(runtime, project, workspace, progress_callback=progress.append)
    assert (result.thread_id, result.turn_id, result.status) == ("actual-thread", "actual-turn", "completed")
    assert result.reply == "Done"
    assert {e["event"] for e in progress} >= {"turn/started", "turn/plan/updated", "item/agentMessage/delta", "turn/completed"}
    assert "PRIVATE_REASONING" not in json.dumps(progress)
    assert all(e["turn_id"] == "actual-turn" for e in progress)
    assert process.stopped and runtime.cancel_turn(project)["status"] == "not_running"


def test_cancel_before_start_response_defers_real_interrupt_and_blocks_tool(tmp_path, monkeypatch):
    start_seen = threading.Event()
    start_message = {}

    def start(process, message):
        start_message.update(message)
        start_seen.set()

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start=start))
    dispatched = []
    thread, outcome = launch(lambda: run(runtime, project, workspace, tool_handler=lambda *args: dispatched.append(args)))
    assert start_seen.wait(3)
    receipt = runtime.cancel_turn(project)
    assert receipt["status"] == "requested" and receipt["turn_id"] == ""
    assert not receipt["interrupt_sent"] and not receipt["interrupted_confirmed"]
    process.feed(tool_request())
    process.feed({"id": start_message["id"], "result": {"turn": {"id": "actual-turn"}}})
    thread.join(3)
    assert not thread.is_alive() and "error" not in outcome
    assert outcome["value"].status == "interrupted"
    assert not dispatched
    interrupt = [m for m in process.sent if m.get("method") == "turn/interrupt"]
    assert len(interrupt) == 1
    assert interrupt[0]["params"] == {"threadId": "actual-thread", "turnId": "actual-turn"}
    assert not next(m for m in process.sent if m.get("id") == 20 and "result" in m)["result"]["success"]


def test_cancel_in_flight_keeps_reader_live_and_does_not_claim_rollback(tmp_path, monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})
        process.feed(tool_request())

    def interrupt(process, message):
        process.feed({"id": message["id"], "result": {}})
        process.feed(tool_request(21))
        process.complete("interrupted")

    def handler(*args):
        entered.set()
        assert release.wait(3)
        return {"success": True}

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start, interrupt))
    thread, outcome = launch(lambda: run(runtime, project, workspace, tool_handler=handler))
    assert entered.wait(3)
    receipt = runtime.cancel_turn(project)
    assert receipt["interrupt_sent"] and receipt["in_flight_tool"] == "safe_tool"
    assert not receipt["rollback_performed"] and not receipt["interrupted_confirmed"]
    assert runtime.cancel_turn(project)["status"] == "already_requested"
    release.set()
    thread.join(3)
    assert not thread.is_alive() and "error" not in outcome
    assert outcome["value"].status == "interrupted" and outcome["value"].tool_call_count == 1
    assert outcome["value"].cancellation_requested
    assert len([m for m in process.sent if m.get("method") == "turn/interrupt"]) == 1
    assert next(m for m in process.sent if m.get("id") == 20 and "result" in m)["result"]["success"]
    assert not next(m for m in process.sent if m.get("id") == 21 and "result" in m)["result"]["success"]


def test_interrupt_ack_is_not_terminal_and_completed_race_stays_completed(tmp_path, monkeypatch):
    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})

    def interrupt(process, message):
        process.feed({"id": message["id"], "result": {}})
        process.complete("completed")

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start, interrupt))
    progress = []

    def observe(event):
        progress.append(event)
        if event["event"] == "turn_started":
            runtime.cancel_turn(project)

    result = run(runtime, project, workspace, progress_callback=observe)
    ack = next(e for e in progress if e["event"] == "interrupt_acknowledged")
    assert ack["interrupt_acknowledged"] and not ack["interrupted_confirmed"]
    assert result.status == "completed" and result.cancellation_requested


def test_foreign_turn_tool_and_terminal_cannot_affect_active_turn(tmp_path, monkeypatch):
    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})
        process.feed(tool_request(turn_id="stale-turn"))
        process.complete("interrupted", "stale-turn")
        process.complete()

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start))
    calls = []
    result = run(runtime, project, workspace, tool_handler=lambda *args: calls.append(args))
    assert result.status == "completed" and not calls
    assert not next(m for m in process.sent if m.get("id") == 20 and "result" in m)["result"]["success"]


def test_missing_turn_id_fails_closed_and_cleans_registry(tmp_path, monkeypatch):
    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"status": "inProgress"}}})

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start))
    with pytest.raises(subject.NativeAgentUnavailable, match="no turn id") as caught:
        run(runtime, project, workspace)
    assert caught.value.partial_result.status == "failed"
    assert runtime.cancel_turn(project)["status"] == "not_running" and process.stopped


def test_registry_cancels_nested_readonly_and_pending_registration(tmp_path):
    registry = NativeTurnRegistry()
    sent = []
    builder = NativeTurnControl(sent.append, lambda: None)
    critic = NativeTurnControl(sent.append, lambda: None)
    builder.bind_thread("builder-thread")
    builder.bind_turn({"turn": {"id": "builder-turn"}})
    registry.register(tmp_path, builder)
    registry.cancel(tmp_path)
    registry.register(tmp_path, critic)
    assert critic.cancel_requested and not critic.begin_tool("tool")
    critic.bind_thread("critic-thread")
    critic.bind_turn({"turn": {"id": "critic-turn"}})
    assert {m["params"]["turnId"] for m in sent} == {"builder-turn", "critic-turn"}
    registry.unregister(tmp_path, critic)
    registry.unregister(tmp_path, builder)
    assert registry.cancel(tmp_path)["status"] == "not_running"


def test_public_progress_is_bounded_and_excludes_reasoning_commands_and_args():
    assert native_progress_event("item/reasoning/summaryTextDelta", {"delta": "secret"}, thread_id="t", turn_id="u") is None
    event = native_progress_event("item/started", {"item": {
        "type": "commandExecution", "command": "private command", "arguments": {"key": "secret"}}}, thread_id="t", turn_id="u")
    assert "private" not in json.dumps(event) and "secret" not in json.dumps(event)
    event = native_progress_event("item/agentMessage/delta", {"delta": "x" * 5000}, thread_id="t", turn_id="u")
    assert len(event["text"]) == 4000


def test_readonly_intent_role_and_callback_failure_do_not_change_result(tmp_path, monkeypatch):
    runtime, project, workspace, process = fixture(tmp_path, monkeypatch)

    def failed_observer(event):
        raise ValueError("observer failure")

    result = run(runtime, project, workspace, mcp_enabled=False, dynamic_tools=[], read_only=True,
                 readonly_role="conversation_intent", progress_callback=failed_observer)
    assert result.status == "completed"
    records = [json.loads(line) for line in next((project / "runtime/agent_events").glob("*.jsonl")).read_text().splitlines()]
    assert next(e for e in records if e["event"] == "turn_input")["role"] == "conversation_intent"
    assert all(not e["is_builder"] for e in records if "is_builder" in e)
    params = next(m["params"] for m in process.sent if m.get("method") == "turn/start")
    assert params["sandboxPolicy"] == {"type": "readOnly", "networkAccess": False}


def test_ack_then_closed_stream_is_unconfirmed_failure(tmp_path, monkeypatch):
    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})

    def interrupt(process, message):
        process.feed({"id": message["id"], "result": {}})
        process.stdout.lines.put(b"")

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start, interrupt))
    progress = []

    def observe(event):
        progress.append(event)
        if event["event"] == "turn_started":
            runtime.cancel_turn(project)

    with pytest.raises(subject.NativeAgentUnavailable, match="not confirmed") as caught:
        run(runtime, project, workspace, progress_callback=observe)
    assert caught.value.partial_result.status == "failed"
    assert caught.value.partial_result.cancellation_requested
    failure = next(e for e in progress if e["event"] == "turn_failed")
    assert not failure["interrupted_confirmed"] and not failure["rollback_performed"]


def test_missing_request_identity_cannot_dispatch_or_finish(tmp_path, monkeypatch):
    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})
        request = tool_request()
        request["params"].pop("turnId")
        process.feed(request)
        process.feed({"method": "turn/completed", "params": {"turn": {"status": "interrupted"}}})
        process.complete()

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start))
    calls = []
    result = run(runtime, project, workspace, tool_handler=lambda *args: calls.append(args))
    assert result.status == "completed" and not calls


def test_interrupt_rejection_is_not_confirmation_or_permission_to_resume_tools():
    sent, progress = [], []
    control = NativeTurnControl(sent.append, lambda: None, progress.append)
    control.bind_thread("thread")
    control.bind_turn({"turn": {"id": "turn"}})
    control.request_cancel()
    control.handle_response({"id": sent[0]["id"], "error": {"message": "not active"}})
    receipt = control.receipt()
    assert receipt["cancellation_requested"] and not receipt["interrupted_confirmed"]
    assert not receipt["interrupt_acknowledged"] and receipt["interrupt_error"] == "not active"
    assert not control.begin_tool("write")
    assert progress[-1]["event"] == "interrupt_rejected"


def test_unlimited_turn_cancel_has_bounded_wait_even_with_event_flood(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(subject.time, "monotonic", lambda: clock[0])

    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})

    def interrupt(process, message):
        process.feed({"id": message["id"], "result": {}})
        for _ in range(5):
            process.feed({"method": "item/agentMessage/delta", "params": {"delta": "still pending"}})

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start, interrupt))
    runtime.timeout_seconds = 0

    def observe(event):
        if event["event"] == "turn_started":
            runtime.cancel_turn(project)
        if event["event"] == "interrupt_acknowledged":
            clock[0] += 31

    with pytest.raises(subject.NativeAgentUnavailable, match="no terminal interruption") as caught:
        run(runtime, project, workspace, progress_callback=observe)
    assert caught.value.partial_result.status == "failed" and process.stopped


def test_cancel_from_tool_start_progress_blocks_dispatch_boundary(tmp_path, monkeypatch):
    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})
        process.feed(tool_request())

    runtime, project, workspace, process = fixture(tmp_path, monkeypatch, process=FakeProcess(start))
    calls = []

    def observe(event):
        if event["event"] == "tool_started":
            runtime.cancel_turn(project)

    result = run(runtime, project, workspace, tool_handler=lambda *args: calls.append(args), progress_callback=observe)
    assert result.status == "interrupted" and not calls
    assert not next(m for m in process.sent if m.get("id") == 20 and "result" in m)["result"]["success"]


def test_uncertain_interrupt_write_is_not_claimed_sent_or_retried():
    attempts = []

    def failed_send(message):
        attempts.append(message)
        raise BrokenPipeError("closed")

    control = NativeTurnControl(failed_send, lambda: None)
    control.bind_thread("thread")
    control.bind_turn({"turn": {"id": "turn"}})
    first = control.request_cancel()
    second = control.request_cancel()
    assert first["interrupt_attempted"] and not first["interrupt_sent"]
    assert first["interrupt_error"] == "closed"
    assert second["status"] == "already_requested" and len(attempts) == 1
    assert not control.begin_tool("writer")

@pytest.mark.parametrize('receipt',[
    {'backend':'sketchup','revision':3,'connections':[{'status':'unverified'}]},
    {'backend':'blender','revision':2,'zones':[{'status':'clear_for_declared_zone'}]},
    {'success':True,'contentItems':[{'type':'inputText','text':'existing response'}]},
])
def test_actual_json_lines_dynamic_response_wraps_structured_receipt(tmp_path,monkeypatch,receipt):
    def start(process,message):
        process.feed({'id':message['id'],'result':{'turn':{'id':'actual-turn'}}})
        process.feed(tool_request())
        process.complete()
    runtime,project,workspace,process=fixture(tmp_path,monkeypatch,process=FakeProcess(start=start))
    result=run(runtime,project,workspace,tool_handler=lambda *_:receipt)
    assert result.status=='completed'
    response=next(x['result'] for x in process.sent if x.get('id')==20)
    assert set(response)=={'success','contentItems'} and response['success'] is True
    if 'contentItems' in receipt:assert response['contentItems']==receipt['contentItems']
    else:assert json.loads(response['contentItems'][0]['text'])==receipt
