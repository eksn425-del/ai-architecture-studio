"""Synthetic negative/positive cases; NEVER evidence of actual SU2024 source quality."""
from copy import deepcopy

from scripts.audit_scoped_native_edit import audit_scoped_edit

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64


def node(name, sha, pid):
    return {"name": name, "geometry_material_sha256": sha,
            "counts": {"faces": 3, "edges": 9, "instances": 0}, "pid": pid,
            "local_transform": [1] * 16, "world_transform": [1] * 16,
            "hidden": False, "tag": {"name": "Layer0", "visible": True}}


def capture():
    return {"collector": "KStudioNativeDeepFingerprint/1", "schema_version": 2,
            "root_pid": 20606, "root_name": "BUILDING", "root_geometry_material_sha256": B,
            "document_geometry_material_sha256": C, "presentation_sha256": D,
            "groups": [node("TENSION_BRACING", A, 12), node("ROOF_TIMBER", B, 13), node("RAMPS", E, 14)],
            "document_groups": [node("BUILDING", B, 20606), node("OUTSIDE_ROOT", F, 99)]}


def edited():
    a = capture()
    a["groups"][0]["geometry_material_sha256"] = E
    a["root_geometry_material_sha256"] = E
    a["document_geometry_material_sha256"] = E
    a["document_groups"][0]["geometry_material_sha256"] = E
    return a


def test_one_target_only_is_direct_scope_pass_not_visual_pass():
    r = audit_scoped_edit(capture(), edited(), expected_before_document_sha=C)
    assert r["status"] == "PASS" and r["direct_scope_proven"]
    assert r["visual_source_fidelity"] == "NOT_ASSESSED"
    assert r["native_delivery"] == "NOT_ASSESSED"
    assert r["protected_direct_groups_checked"] == 2


def test_protected_group_even_same_counts_fails():
    b = edited()
    b["groups"][1]["geometry_material_sha256"] = E
    assert audit_scoped_edit(capture(), b)["status"] == "FAIL"


def test_outside_root_escape_fails():
    b = edited()
    b["document_groups"][1]["geometry_material_sha256"] = A
    assert audit_scoped_edit(capture(), b)["status"] == "FAIL"


def test_noop_or_wrong_baseline_not_pass():
    assert audit_scoped_edit(capture(), capture())["status"] == "FAIL"
    assert audit_scoped_edit(capture(), edited(), expected_before_document_sha=A)["status"] == "BLOCKED"


def test_target_missing_or_duplicate_fails_closed():
    a = capture()
    a["groups"][0]["name"] = "NOT_BRACING"
    assert audit_scoped_edit(a, edited())["status"] == "BLOCKED"
    a = capture()
    a["groups"].append(deepcopy(a["groups"][0]))
    assert audit_scoped_edit(a, edited())["status"] == "BLOCKED"


def test_missing_capture_or_root_transform_or_presentation_fails():
    a = capture()
    del a["document_groups"]
    assert audit_scoped_edit(a, edited())["status"] == "BLOCKED"
    b = edited()
    b["document_groups"][0]["world_transform"] = [2] * 16
    assert audit_scoped_edit(capture(), b)["status"] == "FAIL"
    b = edited()
    b["presentation_sha256"] = A
    assert audit_scoped_edit(capture(), b)["status"] == "FAIL"


def test_root_or_direct_pid_replacement_not_accepted():
    b = edited()
    b["root_pid"] = 222
    assert audit_scoped_edit(capture(), b)["status"] == "BLOCKED"
    b = edited()
    b["groups"][0]["pid"] = 333
    assert audit_scoped_edit(capture(), b)["status"] == "FAIL"


def test_new_top_level_group_is_not_allowed():
    b = edited()
    b["document_groups"].append(node("ESCAPED", E, 111))
    assert audit_scoped_edit(capture(), b)["status"] == "FAIL"
