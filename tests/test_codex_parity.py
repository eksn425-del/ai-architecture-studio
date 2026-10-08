from __future__ import annotations

from pathlib import Path

import pytest

from app.agent_tools import AgentToolSurface
from app.codex_parity import prepare_codex_parity_workspace
from app.workspace_ruby import resolve_workspace_ruby_path, run_workspace_ruby


def test_codex_parity_workspace_is_seeded_without_overwriting_agent_notes(tmp_path):
    workspace = tmp_path / "project" / "runtime" / "agent_workspace"
    prepare_codex_parity_workspace(workspace)

    assert (workspace / "README.md").is_file()
    assert "outer integration agent" in (workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert (workspace / "scripts").is_dir()
    assert (workspace / "notes" / "design_notes.md").is_file()
    facade_schedule = workspace / "notes" / "facade_schedule.json"
    assert facade_schedule.is_file()
    schedule = __import__("json").loads(facade_schedule.read_text(encoding="utf-8"))
    assert schedule["schema_version"] == 1
    assert set(schedule["views"]) == {"front", "rear", "left", "right"}
    assert (workspace / "qa").is_dir()
    assert (workspace / "qa" / "visual_qa.md").is_file()
    assert "NEEDS_FIX" in (workspace / "qa" / "visual_qa.md").read_text(encoding="utf-8")
    assert (workspace / ".architecture-studio.json").is_file()

    notes = workspace / "notes" / "design_notes.md"
    notes.write_text("USER CONFIRMED DECISION\n", encoding="utf-8")
    instructions = workspace / "AGENTS.md"
    instructions.write_text("PROJECT MODELING RULES\n", encoding="utf-8")
    visual_qa = workspace / "qa" / "visual_qa.md"
    visual_qa.write_text("CURRENT REVIEW SURVIVES\n", encoding="utf-8")
    facade_schedule.write_text(
        '{"schema_version":1,"user_confirmed":["rear has three windows"]}\n',
        encoding="utf-8",
    )
    prepare_codex_parity_workspace(workspace)
    assert notes.read_text(encoding="utf-8") == "USER CONFIRMED DECISION\n"
    assert instructions.read_text(encoding="utf-8") == "PROJECT MODELING RULES\n"
    assert visual_qa.read_text(encoding="utf-8") == "CURRENT REVIEW SURVIVES\n"
    assert "rear has three windows" in facade_schedule.read_text(encoding="utf-8")


def test_workspace_ruby_path_is_confined_to_scripts(tmp_path):
    workspace = prepare_codex_parity_workspace(tmp_path / "agent_workspace")
    script = workspace / "scripts" / "massing.rb"
    script.write_text("root.name = 'Massing'\n", encoding="utf-8")

    assert resolve_workspace_ruby_path(workspace, "scripts/massing.rb") == script.resolve()
    with pytest.raises(ValueError, match="scripts"):
        resolve_workspace_ruby_path(workspace, "notes/massing.rb")
    with pytest.raises(ValueError, match="traverse|relative"):
        resolve_workspace_ruby_path(workspace, "scripts/../outside.rb")
    with pytest.raises(ValueError, match=".rb"):
        resolve_workspace_ruby_path(workspace, "scripts/massing.txt")


def test_workspace_ruby_reads_persistent_file_then_uses_existing_guarded_executor(tmp_path):
    workspace = prepare_codex_parity_workspace(tmp_path / "agent_workspace")
    source = "root.name = 'Persistent project script'\n"
    (workspace / "scripts" / "scheme.rb").write_text(source, encoding="utf-8")

    class FakeExecutor:
        def __init__(self):
            self.arguments = None

        def run(self, arguments):
            self.arguments = arguments
            return {"success": True}

    executor = FakeExecutor()
    result = run_workspace_ruby(
        executor,  # type: ignore[arg-type]
        agent_workspace=workspace,
        arguments={"script_id": "scheme", "relative_path": "scripts/scheme.rb"},
    )
    assert result["success"] is True
    assert executor.arguments == {"script_id": "scheme", "ruby_source": source, "update_mode": "replace"}
    run_workspace_ruby(executor, agent_workspace=workspace,
                       arguments={"script_id": "scheme", "relative_path": "scripts/scheme.rb", "update_mode": "edit"})
    assert executor.arguments["update_mode"] == "edit"


def test_agent_tool_surface_exposes_workspace_file_execution_when_ruby_enabled(tmp_path):
    class ToolClient:
        def list_tools(self):
            return [
                {"name": "sketchup_health", "description": "health", "inputSchema": {"type": "object", "properties": {}}},
                {"name": "sketchup_eval_project_file", "description": "raw eval", "inputSchema": {"type": "object", "properties": {}}},
            ]

    surface = AgentToolSurface(tmp_path / "runtime", ToolClient(), oss_backends={})  # type: ignore[arg-type]
    names = [item["name"] for item in surface.dynamic_tools(ruby_enabled=True)]

    assert "sketchup_health" in names
    assert "sketchup_eval_project_file" not in names
    assert "sketchup_run_workspace_ruby" in names
    assert "sketchup_run_project_ruby" in names
    ruby_tool = next(t for t in surface.dynamic_tools(ruby_enabled=True)
                     if t["name"] == "sketchup_run_workspace_ruby")
    assert "root.entities" in ruby_tool["description"]
    assert "host-owned transaction" in ruby_tool["description"]
    assert "Do not redefine root" in ruby_tool["description"]


def test_project_ruby_edit_retains_root_and_empty_root_is_rejected(tmp_path):
    from app.project_ruby import ProjectRubyExecutor
    executor = object.__new__(ProjectRubyExecutor)
    executor.expected_model_path = tmp_path / "blank-disposable.skp"
    executor.expected_model_guid = "snapshot"
    executor.project_id = "test-project"
    paths = (tmp_path / "source.rb", tmp_path / "report.json", 2, 123)
    replace = executor._build_transport_script(*paths)
    edit = executor._build_transport_script(*paths, update_mode="edit")
    assert "root.entities.to_a.each { |entity| entity.erase! }" in replace
    assert "root.entities.to_a.each { |entity| entity.erase! }" not in edit
    assert "remove_owned_group = lambda do |name|" in edit
    assert "KStudioProfessionalHelpers.remove_named_owned_group(root, name)" in edit
    assert "saie_wall_with_openings = lambda" in edit
    assert "KStudioProfessionalHelpers.wall_with_openings(root, params)" in edit
    helper = (Path(__file__).parents[1] / "app/adopted_sketchup_helpers.rb").read_text(encoding="utf-8")
    assert "matches.length == 1" in helper
    assert "current.locked?" in helper
    assert "entities.select" in helper
    from app.project_ruby import validate_project_ruby_source
    assert validate_project_ruby_source("main", "remove_owned_group.call('Balcony')")
    helper = Path("app/vendor/sketchup_architect/scripts/model_session.rb").read_text(encoding="utf-8")
    assert "if root.entities.length.zero?" in helper
    assert "unless has_geometry?(root.entities)" in helper
    assert "seen[definition.object_id]" in helper
    assert helper.index("committed_root_pid = root.persistent_id") < helper.index("unless model.commit_operation")


def test_workspace_facade_schedule_json_is_validated_and_listed(tmp_path):
    import json
    from app.workspace_files import workspace_file_call

    workspace = prepare_codex_parity_workspace(tmp_path / "workspace-json")
    result = workspace_file_call(workspace, "workspace_write", {
        "relative_path": "notes/facade_schedule.json",
        "content": json.dumps({
            "schema_version": 1,
            "views": {"front": {"opening_count": 4, "provenance": "observed"}},
            "user_confirmed": ["rear has three windows"],
        }),
    })
    assert result["success"] is True
    listing = workspace_file_call(workspace, "workspace_read", {"relative_path": "notes/"})
    assert "notes/facade_schedule.json" in listing["files"]
    loaded = json.loads(workspace_file_call(
        workspace, "workspace_read", {"relative_path": "notes/facade_schedule.json"}
    )["content"])
    assert loaded["views"]["front"]["opening_count"] == 4
    assert loaded["views"]["front"]["provenance"] == "observed"

    with pytest.raises(ValueError, match="valid JSON"):
        workspace_file_call(workspace, "workspace_write", {
            "relative_path": "notes/facade_schedule.json",
            "content": "{broken",
        })
    with pytest.raises(ValueError, match="root must be an object"):
        workspace_file_call(workspace, "workspace_write", {
            "relative_path": "notes/facade_schedule.json",
            "content": "[]",
        })
