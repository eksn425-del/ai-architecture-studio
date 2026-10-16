"""Conservative host-side construction progress from REAL owned-root readback.

A planner's "pending" systems can advance to "built" only when all of their
explicit named owned paths were actually read back from the committed model.
Built is NOT visually verified. Nested paths require actual nested snapshots,
not guesses from a parent group's name or the Ruby source.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .construction_strategy import (
    CONSTRUCTION_STAGE_ORDER,
    load_construction_strategy,
    validate_construction_strategy_payload,
)


def collect_verified_strategy_paths(
    strategy: dict[str, Any],
    root_paths: list[list[str]],
    inspect_batch: Callable[[list[list[str]]], list[dict[str, Any]]],
) -> list[list[str]]:
    """Read planned nested targets rather than treating root-only omission as loss.

    An unread/missing nested target fails progress certification; it never implies
    that a previously built roof or floor was deleted. Geometry remains committed.
    """
    checked = [list(path) for path in root_paths]
    roots = {tuple(path) for path in root_paths}
    nested = list(dict.fromkeys(
        tuple(path)
        for system in strategy.get("systems", [])
        for path in system.get("target_paths", [])
        if len(path) > 1 and tuple(path[:1]) in roots
    ))
    if not nested:
        return checked
    if len(nested) > 256:
        raise ValueError("Planned nested path readback exceeds the 256-path native batch contract.")
    requested = [list(path) for path in nested]
    snapshots = inspect_batch(requested)
    if not isinstance(snapshots, list) or len(snapshots) != len(requested):
        raise ValueError("Incomplete planned nested-path native readback.")
    for path, snapshot in zip(requested, snapshots, strict=True):
        if (not isinstance(snapshot, dict) or snapshot.get("path") != path
                or type(snapshot.get("persistent_id")) is not int
                or snapshot["persistent_id"] <= 0
                or type(snapshot.get("objects_total")) is not int
                or snapshot["objects_total"] < 0):
            raise ValueError("Planned nested-path native identity does not match the requested target.")
        checked.append(path)
    return checked


def assess_strategy_progress(
    strategy: dict[str, Any],
    *,
    script_id: str,
    revision: int,
    root_pid: int,
    named_paths: list[list[str]],
    full_readback: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return validated status updates and explicit evidence. No unsupported PASS."""
    checked = {tuple(path) for path in named_paths if path}
    systems = []
    evidence = []
    for system in strategy.get("systems", []):
        item = dict(system)
        targets = item.get("target_paths") or []
        found = [path for path in targets if tuple(path) in checked]
        missing = [path for path in targets if tuple(path) not in checked]
        if not targets:
            result = "no_target_paths"
        elif not full_readback:
            result = "incomplete_readback"
        elif missing:
            result = "unresolved_paths"
            # A prior confirmed build that is now gone cannot stay "built".
            if item["status"] == "built":
                item["status"] = "needs_fix"
        else:
            result = "geometry_present_not_visually_verified"
            if item["status"] == "pending":
                item["status"] = "built"
        systems.append(item)
        evidence.append({
            "system_id": item["id"],
            "target_paths": targets,
            "present_paths": found,
            "missing_paths": missing,
            "result": result,
            "new_status": item["status"],
        })
    selected_stage = next(
        (stage for stage in CONSTRUCTION_STAGE_ORDER if any(
            x["stage"] == stage and x["status"] in {"pending", "needs_fix"} for x in systems
        )),
        "finish" if systems else "pending",
    )
    updated = validate_construction_strategy_payload({
        **strategy, "systems": systems, "current_stage": selected_stage,
    })
    report = {
        "schema_version": 1, "source": "committed_owned_root_named_path_readback",
        "script_id": script_id, "revision": revision, "root_pid": root_pid,
        "full_readback": full_readback,
        "current_stage": selected_stage,
        "systems": evidence,
        "visual_verification": "NOT_RUN",
    }
    return updated, report


def persist_verified_strategy_progress(
    project_dir: Path,
    *,
    script_id: str,
    revision: int,
    root_pid: int,
    named_paths: list[list[str]],
    full_readback: bool,
) -> dict[str, Any] | None:
    """Store report in the existing project workspace; never claim nested truth."""
    strategy = load_construction_strategy(project_dir)
    if strategy is None:
        return None
    updated, report = assess_strategy_progress(
        strategy, script_id=script_id, revision=revision, root_pid=root_pid,
        named_paths=named_paths, full_readback=full_readback,
    )
    path = project_dir.resolve() / "runtime" / "agent_workspace" / "notes" / "construction_strategy.json"
    status_path = path.with_name("construction_progress.json")
    if path.is_symlink() or status_path.is_symlink():
        raise ValueError("Construction strategy/progress path must not be a symlink.")
    if full_readback:
        tmp = path.with_suffix(".verified.tmp")
        tmp.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
    tmp_progress = status_path.with_suffix(".tmp")
    tmp_progress.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_progress.replace(status_path)
    return report
