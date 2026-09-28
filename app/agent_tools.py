from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .oss_backends import discover_oss_backends
from .project_ruby import ProjectRubyExecutor
from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError


@dataclass
class AgentToolContext:
    """The shared project-scoped SketchUp tool surface used by every model provider."""

    dynamic_tools: list[dict[str, Any]]
    dispatch: Callable[[str, dict[str, Any]], dict[str, Any]]


class AgentToolSurface:
    """Compose the existing Kongxing bridge with reusable OSS execution engines.

    Kongxing remains the verified model-identity/lifecycle bridge. Optional OSS
    backends (currently SAIE when explicitly enabled) contribute mature modeling,
    query, BIM and view tools under a namespaced dynamic-tool surface rather than
    being reimplemented here.
    """

    def __init__(self, runtime_root: Path, sketchup_mcp: ConfiguredSketchUpMCP,
                 oss_backends: dict[str, Any] | None = None):
        self.runtime_root = runtime_root.resolve()
        self.sketchup_mcp = sketchup_mcp
        self.oss_backends = discover_oss_backends() if oss_backends is None else dict(oss_backends)

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

    @staticmethod
    def _dynamic_tool(name: str, description: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "function",
            "name": name,
            "description": description,
            "inputSchema": schema,
        }

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
            tools.append(self._dynamic_tool(
                name,
                str(item.get("description") or f"Call the existing Kongxing SketchUp MCP tool {name}."),
                schema,
            ))

        # Mature OSS engines are namespaced so their semantic operations can live
        # beside the existing connector without collisions. They are optional:
        # local Codex must first install/verify the upstream plugin on the user's
        # actual SketchUp version before ARCH_STUDIO_ENABLE_SAIE is enabled.
        for backend_id, backend in sorted(self.oss_backends.items()):
            try:
                backend_tools = backend.list_tools()
            except Exception:
                # An optional backend must never break the already-working local
                # connector. Local diagnostics can inspect the backend separately.
                continue
            for item in backend_tools:
                raw_name = item.get("name")
                schema = item.get("inputSchema")
                if not isinstance(raw_name, str) or not isinstance(schema, dict):
                    continue
                public_name = f"{backend_id}__{raw_name}"
                if public_name in seen:
                    continue
                seen.add(public_name)
                description = str(item.get("description") or raw_name)
                tools.append(self._dynamic_tool(
                    public_name,
                    f"[{backend_id} reusable OSS backend] {description}",
                    schema,
                ))

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
            raise RuntimeError("The configured SketchUp tool stack returned no callable schemas.")
        return tools

    def dispatch(self, name: str, arguments: dict[str, Any], *, project_dir: Path,
                 project_ruby: ProjectRubyExecutor | None) -> dict[str, Any]:
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
                return backend.call_for_agent(raw_name, arguments)
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
