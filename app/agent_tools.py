from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from .codex_parity import prepare_codex_parity_workspace
from .oss_backends import discover_oss_backends
from .project_ruby import ProjectRubyExecutor
from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError
from .workspace_ruby import run_workspace_ruby
from .workspace_files import workspace_file_tools, workspace_file_call


ToolProfile = Literal["full", "reconstruction_coding"]

_RECONSTRUCTION_KONGXING_KEYWORDS = (
    "health", "context", "inspect", "select", "view", "camera", "undo", "transform",
)
_RECONSTRUCTION_SAIE_TOOLS = {
    "scene_summary",
    "inspect_entity",
    "verify_model",
    "view_snapshot",
    "capture_canonical",
    "deep_scan",
    "export_model_json",
    "create_wall",
    "modify_wall",
    "delete_wall",
    "cut_opening",
    "modify_opening",
    "delete_opening",
    "create_slab",
    "create_roof",
    "batch_operations",
}


@dataclass
class AgentToolContext:
    """The shared project-scoped SketchUp tool surface used by every model provider."""

    dynamic_tools: list[dict[str, Any]]
    dispatch: Callable[[str, dict[str, Any]], dict[str, Any]]


class AgentToolSurface:
    """Compose the existing SketchUp bridge with reusable OSS execution engines.

    ``full`` preserves the broad architecture tool surface.
    ``reconstruction_coding`` intentionally keeps a much smaller Direct-Codex-like
    surface: persistent Ruby is primary, the connector handles view/readback/lifecycle,
    and selected SAIE semantic tools remain available as helpers. This prevents a cheap
    model from spending its context choosing among dozens of overlapping operations.
    """

    def __init__(self, runtime_root: Path, sketchup_mcp: ConfiguredSketchUpMCP,
                 oss_backends: dict[str, Any] | None = None):
        self.runtime_root = runtime_root.resolve()
        self.sketchup_mcp = sketchup_mcp
        self.oss_backends = discover_oss_backends() if oss_backends is None else dict(oss_backends)

    def prepare(self, *, project_dir: Path, mcp_enabled: bool, model_path: Path | None,
                model_guid: str, ruby_enabled: bool,
                ruby_state: dict[str, dict[str, Any]] | None,
                tool_profile: ToolProfile = "full", workspace_tools_enabled: bool = False) -> AgentToolContext:
        resolved_project_dir = project_dir.resolve()
        prepare_codex_parity_workspace(resolved_project_dir / "runtime" / "agent_workspace")

        executor = None
        if mcp_enabled and ruby_enabled:
            if model_path is None or not model_guid:
                raise ValueError("The guarded project Ruby tool requires a verified disposable model path and GUID.")
            executor = ProjectRubyExecutor(
                self.runtime_root, project_dir.name, expected_model_path=model_path,
                expected_model_guid=model_guid, mcp=self.sketchup_mcp, ruby_state=ruby_state,
            )
        dynamic_tools = self.dynamic_tools(
            ruby_enabled=executor is not None,
            tool_profile=tool_profile,
        ) if mcp_enabled else []
        if workspace_tools_enabled:
            dynamic_tools.extend(workspace_file_tools())
        return AgentToolContext(
            dynamic_tools=dynamic_tools,
            dispatch=lambda name, arguments: workspace_file_call(
                resolved_project_dir / "runtime" / "agent_workspace", name, arguments,
            ) if workspace_tools_enabled and name in {"workspace_read", "workspace_write"} else self.dispatch(
                name, arguments, project_dir=resolved_project_dir, project_ruby=executor,
            ),
        )

    @staticmethod
    def _dynamic_tool(name: str, description: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {"type": "function", "name": name, "description": description, "inputSchema": schema}

    @staticmethod
    def _allow_kongxing(name: str, tool_profile: ToolProfile) -> bool:
        if tool_profile == "full":
            return True
        folded = name.casefold()
        if name in {"sketchup_eval_project_file", "sketchup_create_mass", "sketchup_create_road"}:
            return False
        return any(keyword in folded for keyword in _RECONSTRUCTION_KONGXING_KEYWORDS)

    @staticmethod
    def _allow_backend_tool(backend_id: str, raw_name: str, tool_profile: ToolProfile) -> bool:
        if tool_profile == "full":
            return True
        if backend_id == "saie":
            return raw_name in _RECONSTRUCTION_SAIE_TOOLS
        # ArchFlow and other broad backends are useful later, but they add noise to
        # the single-image reconstruction loop and are therefore hidden here.
        return False

    def dynamic_tools(self, *, ruby_enabled: bool = False,
                      tool_profile: ToolProfile = "full") -> list[dict[str, Any]]:
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
            if name == "sketchup_eval_project_file" or name.startswith("archflow_"):
                continue
            if not self._allow_kongxing(name, tool_profile):
                continue
            seen.add(name)
            tools.append(self._dynamic_tool(
                name,
                str(item.get("description") or f"Call the existing Kongxing SketchUp MCP tool {name}."),
                schema,
            ))

        for backend_id, backend in sorted(self.oss_backends.items()):
            try:
                backend_tools = backend.list_tools()
            except Exception:
                # Optional reuse must never break the already-working Kongxing-only path.
                continue
            for item in backend_tools:
                raw_name = item.get("name")
                schema = item.get("inputSchema")
                if not isinstance(raw_name, str) or not isinstance(schema, dict):
                    continue
                if not self._allow_backend_tool(backend_id, raw_name, tool_profile):
                    continue
                public_name = f"{backend_id}__{raw_name}"
                if public_name in seen:
                    continue
                seen.add(public_name)
                tools.append(self._dynamic_tool(
                    public_name,
                    f"[{backend_id} reusable OSS helper] {str(item.get('description') or raw_name)}",
                    schema,
                ))

        if ruby_enabled:
            tools.append({
                "type": "function",
                "name": "sketchup_run_workspace_ruby",
                "description": (
                    "PRIMARY project-specific modeling tool. Execute a persistent Ruby file authored under "
                    "agent_workspace/scripts. For image reconstruction, prefer this for repeated/custom geometry, "
                    "components, facade systems, canopies, louvers and other source-specific work. Revise and rerun the "
                    "same file so the project keeps an inspectable coding history. The guarded transaction returns "
                    "model readback plus a screenshot. update_mode=replace (default) CLEARS the owned root before running "
                    "the complete reconstruction script. update_mode=edit retains that existing script_id root for "
                    "incremental corrections. Never use replace with inspection-only or partial patch code; use readback "
                    "tools for inspection. edit requires the same existing script_id."
                ),
                "inputSchema": {
                    "type": "object",
                    "required": ["script_id", "relative_path"],
                    "properties": {
                        "script_id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,47}$"},
                        "relative_path": {"type": "string", "pattern": "^scripts/[A-Za-z0-9_.-]+\\.rb$", "maxLength": 160},
                        "update_mode": {"type": "string", "enum": ["replace", "edit"], "default": "replace"},
                    },
                    "additionalProperties": False,
                },
            })
            if tool_profile == "full":
                tools.append({
                    "type": "function",
                    "name": "sketchup_run_project_ruby",
                    "description": (
                        "Run a short task-specific Ruby snippet inside SketchUp on this verified disposable project model. "
                        "For non-trivial or revisable work prefer sketchup_run_workspace_ruby. Source is stored only in the "
                        "ignored project runtime. Use the same script_id to revise the existing script/model."
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
            raise RuntimeError("The configured SketchUp tool stack returned no callable schemas.")
        return tools

    def dispatch(self, name: str, arguments: dict[str, Any], *, project_dir: Path,
                 project_ruby: ProjectRubyExecutor | None) -> dict[str, Any]:
        if name == "sketchup_run_workspace_ruby":
            if project_ruby is None:
                raise MCPCallError("The workspace Ruby tool is not enabled for this session.")
            return run_workspace_ruby(
                project_ruby,
                agent_workspace=project_dir / "runtime" / "agent_workspace",
                arguments=arguments,
            )

        if name == "sketchup_run_project_ruby":
            if project_ruby is None:
                raise MCPCallError("The project Ruby tool is not enabled for this session.")
            return project_ruby.run(arguments)

        if "__" in name:
            backend_id, raw_name = name.split("__", 1)
            backend = self.oss_backends.get(backend_id)
            if backend is None:
                raise MCPCallError(f"Optional OSS backend {backend_id!r} is not active for this session.")
            try:
                return backend.call_for_agent(raw_name, arguments, project_dir=project_dir)
            finally:
                if project_ruby is not None:
                    project_ruby.refresh_active_model_snapshot()

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
