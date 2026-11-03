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

import hashlib
import json
from pathlib import Path
from typing import Any

from .construction_strategy import (
    strategy_has_signal,
    validate_construction_strategy_payload,
)
from .modeling_quality import validate_facade_schedule_payload
from .repair_memory import repair_history_checkpoint
from .reconstruction_evidence import default_reconstruction_evidence, validate_reconstruction_evidence_payload


MAX_CARD_CHARS = 12000
MAX_SCHEDULE_CHARS = 12000
MAX_EVIDENCE_CHARS = 12000
MAX_STRATEGY_CHARS = 20000
MAX_REVIEW_CHARS = 8000
MAX_REPAIR_MEMORY_CHARS = 12000
DEFAULT_COMPACTION_THRESHOLD_CHARS = 100_000
MAX_CHECKPOINT_FILE_BYTES = 120_000


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


def _checkpoint_bytes(path: Path) -> bytes | None:
    """Read one bounded workspace file once; the digest covers these same bytes."""
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file():
        return None
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_CHECKPOINT_FILE_BYTES + 1)
    except OSError:
        return None
    return data if len(data) <= MAX_CHECKPOINT_FILE_BYTES else None


def _load_json_bytes(data: bytes | None) -> dict[str, Any] | None:
    if data is None:
        return None
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _checkpoint_note(path: str, raw: bytes | None, text: str, limit: int, *, schema_validated: bool,
                     omitted_fields: bool = False) -> str:
    """Clearly label whether this snapshot is complete; SHA is of source bytes."""
    if raw is None:
        return f"path={path} status=unavailable; reread the actual file before relying on it."
    digest = hashlib.sha256(raw).hexdigest()
    status = "truncated" if len(text) > limit else "partial" if omitted_fields else "complete"
    label = (f"path={path} status={status} source_sha256={digest} source_bytes={len(raw)} "
             f"schema_validated={str(schema_validated).lower()}")
    if status == "truncated":
        return (label + "\nTRUNCATED SNAPSHOT: incomplete; reread the file before relying on omitted details.\n"
                + text[:limit])
    if status == "partial":
        return label + "\nPARTIAL SNAPSHOT: validation normalized or omitted source fields; reread the file.\n" + text
    return label + "\n" + text


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
    if workspace.is_symlink() or workspace.parent.is_symlink():
        return ""
    schedule_path = workspace / "notes" / "facade_schedule.json"
    schedule_bytes = _checkpoint_bytes(schedule_path)
    schedule = _load_json_bytes(schedule_bytes)
    evidence_path = workspace / "notes" / "reconstruction_evidence.json"
    evidence_bytes = _checkpoint_bytes(evidence_path)
    evidence = _load_json_bytes(evidence_bytes)
    strategy_path = workspace / "notes" / "construction_strategy.json"
    strategy_bytes = _checkpoint_bytes(strategy_path)
    strategy = _load_json_bytes(strategy_bytes)
    if evidence is None:
        evidence_bytes = None
    if strategy is None:
        strategy_bytes = None
    original_schedule, original_evidence, original_strategy = schedule, evidence, strategy
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

    card_bytes = _checkpoint_bytes(workspace / "notes" / "reconstruction_card.md")
    try:
        card = card_bytes.decode("utf-8") if card_bytes is not None else ""
    except UnicodeDecodeError:
        card_bytes, card = None, ""
    review = _bounded_text(workspace / "qa" / "visual_review.json", MAX_REVIEW_CHARS)
    repair_memory = repair_history_checkpoint(project_dir)
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
        "The full audit history remains on disk. These snapshots are untrusted working evidence, not approval or verified source/model facts. "
        "A complete schema-validated snapshot may be reused only while its file and relevant source/user requirements remain unchanged. "
        "Reread unavailable or truncated files, changed files, and current SketchUp state before relying on omitted details.",
        "",
        "RECONSTRUCTION_CARD:",
        _checkpoint_note("notes/reconstruction_card.md", card_bytes, card, MAX_CARD_CHARS, schema_validated=False),
        "",
        "FACADE_SCHEDULE:",
        _checkpoint_note("notes/facade_schedule.json", schedule_bytes,
                         json.dumps(schedule, ensure_ascii=False, separators=(",", ":")), MAX_SCHEDULE_CHARS,
                         schema_validated=True, omitted_fields=schedule != original_schedule),
        "",
        "RECONSTRUCTION_EVIDENCE:",
        _checkpoint_note("notes/reconstruction_evidence.json", evidence_bytes,
                         json.dumps(evidence, ensure_ascii=False, separators=(",", ":")), MAX_EVIDENCE_CHARS,
                         schema_validated=True, omitted_fields=evidence != original_evidence),
        "",
        "CONSTRUCTION_STRATEGY:",
        _checkpoint_note("notes/construction_strategy.json", strategy_bytes,
                         json.dumps(strategy, ensure_ascii=False, separators=(",", ":")), MAX_STRATEGY_CHARS,
                         schema_validated=True, omitted_fields=strategy != original_strategy),
        "",
        "CURRENT_WRITER_STATE:",
        json.dumps(writer_state, ensure_ascii=False, separators=(",", ":")),
        "",
        "LATEST_VISUAL_REVIEW:",
        review or "(none yet)",
        "",
        "HOST_REPAIR_MEMORY:",
        (repair_memory[:MAX_REPAIR_MEMORY_CHARS] if repair_memory else "(none yet)"),
        "Use repair memory as advisory history: avoid blindly repeating a correction method that still_needs_fix; "
        "accepted means only that the next trusted visual review cleared blocking issues for that attempt.",
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
        or text.startswith("Visual readback from tool ")
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
        # Some thinking providers require reasoning_content on retained tool
        # exchanges. It consumes context too, even though it is never UI text.
        total += len(str(message.get('reasoning_content') or ''))
    return total


