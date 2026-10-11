"""Protect model reproducibility: counts-only 'PASS' is forbidden."""
import json
from pathlib import Path
from scripts.compare_native_replay import compare


def payload(*items):
    return {"root_pid": 1, "revision": 1, "groups": list(items)}


def item(name, sha="a" * 64, *, pid=1, count=1):
    return {"name": name, "pid": pid, "counts": {"faces": count, "edges": 3 * count, "instances": 0},
            "geometry_material_sha256": sha}


def test_new_root_ids_are_normal_for_same_geometry():
    result = compare(payload(item("ROOF", pid=1)), payload(item("ROOF", pid=999)))
    assert result["status"] == "PASS"
    assert result["persistent_ids_ignored"]


def test_same_names_and_counts_but_different_geometry_must_fail():
    result = compare(payload(item("GLASS", "a" * 64)), payload(item("GLASS", "b" * 64)))
    assert result["status"] == "FAIL"
    assert result["changed_groups"][0]["counts_equal"] is True


def test_missing_new_and_duplicate_names_fail():
    result = compare(payload(item("ROOF")), payload(item("OTHER")))
    assert result["status"] == "FAIL"
    assert result["missing_groups"] == ["ROOF"]
    assert result["added_groups"] == ["OTHER"]
    try:
        compare(payload(item("ROOF"), item("ROOF", pid=3)), payload(item("ROOF")))
    except ValueError as exc:
        assert "Duplicate" in str(exc)
    else:
        raise AssertionError("Duplicate group names cannot be silently matched")


def test_actual_dream_coffee_evidence_remains_fail_not_false_pass():
    base = Path(__file__).resolve().parents[1] / "docs/test-results/windows"
    old = json.loads((base / "2026-10-11-dream-coffee-protected-repair/model/protected-after-fingerprints.json").read_text(encoding="utf8"))
    replay = json.loads((base / "2026-10-11-dream-coffee-native-replay/model/replay-fingerprints.json").read_text(encoding="utf8"))
    result = compare(old, replay)
    assert result["status"] == "FAIL"
    assert result["before_group_count"] == result["replay_group_count"] == 116
    assert {x["name"] for x in result["changed_groups"]} == {
        "FRONT_SLOPED_GLAZING", "FRONT_STORE_FRONT_GLAZING", "UPPER_GLASS_PAVILION"}
    assert all(x["counts_equal"] for x in result["changed_groups"])
