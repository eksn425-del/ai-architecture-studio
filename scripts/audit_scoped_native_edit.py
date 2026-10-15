"""Fail-closed, read-only scope audit for two verified native SketchUp captures.

Proof is LIMITED to protected direct groups, outside-root groups, root
transform and presentation. It is NOT a source-image, save/reopen, root-owned
loose-geometry, or product-quality verdict. Existing native delivery audit
and host KEEP/transaction remain mandatory. Never writes a SketchUp model.

python -m scripts.audit_scoped_native_edit BEFORE.json AFTER.json \
  --expected-before-document-sha b3fb8fbde6ae874a78570201b78dbd635072b9204ca9881c8972d189bfd14e10 \
  --allowed-direct-group TENSION_BRACING --json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")
COLLECTOR = "KStudioNativeDeepFingerprint/1"


def _digest(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _index(nodes: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(nodes, list):
        raise ValueError(f"{label}: missing native node list")
    found: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("name"), str) or not node["name"]:
            raise ValueError(f"{label}: unnamed native node")
        name = node["name"]
        if name in found:
            raise ValueError(f"{label}: ambiguous duplicate group {name}")
        if not _digest(node.get("geometry_material_sha256")) or not isinstance(node.get("counts"), dict):
            raise ValueError(f"{label}: missing deep SHA or counts for {name}")
        found[name] = node
    return found


def _capture(payload: Any, label: str) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(payload, dict) or payload.get("collector") != COLLECTOR or payload.get("schema_version") != 2:
        raise ValueError(f"{label}: requires actual native deep collector schema v2")
    for key in ("root_geometry_material_sha256", "document_geometry_material_sha256", "presentation_sha256"):
        if not _digest(payload.get(key)):
            raise ValueError(f"{label}: missing complete {key}")
    if not isinstance(payload.get("root_pid"), int) or not payload.get("root_name"):
        raise ValueError(f"{label}: missing root identity")
    direct = _index(payload.get("groups"), label + ".groups")
    document = _index(payload.get("document_groups"), label + ".document_groups")
    if payload["root_name"] not in document or document[payload["root_name"]].get("pid") != payload["root_pid"]:
        raise ValueError(f"{label}: root not verified among whole document groups")
    if document[payload["root_name"]]["geometry_material_sha256"] != payload["root_geometry_material_sha256"]:
        raise ValueError(f"{label}: root/document captures conflict")
    return direct, document


def audit_scoped_edit(before: dict[str, Any], after: dict[str, Any], *,
                      allowed_direct_group: str = "TENSION_BRACING",
                      expected_before_document_sha: str | None = None) -> dict[str, Any]:
    """PASS confirms only the explicitly limited direct-group scope."""
    report: dict[str, Any] = {
        "schema_version": 1, "status": "BLOCKED", "direct_scope_proven": False,
        "visual_source_fidelity": "NOT_ASSESSED", "native_delivery": "NOT_ASSESSED",
        "strict_blank_replay": "NOT_ASSESSED", "allowed_direct_group": allowed_direct_group,
        "failures": [],
    }
    try:
        old, old_doc = _capture(before, "before")
        new, new_doc = _capture(after, "after")
        if not isinstance(allowed_direct_group, str) or not allowed_direct_group or "/" in allowed_direct_group:
            raise ValueError("Scope requires one exact DIRECT group name, not an ancestor/path/wildcard")
        if expected_before_document_sha is not None and not _digest(expected_before_document_sha):
            raise ValueError("Malformed expected whole-document baseline SHA")
        if before["root_pid"] != after["root_pid"] or before["root_name"] != after["root_name"]:
            raise ValueError("Root PID/name changed; may be another native project")
        if expected_before_document_sha is not None and before["document_geometry_material_sha256"] != expected_before_document_sha:
            raise ValueError("Before capture does not match approved r4 whole-document baseline")
        if allowed_direct_group not in old or allowed_direct_group not in new:
            raise ValueError("Target not unambiguously named DIRECT root child; diagnose hierarchy before writing")
    except (ValueError, TypeError, KeyError) as exc:
        report["failures"].append(str(exc))
        return report

    failures: list[str] = []
    if old.keys() != new.keys():
        failures.append(f"Direct groups added/deleted: before_only={sorted(old.keys()-new.keys())}, after_only={sorted(new.keys()-old.keys())}")
    if old_doc.keys() != new_doc.keys():
        failures.append("Document top-level groups added/deleted")
    protected = sorted((old.keys() & new.keys()) - {allowed_direct_group})
    changed_protected: list[str] = []
    for name in protected:
        a, b = old[name], new[name]
        if (a["geometry_material_sha256"] != b["geometry_material_sha256"] or
                a["counts"] != b["counts"] or a.get("pid") != b.get("pid")):
            changed_protected.append(name)
    if changed_protected:
        failures.append(f"Protected groups changed: {changed_protected}")
    root = before["root_name"]
    for name in sorted((old_doc.keys() & new_doc.keys()) - {root}):
        a, b = old_doc[name], new_doc[name]
        if (a["geometry_material_sha256"] != b["geometry_material_sha256"] or
                a["counts"] != b["counts"] or a.get("pid") != b.get("pid")):
            failures.append(f"Top-level external group changed: {name}")
    old_root, new_root = old_doc[root], new_doc[root]
    for field in ("pid", "local_transform", "world_transform", "hidden", "tag"):
        if field not in old_root or field not in new_root or old_root[field] != new_root[field]:
            failures.append(f"Root {field} changed or unavailable")
    if before["presentation_sha256"] != after["presentation_sha256"]:
        failures.append("Presentation/tags/page/section state changed")
    if old[allowed_direct_group].get("pid") != new[allowed_direct_group].get("pid"):
        failures.append("Allowed group PID changed; possible replacement/regroup")
    if old[allowed_direct_group]["geometry_material_sha256"] == new[allowed_direct_group]["geometry_material_sha256"]:
        failures.append("Allowed group deep geometry/material SHA unchanged; no verified local edit")
    if before["root_geometry_material_sha256"] == after["root_geometry_material_sha256"]:
        failures.append("Whole root deep SHA unchanged")
    if before["document_geometry_material_sha256"] == after["document_geometry_material_sha256"]:
        failures.append("Whole-document deep SHA unchanged")
    report.update({
        "status": "FAIL" if failures else "PASS", "direct_scope_proven": not failures,
        "failures": failures, "protected_direct_groups_checked": len(protected),
        "external_document_groups_checked": len((old_doc.keys() & new_doc.keys()) - {root}),
        "before_document_sha256": before["document_geometry_material_sha256"],
        "after_document_sha256": after["document_geometry_material_sha256"],
        "limitations": [
            "Scope-only. Independent source-matched Critic and real native 3-stage save/download/reopen separately required.",
            "Direct child hashes cannot isolate loose root-owned geometry; separately inspect root-owned entities plus host KEEP/scope transaction.",
            "PASS is not a visual-quality, whole-product or strict-replay verdict.",
        ],
    })
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--allowed-direct-group", default="TENSION_BRACING")
    p.add_argument("--expected-before-document-sha")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    result = audit_scoped_edit(json.loads(args.before.read_text(encoding="utf-8")),
                               json.loads(args.after.read_text(encoding="utf-8")),
                               allowed_direct_group=args.allowed_direct_group,
                               expected_before_document_sha=args.expected_before_document_sha)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"], "; ".join(result["failures"]))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
