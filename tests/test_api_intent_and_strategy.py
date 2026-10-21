"""Offline provider fixtures, never evidence of paid/native modeling quality."""
import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest

from app.construction_strategy import default_construction_strategy
from app.contextual_turn import resolve_host_action
from app.litellm_runtime import LiteLLMRuntime
from app.models import AgentSession, ConversationRequest, ProjectContext
from app.native_agent import NativeAgentUnavailable
from app.strategy_tools import PATH, strategy_update_tool
from app.workspace_files import workspace_file_call


def provider_fixture(tmp_path, monkeypatch, decide):
    runtime = LiteLLMRuntime(tmp_path, model="openai/fixture-model")
    runtime.session_api_key = "fixture-credential"
    monkeypatch.setattr(LiteLLMRuntime, "available", property(lambda _: True))
    requests = []
    def complete(**kwargs):
        requests.append(kwargs)
        snap = json.loads(kwargs["messages"][1]["content"][0]["text"])["CURRENT_USER"]
        decision = dict(action="plan", user_message=snap["user_message"],
            user_message_id=snap["user_message_id"], plan_sha256=snap["plan_sha256"],
            changes_plan=False, conditional=False, reason="fixture")
        decision.update(decide(snap))
        return SimpleNamespace(model="fixture-model", usage={"prompt_tokens": 123, "completion_tokens": 15},
            choices=[SimpleNamespace(finish_reason="stop", message={"content": json.dumps(decision)})])
    monkeypatch.setattr(runtime, "completion_callable", lambda: complete)
    route = SimpleNamespace(provider="litellm", model=runtime.model, reasoning_effort="low")
    router = SimpleNamespace(codex_runtime=object(), providers={"litellm": runtime}, route=lambda _: route)
    return runtime, router, requests


def test_api_plan_with_no_build_uses_selected_readonly_interpreter(tmp_path, monkeypatch):
    runtime, router, requests = provider_fixture(tmp_path, monkeypatch, lambda _: {})
    message = "继续补齐未完成的主楼方案，暂不建模。"
    result = resolve_host_action(router, project=tmp_path,
        session=AgentSession(project_id="test", reconstruction_state="clarifying"),
        request=ConversationRequest(message=message, workflow_mode="image_reconstruction"), context=ProjectContext())
    assert result[0] == "plan" and result[1]["execution_granted"] is False
    assert result[1]["provider"] == "api_readonly_intent"
    assert result[1]["usage"]["input_tokens"] == 123
    assert len(requests) == 1 and requests[0]["model"] == runtime.model
    assert not {"tools", "tool_choice", "parallel_tool_calls"} & requests[0].keys()
    assert not (tmp_path / "runtime/provider_sessions").exists()


def test_api_intent_stale_plan_and_false_execution_are_host_vetoed(tmp_path, monkeypatch):
    from app.design_scope_approval import capture_pending_design_plan
    card = tmp_path / "runtime/agent_workspace/notes/reconstruction_card.md"
    card.parent.mkdir(parents=True)
    card.write_text("两层；保留屋顶。", encoding="utf-8")
    pending = capture_pending_design_plan(tmp_path, card.read_text(encoding="utf-8"), is_followup=False)
    _, router, requests = provider_fixture(tmp_path, monkeypatch, lambda _: {"action": "execute"})
    session = AgentSession(project_id="test", reconstruction_state="planned")
    req = ConversationRequest(message="不要开始建模，先解释。", workflow_mode="image_reconstruction",
        approved_plan_sha256=pending["plan_sha256"], approved_pending_plan_id=pending["pending_plan_id"])
    action, receipt = resolve_host_action(router, project=tmp_path, session=session, request=req, context=ProjectContext())
    assert action == "clarify" and not receipt["execution_granted"]
    req.message = "我批准。"
    req.approved_plan_sha256 = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        resolve_host_action(router, project=tmp_path, session=session, request=req, context=ProjectContext())
    assert len(requests) == 2


def test_api_explicit_button_has_no_extra_billable_interpretation(tmp_path, monkeypatch):
    from app.design_scope_approval import capture_pending_design_plan
    card = tmp_path / "runtime/agent_workspace/notes/reconstruction_card.md"
    card.parent.mkdir(parents=True)
    card.write_text("两层。", encoding="utf-8")
    pending = capture_pending_design_plan(tmp_path, card.read_text(encoding="utf-8"), is_followup=False)
    _, router, requests = provider_fixture(tmp_path, monkeypatch, lambda _: {})
    req = ConversationRequest(message="确认，按当前计划开始建模。", workflow_mode="image_reconstruction",
        approval_gesture="plan_button", approved_plan_sha256=pending["plan_sha256"],
        approved_pending_plan_id=pending["pending_plan_id"])
    action, receipt = resolve_host_action(router, project=tmp_path,
        session=AgentSession(project_id="test", reconstruction_state="planned"), request=req, context=ProjectContext())
    assert action == "execute" and receipt["provider"] == "explicit_button" and requests == []


