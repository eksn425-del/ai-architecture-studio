"""Compare committed SketchUp model fingerprints, ignoring new model persistent IDs.

Does not claim geometric equivalence when only counts match. Hash mismatch is
a failure and needs child-level vertex/material investigation on the native host.
Usage: python scripts/compare_native_replay.py before.json replay.json [--json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _indexed(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("groups"), list):
        raise ValueError("Expected a model fingerprint object with groups list")
    index: dict[str, dict[str, Any]] = {}
    for item in payload["groups"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            raise ValueError("All fingerprint groups require a valid name")
        name = item["name"]
        if name in index:
            raise ValueError(f"Duplicate named SketchUp group: {name}")
        if not isinstance(item.get("counts"), dict) or not isinstance(item.get("geometry_material_sha256"), str):
            raise ValueError(f"Incomplete fingerprint for {name}")
        index[name] = item
    return index


def compare(before: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    old, new = _indexed(before), _indexed(replay)
    missing = sorted(old.keys() - new.keys())
    added = sorted(new.keys() - old.keys())
    changed = []
    for name in sorted(old.keys() & new.keys()):
        a, b = old[name], new[name]
        if a["counts"] != b["counts"] or a["geometry_material_sha256"] != b["geometry_material_sha256"]:
            changed.append({
                "name": name,
                "counts_equal": a["counts"] == b["counts"],
                "before_counts": a["counts"],
                "replay_counts": b["counts"],
                "before_sha256": a["geometry_material_sha256"],
                "replay_sha256": b["geometry_material_sha256"],
                "child_differences": child_differences(a, b),
                "next_diagnostic": (
                    "Inspect per-child named transforms, normalized world-space face/edge coordinates,"
                    " front/back face material and inherited material in a read-only native traversal."
                ),
            })
    # New fixed SU2024 collector includes FULL root and global rendering state.
    # Old test JSON without these fields remains backward compatible but is NOT
    # silently upgraded into proof of deep native deliverability.
    root_before, root_after = before.get("root_geometry_material_sha256"), replay.get("root_geometry_material_sha256")
    root_changed = root_before != root_after if root_before is not None and root_after is not None else None
    presentation_before, presentation_after = before.get("presentation_sha256"), replay.get("presentation_sha256")
    presentation_changed = (
        presentation_before != presentation_after
        if presentation_before is not None and presentation_after is not None else None
    )
    document_before = before.get("document_geometry_material_sha256")
    document_after = replay.get("document_geometry_material_sha256")
    document_changed = (
        document_before != document_after
        if document_before is not None and document_after is not None else None
    )
    return {
        "schema_version": 1,
        "status": "PASS" if not (missing or added or changed or root_changed or presentation_changed or document_changed) else "FAIL",
        "document_geometry_changed": document_changed,
        "root_geometry_changed": root_changed,
        "presentation_changed": presentation_changed,
        "deep_native_collector_both_stages": before.get("collector") == replay.get("collector") == "KStudioNativeDeepFingerprint/1",
        "before_group_count": len(old),
        "replay_group_count": len(new),
        "missing_groups": missing,
        "added_groups": added,
        "changed_groups": changed,
        "persistent_ids_ignored": True,
        "equal_group_counts_do_not_prove_geometry_equality": True,
    }


def child_differences(before: dict[str, Any], replay: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Optional actual native child transforms/bounds/materials; never substitute
    this diagnostic for the strict full geometry/material hash comparison.
    """
    if not isinstance(before.get("children"), list) or not isinstance(replay.get("children"), list):
        return None
    old = {x["name"]: x for x in before["children"]}
    new = {x["name"]: x for x in replay["children"]}
    return [{"name": name, "before": old.get(name), "replay": new.get(name)}
            for name in sorted(old.keys() | new.keys()) if old.get(name) != new.get(name)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--json", action="store_true", help="Print machine-readable report")
    args = parser.parse_args()
    result = compare(
        json.loads(args.before.read_text(encoding="utf-8")),
        json.loads(args.replay.read_text(encoding="utf-8")),
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"], "before", result["before_group_count"],
              "replay", result["replay_group_count"])
        print("Missing:", result["missing_groups"], "Added:", result["added_groups"])
        for group in result["changed_groups"]:
            print(group["name"], "count_equal=", group["counts_equal"],
                  "old=", group["before_sha256"][:12], "new=", group["replay_sha256"][:12])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
