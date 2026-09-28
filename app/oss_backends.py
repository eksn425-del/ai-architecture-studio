from __future__ import annotations

import asyncio
import importlib.util
import os
import shlex
import shutil
from dataclasses import dataclass
from typing import Any


# These tools can change/open/save the whole SketchUp document or bypass the
# product-owned execution boundary. The website already owns model lifecycle and
# provides guarded project Ruby separately, so imported OSS backends expose their
# modeling/query surface but not these host-level operations.
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

        params = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env,
        )
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

        params = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
        content_items = [item for part in result.content if (item := _content_item(part)) is not None]
        is_error = bool(getattr(result, "isError", getattr(result, "is_error", False)))
        return {
            "success": not is_error,
            "isError": is_error,
            "contentItems": content_items,
        }

    def call_for_agent(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name in self.blocked_tools:
            raise ValueError(f"{self.backend_id} tool {name!r} is blocked by the website lifecycle boundary.")
        if not self.available:
            raise RuntimeError(f"Optional OSS backend {self.backend_id!r} is not installed or its MCP SDK is unavailable.")
        return asyncio.run(self._call_tool_async(name, arguments))


def discover_oss_backends() -> dict[str, SdkStdioMCPBackend]:
    """Discover explicitly enabled reusable OSS execution backends.

    SAIE stays opt-in because its current upstream targets SketchUp 2025 and the
    user's local workstation/version must be checked before enabling it. No paid
    model call is needed for this discovery step.
    """
    backends: dict[str, SdkStdioMCPBackend] = {}
    if _truthy_env("ARCH_STUDIO_ENABLE_SAIE"):
        command = os.environ.get("ARCH_STUDIO_SAIE_COMMAND", "saie-mcp").strip() or "saie-mcp"
        args = tuple(shlex.split(os.environ.get("ARCH_STUDIO_SAIE_ARGS", ""), posix=os.name != "nt"))
        backend = SdkStdioMCPBackend("saie", command, args)
        if backend.available:
            backends[backend.backend_id] = backend
    return backends
