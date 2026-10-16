from copy import deepcopy
import hashlib
import json

import pytest

from scripts.audit_native_path_scope import validate_surface_protection


def fixture():
    tag = {"name": "Layer0", "visible": True}
    verts = [{"pid": 4 + i, "point_mm": p} for i, p in enumerate([[0, 0, 0], [1, 0, 0], [0, 1, 0]])]
    shape = {"type": "Group", "pid": 1, "name": "L0", "definition_name": "Floor",
             "transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
             "material": None, "tag": tag, "hidden": False, "locked": False, "entities": [
                 {"type": "Face", "pid": 2, "loops": [{"outer": True, "vertices": verts}],
                  "normal": [0, 0, 1], "front": "approved_material", "back": "approved_material", "hidden": False, "tag": tag},
                 {"type": "Edge", "pid": 3, "vertices": verts[:2], "soft": "approved_seam", "smooth": "approved_seam", "hidden": False, "tag": tag}]}
    rows = [{"path": ["FLOORS", "L0"], "shape": shape}]
    canonical = json.dumps(rows)
    return {"contract": "native_constrained_surface_edits_v1", "paths": [["FLOORS", "L0"]],
            "face_material_pids": [2], "soft_smooth_edge_pids": [3], "canonical_shape_json": canonical,
            "shape_sha256": hashlib.sha256(canonical.encode()).hexdigest(), "captured_entities": 2}


def test_complete_native_surface_payload_is_verifiable():
    validate_surface_protection(fixture())


@pytest.mark.parametrize("fault", ["sha", "face_mask", "edge_mask", "unapproved_mask", "geometry", "count", "paths"])
def test_surface_receipt_cannot_hide_unapproved_or_missing_geometry(fault):
    value = deepcopy(fixture())
    rows = json.loads(value["canonical_shape_json"])
    if fault == "sha":
        value["shape_sha256"] = "0" * 64
    elif fault == "face_mask":
        value["face_material_pids"] = [99]
    elif fault == "edge_mask":
        value["soft_smooth_edge_pids"] = [99]
    elif fault == "unapproved_mask":
        rows[0]["shape"]["entities"][0]["pid"] = 98
    elif fault == "geometry":
        rows[0]["shape"]["entities"][0]["loops"] = []
    elif fault == "count":
        value["captured_entities"] = 0
    else:
        value["paths"] = [["FLOORS", "OTHER"]]
    if fault in {"unapproved_mask", "geometry"}:
        value["canonical_shape_json"] = json.dumps(rows)
        value["shape_sha256"] = hashlib.sha256(value["canonical_shape_json"].encode()).hexdigest()
    with pytest.raises(ValueError):
        validate_surface_protection(value)