def test_api_intent_honors_same_durable_budget_without_dispatch(tmp_path, monkeypatch):
    runtime, router, requests = provider_fixture(tmp_path, monkeypatch, lambda _: {})
    budget = tmp_path / "budget.json"
    original = dict(model=runtime.model, api_base=runtime.api_base, limit_usd="0.01",
        input_usd_per_million="0.3", output_usd_per_million="1.2", max_input_tokens=1048576,
        max_output_tokens=32768, requests=[dict(id="old", status="unresolved", liability_usd="0.01")])
    budget.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setenv("K_STUDIO_LOCAL_API_TEST_BUDGET", str(budget))
    with pytest.raises(NativeAgentUnavailable, match="安全边界"):
        resolve_host_action(router, project=tmp_path, session=AgentSession(project_id="test"),
            request=ConversationRequest(message="补齐方案，暂不建模。"), context=ProjectContext())
    assert requests == [] and json.loads(budget.read_text()) == original


def seed(tmp_path):
    (tmp_path / "notes").mkdir()
    return workspace_file_call(tmp_path, "workspace_write", {"relative_path": PATH,
        "content": json.dumps(default_construction_strategy())})


def parameter(**changes):
    return dict(name="width", value=10800, units="mm", provenance="user_confirmed", source="user", **changes)


def test_typed_strategy_update_preserves_other_parameters_and_versions(tmp_path):
    first = seed(tmp_path)
    p = parameter()
    second = workspace_file_call(tmp_path, "workspace_update_strategy", {
        "expected_sha256": first["file_sha256"], "parameters": [p]})
    third = workspace_file_call(tmp_path, "workspace_update_strategy", {
        "expected_sha256": second["file_sha256"], "parameters": [{**p, "name": "floors", "value": 10, "units": "count"}]})
    saved = workspace_file_call(tmp_path, "workspace_read", {"relative_path": PATH})
    parameters = json.loads(saved["content"])["shared_parameters"]
    assert parameters["width"]["value"] == 10800 and parameters["floors"]["value"] == 10
    assert saved["file_sha256"] == third["file_sha256"] != first["file_sha256"]
    with pytest.raises(ValueError, match="changed"):
        workspace_file_call(tmp_path, "workspace_update_strategy", {"expected_sha256": first["file_sha256"], "parameters": [p]})
    assert (tmp_path / PATH).read_bytes() == saved["content"].encode()


@pytest.mark.parametrize("changes", [
    {"provenance": "generated"}, {"value": [0, 0, 0]}, {"value": "10800"},
    {"units": "text"}, {"units": []}, {"value": float("inf")}, {"value": True},
    {"units": "count", "value": 1.5}, {"unit": "mm"},
])
def test_invalid_plan_fields_never_coerce_or_change_file(tmp_path, changes):
    original = seed(tmp_path)
    before = (tmp_path / PATH).read_bytes()
    with pytest.raises(ValueError):
        workspace_file_call(tmp_path, "workspace_update_strategy", {
            "expected_sha256": original["file_sha256"], "parameters": [{**parameter(), **changes}]})
    assert (tmp_path / PATH).read_bytes() == before
    assert not list((tmp_path / "notes").glob("*.tmp"))


def test_strategy_batch_validation_is_all_or_nothing(tmp_path):
    original = seed(tmp_path)
    system_schema = strategy_update_tool()["inputSchema"]["properties"]["systems"]["items"]
    assert "level_slabs" not in system_schema["properties"]["role"]["enum"]
    with pytest.raises(ValueError):
        workspace_file_call(tmp_path, "workspace_update_strategy", {
            "expected_sha256": original["file_sha256"], "parameters": [parameter()],
            "systems": [{"id": "slabs", "stage": "primary_form", "role": "level_slabs",
                "method": "custom_owned_ruby", "method_id": "custom.ruby", "selection_reason": "fixture",
                "depends_on": ["width"], "target_paths": [], "verification_views": ["front"], "notes": []}]})
    assert hashlib.sha256((tmp_path / PATH).read_bytes()).hexdigest() == original["file_sha256"]


