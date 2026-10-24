"""Zero-paid replay/fake transport tests; no credentials or upstream requests."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from app.litellm_runtime import LiteLLMRuntime
from app.run_usage_audit import audit_run, read_audit, usage_fields
from tests.test_provider_test_budget import configured


def response(usage=None):
    return SimpleNamespace(model="deepseek-v4.1-flash", usage=usage)


def runtime(tmp_path):
    rt = LiteLLMRuntime(tmp_path, model="openai/deepseek-v4.1-flash")
    # A fake callable below is the only provider. Never resolve/import a real SDK.
    rt.custom_api_base = "https://fixture.invalid/v1"
    return rt


def invoke(rt, events, complete):
    return rt._invoke_provider({"model": rt.model}, record=events.append, completion=complete)


@pytest.mark.parametrize("usage", [None, {}, {"prompt_tokens": True, "completion_tokens": -1}])
def test_missing_or_invalid_usage_is_unknown(tmp_path, monkeypatch, usage):
    monkeypatch.delenv("K_STUDIO_LOCAL_API_TEST_BUDGET", raising=False)
    events = []
    invoke(runtime(tmp_path), events, lambda **_: response(usage))
    audit = audit_run(events)
    assert audit["usage"]["input_tokens"] is None
    assert audit["usage"]["complete"] is False
    assert audit["counts"]["unresolved_attempts"] == 1
    assert audit["cost"]["billed_usd"] is None


def test_cache_and_reasoning_are_subsets_not_additional_tokens():
    fields = usage_fields(response({"prompt_tokens": 100, "completion_tokens": 20,
        "prompt_tokens_details": {"cached_tokens": 80},
        "completion_tokens_details": {"reasoning_tokens": 15}}))
    audit = audit_run([{"event": "provider_dispatch_finished", "attempt_id": "a", "status": "returned", **fields}])
    assert audit["usage"]["input_tokens"] == 100
    assert audit["usage"]["cached_input_tokens"] == 80
    assert audit["usage"]["uncached_input_tokens"] == 20
    assert audit["usage"]["output_tokens"] == 20


@pytest.mark.parametrize("cache", [None, True, -1, 101])
def test_missing_or_invalid_cache_cannot_be_guessed(cache):
    fields = usage_fields(response({"prompt_tokens": 100, "completion_tokens": 20,
        "prompt_tokens_details": {"cached_tokens": cache}}))
    assert fields["cached_input_tokens"] is None
    assert fields["uncached_input_tokens"] is None


def test_duplicate_dispatch_receipt_does_not_duplicate_usage():
    event = {"event": "provider_dispatch_finished", "attempt_id": "a", "status": "returned",
             "input_tokens": 100, "output_tokens": 20, "cached_input_tokens": 80}
    audit = audit_run([event, dict(event), {"event": "provider_response", "input_tokens": 100, "output_tokens": 20}])
    assert audit["usage"]["input_tokens"] == 100
    assert audit["counts"]["host_dispatch_attempts"] == 1
    assert audit["counts"]["http_requests"] is None
    assert audit["counts"]["internal_retries"] is None


def test_native_cumulative_deltas_use_latest_not_sum():
    samples = [{"event": "token_usage", "scope": "turn_delta_from_thread_total",
                "input_tokens": n, "output_tokens": n // 10, "cached_input_tokens": n // 2} for n in (100, 150, 150)]
    audit = audit_run(samples)
    assert audit["usage"]["input_tokens"] == 150
    assert audit["usage"]["cached_input_tokens"] == 75
    assert audit["counts"]["host_dispatch_attempts"] is None
    audit = audit_run(samples + [{"event": "token_usage", "scope": "turn_delta_from_thread_total",
                                 "input_tokens": None, "output_tokens": None}])
    assert audit["usage"]["input_tokens"] is None  # counter reset cannot reuse old value


@pytest.mark.parametrize("error", [TimeoutError, asyncio.CancelledError, KeyboardInterrupt])
def test_timeout_and_cancellation_preserve_linked_liability(tmp_path, monkeypatch, error):
    path = configured(tmp_path, monkeypatch)
    # Fixture budget must match the fake endpoint; no account or old ledger read.
    data = json.loads(path.read_text())
    data["api_base"] = "https://fixture.invalid/v1"
    path.write_text(json.dumps(data))
    events = []
    def lost(**_):
        assert json.loads(path.read_text())["requests"][-1]["status"] == "reserved"
        raise error()
    with pytest.raises(error):
        invoke(runtime(tmp_path), events, lost)
    data = json.loads(path.read_text())
    assert data["requests"][0]["status"] == "unresolved"
    assert data["requests"][0]["id"] == events[0]["attempt_id"]
    audit = audit_run(events, data)
    assert audit["counts"]["unresolved_attempts"] == 1
    assert audit["cost"]["ledger_rows"][0]["liability_usd"] != "0"
    assert audit["cost"]["billed_usd"] is None


def test_known_usage_settles_upper_bound_but_not_invoice(tmp_path, monkeypatch):
    path = configured(tmp_path, monkeypatch)
    data = json.loads(path.read_text())
    data["api_base"] = "https://fixture.invalid/v1"
    path.write_text(json.dumps(data))
    events = []
    invoke(runtime(tmp_path), events, lambda **_: response({"prompt_tokens": 100, "completion_tokens": 20,
        "prompt_tokens_details": {"cached_tokens": 80}}))
    trace = tmp_path / "trace.jsonl"
    trace.write_text("\n".join(json.dumps(e) for e in events))
    before = path.read_bytes()
    audit = read_audit(trace, path)
    assert path.read_bytes() == before
    assert audit["cost"]["ledger_coverage_complete"] is True
    assert audit["cost"]["ledger_rows"][0]["status"] == "settled_upper_bound"
    assert audit["cost"]["billed_usd"] is None
    assert audit["usage"]["uncached_input_tokens"] == 20


def test_legacy_model_events_never_become_http_requests():
    audit = audit_run([{"event": "provider_response", "input_tokens": 100, "output_tokens": 20}] * 13)
    assert audit["counts"]["model_response_events"] == 13
    assert audit["counts"]["http_requests"] is None
    assert audit["counts"]["host_dispatch_attempts"] is None
    assert audit["provenance"]["code_sha"] is None
    assert audit["delivery"]["save_reopen"] == "NOT_VERIFIED"
    assert audit["usage"]["input_tokens"] is None


def test_conflicting_duplicate_receipts_fail_unknown():
    event = {"event": "provider_dispatch_finished", "attempt_id": "a", "status": "returned",
             "input_tokens": 100, "output_tokens": 20}
    audit = audit_run([event, {**event, "input_tokens": 200}])
    assert audit["usage"]["input_tokens"] is None
    assert audit["counts"]["unresolved_attempts"] == 1


def test_native_delivery_receipt_does_not_invent_keep_or_quality_acceptance():
    audit = audit_run([{"event": "tool_receipt", "tool": "blender_update_objects", "call_id": "edit",
        "output": {"geometry": {"rail": {}}, "revision": 2, "native_reopen": "PASS", "sha256": "a" * 64,
                   "quality_status": "unverified"}}])
    assert audit["native_delivery_receipts"][0]["native_reopen"] == "PASS"
    assert audit["native_delivery_receipts"][0]["quality_status"] == "unverified"
    assert audit["delivery"]["keep"] == "NOT_VERIFIED"


def test_fresh_run_records_code_identity_and_end_status(tmp_path, monkeypatch):
    monkeypatch.delenv("K_STUDIO_LOCAL_API_TEST_BUDGET", raising=False)
    rt = runtime(tmp_path)
    rt.session_api_key = "synthetic-never-sent"
    rt.completion_callable = lambda: lambda **_: SimpleNamespace(model="deepseek-v4.1-flash",
        usage={"prompt_tokens": 100, "completion_tokens": 20},
        choices=[SimpleNamespace(message={"content": "fixture response"})])
    result = rt.respond(project_dir=tmp_path, thread_id=None, prompt="read only fixture", mcp_enabled=False,
                        developer_instructions="fixture", ruby_enabled=False)
    assert result.status == "completed"
    trace = next((tmp_path / "runtime/agent_events").glob("*.jsonl"))
    audit = read_audit(trace)
    assert len(audit["provenance"]["code_sha"]) == 40
    assert audit["provenance"]["selected_runtime"] == "litellm"
    assert audit["actual_identity"][0]["model"] == "deepseek-v4.1-flash"
    assert audit["usage"]["input_tokens"] == 100
    assert audit["status"] == "completed"
    assert "synthetic-never-sent" not in trace.read_text()
