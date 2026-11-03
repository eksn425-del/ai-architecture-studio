"""Read-only projection of existing agent_events + provider_test_budget ledger.

Transport attempts, model events and HTTP requests are different quantities.
No prices, invoices, credentials or missing telemetry are inferred here.
"""
from __future__ import annotations

import json
import hashlib
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from datetime import datetime, timezone


def count(value):
    return value if type(value) is int and value >= 0 else None


def usage_fields(response):
    def get(obj, name):
        return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
    usage = get(response, "usage")
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    usage = usage if isinstance(usage, dict) else {}
    inp = count(usage.get("prompt_tokens", usage.get("input_tokens")))
    out = count(usage.get("completion_tokens", usage.get("output_tokens")))
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    cache = count(details.get("cached_tokens")) if isinstance(details, dict) else None
    if cache is None:
        cache = count(usage.get("prompt_cache_hit_tokens"))
    if inp is None or cache is not None and cache > inp:
        cache = None
    return {"input_tokens": inp, "output_tokens": out, "cached_input_tokens": cache,
            "uncached_input_tokens": inp - cache if inp is not None and cache is not None else None,
            "usage_source": "provider_response.usage" if usage else "missing",
            "response_model": get(response, "model")}


def run_started(run_id, runtime, provider, model, role):
    root = Path(__file__).resolve().parents[1]
    # Read only Git provenance, without starting another subprocess inside the
    # modeling process boundary. Installed copies can legitimately lack .git.
    sha = None
    digest = None
    try:
        gitdir = root / ".git"
        if gitdir.is_file():
            gitdir = (root / gitdir.read_text(encoding="utf-8").strip().removeprefix("gitdir: ")).resolve()
        head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref = head[5:]
            if ref.startswith("refs/") and ".." not in ref and "\\" not in ref:
                common = (gitdir / (gitdir / "commondir").read_text().strip()).resolve() if (gitdir / "commondir").exists() else gitdir
                if (common / ref).is_file():
                    head = (common / ref).read_text().strip()
                elif (common / "packed-refs").is_file():
                    head = next((line.split()[0] for line in (common / "packed-refs").read_text().splitlines()
                                 if line.endswith(" " + ref)), "")
        sha = head if re.fullmatch(r"[0-9a-f]{40}", head) else None
    except (OSError, ValueError):
        pass
    try:
        hasher = hashlib.sha256()
        for path in sorted((root / "app").rglob("*.py")):
            hasher.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
        digest = hasher.hexdigest()
    except OSError:
        pass
    return {"event": "run_audit_started", "schema_version": 1, "run_id": run_id,
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "code_sha": sha, "runtime_python_source_sha256": digest,
            "working_tree_dirty": None,
            "source_note": "HEAD is provenance; runtime Python digest identifies actual source bytes. Dirty state is not inferred.",
            "selected_runtime": runtime, "selected_provider": provider or None,
            "selected_model": model, "role": role}


