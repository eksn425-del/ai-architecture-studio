"""No download/sha/revision-only claims for native SKP deliverability."""
import hashlib
import json
from pathlib import Path

import pytest

from app.native_delivery import record_delivery_checkpoint
from scripts.audit_native_delivery_stages import audit_stages


def item(name="ROOF", fingerprint="a", *, count=20, pid=1, children=None):
    out = {
        "name": name, "pid": pid,
        "counts": {"faces": count, "edges": count * 3, "instances": 0},
        "geometry_material_sha256": fingerprint * 64,
    }
    if children is not None:
        out["children"] = children
    return out


def model(*groups):
    return {"schema_version": 1, "revision": 1, "groups": list(groups)}


def test_receipt_never_claims_download_sketchup_delivery_pass(tmp_path):
    bound = tmp_path / "outputs/model/blank-disposable-user.skp"
    exported = tmp_path / "outputs/model/fast-assembly-agent.skp"
    bound.parent.mkdir(parents=True)
    bound.write_bytes(b"valid bound file for fixture")
    exported.write_bytes(b"valid candidate file for fixture")
    result = record_delivery_checkpoint(tmp_path, bound, exported,
         roots=[20606], revisions={"glass_curved_roof": 1})
    assert result["status"] == "UNVERIFIED_NATIVE_REOPEN"
    assert result["bound_document"]["sha256"] == hashlib.sha256(bound.read_bytes()).hexdigest()
    assert result["download_candidate"]["sha256"] == hashlib.sha256(exported.read_bytes()).hexdigest()
    assert json.loads((tmp_path / "runtime/native_delivery_checkpoint.json").read_text()) == result
    assert "clean_download_reopened_native_fingerprint" in result["required_next"]
    with pytest.raises(ValueError):
        record_delivery_checkpoint(tmp_path, bound, exported,
             roots=[], revisions={"glass_curved_roof": 1})
    exported.write_bytes(b"")
    with pytest.raises(ValueError, match="nonempty"):
        record_delivery_checkpoint(tmp_path, bound, exported,
             roots=[20606], revisions={"glass_curved_roof": 1})


def test_deep_roof_change_fails_even_when_reopen_revision_and_direct_counts_match():
    initial = model(item("ROOF_TIMBER", children=[{"name": "CURVED_SHELL", "transform": "T1"}]),
                    item("STRUCTURE_EXISTING", "b", pid=7))
    same_reopened = model(item("ROOF_TIMBER", pid=401,
                               children=[{"name": "CURVED_SHELL", "transform": "T1"}]),
                          item("STRUCTURE_EXISTING", "b", pid=3))
    broken_clean = model(item("ROOF_TIMBER", fingerprint="c", pid=401, count=20,
                              children=[{"name": "CURVED_SHELL", "transform": "T2"}]),
                         item("STRUCTURE_EXISTING", "b", pid=3))
    result = audit_stages(initial, same_reopened, broken_clean)
    assert result["status"] == "FAIL"
    assert result["first_failing_transition"] == "bound_reopen_to_clean_download_reopen"
    changed = result["transitions"][1]["comparison"]["changed_groups"][0]
    assert changed["counts_equal"]
    assert changed["name"] == "ROOF_TIMBER"
    assert changed["child_differences"] == [{"name": "CURVED_SHELL",
                                           "before": {"name": "CURVED_SHELL", "transform": "T1"},
                                           "replay": {"name": "CURVED_SHELL", "transform": "T2"}}]


def test_first_failing_transition_localizes_bound_save_and_no_false_clean_pass():
    first = model(item("ROOF"))
    broken = model(item("ROOF", "b"))
    result = audit_stages(first, broken, broken)
    assert result["status"] == "FAIL"
    assert result["first_failing_transition"] == "before_save_to_bound_reopen"
    assert result["transitions"][1]["comparison"]["status"] == "PASS"
    assert not result["native_delivery_proven"]


def test_download_receipt_detects_changed_bytes_before_comparing_geometry():
    source = model(item("ROOF"))
    valid_bytes = b"original candidate"
    receipt = {"status": "UNVERIFIED_NATIVE_REOPEN",
        "download_candidate": {"sha256": hashlib.sha256(valid_bytes).hexdigest()}}
    changed = audit_stages(source, source, source, receipt=receipt, downloaded_bytes=b"different")
    assert changed["status"] == "FAIL" and changed["reason"] == "download_candidate_sha_mismatch"
    result = audit_stages(source, source, source, receipt=receipt, downloaded_bytes=valid_bytes)
    assert result["status"] == "PASS"
    assert result["native_delivery_proven"]
    with pytest.raises(ValueError):
        audit_stages(source, source, source, receipt=receipt)


def test_no_auto_verified_label_on_candidate_site_ui():
    source = (Path(__file__).parents[1] / "app/static/studio.js").read_text(encoding="utf8")
    assert 'delivery_status === "UNVERIFIED_NATIVE_REOPEN"' in source
    assert "尚未通过 SketchUp 原生重开" in source
    host = (Path(__file__).parents[1] / "app/main.py").read_text(encoding="utf8")
    assert "record_delivery_checkpoint(" in host
    assert '"delivery_status"' in host
