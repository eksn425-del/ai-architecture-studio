import json
import sys
from pathlib import Path

import pytest

from app.agent_tools import AgentToolSurface
from app.architecture_skill import load_architecture_skill_context
from app.native_agent import _agent_workspace, _composed_tool_instructions, _workspace_write_policy
from app.oss_backends import ArchFlowCLIBackend, DEFAULT_BLOCKED_TOOLS, SdkStdioMCPBackend


class FakeKongxing:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [{
            "name": "sketchup_health",
            "description": "Read bridge health.",
            "inputSchema": {"type": "object", "properties": {}},
        }]

    def call_for_agent(self, name, arguments):
        self.calls.append((name, arguments))
        return {"success": True, "contentItems": []}


class FakeSaie:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [
            {
                "name": "create_wall",
                "description": "Create a wall with stable AI identity.",
                "inputSchema": {
                    "type": "object",
                    "required": ["ai_id"],
                    "properties": {"ai_id": {"type": "string"}},
                },
            },
            {
                "name": "view_snapshot",
                "description": "Return a current SketchUp image.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def call_for_agent(self, name, arguments, *, project_dir=None):
        self.calls.append((name, arguments, project_dir))
        return {"success": True, "contentItems": [{"type": "inputText", "text": name}]}


def test_agent_surface_composes_namespaced_oss_tools(tmp_path: Path) -> None:
    kongxing = FakeKongxing()
    saie = FakeSaie()
    surface = AgentToolSurface(tmp_path, kongxing, oss_backends={"saie": saie})

    tools = surface.dynamic_tools(ruby_enabled=False)
    names = {tool["name"] for tool in tools}

    assert "sketchup_health" in names
    assert "saie__create_wall" in names
    assert "saie__view_snapshot" in names
    assert next(tool for tool in tools if tool["name"] == "saie__create_wall")["inputSchema"]["required"] == ["ai_id"]


def test_agent_surface_dispatches_oss_tool_without_reimplementing_it(tmp_path: Path) -> None:
    kongxing = FakeKongxing()
    saie = FakeSaie()
    surface = AgentToolSurface(tmp_path, kongxing, oss_backends={"saie": saie})

    result = surface.dispatch(
        "saie__create_wall",
        {"ai_id": "wall-a"},
        project_dir=tmp_path,
        project_ruby=None,
    )

    assert saie.calls == [("create_wall", {"ai_id": "wall-a"}, tmp_path.resolve())]
    assert result["success"] is True
    assert kongxing.calls == []


def test_saie_lifecycle_and_raw_ruby_tools_are_blocked_by_default() -> None:
    assert {"execute_ruby", "clear_model", "open_file", "save_as"}.issubset(DEFAULT_BLOCKED_TOOLS)
    backend = SdkStdioMCPBackend("saie", "definitely-not-installed-saie-mcp")
    assert backend.available is False


def test_architecture_context_allows_user_requested_strong_precedent_adaptation() -> None:
    context = load_architecture_skill_context()
    assert "User-controlled precedent fidelity" in context
    assert "strong adaptation" in context
    assert "Do not flatten a requested strong-form reference into generic boxes" in context


def test_architecture_context_prefers_mature_oss_tools_before_project_ruby() -> None:
    context = load_architecture_skill_context()
    assert "Execution-tool preference" in context
    assert "saie__" in context
    assert "guarded project Ruby" in context


def test_agent_workspace_is_nested_under_generated_project_runtime(tmp_path: Path) -> None:
    project = tmp_path / "runtime" / "projects" / "demo"
    (project / "inputs" / "brief").mkdir(parents=True)
    source = project / "inputs" / "brief" / "taskbook.txt"
    source.write_text("private source input", encoding="utf-8")

    workspace = _agent_workspace(project)

    assert workspace == (project / "runtime" / "agent_workspace").resolve()
    assert workspace.is_dir()
    assert not source.is_relative_to(workspace)


def test_workspace_write_policy_allows_only_agent_workspace_and_no_network(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    workspace = _agent_workspace(project)

    policy = _workspace_write_policy(workspace)

    assert policy == {
        "type": "workspaceWrite",
        "writableRoots": [str(workspace.resolve())],
        "networkAccess": False,
        "excludeTmpdirEnvVar": True,
        "excludeSlashTmp": True,
    }
    assert str((project / "inputs").resolve()) not in policy["writableRoots"]


def test_composed_tool_override_supersedes_legacy_kongxing_only_instruction() -> None:
    legacy = "Use only the whitelisted kongxing_sketchup MCP."
    effective = _composed_tool_instructions(legacy, mcp_enabled=True)

    assert legacy in effective
    assert "dynamic tools supplied on this turn are the authoritative" in effective
    assert "saie__* are allowed" in effective
    assert "mature semantic OSS tools first" in effective
    assert _composed_tool_instructions(legacy, mcp_enabled=False) == legacy


def test_archflow_backend_exposes_upstream_semantic_pipeline_tools(tmp_path: Path) -> None:
    backend = ArchFlowCLIBackend(command=sys.executable)
    names = {tool["name"] for tool in backend.list_tools()}

    assert {"doctor", "check_project", "plan_run", "run"}.issubset(names)

    project = tmp_path / "projects" / "demo"
    workspace = project / "runtime" / "agent_workspace"
    workspace.mkdir(parents=True)
    manifest = workspace / "archflow.project.json"
    manifest.write_text(json.dumps({
        "schema_version": "0.1",
        "project": {"id": "demo", "title": "Demo", "mode": "concept"},
        "inputs": {"site_cad": None, "requirements": None, "legal_sources": []},
        "model": {"building_model": "model/building_model.json"},
        "pipeline": {"output_root": "outputs/runs", "execute_sketchup": False, "render_provider": "none"},
    }), encoding="utf-8")

    assert backend._manifest(project, "archflow.project.json") == manifest.resolve()
    with pytest.raises(ValueError, match="relative"):
        backend._manifest(project, str(manifest.resolve()))
    with pytest.raises(ValueError):
        backend._manifest(project, "../outside.json")


def test_archflow_backend_rejects_manifest_that_requests_sketchup_execution(tmp_path: Path) -> None:
    backend = ArchFlowCLIBackend(command=sys.executable)
    project = tmp_path / "projects" / "demo"
    workspace = project / "runtime" / "agent_workspace"
    workspace.mkdir(parents=True)
    manifest = workspace / "unsafe.json"
    manifest.write_text(json.dumps({"pipeline": {"execute_sketchup": True}}), encoding="utf-8")

    with pytest.raises(ValueError, match="execute_sketchup"):
        backend._manifest(project, "unsafe.json")
