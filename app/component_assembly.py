"""Readback diagnostics, not structural certification or visual acceptance."""
from __future__ import annotations

from typing import Any


def native_component_diagnostics(snapshot: dict[str, Any]) -> dict[str, Any]:
    objects = snapshot.get("objects", [])
    groups = [x for x in objects if isinstance(x, dict)]
    issues = []
    names = [x.get("name") for x in groups]
    if not groups:
        issues.append("No native named assemblies read back")
    if any(not isinstance(n, str) or not n.strip() for n in names):
        issues.append("Unnamed native assembly")
    if len(names) != len(set(names)):
        issues.append("Duplicate sibling semantic paths")
    for g in groups:
        if not g.get("persistent_id"):
            issues.append("Missing native persistent ID: " + str(g.get("name")))
        size = (g.get("bounds_mm") or {}).get("size")
        if not isinstance(size, list) or len(size) != 3 or any(type(v) not in {int, float} or v < 0 for v in size):
            issues.append("Invalid dimension readback: " + str(g.get("name")))
    return {"schema_version": 1, "status": "FAIL" if issues else "PARTIAL",
        "named_native_group_checks": "FAIL" if issues else "PASS",
        "group_count": len(groups), "issues": issues,
        "components": [{"path": [g.get("name")], "persistent_id": g.get("persistent_id"),
                        "bounds_mm": g.get("bounds_mm"), "locked": g.get("locked")} for g in groups],
        "actual_geometry_and_material_equality": "Requires independent recursive fingerprint/replay evidence",
        "roof_wall_window_stair_joint_quality": "NOT_VERIFIED_BY_NAMES_OR_BOUNDS",
        "source_fidelity": "Requires source-matched visual review",
        "not_structural_or_regulatory_certification": True}
