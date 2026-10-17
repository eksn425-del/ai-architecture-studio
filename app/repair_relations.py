"""Bounded advisory repair plans, measured against trusted native scene receipts.

This module neither writes geometry nor certifies appearance. A proposed issue
may be NEEDS_FIX before a repair; an independent Critic PASS is never required.
Callers must supply scenes from BlenderBackend, never model-authored receipts.
Keep the returned plan host-owned and pass it to evaluate_relation_repairs after
an ordinary guarded backend write. Review proposals are explicitly untrusted.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any

from .blender_connections import audit_connections

SCHEMA_VERSION = 1
MAX_REPAIRS = 8
MAX_CONNECTIONS = 64
MAX_ATTEMPTS = 12


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _text(value: Any, name: str, limit: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{name} must be a nonempty string of at most {limit} characters")
    return value.strip()


def _vector(value: Any, name: str, *, positive: bool = False) -> list:
    if (not isinstance(value, list) or len(value) != 3
            or any(type(n) not in (int, float) or not math.isfinite(n)
                   or (positive and n <= 0) for n in value)):
        raise ValueError(f"Invalid native {name}")
    return value


def _native_objects(scene: dict) -> dict:
    """Convert native readback, not proposed dimensions, to audit input.

    Backend meshes always have a dimensions field in their native snapshot.
    Preserve their mesh classification from the source spec so AABB contact
    cannot accidentally become an exact mesh-surface claim.
    """
    if (not isinstance(scene, dict) or type(scene.get("revision")) is not int
            or scene["revision"] < 1 or scene.get("native_reopen") != "PASS"
            or not isinstance(scene.get("objects"), dict)
            or not isinstance(scene.get("geometry"), dict)
            or set(scene["objects"]) != set(scene["geometry"])
            or not 1 <= len(scene["objects"]) <= 2048):
        raise ValueError("A trusted saved/reopened native scene receipt is required")
    measured = {}
    for name, spec in scene["objects"].items():
        native = scene["geometry"][name]
        if not isinstance(spec, dict) or not isinstance(native, dict):
            raise ValueError("Invalid native object receipt")
        item = {"location": _vector(native.get("location"), "location")}
        if "dimensions" in spec:
            item["dimensions"] = _vector(native.get("dimensions"), "dimensions", positive=True)
        else:
            vertices = native.get("vertices")
            if not isinstance(vertices, list) or not 3 <= len(vertices) <= 256:
                raise ValueError("Invalid native mesh vertices")
            item["vertices"] = [_vector(v, "mesh vertex") for v in vertices]
        measured[name] = item
    return measured


def _priorities(review: dict) -> dict[int, dict]:
    if not isinstance(review, dict) or not isinstance(review.get("issues"), list):
        raise ValueError("A review proposal with an issues list is required")
    if not 1 <= len(review["issues"]) <= 64:
        raise ValueError("Expected 1 to 64 proposed review issues")
    result = {}
    for issue in review["issues"]:
        if not isinstance(issue, dict):
            raise ValueError("Invalid proposed review issue")
        priority = issue.get("priority")
        if type(priority) is not int or not 1 <= priority <= 1000 or priority in result:
            raise ValueError("Issue priorities must be unique integers in 1..1000")
        result[priority] = {
            "priority": priority,
            "problem": _text(issue.get("problem"), "Issue problem"),
            "action": str(issue.get("action") or "")[:1000],
        }
    return result


def _subset(scene: dict, ids: list[str], field: str) -> dict:
    return {name: scene[field][name] for name in ids if name in scene[field]}


def _measure(measured: dict, connections: list[dict]) -> dict:
    rows = audit_connections(measured, connections)["connections"]
    checks = []
    for connection, row in zip(connections, rows):
        if row["mesh_surface_verification_required"]:
            status = "unverified_mesh_surface"
        elif row["bounds_status"] == "contact":
            status = "satisfied"
        else:
            status = "needs_fix"
        checks.append({**row, "tolerance_m": connection["tolerance"],
                       "expected_relation": "oriented_contact", "check_status": status})
    return {"status": "satisfied" if all(c["check_status"] == "satisfied" for c in checks)
            else "unverified" if any(c["check_status"] == "unverified_mesh_surface" for c in checks)
            else "needs_fix", "checks": checks}


def _summarize(plan: dict) -> None:
    resolved = [r["priority"] for r in plan["repairs"] if r["current"]["status"] == "satisfied"]
    unresolved = sorted(set(plan["review_priorities"]) - set(resolved))
    plan["resolved_relation_priorities"] = sorted(resolved)
    plan["unresolved_priorities"] = unresolved
    plan["unmapped_priorities"] = sorted(set(plan["review_priorities"]) -
                                          {r["priority"] for r in plan["repairs"]})
    plan["remaining_attempts"] = max(0, plan["max_attempts"] - plan["attempts"])
    plan["declared_relations_satisfied"] = len(resolved) == len(plan["repairs"])
    plan["visual_quality_status"] = "unverified"
    plan["source_fidelity_status"] = "unverified"
    plan["independent_critic_pass"] = False
    plan["automatic_geometry_changes"] = False
    plan["note"] = ("Declared relations use native metre measurements; exact only for axis-aligned "
                    "boxes. Resolved relation priorities do not resolve independent visual review. "
                    "Unmapped priorities and mesh surfaces remain unverified. No geometry was changed.")


def plan_relation_repairs(review: dict, scene: dict, repairs: list[dict], *,
                          max_attempts: int = 2) -> dict:
    """Map proposed priorities to exact targets and measurable oriented contacts.

    repairs: [{priority, component_ids, planned_edit,
               connections: [{a, b, axis, tolerance}]}].
    All targets must already exist. At least one endpoint of each connection
    must be in that repair's target set. All other objects are protected KEEP.
    The caller, not this helper, owns approval and guarded geometry mutation.
    """
    measured = _native_objects(scene)
    priorities = _priorities(review)
    if type(max_attempts) is not int or not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise ValueError("max_attempts must be an integer in 1..12")
    if not isinstance(repairs, list) or not 1 <= len(repairs) <= MAX_REPAIRS:
        raise ValueError("Expected 1 to 8 scoped relation repairs")
    rows, selected, targets = [], set(), set()
    total_connections = 0
    for repair in repairs:
        if not isinstance(repair, dict) or set(repair) != {
                "priority", "component_ids", "planned_edit", "connections"}:
            raise ValueError("Invalid relation repair fields")
        priority = repair["priority"]
        if type(priority) is not int or priority not in priorities or priority in selected:
            raise ValueError("Each repair must map one unique existing issue priority")
        selected.add(priority)
        ids = repair["component_ids"]
        if (not isinstance(ids, list) or not 1 <= len(ids) <= 256
                or any(not isinstance(i, str) or i not in measured for i in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError("Repair component_ids must be unique exact existing IDs")
        planned_edit = _text(repair["planned_edit"], "Planned edit")
        connections = repair["connections"]
        if not isinstance(connections, list) or not connections:
            raise ValueError("Each repair requires declared connections")
        total_connections += len(connections)
        if total_connections > MAX_CONNECTIONS:
            raise ValueError("At most 64 total repair connections")
        # Existing strict audit validation is reused, including finite tolerances.
        before = _measure(measured, connections)
        if any(c["a"] not in ids and c["b"] not in ids for c in connections):
            raise ValueError("A declared connection must involve a repair component")
        targets.update(ids)
        rows.append({"priority": priority, "problem": priorities[priority]["problem"],
                     "component_ids": list(ids), "planned_edit": planned_edit,
                     "connections": deepcopy(connections), "before": before,
                     "current": deepcopy(before)})
    object_ids = sorted(measured)
    keep_ids = sorted(set(object_ids) - targets)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "review_provenance": "agent_proposed_not_independent_critic",
        "review_priorities": sorted(priorities),
        "proposed_review": list(priorities.values()),
        "review_needs_fix": review.get("needs_fix") is True,
        "start_revision": scene["revision"], "last_revision": scene["revision"],
        "baseline_object_ids": object_ids, "component_ids": sorted(targets),
        "keep_ids": keep_ids,
        "keep_native_sha256": _digest(_subset(scene, keep_ids, "geometry")),
        "keep_spec_sha256": _digest(_subset(scene, keep_ids, "objects")),
        "last_native_sha256": _digest(scene["geometry"]),
        "last_spec_sha256": _digest(scene["objects"]),
        "max_attempts": max_attempts, "attempts": 0, "history": [],
        "repairs": sorted(rows, key=lambda row: row["priority"]),
        "keep_verified": True, "native_reopen": scene["native_reopen"],
        "status": "ready_to_repair", "block_reason": "",
    }
    _summarize(plan)
    if plan["declared_relations_satisfied"]:
        plan["status"] = "relations_satisfied"
    return plan


def evaluate_relation_repairs(plan: dict, scene: dict) -> dict:
    """Check an ordinary native repair commit; never accept just tool success.

    Re-reading a revision does not consume an attempt. Scope/KEEP violations
    fail closed and cannot be cleared by subsequent calls; retain or roll back
    the candidate with the existing writer, then prepare a new scoped plan.
    A check consumes one attempt per observed newer revision; skipped revisions
    are rejected because their intermediate mutations were never checked.
    """
    if not isinstance(plan, dict) or plan.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Expected a host-owned relation repair plan")
    result = deepcopy(plan)
    if result.get("status") == "blocked":
        return result
    measured = _native_objects(scene)
    revision = scene["revision"]
    same_native = _digest(scene["geometry"]) == result["last_native_sha256"]
    same_spec = _digest(scene["objects"]) == result["last_spec_sha256"]
    if revision == result["last_revision"] and same_native and same_spec:
        return result
    reason = ""
    if revision != result["last_revision"] + 1:
        reason = "revision_not_next_checked_commit"
    elif result["attempts"] >= result["max_attempts"]:
        reason = "repair_attempt_budget_exhausted"
    elif sorted(measured) != result["baseline_object_ids"]:
        reason = "object_inventory_changed_outside_existing_target_contract"
    elif (_digest(_subset(scene, result["keep_ids"], "geometry")) != result["keep_native_sha256"]
          or _digest(_subset(scene, result["keep_ids"], "objects")) != result["keep_spec_sha256"]):
        reason = "protected_KEEP_changed"
    elif same_native:
        reason = "no_native_geometry_progress"
    result["keep_verified"] = (
        sorted(measured) == result["baseline_object_ids"]
        and _digest(_subset(scene, result["keep_ids"], "geometry")) == result["keep_native_sha256"]
        and _digest(_subset(scene, result["keep_ids"], "objects")) == result["keep_spec_sha256"])
    if reason:
        result["status"] = "blocked"
        result["block_reason"] = reason
        result["observed_revision"] = revision
        _summarize(result)
        return result
    result["attempts"] += 1
    result["last_revision"] = revision
    result["last_native_sha256"] = _digest(scene["geometry"])
    result["last_spec_sha256"] = _digest(scene["objects"])
    for repair in result["repairs"]:
        repair["current"] = _measure(measured, repair["connections"])
    _summarize(result)
    result["history"].append({
        "attempt": result["attempts"], "revision": revision,
        "keep_verified": result["keep_verified"], "native_reopen": scene["native_reopen"],
        "repairs": [{"priority": r["priority"], **deepcopy(r["current"])} for r in result["repairs"]],
    })
    result["native_reopen"] = scene["native_reopen"]
    if result["declared_relations_satisfied"]:
        result["status"] = "relations_satisfied"
    elif result["remaining_attempts"] == 0:
        result["status"] = "blocked"
        result["block_reason"] = "repair_attempt_budget_exhausted"
    else:
        result["status"] = "still_needs_fix"
    return result
