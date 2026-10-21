"""Fault injection with a simulated provider and counter-only native effects."""
import json
from types import SimpleNamespace

import pytest

from app.litellm_runtime import LiteLLMRuntime
from app.native_agent import NativeAgentUnavailable


def call(identifier="c1", name="write", arguments="{}"):
    return {"id": identifier, "function": {"name": name, "arguments": arguments}}


def response(calls=None, *, model="deepseek-flash", usage=None, finish="stop"):
    return SimpleNamespace(model=model,
        usage={"prompt_tokens": 10, "completion_tokens": 2} if usage is None else usage,
        choices=[SimpleNamespace(finish_reason=finish,
            message={"content": None if calls else "完成检查", "tool_calls": calls or []})])


def runtime(tmp_path, monkeypatch, replies, dispatch=None):
    r = LiteLLMRuntime(tmp_path, model="deepseek/deepseek-flash")
    r.session_api_key = "fixture-key-not-a-credential"
    r.custom_api_base = ""
    r.region = "beijing"
    effects, requests = [], []
    def execute(name, args):
        effects.append((name, args))
        if dispatch:
            dispatch(name, args)
        return {"success": True}
    context = SimpleNamespace(dynamic_tools=[{"name": "write", "inputSchema": {"type": "object"}}],
                              quality_state={}, dispatch=execute)
    monkeypatch.setattr(r.tool_surface, "prepare", lambda **_: context)
    def complete(**kwargs):
        requests.append(kwargs)
        return replies[len(requests) - 1]
    monkeypatch.setattr(r, "completion_callable", lambda: complete)
    return r, effects, requests


def run(r, root, thread=None):
    return r.respond(project_dir=root, thread_id=thread, prompt="只修改副本的扶手颜色。",
                     mcp_enabled=True, ruby_enabled=False, developer_instructions="fixture")


@pytest.mark.parametrize("bad", [
    response([call()], model="different-model"),
    response([call()], model=None),
    response([call()], usage={}),
    response([call()], usage={"prompt_tokens": True, "completion_tokens": 2}),
    response([call()], usage={"prompt_tokens": -1, "completion_tokens": 2}),
    response([call()], finish="length"),
    response([call()], finish="content_filter"),
    response([call()], finish=[]),
    SimpleNamespace(model="deepseek-flash", usage={"prompt_tokens": 10, "completion_tokens": 2}, choices=[]),
    SimpleNamespace(model="deepseek-flash", usage={"prompt_tokens": 10, "completion_tokens": 2},
                    choices=[SimpleNamespace(message=None)]),
])
def test_bad_provider_response_has_zero_effects_and_no_retry(tmp_path, monkeypatch, bad):
    r, effects, requests = runtime(tmp_path, monkeypatch, [bad])
    with pytest.raises(NativeAgentUnavailable) as caught:
        run(r, tmp_path)
    assert caught.value.partial_result.status == "interrupted"
    assert effects == [] and len(requests) == 1
    events = [json.loads(line) for p in (tmp_path / "runtime/agent_events").glob("*.jsonl")
              for line in p.read_text(encoding="utf-8").splitlines()]
    assert any(e["event"] == "provider_contract_rejected" for e in events)


@pytest.mark.parametrize("batch", [
    [call(), call()],
    [call(), call(None)],
    [call(), call("c2", name="")],
    [call(), call("c2", arguments="[]")],
    [call(), call("c2", arguments="{")],
    [call(), call("c2", name="unregistered_write")],
    [call(), {"id": "c2", "function": {"name": "write"}}],
])
def test_entire_batch_validates_before_first_effect(tmp_path, monkeypatch, batch):
    r, effects, requests = runtime(tmp_path, monkeypatch, [response(batch)])
    with pytest.raises(NativeAgentUnavailable):
        run(r, tmp_path)
    assert effects == [] and len(requests) == 1


def test_repeated_id_cannot_repeat_completed_effect(tmp_path, monkeypatch):
    r, effects, requests = runtime(tmp_path, monkeypatch, [response([call()]), response([call()])])
    with pytest.raises(NativeAgentUnavailable, match="repeated"):
        run(r, tmp_path)
    assert len(effects) == 1 and len(requests) == 2


def test_intent_is_durable_before_dispatch_and_complete_history_resumes(tmp_path, monkeypatch):
    def inspect_intent(*_):
        saved = json.loads(next((tmp_path / "runtime/provider_sessions").glob("*.json")).read_text(encoding="utf-8"))
        assert saved["messages"][-1]["role"] == "assistant"
        assert saved["messages"][-1]["tool_calls"][0]["id"] == "c1"
    r, effects, requests = runtime(tmp_path, monkeypatch,
        [response([call()]), response(), response()], inspect_intent)
    result = run(r, tmp_path)
    again = run(r, tmp_path, result.thread_id)
    assert again.reply == "完成检查"
    assert len(effects) == 1 and len(requests) == 3


