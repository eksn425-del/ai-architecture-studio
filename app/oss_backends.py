from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_BLOCKED_TOOLS = frozenset({
    "execute_ruby",
    "clear_model",
    "new_file",
    "open_file",
    "save_file",
    "save_as",
    "create_project",
    "set_active_project",
})


def _truthy_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _content_item(part: Any) -> dict[str, str] | None:
    if hasattr(part, "model_dump"):
        value = part.model_dump(exclude_none=True, by_alias=True)
    elif isinstance(part, dict):
        value = part
    else:
        value = {
            "type": getattr(part, "type", ""),
            "text": getattr(part, "text", None),
            "data": getattr(part, "data", None),
            "mimeType": getattr(part, "mimeType", getattr(part, "mime_type", None)),
        }
    kind = str(value.get("type") or "")
    if kind == "text" and isinstance(value.get("text"), str):
        return {"type": "inputText", "text": value["text"]}
    if kind == "image" and isinstance(value.get("data"), str):
        mime_type = str(value.get("mimeType") or value.get("mime_type") or "image/png")
        return {"type": "inputImage", "imageUrl": f"data:{mime_type};base64,{value['data']}"}
    resource = value.get("resource")
    if kind == "resource" and isinstance(resource, dict) and isinstance(resource.get("text"), str):
        return {"type": "inputText", "text": resource["text"]}
    return None