def test_real_sse_adapter_workspace_journal_and_typed_plan_loop_offline(tmp_path, monkeypatch):
    """Real product code + mock HTTP. Not a live-model/native acceptance test."""
    from app import bai_transport
    original = bai_transport.complete_bai
    requests = []
    def server(request):
        body = json.loads(request.content)
        requests.append(body)
        assert body["model"] == "fixture-model"
        assert any(t["function"]["name"] == "workspace_update_strategy" for t in body["tools"])
        number = len(requests)
        if number == 1:
            name, args = "workspace_read", {"relative_path": PATH}
        elif number == 2:
            # The transport must retain the previous thinking/tool exchange.
            assert any(m.get("reasoning_content") == "fixture-private-state" for m in body["messages"])
            result = json.loads(body["messages"][-1]["content"])
            name, args = "workspace_update_strategy", {"expected_sha256": result["file_sha256"],
                "parameters": [parameter(), {**parameter(), "name": "floors", "units": "count", "value": 10}],
                "systems": [{"id": "shell", "stage": "primary_form", "role": "shell",
                    "method": "continuous_wall_with_openings", "method_id": "saie.wall_with_openings",
                    "selection_reason": "fixture rectangular host", "depends_on": ["width", "floors"],
                    "target_paths": [["SHELL"]], "verification_views": ["front", "oblique"], "notes": []}]}
        else:
            assert number == 3 and json.loads(body["messages"][-1]["content"])["success"]
            name = None
        delta = {"tool_calls": [{"index": 0, "id": "fixture-" + str(number), "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}]} if name else {"content": "方案已整理，等待确认。"}
        chunks = [dict(model="fixture-model", choices=[dict(index=0, delta={"reasoning_content": "fixture-private-state"})]),
            dict(model="fixture-model", choices=[dict(index=0, delta=delta)]),
            dict(model="fixture-model", choices=[dict(index=0, delta={}, finish_reason="tool_calls" if name else "stop")]),
            dict(model="fixture-model", choices=[], usage=dict(prompt_tokens=100, completion_tokens=50))]
        wire = "".join("data: " + json.dumps(c) + "\n\n" for c in chunks) + "data: [DONE]\n\n"
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=wire)
    monkeypatch.setattr(bai_transport, "complete_bai", lambda kwargs, record: original(
        kwargs, record=record, transport=httpx.MockTransport(server)))
    runtime = LiteLLMRuntime(tmp_path, model="openai/fixture-model")
    runtime.custom_api_base = "https://api.b.ai/v1"
    runtime.session_api_key = "fixture-key"
    # No LiteLLM import or network: B.AI uses its own real SSE adapter.
    monkeypatch.setattr(runtime, "completion_callable", lambda: lambda **_: pytest.fail("wrong transport"))
    result = runtime.respond(project_dir=tmp_path / "project", thread_id=None,
        prompt="请整理十层主楼方案，暂不建模。", mcp_enabled=False, ruby_enabled=False,
        developer_instructions="offline fixture", workflow_mode="image_reconstruction",
        tool_profile="reconstruction_coding", reasoning_effort="low")
    assert result.status == "completed" and result.tool_call_count == 2 and result.failed_tool_calls == 0
    assert result.input_tokens == 300 and result.output_tokens == 150
    strategy = json.loads((tmp_path / "project/runtime/agent_workspace" / PATH).read_text(encoding="utf-8"))
    assert strategy["shared_parameters"]["floors"]["value"] == 10 and len(strategy["systems"]) == 1
    assert not list(tmp_path.rglob("*.skp"))
    saved = json.loads(next(tmp_path.rglob("litellm-*.json")).read_text(encoding="utf-8"))
    assert len([m for m in saved["messages"] if m["role"] == "tool"]) == 2


@pytest.mark.parametrize("failure,phase", [(httpx.ConnectTimeout("fixture"), "connecting"),
                                        (httpx.ReadTimeout("fixture"), "streaming")])
def test_transport_diagnostics_distinguish_connection_and_stream_stall(failure, phase):
    from app.bai_transport import complete_bai
    records = []
    class Stall(httpx.SyncByteStream):
        def __iter__(self):
            raise failure
            yield b""
    def server(_):
        if phase == "connecting":
            raise failure
        return httpx.Response(200, headers={"content-type": "text/event-stream", "x-request-id": "safe-id"}, stream=Stall())
    with pytest.raises(type(failure)):
        complete_bai(dict(model="openai/fixture", api_base="https://api.b.ai/v1", api_key="fixture-key", messages=[]),
            record=records.append, transport=httpx.MockTransport(server))
    assert records[-1]["phase"] == phase and records[-1]["event"] == "provider_transport_failed"
    assert records[-1]["error_type"] == type(failure).__name__
    assert "fixture-key" not in json.dumps(records)
