"""Existing native-contract test doubles only; actual SketchUp NOT_RUN."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.su_relation_audit import (audit_su_relations, inspect_su_relation_evidence,
                                   owned_path_id, prepare_su_relation_tools)
from app.spatial_clearance import audit_spatial_clearance


def snapshot(path, pid, low, high):
    # Exact schema emitted by inspect_named_owned_group(..., 0, 1, true).
    return {"path": path, "persistent_id": pid, "locked": False,
            "definition_instances": 1, "definition_name": "fixture",
            "bounds_units": "mm", "bounds_frame": "parent-local",
            "bounds_mm": {"min": low, "max": high,
                          "size": [b - a for a, b in zip(low, high)]},
            "object_bounds_frame": "selected-group-local", "objects_total": 0,
            "offset": 0, "next_offset": None, "truncated": False, "objects": [],
            "deep_fingerprint_collector": "KStudioNativeDeepFingerprint/1",
            "deep_geometry_material_sha256": str(pid % 10) * 64}


class ContractExecutor:
    """Explicit mock, not a claim of real native execution."""
    def __init__(self):
        self.project_id = "mock-contract-project"
        self.expected_model_path = Path("/mock/owned.skp")
        self.expected_model_guid = "mock-guid"
        self.ruby_state = {"main": {"root_pid": 701, "revision": 3}}
        self.snapshots = [snapshot(["STAIR"], 12, [0, 0, 0], [1000, 1200, 1000]),
                          snapshot(["LANDING"], 13, [1000, 0, 0], [2000, 1200, 1000])]
        self.calls = []
        self.change = lambda payload: None

    def inspect_owned(self, arguments):
        self.calls.append(deepcopy(arguments))
        payload = {"script_id": "main", "revision": 3, "read_only": True,
                   "snapshots": deepcopy(self.snapshots), "oss_method_ledger": None,
                   "edit_scope_receipt": None}
        self.change(payload)
        return {"success": True, "contentItems": [{"type": "inputText", "text": json.dumps(payload)}]}


def relation(a=None, b=None):
    return {"a": a or ["STAIR"], "b": b or ["LANDING"], "axis": 0, "tolerance": .001}


def test_same_parent_native_mm_contact_is_only_proxy_with_identity():
    executor = ContractExecutor()
    result = audit_su_relations(executor, "main", [relation()])
    row = result["connections"][0]
    assert row["bounds_status"] == "contact"
    assert row["signed_gap_m"] == pytest.approx(0)
    assert row["status"] == "unverified" and row["exact_for_boxes"] is False
    assert row["metric_frame_verified"] is False
    assert result["model_identity"] == {"project_id": executor.project_id, "script_id": "main",
                                        "model_path": str(executor.expected_model_path), "model_guid": "mock-guid", "root_pid": 701}
    assert result["revision"] == 3 and result["inventory_complete"] is False
    assert result["automatic_geometry_changes"] is False
    assert result["actual_walkability"] == "unverified"
    assert executor.calls == [{"script_id": "main", "paths": [["STAIR"], ["LANDING"]]}]
    assert len(result["provenance"]["inspection_sha256"]) == 64


def test_measured_native_gap_uses_mm_conversion_not_requested_dimensions():
    executor = ContractExecutor()
    executor.snapshots[1]["bounds_mm"]["min"][0] = 1050
    result = audit_su_relations(executor, "main", [relation()])["connections"][0]
    assert result["bounds_status"] == "gap" and result["signed_gap_m"] == pytest.approx(.05)
    assert result["status"] == "unverified"


def test_different_parent_frames_do_not_compare_or_guess_transform():
    executor = ContractExecutor()
    executor.snapshots[0]["path"] = ["LEVEL_ONE", "STAIR"]
    executor.snapshots[1]["path"] = ["LEVEL_TWO", "LANDING"]
    row = audit_su_relations(executor, "main", [relation(*[s["path"] for s in executor.snapshots])])["connections"][0]
    assert row["status"] == row["bounds_status"] == "unverified"
    assert row["signed_gap_m"] is None and "different_parent" in row["reason"]


@pytest.mark.parametrize("change", [
    lambda p: p.update(read_only=False), lambda p: p.update(script_id="other"),
    lambda p: p.update(revision=4), lambda p: p.update(revision=True),
    lambda p: p["snapshots"].pop(), lambda p: p["snapshots"].append(p["snapshots"][0]),
    lambda p: p["snapshots"][1].update(path=["STAIR"]),
    lambda p: p["snapshots"][1].update(path=["SUBSTITUTED"]),
    lambda p: p["snapshots"][0].update(bounds_units="inch"),
    lambda p: p["snapshots"][0].update(bounds_frame="world"),
    lambda p: p["snapshots"][0].update(persistent_id=True),
    lambda p: p["snapshots"][0].pop("deep_geometry_material_sha256"),
    lambda p: p["snapshots"][0].update(deep_fingerprint_collector="invented"),
    lambda p: p["snapshots"][0]["bounds_mm"].update(min=[float("nan"), 0, 0]),
    lambda p: p["snapshots"][0]["bounds_mm"].update(min=[2000, 0, 0]),
])
def test_missing_stale_substituted_or_unsupported_native_evidence_rejected(change):
    executor = ContractExecutor()
    executor.change = change
    with pytest.raises(ValueError):
        audit_su_relations(executor, "main", [relation()])


@pytest.mark.parametrize("attribute,value", [("expected_model_guid", "new-guid"),
                                             ("expected_model_path", Path("/different.skp"))])
def test_identity_race_fails_closed(attribute, value):
    executor = ContractExecutor()
    executor.change = lambda _: setattr(executor, attribute, value)
    with pytest.raises(ValueError, match="changed"):
        audit_su_relations(executor, "main", [relation()])


def test_revision_race_fails_closed():
    executor = ContractExecutor()
    executor.change = lambda _: executor.ruby_state["main"].update(revision=4)
    with pytest.raises(ValueError, match="changed"):
        audit_su_relations(executor, "main", [relation()])


def test_verified_preexisting_guid_refresh_precedes_race_baseline():
    executor = ContractExecutor()
    executor.verify_active_model = lambda: setattr(executor, "expected_model_guid", "verified-autosave")
    result = audit_su_relations(executor, "main", [relation()])
    assert result["model_identity"]["model_guid"] == "verified-autosave"
    executor.change = lambda _: setattr(executor, "expected_model_guid", "changed-during-read")
    with pytest.raises(ValueError, match="changed"):
        audit_su_relations(executor, "main", [relation()])


def test_failed_owned_identity_preflight_never_inspects_geometry():
    executor = ContractExecutor()
    def reject():
        raise ValueError("native ownership proof failed")
    executor.verify_active_model = reject
    with pytest.raises(ValueError, match="ownership"):
        audit_su_relations(executor, "main", [relation()])
    assert not executor.calls


def test_paths_are_unambiguous_and_bounded():
    assert owned_path_id(["A/B"]) != owned_path_id(["A", "B"])
    executor = ContractExecutor()
    for paths in ([], [["a"]] * 2, [[str(i)] for i in range(49)], [[""]], [["a"] * 9]):
        with pytest.raises(ValueError):
            inspect_su_relation_evidence(executor, "main", paths)
    assert not executor.calls


def test_invalid_connection_rejected_before_native_read():
    executor = ContractExecutor()
    with pytest.raises(ValueError):
        audit_su_relations(executor, "main", [{**relation(), "axis": True}])
    assert not executor.calls


def test_native_geometry_cannot_be_promoted_by_unsolicited_box_or_transform_flags():
    executor = ContractExecutor()
    for item in executor.snapshots:
        item.update(exact_box=True, geometry_type="box", world_transform=[1, 0, 0, 0] * 4)
    row = audit_su_relations(executor, "main", [relation()])["connections"][0]
    assert row["status"] == "unverified" and row["exact_for_boxes"] is False


def test_su_clearance_cannot_pass_empty_zone_or_contact_endpoint():
    executor = ContractExecutor()
    evidence = inspect_su_relation_evidence(executor, "main", [["STAIR"], ["LANDING"]])
    result = audit_spatial_clearance(evidence, [{"name": "corridor", "location": [20, 0, 2],
        "dimensions": [1, 1, 2], "ignore_ids": []}], [{"a": owned_path_id(["STAIR"]),
        "b": owned_path_id(["LANDING"]), "axis": 0, "min_width_m": 1,
        "max_step_m": .01, "tolerance_m": .001}])
    assert result["zones"][0]["status"] == result["endpoints"][0]["status"] == "unverified"
    assert result["endpoints"][0]["checks"] == {"oriented_contact": True, "minimum_width": True, "maximum_step": True}


def test_product_tools_acquire_native_evidence_and_reject_receipt_injection():
    executor = ContractExecutor()
    specs, dispatch = prepare_su_relation_tools(executor)
    assert {s["name"] for s in specs} == {"sketchup_audit_relations", "sketchup_audit_clearance"}
    with pytest.raises(ValueError):
        dispatch("sketchup_audit_relations", {"script_id": "main", "connections": [relation()], "receipt": {}})
    assert not executor.calls
    assert dispatch("sketchup_audit_relations", {"script_id": "main", "connections": [relation()]})["revision"] == 3
    result = dispatch("sketchup_audit_clearance", {"script_id": "main", "paths": [["STAIR"], ["LANDING"]],
        "zones": [{"name": "corridor", "location": [4, 4, 4], "dimensions": [1, 1, 2],
                   "ignore_paths": [], "parent_path": []}], "endpoints": []})
    assert result["zones"][0]["status"] == "unverified"


def test_actual_project_executor_guarded_contract_is_used(tmp_path, monkeypatch):
    from tests.test_quality_lift import _executor
    executor, _, mcp, _ = _executor(tmp_path, state={"main": {"root_pid": 701, "revision": 3}})
    monkeypatch.setenv("ARCHFLOW_GENERATED_SCRIPT_DIR", str(tmp_path / "transport"))
    fixture = ContractExecutor()
    calls = []

    def native_contract(name, arguments):
        source = Path(arguments["script_path"]).read_text(encoding="utf-8")
        calls.append(source)
        assert name == "sketchup_eval_project_file"
        for guard in ("Active model path changed", "Active model GUID changed", "Project identity mismatch", "Revision mismatch"):
            assert guard in source
        assert "inspect_named_owned_group(root, p, 0, 1, true)" in source
        assert "start_operation" not in source and "erase!" not in source
        return {"result": {"snapshots": fixture.snapshots, "revision": 3}}

    mcp.call = native_contract
    result = audit_su_relations(executor, "main", [relation()])
    assert len(calls) == 1
    assert result["connections"][0]["status"] == "unverified"
    assert executor.ruby_state["main"] == {"root_pid": 701, "revision": 3}
