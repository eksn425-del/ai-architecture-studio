"""No private SKP/test input; validate host-only readback gates with deterministic fixtures."""
import json
from pathlib import Path

import pytest

from app.sketchup_mcp import MCPCallError, SketchUpAdapter
from app.spatial_spec import validate_spatial_spec
from scripts.audit_native_delivery_stages import audit_stages
from scripts.compare_native_replay import compare


def native(name="ROOF_TIMBER", digest="a" * 64, *, presentation="p" * 64):
    return {
        "collector": "KStudioNativeDeepFingerprint/1",
        "root_geometry_material_sha256": digest,
        "document_geometry_material_sha256": digest,
        "presentation_sha256": presentation,
        "groups": [{"name": name, "counts": {"faces": 2, "edges": 4, "instances": 1},
                    "geometry_material_sha256": digest, "children": []}],
    }


def test_native_hash_catches_unchanged_bbox_or_count_and_changed_presentation():
    before = native()
    changed = native(digest="b" * 64)
    assert compare(before, changed)["root_geometry_changed"] is True
    assert compare(before, changed)["status"] == "FAIL"
    visibility = native(presentation="q" * 64)
    result = compare(before, visibility)
    assert result["status"] == "FAIL" and result["presentation_changed"] is True
    assert compare(before, native())["status"] == "PASS"


def test_actual_delivery_cli_contract_requires_three_fixed_source_captures():
    original = native()
    absent_before_save = {"groups": original["groups"]}
    r = audit_stages(absent_before_save, original, original, require_deep=True)
    assert r["status"] == "BLOCKED" and not r["native_delivery_proven"]
    r = audit_stages(original, original, original, require_deep=True)
    assert r["status"] == "PASS" and r["native_delivery_proven"]


def test_host_fixed_collector_verified_identity_before_and_after_and_fresh_file(tmp_path, monkeypatch):
    active_path = tmp_path / "private-model-copy.skp"
    out = tmp_path / "audit.json"
    called = []
    class Client:
        def call(self, name, kwargs):
            assert name == "sketchup_eval_project_file"
            script = Path(kwargs["script_path"]).read_text(encoding="utf-8")
            assert "KStudioNativeDeepFingerprint.capture" in script
            assert "JSON.generate(KStudioNativeDeepFingerprint.capture" not in script
            assert "model.save" not in script and "model.start_operation" not in script
            assert "\\n" not in script
            called.append(script)
            return {"result": {
                "collector": "KStudioNativeDeepFingerprint/1",
                "root_pid": 20606, "model_path": str(active_path.resolve()),
                "model_guid": "actual-owner-copy-guid",
                "groups": native()["groups"],
                "root_geometry_material_sha256": "a" * 64,
                "presentation_sha256": "p" * 64,
                "root_name": "glass_curved_roof", "visited_entities": 9,
            }}
    adapter = SketchUpAdapter(Client())
    identity = {"model_path": str(active_path.resolve()), "model_guid": "actual-owner-copy-guid",
                "active_context": False}
    monkeypatch.setattr(adapter, "get_active_model_identity", lambda: identity)
    monkeypatch.setattr("app.sketchup_mcp._generated_script_dir", lambda: tmp_path)
    payload = adapter.capture_native_deep_fingerprint(
        expected_model_path=active_path, expected_guid="actual-owner-copy-guid",
        root_pid=20606, output_path=out,
    )
    assert len(called) == 1
    assert payload == json.loads(out.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="fresh file"):
        adapter.capture_native_deep_fingerprint(expected_model_path=active_path,
            expected_guid="actual-owner-copy-guid", root_pid=20606, output_path=out)
    identity["active_context"] = True
    with pytest.raises(MCPCallError, match="exit nested"):
        adapter.capture_native_deep_fingerprint(expected_model_path=active_path,
            expected_guid="actual-owner-copy-guid", root_pid=20606, output_path=tmp_path/"other.json")


