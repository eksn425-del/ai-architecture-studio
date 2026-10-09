"""Host-owned repair memory for image-reconstruction iterations.

This is inspired by two upstream patterns:
- 3DCodeBench keeps critique history and last-known-good attempts instead of
  replaying every failed visual-fix trace.
- SketchUp Agent Harness keeps project-local runtime memory separate from
  canonical geometry truth.

K Studio stores only compact, host-generated repair attempts here. The file is
advisory memory for the next correction after active-context compaction; it is
not geometry truth and the model cannot write it directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MAX_REPAIR_ENTRIES = 12
MAX_CHECKPOINT_ENTRIES = 4


def _history_path(project_dir: Path) -> Path:
    return (
        project_dir.resolve()
        / "runtime"
        / "agent_workspace"
        / "qa"
        / "repair_history.json"
    )


def _bounded_text(value: Any, limit: int = 800) -> str:
    text = str(value or "").strip()
    return text[:limit]


def _review_summary(review: Any) -> dict[str, Any]:
    if not isinstance(review, dict):
        return {}
    issues = []
    for item in review.get("issues") or []:
        if not isinstance(item, dict):
            continue
        issues.append({
            "priority": int(item.get("priority", len(issues) + 1) or len(issues) + 1),
            "view": _bounded_text(item.get("view"), 40),
            "problem": _bounded_text(item.get("problem"), 500),
            "action": _bounded_text(item.get("action"), 500),
        })
        if len(issues) >= 3:
            break
    keep = [
        _bounded_text(item, 300)
        for item in (review.get("keep") or [])
        if str(item or "").strip()
    ][:24]
    revisions = {}
    for key, value in (review.get("model_revisions") or {}).items():
        try:
            revisions[str(key)] = int(value)
        except (TypeError, ValueError):
            continue
    reviewer = review.get("reviewer")
    return {
        "needs_fix": bool(review.get("needs_fix")),
        "assessment": _bounded_text(review.get("assessment"), 1000),
        "issues": issues,
        "keep": keep,
        "model_revisions": revisions,
        "reviewer_mode": _bounded_text(
            reviewer.get("mode") if isinstance(reviewer, dict) else reviewer,
            80,
        ),
    }


def _writer_summary(writer: Any) -> dict[str, Any]:
    if not isinstance(writer, dict):
        return {}
    guard = writer.get("precommit_keep_guard")
    if not isinstance(guard, dict):
        guard = {}
    preservation = writer.get("preservation_verification")
    if not isinstance(preservation, dict):
        preservation = {}
    return {
        "script_id": _bounded_text(writer.get("script_id"), 80),
        "revision": int(writer.get("revision", 0) or 0),
        "relative_path": _bounded_text(writer.get("relative_path"), 200),
        "update_mode": _bounded_text(writer.get("update_mode"), 20),
        "source_sha256": _bounded_text(writer.get("source_sha256"), 128),
        "precommit_keep_guard": {
            "armed": bool(guard.get("armed")),
            "passed": guard.get("passed"),
            "paths": [_bounded_text(item, 400) for item in (guard.get("paths") or [])][:24],
        },
        "postcommit_keep_verified": bool(preservation.get("verified")),
    }


def load_repair_history(project_dir: Path) -> dict[str, Any]:
    path = _history_path(project_dir)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 128 * 1024:
        return {"schema_version": SCHEMA_VERSION, "entries": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "entries": []}
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        return {"schema_version": SCHEMA_VERSION, "entries": []}
    entries = value.get("entries")
    if not isinstance(entries, list):
        entries = []
    return {"schema_version": SCHEMA_VERSION, "entries": entries[-MAX_REPAIR_ENTRIES:]}


def _save_repair_history(project_dir: Path, history: dict[str, Any]) -> None:
    path = _history_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.resolve().is_relative_to(project_dir.resolve()):
        raise ValueError("Repair history directory escaped the project.")
    entries = history.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Repair history entries must be a list.")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "entries": entries[-MAX_REPAIR_ENTRIES:],
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def record_repair_attempt(
    project_dir: Path,
    before_review: dict[str, Any],
    writer: dict[str, Any],
) -> dict[str, Any]:
    """Persist one committed correction waiting for the next visual review."""
    history = load_repair_history(project_dir)
    entries = history["entries"]
    sequence = 1
    for item in entries:
        if isinstance(item, dict):
            attempt_id = str(item.get("attempt_id") or "")
            if attempt_id.startswith("repair-"):
                try:
                    sequence = max(sequence, int(attempt_id.removeprefix("repair-")) + 1)
                except ValueError:
                    pass
    entry = {
        "attempt_id": f"repair-{sequence:03d}",
        "status": "awaiting_review",
        "before_review": _review_summary(before_review),
        "writer": _writer_summary(writer),
        "after_review": None,
        "outcome": "pending",
    }
    entries.append(entry)
    _save_repair_history(project_dir, history)
    return entry


def finalize_latest_repair_attempt(
    project_dir: Path,
    after_review: dict[str, Any],
) -> dict[str, Any] | None:
    """Attach the next trusted review to the newest pending repair attempt."""
    history = load_repair_history(project_dir)
    entries = history["entries"]
    for entry in reversed(entries):
        if isinstance(entry, dict) and entry.get("status") == "awaiting_review":
            after = _review_summary(after_review)
            entry["after_review"] = after
            entry["status"] = "reviewed"
            before = entry.get("before_review") or {}
            if before.get("needs_fix") and not after.get("needs_fix"):
                entry["outcome"] = "accepted"
            elif after.get("needs_fix"):
                entry["outcome"] = "still_needs_fix"
            else:
                entry["outcome"] = "reviewed"
            _save_repair_history(project_dir, history)
            return entry
    return None


def repair_history_checkpoint(project_dir: Path, *, limit: int = MAX_CHECKPOINT_ENTRIES) -> str:
    """Return compact trusted repair memory for active-context compaction."""
    history = load_repair_history(project_dir)
    entries = [item for item in history["entries"] if isinstance(item, dict)][-max(1, limit):]
    if not entries:
        return ""
    compact = []
    for item in entries:
        compact.append({
            "attempt_id": item.get("attempt_id"),
            "status": item.get("status"),
            "outcome": item.get("outcome"),
            "before_issues": (item.get("before_review") or {}).get("issues", []),
            "writer": item.get("writer", {}),
            "after_needs_fix": (item.get("after_review") or {}).get("needs_fix")
                if isinstance(item.get("after_review"), dict) else None,
            "after_issues": (item.get("after_review") or {}).get("issues", [])
                if isinstance(item.get("after_review"), dict) else [],
        })
    return json.dumps(
        {"schema_version": SCHEMA_VERSION, "entries": compact},
        ensure_ascii=False,
        separators=(",", ":"),
    )
