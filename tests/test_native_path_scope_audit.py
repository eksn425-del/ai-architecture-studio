from copy import deepcopy
from scripts.audit_native_path_scope import audit
import pytest


def fixture():
    before = {"collector": "KStudioPathScopeNative/1", "geometry_writes": 0, "revision": 4,
              "snapshot": {"paths": [["RAMPS", "RAMP_1"]], "masked_root": {"metadata": {"pid": 20606}, "protected": "deep"},
                           "document_loose_sha": "loose", "external": [], "presentation_sha": "scene", "model_path": "same.skp", "model_guid": "before"}}
    after = deepcopy(before); after["revision"] = 5; after["snapshot"]["model_guid"] = "after"
    writer = {"root_pid": 20606, "revision": 5, "model_guid": "after", "last_verification": {"verified": True},
              "last_precommit_keep_guard": {"passed": True}, "last_edit_scope_receipt": {"guard": "deep_exact_paths_v1", "status": "passed", "allowed_paths": before["snapshot"]["paths"]}}
    return before, after, writer


def test_actual_writer_binds_guid_change_without_weakening_protected_geometry():
    a, b, w = fixture(); r = audit(a, b, w)
    assert r["status"] == "PASS" and r["before_protected_sha256"] == r["after_protected_sha256"]
    b["snapshot"]["masked_root"]["protected"] = "same-bounds-changed-material"
    assert audit(a, b, w)["status"] == "FAIL"


@pytest.mark.parametrize("field,value", [("document_loose_sha", "changed"), ("model_path", "other.skp"), ("model_guid", "unrecognized"), ("paths", [["RAMPS"]])])
def test_changes_cannot_be_excused_by_guid_transition(field, value):
    a, b, w = fixture(); b["snapshot"][field] = value
    assert audit(a, b, w)["status"] != "PASS"


def test_missing_or_uncommitted_proof_blocks():
    a, b, w = fixture(); w["last_verification"]["verified"] = False
    assert audit(a, b, w)["status"] == "BLOCKED"


def test_autosave_guid_needs_real_owned_readback_not_blind_guid_ignore():
    a, b, w = fixture()
    a["snapshot"]["masked_root"]["metadata"]["name"] = "Architecture case"
    b["snapshot"]["masked_root"]["metadata"]["name"] = "Architecture case"
    b["snapshot"]["model_guid"] = "after-autosave"
    assert audit(a, b, w)["status"] == "BLOCKED"
    b["identity_proof"] = {"collector": "KStudioOwnedGuidReadback/1", "read_only": True, "model_path": "same.skp",
                           "model_guid": "after-autosave", "root_pid": 20606, "project_id": "case", "revision": 5}
    assert audit(a, b, w)["status"] == "PASS"
    b["identity_proof"]["revision"] = 4
    assert audit(a, b, w)["status"] == "BLOCKED"
