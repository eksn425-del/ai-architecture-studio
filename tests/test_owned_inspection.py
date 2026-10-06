import json

import pytest

from app.sketchup_mcp import MCPCallError
from tests.test_quality_lift import _executor


def test_owned_inspection_is_guarded_readonly_and_does_not_change_state(tmp_path, monkeypatch):
    executor, adapter, mcp, _ = _executor(tmp_path, state={"main": {"root_pid": 701, "revision": 3}})
    monkeypatch.setenv("ARCHFLOW_GENERATED_SCRIPT_DIR", str(tmp_path / "transport"))
    sources = []

    def inspect_call(name, args):
        from pathlib import Path
        source = Path(args["script_path"]).read_text(encoding="utf-8")
        sources.append(source)
        assert name == "sketchup_eval_project_file"
        assert "Project identity mismatch" in source and "Revision mismatch" in source
        assert "Active model GUID changed" in source and "Active model path changed" in source
        assert "start_operation" not in source and "erase!" not in source
        return {"result": {"objects": [], "next_offset": None, "bounds_units": "mm"}}

    mcp.call = inspect_call
    before = json.dumps(executor.ruby_state)
    result = executor.inspect_owned({"script_id": "main", "path": ["SHELL", '#{raise "injected"}'], "offset": 100})
    assert result["success"] and json.loads(result["contentItems"][0]["text"])["read_only"]
    assert json.dumps(executor.ruby_state) == before
    assert '\\#{raise' in sources[0]
    assert not list((tmp_path / "transport").glob("*.rb"))
    assert not adapter.captures


@pytest.mark.parametrize("args", [
    {"path": "SHELL"}, {"path": [""]}, {"path": [1]}, {"path": ["x"] * 9},
    {"limit": 0}, {"limit": 101}, {"limit": True}, {"offset": -1}, {"offset": 0.5},
])
def test_inspection_rejects_invalid_scope_and_paging(tmp_path, args):
    executor, _, mcp, _ = _executor(tmp_path, state={"main": {"root_pid": 701, "revision": 3}})
    with pytest.raises(ValueError):
        executor.inspect_owned({"script_id": "main", **args})
    assert not mcp.calls


def test_inspection_requires_existing_owned_script(tmp_path):
    executor, _, mcp, _ = _executor(tmp_path)
    with pytest.raises(MCPCallError, match="existing owned root"):
        executor.inspect_owned({"script_id": "missing"})
    assert not mcp.calls


def test_inspection_rejects_switched_original_document(tmp_path):
    executor, _, mcp, _ = _executor(tmp_path, active_model=tmp_path / "original.skp", state={"main": {"root_pid": 701}})
    with pytest.raises(MCPCallError, match="disposable"):
        executor.inspect_owned({"script_id": "main"})
    assert not mcp.calls


def test_desktop_bundles_and_verifies_owned_ruby_helper():
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    build = (repo / "scripts/build_desktop.ps1").read_text(encoding="utf-8")
    install = (repo / "scripts/install_desktop.ps1").read_text(encoding="utf-8")
    assert '--add-data "$repoPath/app/adopted_sketchup_helpers.rb;app"' in build
    assert "_internal\\app\\adopted_sketchup_helpers.rb" in install