def specimen():
    def mark(axis, feature, provenance="observed"):
        return {"axis": axis, "source": "owner-original-01.jpg", "feature": feature,
                "provenance": provenance}
    return {
        "schema_version": 1, "status": "DRAFT_NEEDS_OWNER_REVIEW",
        "model_axes": {"positive_x": "long building direction as shown in owner plan",
                       "positive_y": "from south atrium to northern outside",
                       "positive_z": "upwards from ground floor"},
        "source_views": [
            {"filename": "owner-original-01.jpg", "kind": "exterior", "looking_towards": "-X"},
            {"filename": "owner-original-02.jpg", "kind": "section", "looking_towards": "not_applicable"}
        ],
        "roof": {"high_end": mark("+Y", "higher edge"), "low_end": mark("-Y", "lower edge")},
        "ramp": {"entry": mark("-X", "entry landing"), "exit": mark("+X", "exit landing")},
        "owner_review_note": "",
    }


def test_spatial_probe_rejects_same_direction_and_false_owner_confirmation():
    draft = specimen()
    assert validate_spatial_spec(draft)["status"] == "DRAFT_NEEDS_OWNER_REVIEW"
    draft["roof"]["low_end"]["axis"] = "+Y"
    with pytest.raises(ValueError, match="high and low"):
        validate_spatial_spec(draft)
    draft = specimen()
    draft["status"] = "OWNER_CONFIRMED"
    with pytest.raises(ValueError, match="review note"):
        validate_spatial_spec(draft)
    draft["owner_review_note"] = "Checked owner source orientation"
    draft["roof"]["high_end"]["provenance"] = "estimated"
    with pytest.raises(ValueError, match="falsely certify"):
        validate_spatial_spec(draft)
    draft["roof"]["high_end"]["provenance"] = "user_confirmed"
    assert validate_spatial_spec(draft)["status"] == "OWNER_CONFIRMED"


def test_native_audit_requires_complete_document_and_catches_escaped_geometry():
    before = native()
    after = native()
    after["document_geometry_material_sha256"] = "b" * 64
    result = compare(before, after)
    assert result["root_geometry_changed"] is False
    assert result["document_geometry_changed"] is True
    assert result["status"] == "FAIL"
    incomplete = native()
    del incomplete["document_geometry_material_sha256"]
    assert audit_stages(incomplete, before, before, require_deep=True)["status"] == "BLOCKED"


def test_delegated_spatial_review_is_distinct_from_owner_confirmation():
    draft = specimen()
    draft['status'] = 'AGENT_REVIEWED_OWNER_DELEGATED'
    with pytest.raises(ValueError, match='delegation'):
        validate_spatial_spec(draft)
    draft['owner_delegation_note'] = 'Please judge the source directions yourself.'
    draft['agent_review_note'] = 'Compared the original section and ramp-end photograph.'
    result = validate_spatial_spec(draft)
    assert result['owner_review_note'] == ''
    assert result['status'] == 'AGENT_REVIEWED_OWNER_DELEGATED'
    draft['ramp']['entry']['provenance'] = 'unresolved'
    with pytest.raises(ValueError, match='unresolved'):
        validate_spatial_spec(draft)


def test_ruby_collector_is_fixed_read_only_and_cap_and_safety_are_present():
    source = (Path(__file__).parents[1] / "app/native_deep_fingerprint.rb").read_text(encoding="utf8")
    assert "MAX_ENTITIES = 250_000" in source
    assert "vertices_world_mm" in source and "world_transform" in source
    assert "presentation_sha256" in source
    assert "model.save" not in source and "start_operation" not in source and ".erase!" not in source
    assert "root_pid" in source and "active_path.nil?" in source
    guard = (Path(__file__).parents[1] / "app/adopted_sketchup_helpers.rb").read_text(encoding="utf8")
    assert "expectations.length > 256" in guard
    assert "expectations.length > 24" not in guard