def test_process_loss_after_effect_blocks_resume_before_request(tmp_path, monkeypatch):
    class ProcessLost(BaseException):
        pass
    def lose_process(*_):
        raise ProcessLost()
    r, effects, requests = runtime(tmp_path, monkeypatch, [response([call()])], lose_process)
    with pytest.raises(ProcessLost):
        run(r, tmp_path)
    saved = next((tmp_path / "runtime/provider_sessions").glob("*.json"))
    with pytest.raises(NativeAgentUnavailable, match="工具结果未确认"):
        run(r, tmp_path, saved.stem)
    assert len(effects) == 1 and len(requests) == 1


def test_disk_failure_before_intent_has_zero_effects(tmp_path, monkeypatch):
    from pathlib import Path
    original = Path.write_text
    def disk_full(path, *args, **kwargs):
        if path.parent.name == "provider_sessions":
            raise OSError("simulated disk full")
        return original(path, *args, **kwargs)
    r, effects, requests = runtime(tmp_path, monkeypatch, [response([call()])])
    monkeypatch.setattr(Path, "write_text", disk_full)
    with pytest.raises(OSError, match="disk full"):
        run(r, tmp_path)
    assert effects == [] and len(requests) == 1


def test_old_user_keep_survives_model_checkpoint_and_current_tools_unchanged():
    from app.context_compaction import compact_active_reconstruction_context
    keep = {"role": "user", "content": "门窗和屋顶全部保留；不要修改原件，只改副本。"}
    current = [{"role": "user", "content": "扶手改成铜色。"},
               {"role": "assistant", "content": None, "tool_calls": [call()]},
               {"role": "tool", "tool_call_id": "c1", "content": "ok"}]
    messages = [{"role": "system", "content": "rules"}, keep,
                {"role": "assistant", "content": "x" * 120000}, *current]
    active, meta = compact_active_reconstruction_context(messages, "ACTIVE RECONSTRUCTION CHECKPOINT\nroof changed")
    assert meta["compacted"] and active[1] == keep
    assert active[-3:] == current and messages[2]["content"] == "x" * 120000


@pytest.mark.parametrize("one_batch", [False, True])
def test_three_failed_plan_writes_stop_paid_loop_and_answer_all_batch_ids(tmp_path, monkeypatch, one_batch):
    args = json.dumps({"relative_path": "notes/construction_strategy.json", "content": "invalid"})
    calls = [call("plan-" + str(i), "workspace_write", args) for i in range(4)]
    replies = [response(calls)] if one_batch else [response([c]) for c in calls]
    r, _, requests = runtime(tmp_path, monkeypatch, replies)
    attempted = []
    def reject(name, arguments):
        attempted.append(name)
        return {"success": False, "text": "invalid schema; fixture"}
    context = SimpleNamespace(dynamic_tools=[{"name": "workspace_write", "inputSchema": {"type": "object"}}],
                              quality_state={}, dispatch=reject)
    monkeypatch.setattr(r.tool_surface, "prepare", lambda **_: context)
    with pytest.raises(NativeAgentUnavailable, match="连续 3 次校验失败"):
        run(r, tmp_path)
    assert len(attempted) == 3
    assert len(requests) == (1 if one_batch else 3)
    saved = json.loads(next((tmp_path / "runtime/provider_sessions").glob("*.json")).read_text(encoding="utf-8"))["messages"]
    answers = [m["tool_call_id"] for m in saved if m["role"] == "tool"]
    assert answers == [c["id"] for c in (calls if one_batch else calls[:3])]


def test_critic_model_mismatch_stops_without_paid_recovery_or_review_dispatch(tmp_path, monkeypatch):
    import app.litellm_runtime as module
    image = tmp_path / "inputs/reference/source.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"fixture-not-real-pixels")
    r, effects, requests = runtime(tmp_path, monkeypatch,
        [response([call(name="sketchup_submit_visual_review", arguments='{"views":{}}')]),
         response(model="different-critic")])
    context = SimpleNamespace(dynamic_tools=[{"name": "sketchup_submit_visual_review", "inputSchema": {"type": "object"}}],
                              quality_state={}, dispatch=lambda *args: effects.append(args))
    monkeypatch.setattr(r.tool_surface, "prepare", lambda **_: context)
    monkeypatch.setattr(module, "validate_visual_review_views", lambda *a: ({}, None,
        {name: image for name in module.CANONICAL_REVIEW_VIEWS}))
    monkeypatch.setattr(module, "validate_source_matched_pairs", lambda *a: [])
    with pytest.raises(NativeAgentUnavailable) as caught:
        r.respond(project_dir=tmp_path, thread_id=None, prompt="检查副本", mcp_enabled=True,
            ruby_enabled=False, ruby_state={}, developer_instructions="fixture",
            workflow_mode="image_reconstruction", tool_profile="reconstruction_coding")
    assert len(requests) == 2 and effects == []
    assert caught.value.partial_result.input_tokens == 20
    assert caught.value.partial_result.output_tokens == 4
    events = [json.loads(line) for p in (tmp_path / "runtime/agent_events").glob("*.jsonl")
              for line in p.read_text(encoding="utf-8").splitlines()]
    rejected = next(e for e in events if e["event"] == "visual_critic_contract_rejected")
    assert rejected["input_tokens"] == 10 and rejected["output_tokens"] == 2
