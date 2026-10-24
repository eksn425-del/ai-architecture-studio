"""Zero-paid fake-provider replay; writes synthetic events and the EXISTING ledger format.

No SDK resolution, credential access, network, native model or GPU operation.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.litellm_runtime import LiteLLMRuntime
from app.run_usage_audit import audit_run, read_audit, run_started


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    reports = {}
    for case in ("cache", "missing_usage", "timeout", "cancelled"):
        folder = output / case
        folder.mkdir()
        ledger = folder / "budget.json"
        # Toy fixture rates are NOT a pricing recommendation or a spend approval.
        dump(ledger, {"model": "openai/fixture-model", "api_base": "https://fixture.invalid/v1",
            "limit_usd": "1", "input_usd_per_million": "1", "output_usd_per_million": "1",
            "max_input_tokens": 1000, "max_output_tokens": 1000})
        rt = LiteLLMRuntime(folder, model="openai/fixture-model")
        rt.custom_api_base = "https://fixture.invalid/v1"
        trace = folder / "events.jsonl"
        def record(event):
            with trace.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event) + "\n")
        record(run_started(case, "litellm", "fixture.invalid", rt.model, "synthetic_replay"))
        def fake(**kwargs):
            if case == "timeout":
                raise TimeoutError("synthetic")
            if case == "cancelled":
                raise asyncio.CancelledError("synthetic")
            return SimpleNamespace(model="fixture-model", usage=None if case == "missing_usage" else {
                "prompt_tokens": 100, "completion_tokens": 20,
                "prompt_tokens_details": {"cached_tokens": 80}})
        with patch.dict(os.environ, {"K_STUDIO_LOCAL_API_TEST_BUDGET": str(ledger)}):
            try:
                rt._invoke_provider({"model": rt.model}, record=record, completion=fake)
            except (TimeoutError, asyncio.CancelledError, ValueError):
                record({"event": "run_audit_finished", "status": "failed_or_cancelled"})
            else:
                record({"event": "run_audit_finished", "status": "completed"})
        before = ledger.read_bytes()
        report = read_audit(trace, ledger)
        assert before == ledger.read_bytes()
        assert report["cost"]["billed_usd"] is None
        assert report["cost"]["ledger_coverage_complete"]
        assert report["counts"]["http_requests"] is None
        if case == "cache":
            assert report["usage"]["input_tokens"] == 100
            assert report["usage"]["uncached_input_tokens"] == 20
        else:
            assert report["usage"]["input_tokens"] is None
            assert report["cost"]["ledger_rows"][0]["status"] == "unresolved"
        dump(folder / "audit.json", report)
        reports[case] = report
    sample = {"event": "token_usage", "scope": "turn_delta_from_thread_total",
              "input_tokens": 150, "output_tokens": 20, "cached_input_tokens": 80}
    cumulative = audit_run([{**sample, "input_tokens": 100}, sample, dict(sample)])
    assert cumulative["usage"]["input_tokens"] == 150
    legacy = audit_run([{"event": "provider_response"}] * 13)
    assert legacy["counts"]["model_response_events"] == 13
    assert legacy["counts"]["http_requests"] is None
    dump(output / "summary.json", {"test_kind": "synthetic zero-paid replay",
        "real_provider_calls": "NOT_RUN", "invoice": "unknown_not_zero",
        "cases": reports, "duplicate_cumulative": cumulative, "13_legacy_events": legacy})
    print("PASS: four fake-provider ledger scenarios + duplicate cumulative replay + 13-event ambiguity")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output)
