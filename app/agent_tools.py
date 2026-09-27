from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .project_ruby import ProjectRubyExecutor
from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError


@dataclass
class AgentToolContext:
    """The shared project-scoped SketchUp tool surface used by every model provider."""

    dynamic_tools: list[dict[str, Any]]
    dispatch: Callable[[str, dict[str, Any]], dict[str, Any]]


class AgentToolSurface:
    def __init__(self, runtime_root: Path, sketchup_mcp: ConfiguredSketchUpMCP):
        self.runtime_root = runtime_root.resolve()
        self.sketchup_mcp = sketchup_mcp

    def prepare(self, *, project_dir: Path, mcp_enabled: bool, model_path: Path | None,
                model_guid: str, ruby_enabled: bool,
                ruby_state: dict[str, dict[str, Any]] | None) -> AgentToolContext:
        executor = None
        if mcp_enabled and ruby_enabled:
            if model_path is None or not model_guid:
                raise ValueError("The guarded project Ruby tool requires a verified disposable model path and GUID.")
            executor = ProjectRubyExecutor(
                self.runtime_root, project_dir.name, expected_model_path=model_path,
                expected_model_guid=model_guid, mcp=self.sketchup_mcp, ruby_state=ruby_state,
            )
        dynamic_tools = self.dynamic_tools(ruby_enabled=executor is not None) if mcp_enabled else []
        resolved_project_dir = project_dir.resolve()
        return AgentToolContext(
            dynamic_tools=dynamic_tools,
            dispatch=lambda name, arguments: self.dispatch(
                name, arguments, project_dir=resolved_project_dir, project_ruby=executor,
            ),
        )

    def dynamic_tools(self, *, ruby_enabled: bool = False) -> list[dict[str, Any]]:
        try:
            discovered = self.sketchup_mcp.list_tools()
        except (ConnectorUnavailable, MCPCallError) as error:
            raise RuntimeError(f"The configured Kongxing SketchUp MCP could not list its tools: {error}") from error
        tools: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in discovered:
            name = item.get("name")
            schema = item.get("inputSchema")
            if not isinstance(name, str) or not isinstance(schema, dict) or name in seen:
                continue
            # The connector's raw path-taking eval endpoint is host infrastructure,
            # never a model-facing tool. Project Ruby is exposed through the guard below.
            if name == "sketchup_eval_project_file" or name.startswith("archflow_"):
                continue
            seen.add(name)
            tools.append({
                "type": "function",
                "name": name,
                "description": str(item.get("description") or f"Call the existing Kongxing SketchUp MCP tool {name}."),
                "inputSchema": schema,
            })
        if ruby_enabled:
            tools.append({
                "type": "function",
                "name": "sketchup_run_project_ruby",
                "description": (
                    "Run task-specific Ruby source inside SketchUp on this verified disposable project model. "
                    "Source is stored only in the ignored project runtime. Use the same script_id to revise the existing script/model; "
                    "each revision replaces geometry only inside this script's owned project root and returns transaction readback plus a screenshot. "
                    "The source must use the supplied local variables model and root. Do not access files, processes, network, reflection, other models, or whole-model edit/save APIs."
                ),
                "inputSchema": {
                    "type": "object",
                    "required": ["script_id", "ruby_source"],
                    "properties": {
                        "script_id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,47}$"},
                        "ruby_source": {"type": "string", "maxLength": 120000},
                    },
                    "additionalProperties": False,
                },
            })
        if not tools:
            raise RuntimeError("The configured Kongxing SketchUp MCP returned no callable tool schemas.")
        return tools

    def dispatch(self, name: str, arguments: dict[str, Any], *, project_dir: Path,
                 project_ruby: ProjectRubyExecutor | None) -> dict[str, Any]:
        if name == "sketchup_run_project_ruby":
            if project_ruby is None:
                raise MCPCallError("The project Ruby tool is not enabled for this session.")
            return project_ruby.run(arguments)
        if name == "sketchup_export_view_image":
            output_path = project_dir / "outputs" / "renders" / f"agent-view-{uuid.uuid4().hex[:10]}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            safe_arguments = dict(arguments)
            safe_arguments["output_path"] = str(output_path.resolve())
            try:
                result = self.sketchup_mcp.call_for_agent(name, safe_arguments)
            finally:
                if project_ruby is not None:
                    project_ruby.refresh_active_model_snapshot()
            if output_path.is_file() and output_path.stat().st_size <= 8 * 1024 * 1024:
                result.setdefault("contentItems", []).append({
                    "type": "inputImage",
                    "imageUrl": "data:image/png;base64," + base64.b64encode(output_path.read_bytes()).decode("ascii"),
                })
            return result
        try:
            result = self.sketchup_mcp.call_for_agent(name, arguments)
        finally:
            if project_ruby is not None:
                project_ruby.refresh_active_model_snapshot()
        return result
