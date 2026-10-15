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


@pytest.mark.parametrize("source", ["KStudioPathScopeGuard.capture(root, [])", "KStudioNativeDeepFingerprint.scan([])"])
def test_agent_cannot_call_host_guard_or_collector(source):
    with pytest.raises(ValueError, match="blocked host"):
        validate_project_ruby_source("building", source)


@pytest.mark.parametrize("paths", [None, []])
def test_edit_cannot_omit_scope_even_without_critic_context(paths):
    ex = object.__new__(ProjectRubyExecutor)
    with pytest.raises(ValueError, match="explicit allowed_mutation_paths"):
        ex.run({"script_id": "building", "ruby_source": "length = 1", "update_mode": "edit", "allowed_mutation_paths": paths})