@dataclass
class SdkStdioMCPBackend:
    """Thin adapter around the official MCP Python SDK.

    This does not reimplement an OSS SketchUp engine. It launches an already
    installed MCP server (for example SAIE's ``saie-mcp``) and converts its
    standard tool schemas/results into the dynamic-tool shape already used by
    AI Architecture Studio.
    """

    backend_id: str
    command: str
    args: tuple[str, ...] = ()
    env: dict[str, str] | None = None
    blocked_tools: frozenset[str] = DEFAULT_BLOCKED_TOOLS

    @property
    def available(self) -> bool:
        command_available = bool(shutil.which(self.command) or os.path.isfile(self.command))
        try:
            sdk_available = importlib.util.find_spec("mcp") is not None
        except (ImportError, ValueError):
            sdk_available = False
        return command_available and sdk_available

    async def _list_tools_async(self) -> list[dict[str, Any]]:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=self.command, args=list(self.args), env=self.env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
        tools: list[dict[str, Any]] = []
        for tool in result.tools:
            if hasattr(tool, "model_dump"):
                value = tool.model_dump(exclude_none=True, by_alias=True)
            elif isinstance(tool, dict):
                value = tool
            else:
                value = {}
            name = getattr(tool, "name", None) or value.get("name")
            schema = (
                getattr(tool, "inputSchema", None)
                or getattr(tool, "input_schema", None)
                or value.get("inputSchema")
                or value.get("input_schema")
            )
            description = getattr(tool, "description", None) or value.get("description")
            if not isinstance(name, str) or name in self.blocked_tools or not isinstance(schema, dict):
                continue
            tools.append({
                "name": name,
                "description": str(description or f"{self.backend_id} tool {name}"),
                "inputSchema": schema,
            })
        return tools

    def list_tools(self) -> list[dict[str, Any]]:
        if not self.available:
            return []
        return asyncio.run(self._list_tools_async())

    async def _call_tool_async(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=self.command, args=list(self.args), env=self.env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
        content_items = [item for part in result.content if (item := _content_item(part)) is not None]
        is_error = bool(getattr(result, "isError", getattr(result, "is_error", False)))
        return {"success": not is_error, "isError": is_error, "contentItems": content_items}

    def call_for_agent(self, name: str, arguments: dict[str, Any], *,
                       project_dir: Path | None = None) -> dict[str, Any]:
        del project_dir
        if name in self.blocked_tools:
            raise ValueError(f"{self.backend_id} tool {name!r} is blocked by the website lifecycle boundary.")
        if not self.available:
            raise RuntimeError(f"Optional OSS backend {self.backend_id!r} is not installed or its MCP SDK is unavailable.")
        return asyncio.run(self._call_tool_async(name, arguments))


@dataclass
class ArchFlowCLIBackend:
    """Directly adopt ArchFlow's CLI/pipeline rather than rebuilding semantic CAD.

    ArchFlow remains an external Apache-2.0 checkout/package. The adapter only
    allows manifests stored inside the generated agent workspace, so its immutable
    run outputs cannot write back into taskbook/site/reference inputs.
    """

    backend_id: str = "archflow"
    command: str = ""
    core_skill: str = ""
    timeout_seconds: int = 300

    def __post_init__(self) -> None:
        if not self.command:
            configured = os.environ.get("ARCH_STUDIO_ARCHFLOW_COMMAND", "").strip()
            sibling = Path(sys.executable).resolve().parent / ("archflow.exe" if os.name == "nt" else "archflow")
            self.command = configured or (str(sibling) if sibling.is_file() else (shutil.which("archflow") or "archflow"))
        if not self.core_skill:
            self.core_skill = os.environ.get("ARCHFLOW_CORE_SKILL", "").strip()

    @property
    def available(self) -> bool:
        return bool(shutil.which(self.command) or os.path.isfile(self.command))

    def list_tools(self) -> list[dict[str, Any]]:
        if not self.available:
            return []
        manifest_schema = {
            "type": "object",
            "required": ["manifest"],
            "properties": {
                "manifest": {
                    "type": "string",
                    "description": "Path relative to runtime/agent_workspace, usually archflow.project.json.",
                },
            },
            "additionalProperties": False,
        }
        run_schema = {
            "type": "object",
            "required": ["manifest", "stage"],
            "properties": {
                "manifest": {"type": "string"},
                "stage": {"type": "string", "enum": ["parse", "validate", "build"]},
            },
            "additionalProperties": False,
        }
        return [
            {
                "name": "doctor",
                "description": "Run upstream ArchFlow doctor and report whether semantic CAD/SketchUp generation capabilities are installed.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "check_project",
                "description": "Use upstream ArchFlow to validate a project manifest and its referenced files.",
                "inputSchema": manifest_schema,
            },
            {
                "name": "plan_run",
                "description": "Ask upstream ArchFlow for an immutable parse/validate/build plan without executing it.",
                "inputSchema": run_schema,
            },
            {
                "name": "run",
                "description": "Run upstream ArchFlow inside the generated agent workspace to produce deterministic semantic validation/DXF/Ruby/review artifacts. It does not execute SketchUp in ArchFlow manifest schema 0.1.",
                "inputSchema": run_schema,
            },
        ]

    @staticmethod
    def _workspace(project_dir: Path) -> Path:
        workspace = (project_dir.resolve() / "runtime" / "agent_workspace").resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        if not workspace.is_relative_to(project_dir.resolve()) or workspace.is_symlink():
            raise ValueError("ArchFlow workspace resolved outside the generated project runtime.")
        return workspace

    def _manifest(self, project_dir: Path, value: Any) -> Path:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("ArchFlow manifest must be a non-empty relative path.")
        relative = Path(value)
        if relative.is_absolute():
            raise ValueError("ArchFlow manifest must be relative to the generated agent workspace.")
        workspace = self._workspace(project_dir)
        manifest = (workspace / relative).resolve()
        if not manifest.is_relative_to(workspace) or manifest.is_symlink():
            raise ValueError("ArchFlow manifest escaped the generated agent workspace.")
        if not manifest.is_file():
            raise ValueError(f"ArchFlow manifest does not exist: {relative.as_posix()}")
        # ArchFlow itself validates every manifest path as relative to manifest root.
        # We additionally reject any manifest that asks ArchFlow to execute SketchUp.
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"ArchFlow manifest is invalid JSON: {error}") from error
        pipeline = payload.get("pipeline") if isinstance(payload, dict) else None
        if isinstance(pipeline, dict) and pipeline.get("execute_sketchup", False) is not False:
            raise ValueError("ArchFlow manifest pipeline.execute_sketchup must remain false.")
        return manifest

    def _run(self, args: list[str], *, workspace: Path) -> dict[str, Any]:
        env = os.environ.copy()
        if self.core_skill:
            env["ARCHFLOW_CORE_SKILL"] = self.core_skill
        completed = subprocess.run(
            [self.command, *args], cwd=workspace, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=self.timeout_seconds, check=False,
        )
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        content = stdout[-60_000:] if stdout else stderr[-60_000:]
        return {
            "success": completed.returncode == 0,
            "isError": completed.returncode != 0,
            "contentItems": [{"type": "inputText", "text": content or f"ArchFlow exited {completed.returncode}."}],
        }

    def call_for_agent(self, name: str, arguments: dict[str, Any], *,
                       project_dir: Path | None = None) -> dict[str, Any]:
        if project_dir is None:
            raise ValueError("ArchFlow requires a project directory.")
        if not self.available:
            raise RuntimeError("ArchFlow CLI is not installed in the project environment.")
        workspace = self._workspace(project_dir)
        if name == "doctor":
            return self._run(["doctor", "--json"], workspace=workspace)
        manifest = self._manifest(project_dir, arguments.get("manifest"))
        if name == "check_project":
            return self._run(["check", str(manifest)], workspace=workspace)
        stage = str(arguments.get("stage") or "")
        if stage not in {"parse", "validate", "build"}:
            raise ValueError("ArchFlow stage must be parse, validate, or build.")
        command = ["run", str(manifest), "--stage", stage]
        if name == "plan_run":
            command.append("--plan")
        elif name != "run":
            raise ValueError(f"Unknown ArchFlow tool: {name}")
        return self._run(command, workspace=workspace)


def discover_oss_backends() -> dict[str, Any]:
    """Discover explicitly enabled reusable OSS execution backends."""
    backends: dict[str, Any] = {}
    if _truthy_env("ARCH_STUDIO_ENABLE_SAIE"):
        command = os.environ.get("ARCH_STUDIO_SAIE_COMMAND", "saie-mcp").strip() or "saie-mcp"
        args = tuple(shlex.split(os.environ.get("ARCH_STUDIO_SAIE_ARGS", ""), posix=os.name != "nt"))
        backend = SdkStdioMCPBackend("saie", command, args)
        if backend.available:
            backends[backend.backend_id] = backend
    if _truthy_env("ARCH_STUDIO_ENABLE_ARCHFLOW"):
        backend = ArchFlowCLIBackend()
        if backend.available:
            backends[backend.backend_id] = backend
    return backends
