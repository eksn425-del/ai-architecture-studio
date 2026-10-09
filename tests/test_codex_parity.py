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
    evidence_file = workspace / "notes" / "reconstruction_evidence.json"
    assert evidence_file.is_file()
    evidence = __import__("json").loads(evidence_file.read_text(encoding="utf-8"))
    assert evidence["schema_version"] == 1
    assert evidence["fidelity_mode"] == "pending"
    strategy_file = workspace / "notes" / "construction_strategy.json"
    assert strategy_file.is_file()
    strategy = __import__("json").loads(strategy_file.read_text(encoding="utf-8"))
    assert strategy["schema_version"] == 1
    assert strategy["stage_order"] == ["primary_form", "representative_module", "replication", "variants", "finish"]
    assert strategy["systems"] == []
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
    evidence_file.write_text(
        '{"schema_version":1,"fidelity_mode":"single_view_inference","primary_source":"inputs/reference/front.png","sources":[{"path":"inputs/reference/front.png","kind":"exterior_image","provenance":"observed"}],"exterior_views":{"oblique":{"provenance":"observed","source_refs":["inputs/reference/front.png"],"notes":[]}},"floorplan":{"provided":false,"provenance":"pending","source_refs":[],"levels":[],"notes":[]},"cad":{"provided":false,"provenance":"pending","source_refs":[],"notes":[]},"interior":{"provided":false,"provenance":"pending","source_refs":[],"spaces":[],"notes":[]},"scale_anchors":[],"hard_constraints":[],"assumptions":[],"inference_policy":{"unseen_exterior":"infer_coherent","unseen_interior":"infer_plausible","preserve_circulation":true}}\n',
        encoding="utf-8",
    )
    strategy_file.write_text(
        '{"schema_version":1,"current_stage":"representative_module","stage_order":["primary_form","representative_module","replication","variants","finish"],"shared_parameters":{"floor_height":{"value":3200,"units":"mm","provenance":"user_confirmed","source":"user"}},"systems":[{"id":"front-wall","stage":"primary_form","role":"opening_system","method":"continuous_wall_with_openings","status":"built","depends_on":["floor_height"],"target_paths":[["SHELL","FRONT_WALL"]],"verification_views":["front","oblique"],"notes":[]}],"notes":[]}\n',
        encoding="utf-8",
    )
    prepare_codex_parity_workspace(workspace)
    assert notes.read_text(encoding="utf-8") == "USER CONFIRMED DECISION\n"
    assert instructions.read_text(encoding="utf-8") == "PROJECT MODELING RULES\n"
    assert visual_qa.read_text(encoding="utf-8") == "CURRENT REVIEW SURVIVES\n"
    assert "rear has three windows" in facade_schedule.read_text(encoding="utf-8")
    assert "single_view_inference" in evidence_file.read_text(encoding="utf-8")
    assert "continuous_wall_with_openings" in strategy_file.read_text(encoding="utf-8")


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

    with pytest.raises(ValueError, match="provenance"):
        workspace_file_call(workspace, "workspace_write", {
            "relative_path": "notes/facade_schedule.json",
            "content": json.dumps({
                "schema_version": 1,
                "views": {
                    "front": {
                        "provenance": "made_up",
                        "opening_count": 4,
                        "door_count": 1,
                        "features": [],
                        "notes": [],
                    }
                },
            }),
        })


def test_workspace_reconstruction_evidence_json_is_validated(tmp_path):
    import json
    from app.reconstruction_evidence import default_reconstruction_evidence
    from app.workspace_files import workspace_file_call

    workspace = prepare_codex_parity_workspace(tmp_path / "workspace-evidence")
    value = default_reconstruction_evidence()
    value["fidelity_mode"] = "single_view_inference"
    value["primary_source"] = "inputs/reference/source.png"
    value["sources"] = [{
        "path": "inputs/reference/source.png",
        "kind": "exterior_image",
        "provenance": "observed",
        "role": "primary",
    }]
    value["exterior_views"]["oblique"] = {
        "provenance": "observed",
        "source_refs": ["inputs/reference/source.png"],
        "notes": [],
    }
    result = workspace_file_call(workspace, "workspace_write", {
        "relative_path": "notes/reconstruction_evidence.json",
        "content": json.dumps(value),
    })
    assert result["success"] is True
    loaded = json.loads(workspace_file_call(
        workspace, "workspace_read", {"relative_path": "notes/reconstruction_evidence.json"}
    )["content"])
    assert loaded["fidelity_mode"] == "single_view_inference"

    broken = default_reconstruction_evidence()
    broken["fidelity_mode"] = "full_evidence_reconstruction"
    with pytest.raises(ValueError, match="requires observed/confirmed"):
        workspace_file_call(workspace, "workspace_write", {
            "relative_path": "notes/reconstruction_evidence.json",
            "content": json.dumps(broken),
        })


def test_workspace_construction_strategy_json_is_validated(tmp_path):
    import json
    from app.workspace_files import workspace_file_call

    workspace = prepare_codex_parity_workspace(tmp_path / "workspace-strategy")
    good = {
        "schema_version": 1,
        "current_stage": "representative_module",
        "stage_order": ["primary_form", "representative_module", "replication", "variants", "finish"],
        "shared_parameters": {
            "floor_height": {
                "value": 3200,
                "units": "mm",
                "provenance": "user_confirmed",
                "source": "user",
            }
        },
        "systems": [{
            "id": "front-openings",
            "stage": "primary_form",
            "role": "opening_system",
            "method": "continuous_wall_with_openings",
            "status": "built",
            "depends_on": ["floor_height"],
            "target_paths": [["SHELL", "FRONT_WALL"]],
            "verification_views": ["front", "oblique"],
            "notes": [],
        }],
        "notes": [],
    }
    result = workspace_file_call(workspace, "workspace_write", {
        "relative_path": "notes/construction_strategy.json",
        "content": json.dumps(good),
    })
    assert result["success"] is True
    loaded = json.loads(workspace_file_call(
        workspace, "workspace_read", {"relative_path": "notes/construction_strategy.json"}
    )["content"])
    assert loaded["systems"][0]["method"] == "continuous_wall_with_openings"

    bad = dict(good)
    bad["systems"] = [dict(good["systems"][0], depends_on=["unknown_parameter"])]
    with pytest.raises(ValueError, match="unknown parameters"):
        workspace_file_call(workspace, "workspace_write", {
            "relative_path": "notes/construction_strategy.json",
            "content": json.dumps(bad),
        })