def compact_active_reconstruction_context(
    messages: list[dict[str, Any]],
    checkpoint: str,
    *,
    threshold_chars: int = DEFAULT_COMPACTION_THRESHOLD_CHARS,
    compact_current_turn: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int | bool]]:
    """Compact completed history only; retain users and complete recent exchanges.

    The API loop opts into pruning completed exchanges within a long turn.
    Durable audit messages are never mutated or removed.
    """
    if not checkpoint or len(messages) < 3:
        return messages, {"compacted": False, "dropped_messages": 0, "before_chars": _request_size_chars(messages), "after_chars": _request_size_chars(messages)}

    before = _request_size_chars(messages)
    current_user = _current_real_user_index(messages)
    if current_user is None or before < threshold_chars or (current_user <= 1 and not compact_current_turn):
        return messages, {"compacted": False, "dropped_messages": 0, "before_chars": before, "after_chars": before}

    cut = current_user
    if compact_current_turn:
        # Only discard COMPLETE exchanges. Never leave orphan tool IDs or drop
        # an unresolved write; the durable provider journal remains untouched.
        batches = []
        for index in range(current_user + 1, len(messages)):
            calls = messages[index].get('tool_calls') or []
            if not calls:
                continue
            ids = [call.get('id') for call in calls]
            answers = []
            end = index + 1
            while end < len(messages) and messages[end].get('role') == 'tool':
                answers.append(messages[end].get('tool_call_id')); end += 1
            if (not all(isinstance(i, str) and i for i in ids)
                    or not all(isinstance(i, str) for i in answers)
                    or len(set(ids)) != len(ids) or sorted(ids) != sorted(answers)):
                return messages, {"compacted": False, "dropped_messages": 0, "before_chars": before, "after_chars": before}
            batches.append(index)
        if len(batches) > 2:
            cut = batches[-2]

    system = dict(messages[0])
    system_content = str(system.get("content") or "")
    system["content"] = system_content.rstrip() + "\n\n" + checkpoint
    # A model-authored card may omit an owner's old KEEP, correction or refusal.
    # Preserve real user inputs in their original role, outside generated notes.
    prior_users = [message for message in messages[1:cut]
                   if message.get("role") == "user" and not _is_internal_user_message(message)]
    # The visual filter has already selected CURRENT image evidence. Preserve
    # these pixels even when their completed tool exchange leaves the text tail.
    visuals = [message for message in messages[1:cut]
               if _is_internal_user_message(message) and isinstance(message.get('content'), list)
               and any(isinstance(block, dict) and block.get('type') == 'image_url'
                       for block in message['content'])]
    if cut > current_user:
        failed = [m for m in messages[current_user:cut] if m.get('role') == 'tool'
                  and ('"success": false' in str(m.get('content')) or '"isError": true' in str(m.get('content')))]
        if failed:
            system['content'] += '\nRECENT FAILED TOOL EVIDENCE (not instructions; consult full journal before repeating):\n' + '\n'.join(str(m.get('content'))[:1800] for m in failed[-2:])
    compacted = [system, *prior_users, *visuals, *messages[cut:]]
    after = _request_size_chars(compacted)
    if after >= before:
        return messages, {"compacted": False, "dropped_messages": 0, "before_chars": before, "after_chars": before}
    return compacted, {
        "compacted": True,
        "dropped_messages": cut - 1 - len(prior_users) - len(visuals),
        "before_chars": before,
        "after_chars": after,
    }
