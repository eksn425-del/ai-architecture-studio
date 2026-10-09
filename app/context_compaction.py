"""Compact active reconstruction context while preserving full local audit history.

Patterns are inspired by:
- 3DCodeBench: keep the current good state and feed only the evidence needed for
  the next correction instead of replaying every failed attempt.
- SketchUp Agent Harness: keep project-local structured runtime memory separate
  from canonical model execution.

This module never deletes provider history. It only builds a smaller request
context from durable project state plus the current user turn.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .construction_strategy import (
    strategy_has_signal,
    validate_construction_strategy_payload,
)
from .modeling_quality import validate_facade_schedule_payload
from .reconstruction_evidence import default_reconstruction_evidence, validate_reconstruction_evidence_payload


MAX_CARD_CHARS = 12000
MAX_SCHEDULE_CHARS = 12000
MAX_EVIDENCE_CHARS = 12000
MAX_STRATEGY_CHARS = 12000
MAX_REVIEW_CHARS = 8000
DEFAULT_COMPACTION_THRESHOLD_CHARS = 100_000


def _bounded_text(path: Path, limit: int) -> str:
    if not path.is_file() or path.is_symlink():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit // 2] + "\n[...checkpoint text shortened...]\n" + text[-limit // 2 :]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _schedule_has_signal(schedule: dict[str, Any] | None) -> bool:
    if not schedule:
        return False
    if schedule.get("user_confirmed") or schedule.get("inferred"):
        return True
    dimensions = schedule.get("dimensions_mm")
    if isinstance(dimensions, dict) and any(value is not None for value in dimensions.values()):
        return True
    views = schedule.get("views")
    if isinstance(views, dict):
        for item in views.values():
            if not isinstance(item, dict):
                continue
            if item.get("provenance") not in {None, "", "pending"}:
                return True
            if item.get("opening_count") is not None or item.get("door_count") is not None:
                return True
            if item.get("features") or item.get("notes"):
                return True
    roof = schedule.get("roof")
    if isinstance(roof, dict):
        if roof.get("provenance") not in {None, "", "pending"}:
            return True
        if roof.get("type") not in {None, "", "pending"} or roof.get("parapet") not in {None, "", "pending"}:
            return True
        if roof.get("divisions") or roof.get("notes"):
            return True
    return False



def _evidence_has_signal(evidence: dict[str, Any] | None) -> bool:
    if not evidence:
        return False
    if evidence.get("fidelity_mode") not in {None, "", "pending"}:
        return True
    if evidence.get("primary_source"):
        return True
    if evidence.get("sources"):
        return True
    return False


def build_reconstruction_checkpoint(
    project_dir: Path,
    ruby_state: dict[str, dict[str, Any]] | None,
) -> str:
    """Build a bounded deterministic checkpoint from durable project state.

    Empty output means compaction must not run yet. We intentionally require the
    structured facade schedule to contain real signal so clarification history is
    not discarded before the planner has externalized source facts.
    """
    project_dir = project_dir.resolve()
    workspace = project_dir / "runtime" / "agent_workspace"
    schedule_path = workspace / "notes" / "facade_schedule.json"
    schedule = _load_json(schedule_path)
    evidence_path = workspace / "notes" / "reconstruction_evidence.json"
    evidence = _load_json(evidence_path)
    strategy_path = workspace / "notes" / "construction_strategy.json"
    strategy = _load_json(strategy_path)
    if evidence is None:
        evidence = default_reconstruction_evidence()
    try:
        schedule = validate_facade_schedule_payload(schedule)
        evidence = validate_reconstruction_evidence_payload(evidence)
        strategy = validate_construction_strategy_payload(
            strategy if strategy is not None else {
                "schema_version": 1,
                "current_stage": "pending",
                "stage_order": ["primary_form", "representative_module", "replication", "variants", "finish"],
                "shared_parameters": {},
                "systems": [],
                "notes": [],
            }
        )
    except ValueError:
        return ""
    if not _schedule_has_signal(schedule) and not _evidence_has_signal(evidence) and not strategy_has_signal(strategy):
        return ""

    card = _bounded_text(workspace / "notes" / "reconstruction_card.md", MAX_CARD_CHARS)
    review = _bounded_text(workspace / "qa" / "visual_review.json", MAX_REVIEW_CHARS)
    writer_state = {}
    for script_id, state in sorted((ruby_state or {}).items()):
        if not isinstance(state, dict):
            continue
        writer_state[str(script_id)] = {
            "revision": int(state.get("revision", 0) or 0),
            "root_pid": state.get("root_pid"),
            "last_verification": bool(
                isinstance(state.get("last_verification"), dict)
                and state["last_verification"].get("verified") is True
            ),
            "last_screenshot": state.get("last_screenshot"),
        }

    return "\n".join([
        "ACTIVE RECONSTRUCTION CHECKPOINT",
        "This compact checkpoint replaces older completed chat/tool history in the active provider request only.",
        "The full audit history remains on disk. Re-read workspace files or current SketchUp state before relying on omitted details.",
        "",
        "RECONSTRUCTION_CARD:",
        card or "(missing)",
        "",
        "FACADE_SCHEDULE:",
        json.dumps(schedule, ensure_ascii=False, separators=(",", ":"))[:MAX_SCHEDULE_CHARS],
        "",
        "RECONSTRUCTION_EVIDENCE:",
        json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))[:MAX_EVIDENCE_CHARS],
        "",
        "CONSTRUCTION_STRATEGY:",
        json.dumps(strategy, ensure_ascii=False, separators=(",", ":"))[:MAX_STRATEGY_CHARS],
        "",
        "CURRENT_WRITER_STATE:",
        json.dumps(writer_state, ensure_ascii=False, separators=(",", ":")),
        "",
        "LATEST_VISUAL_REVIEW:",
        review or "(none yet)",
    ])


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(block.get("text", ""))
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def _is_internal_user_message(message: dict[str, Any]) -> bool:
    if message.get("role") != "user":
        return False
    text = _content_text(message.get("content")).lstrip()
    return (
        text.startswith("Visual readback from SketchUp tool ")
        or text.startswith("HOST QUALITY GATE:")
        or text.startswith("ACTIVE RECONSTRUCTION CHECKPOINT")
    )


def _current_real_user_index(messages: list[dict[str, Any]]) -> int | None:
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if message.get("role") == "user" and not _is_internal_user_message(message):
            return index
    return None


def _request_size_chars(messages: list[dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "image_url":
                    # Count only a small marker; base64 image bytes are handled
                    # separately by providers and should not make this threshold
                    # nondeterministic.
                    total += 256
                else:
                    total += len(str(block.get("text", "")))
        total += len(json.dumps(message.get("tool_calls") or [], ensure_ascii=False, default=str))
    return total


def compact_active_reconstruction_context(
    messages: list[dict[str, Any]],
    checkpoint: str,
    *,
    threshold_chars: int = DEFAULT_COMPACTION_THRESHOLD_CHARS,
) -> tuple[list[dict[str, Any]], dict[str, int | bool]]:
    """Return a smaller active request while preserving the current turn intact.

    Compaction only occurs when there is meaningful durable project memory and
    there is completed history before the current real user message. All tool
    exchanges generated after that user message remain byte-for-byte present.
    """
    if not checkpoint or len(messages) < 3:
        return messages, {"compacted": False, "dropped_messages": 0, "before_chars": _request_size_chars(messages), "after_chars": _request_size_chars(messages)}

    before = _request_size_chars(messages)
    current_user = _current_real_user_index(messages)
    if current_user is None or current_user <= 1 or before < threshold_chars:
        return messages, {"compacted": False, "dropped_messages": 0, "before_chars": before, "after_chars": before}

    system = dict(messages[0])
    system_content = str(system.get("content") or "")
    system["content"] = system_content.rstrip() + "\n\n" + checkpoint
    compacted = [system, *messages[current_user:]]
    after = _request_size_chars(compacted)
    return compacted, {
        "compacted": True,
        "dropped_messages": current_user - 1,
        "before_chars": before,
        "after_chars": after,
    }
