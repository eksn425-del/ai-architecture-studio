"""Offline transport-contract tests for scoped edits (not native SketchUp proof)."""
from pathlib import Path

from app import project_ruby
from app.project_ruby import ProjectRubyExecutor, validate_project_ruby_source


def _executor(tmp_path: Path):
    value = object.__new__(ProjectRubyExecutor)
    value.project_id = "test-edit-scope"
    value.expected_model_path = tmp_path / "blank-disposable-scope.skp"
    value.expected_model_guid = "approved-guid"
    return value


def test_guard_only_armed_for_explicit_targeted_edit(monkeypatch, tmp_path):
    monkeypatch.setattr(project_ruby, "geometry_helper", lambda *_: None)
    executor = _executor(tmp_path)
    target = executor._build_transport_script(
        tmp_path / "edit.rb", tmp_path / "report.json", 3, 123,
        update_mode="edit", allowed_mutation_names=["FRONT_GLAZING", "FRONT_GLAZING_NEW"],
    )
    assert "KStudioEditScopeGuard.fingerprints(root)" in target
    assert "KStudioEditScopeGuard.verify!(root, edit_scope_before" in target
    assert "FRONT_GLAZING_NEW" in target
    assert "root.set_attribute(CodexSketchupArchitect::DICT, 'edit_scope_receipt'" in target
    assert target.index("eval(source, binding") < target.index("KStudioEditScopeGuard.verify!")
    assert target.index("KStudioEditScopeGuard.verify!") < target.index("oss_method_ledger")

    legacy = executor._build_transport_script(
        tmp_path / "edit.rb", tmp_path / "report.json", 3, 123, update_mode="edit",
    )
    assert "KStudioEditScopeGuard.verify!(" not in legacy
    assert "'edit_scope_receipt', 'null'" in legacy
    assert "KStudioEditScopeGuard.fingerprints(root)" not in legacy
    replacement = executor._build_transport_script(
        tmp_path / "build.rb", tmp_path / "report.json", 0, None,
        update_mode="replace", allowed_mutation_names=["INVALID_IF_REPLACE"],
    )
    assert "KStudioEditScopeGuard.verify!(" not in replacement


def test_agent_cannot_bypass_scope_guard():
    for source in (
        "KStudioEditScopeGuard.verify!(root, nil, [])",
        "edit_scope_before = nil",
        "edit_scope_receipt = {'status' => 'passed'}",
    ):
        try:
            validate_project_ruby_source("building", source)
        except ValueError as error:
            assert "blocked host" in str(error)
        else:
            raise AssertionError("User Ruby bypassed edit-scope source guard")