def audit_run(events, ledger=None):
    """Legacy traces remain readable, with explicit missing provenance/coverage."""
    start = next((e for e in events if e.get("event") == "run_audit_started"), {})
    attempts = {}
    first_finished = {}
    attempt_anomalies = {}
    finished_fields = ("status", "response_model", "requested_model", "runtime", "provider",
                       "response_id", "request_id", "actual_model", "reported_provider",
                       "input_tokens", "output_tokens", "cached_input_tokens", "uncached_input_tokens")
    for e in events:
        if e.get("event") in {"provider_dispatch_started", "provider_dispatch_finished"}:
            attempt_id = e["attempt_id"]
            previous = attempts.setdefault(attempt_id, {})
            conflicts = attempt_anomalies.setdefault(attempt_id, set())
            # A start is lifecycle context, not a competing terminal receipt.
            # A late duplicate start must never overwrite an observed finish.
            for key in ("requested_model", "runtime", "provider"):
                if key in previous and key in e and previous[key] != e[key]:
                    conflicts.add(key)
            if e["event"] == "provider_dispatch_finished":
                if attempt_id in first_finished:
                    first = first_finished[attempt_id]
                    conflicts.update(k for k in finished_fields if first.get(k) != e.get(k))
                else:
                    first_finished[attempt_id] = dict(e)
                    previous.update(e)
            else:
                for key, value in e.items():
                    previous.setdefault(key, value)
            if conflicts:
                previous.update(conflicting_receipts=True, status="conflicting_receipts",
                                response_model=None, input_tokens=None, output_tokens=None,
                                cached_input_tokens=None, uncached_input_tokens=None)
    modern = bool(attempts)
    samples = list(attempts.values()) if modern else [e for e in events if e.get("event") in {
        "provider_response", "visual_critic_response", "visual_critic_contract_rejected"}]
    native = [e for e in events if e.get("event") == "token_usage"
              and e.get("scope") == "turn_delta_from_thread_total"]
    terminal = next((e for e in reversed(events) if e.get("event") in {
        "run_audit_finished", "project_budget_finished", "turn_failed", "turn_interrupted"}), {})
    # Native samples already contain run deltas from resumed thread totals.
    # Never sum them (including duplicate notifications).
    if native:
        samples = [native[-1]]
    def total(key):
        if not modern and not native:
            # Unkeyed historical response events cannot prove deduplication.
            return None
        if modern and any(s.get("status") != "returned" for s in samples):
            return None
        values = [count(s.get(key)) for s in samples]
        return sum(values) if values and all(v is not None for v in values) else None
    inp, cache = total("input_tokens"), total("cached_input_tokens")
    if cache is not None and (inp is None or cache > inp):
        cache = None
    identity = [e for e in events if e.get("event") == "thread_model_identity"]
    actual = [{"runtime": e.get("engine"), "provider": e.get("reported_provider"),
               "model": e.get("reported_model"), "source": e.get("source")} for e in identity]
    actual.extend({"runtime": start.get("selected_runtime"), "provider": None,
                   "model": e.get("response_model"), "source": "provider_response.model"}
                  for e in samples if "response_model" in e)
    rows = (ledger or {}).get("requests", [])
    groups = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"] in attempts:
            groups.setdefault(row["id"], []).append(row)
    missing_ids = sorted(set(attempts) - set(groups))
    linked = [group[0] for group in groups.values() if len(group) == 1]
    # Liability is a conservative reservation/upper bound, never a provider bill.
    ledger_fields = ("id", "status", "liability_usd", "input_tokens", "output_tokens")
    ledger_view = [{k: row[k] for k in ledger_fields if k in row}
                   for row in linked]
    ledger_anomalies = []
    for attempt_id, group in groups.items():
        if len(group) > 1:
            conflicts = [k for k in ledger_fields if any(row.get(k) != group[0].get(k) for row in group[1:])]
            ledger_anomalies.append({"attempt_id": attempt_id, "kind": "duplicate_ledger_id",
                "row_count": len(group), "conflict_fields": conflicts})
            ledger_view.append({"id": attempt_id, "status": "ambiguous_duplicate",
                                "liability_usd": None, "row_count": len(group)})
    coverage_complete = bool(modern and not missing_ids and not ledger_anomalies)
    def liability(status):
        if not coverage_complete:
            return None
        subset = [r for r in linked if r.get("status") in status]
        if not subset:
            return None
        try:
            values = [Decimal(r["liability_usd"]) for r in subset]
            return str(sum(values, Decimal(0))) if all(v.is_finite() and v >= 0 for v in values) else None
        except (KeyError, InvalidOperation, TypeError, ValueError):
            return None
    unknown = sum(e.get("status") != "returned" or count(e.get("input_tokens")) is None
                  or count(e.get("output_tokens")) is None for e in attempts.values()) if modern else None
    delivery = [e for e in events if e.get("event") == "delivery_acceptance"]
    native_receipts = []
    for e in events:
        output = e.get("output")
        if e.get("event") == "tool_receipt" and isinstance(output, dict) and isinstance(output.get("geometry"), dict):
            native_receipts.append({"tool": e.get("tool"), "call_id": e.get("call_id"),
                "revision": output.get("revision"), "model_sha256": output.get("sha256"),
                "geometry_objects": len(output["geometry"]), "native_reopen": output.get("native_reopen"),
                "quality_status": output.get("quality_status", "unverified"),
                "source": "existing host tool_receipt"})
    return {"schema_version": 1, "provenance": start or {"code_sha": None, "reason": "legacy trace has no run stamp"},
        "actual_identity": actual, "status": terminal.get("status", "unknown_or_unfinished"),
        "counts": {"host_dispatch_attempts": len(attempts) if modern else None,
                   "model_response_events": sum(e.get("event") in {"provider_response", "visual_critic_response"} for e in events),
                   "http_requests": None, "internal_retries": None, "unresolved_attempts": unknown},
        "attempt_anomalies": [{"attempt_id": key, "kind": "conflicting_dispatch_receipts",
                               "conflict_fields": sorted(value)}
                              for key, value in attempt_anomalies.items() if value],
        "usage": {"input_tokens": inp, "cached_input_tokens": cache,
                  "uncached_input_tokens": inp - cache if inp is not None and cache is not None else None,
                  "output_tokens": total("output_tokens"),
                  "source": "latest turn_delta telemetry" if native else "provider dispatch receipts" if modern else "legacy response events",
                  "complete": inp is not None and total("output_tokens") is not None
                      and (not native or terminal.get("status") == "completed"),
                  "cache_is_subset_of_input": True, "reasoning_is_subset_of_output": True},
        "cost": {"billed_usd": None, "billing_status": "unknown_no_invoice",
                 "ledger_linked_attempts": len(groups), "ledger_rows": ledger_view,
                 "ledger_missing_attempt_ids": missing_ids, "ledger_anomalies": ledger_anomalies,
                 "ledger_coverage_complete": coverage_complete,
                 "settled_upper_bound_usd": liability({"settled_upper_bound"}),
                 "unresolved_reserved_usd": liability({"reserved", "unresolved"}),
                 "liability_is_not_invoice": True},
        "delivery": delivery[-1] if delivery else {"geometry": "NOT_VERIFIED", "keep": "NOT_VERIFIED",
            "save_reopen": "NOT_VERIFIED", "editable": "NOT_VERIFIED"},
        "native_delivery_receipts": native_receipts,
        "limitations": ["Host dispatches/model events do not prove HTTP request or retry counts.",
            "Missing usage and bills are null; no inferred token or monetary savings.",
            "Interrupted/timeout requests may be billable even with partial known usage."]}


def read_audit(trace: Path, ledger: Path | None = None):
    events = [json.loads(line) for line in trace.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    # Read only the explicitly supplied ledger; never discover credentials/accounts.
    data = json.loads(ledger.read_text(encoding="utf-8-sig")) if ledger else None
    return audit_run(events, data)
