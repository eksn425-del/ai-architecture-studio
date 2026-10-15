from app import project_ruby
from app.project_ruby import ProjectRubyExecutor, validate_project_ruby_source
import pytest


def test_exact_nested_paths_reach_precommit_host_guard(monkeypatch, tmp_path):
    monkeypatch.setattr(project_ruby, "geometry_helper", lambda *_: None)
    ex = object.__new__(ProjectRubyExecutor)
    ex.project_id = "test-path-scope"
    ex.expected_model_path = tmp_path / "blank-disposable.skp"
    ex.expected_model_guid = "guid"
    text = ex._build_transport_script(tmp_path / "edit.rb", tmp_path / "receipt.json", 4, 20606,
        update_mode="edit", allowed_mutation_names=["RAMPS"],
        allowed_mutation_paths=[["RAMPS", "RAMP_1"], ["RAMPS", "RAMP_3"]])
    assert "KStudioPathScopeGuard.capture(root" in text
    assert "RAMP_1" in text and "RAMP_3" in text
    assert text.index("KStudioPathScopeGuard.capture") < text.index("eval(source, binding")
    assert text.index("eval(source, binding") < text.index("KStudioPathScopeGuard.verify!")
    assert text.index("KStudioPathScopeGuard.verify!") < text.index("oss_method_ledger")
    assert "clear_owned_contents = lambda" in text
    assert "clear_named_owned_contents(root, path" in text


@pytest.mark.parametrize("source", ["KStudioPathScopeGuard.capture(root, [])", "KStudioNativeDeepFingerprint.scan([])"])
def test_agent_cannot_call_host_guard_or_collector(source):
    with pytest.raises(ValueError, match="blocked host"):
        validate_project_ruby_source("building", source)


@pytest.mark.parametrize("paths", [None, []])
def test_edit_cannot_omit_scope_even_without_critic_context(paths):
    ex = object.__new__(ProjectRubyExecutor)
    with pytest.raises(ValueError, match="explicit allowed_mutation_paths"):
        ex.run({"script_id": "building", "ruby_source": "length = 1", "update_mode": "edit", "allowed_mutation_paths": paths})


@pytest.mark.parametrize("arguments", [
    {"paths": []}, {"paths": [["X"]] * 49},
    {"path": ["X"], "paths": [["X"]]},
    {"_batch_paths": [["X"]], "paths": [["X"]]},
])
def test_public_batch_rejects_ambiguous_or_unbounded_inspection(arguments):
    ex = object.__new__(ProjectRubyExecutor)
    with pytest.raises(ValueError):
        ex.inspect_owned(arguments)


def test_deep_keep_detects_same_bounds_geometry_and_material_changes():
    from copy import deepcopy
    from app.modeling_quality import owned_inspection_fingerprint, verify_preserved_owned_paths
    value = {"persistent_id": 12, "objects_total": 0, "bounds_mm": {"min": [0, 0, 0], "max": [1, 2, 3]},
             "deep_geometry_material_sha256": "a" * 64}
    before = {"LANDINGS/PROTECTED_NORTH_PAD": value}
    assert verify_preserved_owned_paths(before, deepcopy(before))["verified"]
    after = deepcopy(before); after["LANDINGS/PROTECTED_NORTH_PAD"]["deep_geometry_material_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="deep_geometry_material_sha256"):
        verify_preserved_owned_paths(before, after)
    del after["LANDINGS/PROTECTED_NORTH_PAD"]["deep_geometry_material_sha256"]
    with pytest.raises(ValueError, match="deep_geometry_material_sha256"):
        verify_preserved_owned_paths(before, after)
    value["deep_geometry_material_sha256"] = "unverified"
    with pytest.raises(ValueError, match="SHA is invalid"):
        owned_inspection_fingerprint(value)
