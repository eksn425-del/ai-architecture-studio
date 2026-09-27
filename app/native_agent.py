from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError, _toml_load


class NativeAgentUnavailable(RuntimeError):
    pass


@dataclass
class AgentTurnResult:
    thread_id: str
    reply: str
    status: str = "completed"
    tool_calls: list[dict[str, str]] = field(default_factory=list)
    model_name: str = ""


class CodexAppServerRuntime:
    """Runs Codex app-server with a private, Kongxing-only MCP configuration."""

    def __init__(self, runtime_root: Path, *, codex_executable: str | None = None,
                 model: str | None = None, timeout_seconds: int = 300,
                 sketchup_mcp: ConfiguredSketchUpMCP | None = None,
                 home_root: Path | None = None):
        self.runtime_root = runtime_root.resolve()
        self.codex_executable = codex_executable or os.environ.get("CODEX_CLI_PATH") or shutil.which("codex")
        self.model = model or os.environ.get("ARCH_STUDIO_CODEX_MODEL", "gpt-6-astra")
        self.timeout_seconds = timeout_seconds
        configured_home = home_root
        if configured_home is None and os.environ.get("ARCH_STUDIO_CODEX_HOME"):
            configured_home = Path(os.environ["ARCH_STUDIO_CODEX_HOME"])
        if configured_home is None:
            user_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
            configured_home = user_data / "AI Architecture Studio" / "CodexHome"
        self.home = configured_home.expanduser().resolve()
        self.sketchup_mcp = sketchup_mcp or ConfiguredSketchUpMCP(timeout_seconds=180)
        self._lock = threading.RLock()

    @property
    def available(self) -> bool:
        return bool(self.codex_executable)

    def respond(self, *, project_dir: Path, thread_id: str | None, prompt: str,
                mcp_enabled: bool, developer_instructions: str) -> AgentTurnResult:
        if not self.codex_executable:
            raise NativeAgentUnavailable("Codex CLI is unavailable; install/sign in to Codex CLI to start the native agent.")
        with self._lock:
            dynamic_tools = self._dynamic_tools() if mcp_enabled else []
            self._prepare_home(mcp_enabled=mcp_enabled)
            return self._run_turn(
                project_dir=project_dir.resolve(), thread_id=thread_id,
                prompt=prompt, mcp_enabled=mcp_enabled,
                developer_instructions=developer_instructions, dynamic_tools=dynamic_tools,
            )

    def _dynamic_tools(self) -> list[dict[str, Any]]:
        try:
            discovered = self.sketchup_mcp.list_tools()
        except (ConnectorUnavailable, MCPCallError) as error:
            raise NativeAgentUnavailable(f"The configured Kongxing SketchUp MCP could not list its tools: {error}") from error
        tools: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in discovered:
            name = item.get("name")
            schema = item.get("inputSchema")
            if not isinstance(name, str) or not isinstance(schema, dict) or name in seen:
                continue
            seen.add(name)
            tools.append({
                "type": "function",
                "name": name,
                "description": str(item.get("description") or f"Call the existing Kongxing SketchUp MCP tool {name}."),
                "inputSchema": schema,
            })
        if not tools:
            raise NativeAgentUnavailable("The configured Kongxing SketchUp MCP returned no callable tool schemas.")
        return tools

    def _prepare_home(self, *, mcp_enabled: bool) -> None:
        source_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
        source_config = source_home / "config.toml"
        if not source_config.is_file():
            raise NativeAgentUnavailable("Codex config.toml was not found; the local native agent is not configured.")
        try:
            config = _toml_load(source_config)
        except Exception as error:
            raise NativeAgentUnavailable(f"Could not read Codex configuration: {error}") from error
        self.home.mkdir(parents=True, exist_ok=True)
        source_auth = source_home / "auth.json"
        target_auth = self.home / "auth.json"
        if source_auth.is_file() and not target_auth.exists():
            try:
                os.link(source_auth, target_auth)
            except OSError:
                # The isolated app-server home lives under ignored local runtime data.
                # Copy only Codex's own login cache; no API key or MCP credential is read here.
                shutil.copy2(source_auth, target_auth)
        if not target_auth.is_file():
            raise NativeAgentUnavailable("Codex login cache is unavailable. Sign in to Codex CLI on this computer first.")

        lines = [
            f"model = {json.dumps(self.model)}",
            'model_reasoning_effort = "high"',
            'approval_policy = "never"',
            'sandbox_mode = "read-only"',
            "mcp_optional_startup_grace_ms = 0",
        ]
        temp_config = self.home / f"config.{uuid.uuid4().hex}.tmp"
        config_path = self.home / "config.toml"
        temp_config.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temp_config.replace(config_path)

    def _run_turn(self, *, project_dir: Path, thread_id: str | None, prompt: str,
                  mcp_enabled: bool, developer_instructions: str,
                  dynamic_tools: list[dict[str, Any]]) -> AgentTurnResult:
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(self.home)
        command = [str(self.codex_executable), "app-server"]
        log_path = self.runtime_root / "logs" / "codex-app-server.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_path.open("a", encoding="utf-8")
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log_handle,
                cwd=project_dir,
                env=environment,
                bufsize=0,
            )
        except OSError as error:
            log_handle.close()
            raise NativeAgentUnavailable(f"Could not start Codex app-server: {error}") from error
        events: queue.Queue[str | None] = queue.Queue()

        def read_stdout() -> None:
            assert process.stdout is not None
            for raw in iter(process.stdout.readline, b""):
                events.put(raw.decode("utf-8", errors="replace").strip())
            events.put(None)

        reader = threading.Thread(target=read_stdout, name="codex-app-server-reader", daemon=True)
        reader.start()
        request_id = 0
        buffered: list[dict[str, Any]] = []
        try:
            initialized = self._request(process, events, request_id, "initialize", {
                "clientInfo": {"name": "ai-architecture-studio", "title": "AI Architecture Studio", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True},
            }, buffered)
            request_id += 1
            self._notify(process, "initialized", {})
            thread_params: dict[str, Any] = {
                "model": self.model,
                "cwd": str(project_dir),
                "runtimeWorkspaceRoots": [str(project_dir)],
                "sandbox": "read-only",
                "approvalPolicy": "never",
                "serviceName": "ai_architecture_studio_fast_assembly_v1",
                "developerInstructions": developer_instructions,
            }
            if mcp_enabled:
                thread_params["dynamicTools"] = dynamic_tools
            if thread_id:
                thread_params = {"threadId": thread_id, "developerInstructions": developer_instructions}
                if mcp_enabled:
                    thread_params["dynamicTools"] = dynamic_tools
                thread = self._request(process, events, request_id, "thread/resume", thread_params, buffered)
            else:
                thread = self._request(process, events, request_id, "thread/start", thread_params, buffered)
            request_id += 1
            resolved_thread_id = str((thread.get("thread") or {}).get("id") or thread_id or "")
            if not resolved_thread_id:
                raise NativeAgentUnavailable("Codex app-server returned no thread id.")

            self._send(process, {
                "id": request_id,
                "method": "turn/start",
                "params": {
                    "threadId": resolved_thread_id,
                    "input": [{"type": "text", "text": prompt}],
                    "cwd": str(project_dir),
                    "model": self.model,
                    "approvalPolicy": "never",
                    "sandboxPolicy": {"type": "readOnly"},
                },
            })
            deadline = time.monotonic() + self.timeout_seconds
            tool_calls: list[dict[str, str]] = []
            reply = ""
            turn_status = "failed"
            while time.monotonic() < deadline:
                message = self._next_event(events, deadline)
                if message is None:
                    break
                if message.get("id") == request_id and "error" in message:
                    raise NativeAgentUnavailable(str(message["error"].get("message", "Codex turn could not start.")))
                method = str(message.get("method", ""))
                params = message.get("params") or {}
                if method in {"item/tool/call", "dynamicToolCall"} and message.get("id") is not None:
                    call = _tool_summary(params)
                    tool_calls.append(call)
                    try:
                        if call["tool"] not in {str(tool.get("name", "")) for tool in dynamic_tools}:
                            raise MCPCallError("The agent requested a tool that is not in this turn's Kongxing MCP allowlist.")
                        output = self.sketchup_mcp.call_for_agent(call["tool"], params.get("arguments") or {})
                    except (ConnectorUnavailable, MCPCallError, OSError, ValueError) as error:
                        output = {"success": False, "contentItems": [{"type": "inputText", "text": str(error)}]}
                    self._send(process, {"id": message["id"], "result": output})
                    continue
                item = params.get("item") or {}
                if isinstance(item, dict) and item.get("type") in {"mcpToolCall", "mcp_tool_call"}:
                    tool_calls.append(_tool_summary(item))
                elif isinstance(item, dict) and item.get("type") == "dynamicToolCall":
                    tool_calls.append({"server": "kongxing_sketchup", "tool": str(item.get("tool", "dynamic_tool"))})
                elif method in {"item/started", "item/completed"} and isinstance(item, dict):
                    if item.get("type") in {"mcpToolCall", "mcp_tool_call"}:
                        tool_calls.append(_tool_summary(item))
                    if method == "item/completed" and item.get("type") in {"agentMessage", "agent_message"}:
                        reply = _message_text(item)
                elif "mcpToolCall" in method and isinstance(params, dict):
                    tool_calls.append({
                        "server": str(params.get("server", "kongxing_sketchup")),
                        "tool": str(params.get("tool", "mcp_tool")),
                    })
                if method == "turn/completed":
                    turn = params.get("turn") or {}
                    turn_status = str(turn.get("status", "failed"))
                    if turn_status != "completed":
                        detail = (turn.get("error") or {}).get("message", "Codex agent turn did not complete.")
                        raise NativeAgentUnavailable(str(detail))
                    break
            else:
                raise NativeAgentUnavailable(f"Codex agent turn exceeded {self.timeout_seconds} seconds.")
            if turn_status != "completed":
                raise NativeAgentUnavailable("Codex app-server ended without a completed turn.")
            return AgentTurnResult(
                thread_id=resolved_thread_id,
                reply=reply or "已完成这轮推演；模型操作记录已保存。",
                status=turn_status,
                tool_calls=_dedupe_calls(tool_calls),
                model_name=self.model,
            )
        except (BrokenPipeError, OSError, TimeoutError, json.JSONDecodeError) as error:
            raise NativeAgentUnavailable(f"Codex app-server communication failed: {error}") from error
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            log_handle.close()

    def _request(self, process: subprocess.Popen[bytes], events: queue.Queue[str | None],
                 request_id: int, method: str, params: dict[str, Any],
                 buffered: list[dict[str, Any]]) -> dict[str, Any]:
        self._send(process, {"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + min(self.timeout_seconds, 120)
        while time.monotonic() < deadline:
            message = self._next_event(events, deadline)
            if message is None:
                raise NativeAgentUnavailable("Codex app-server exited before replying.")
            if message.get("id") != request_id:
                buffered.append(message)
                continue
            if "error" in message:
                raise NativeAgentUnavailable(f"Codex {method} failed: {message['error'].get('message', 'unknown error')}")
            result = message.get("result")
            if not isinstance(result, dict):
                raise NativeAgentUnavailable(f"Codex {method} returned an invalid response.")
            return result
        raise NativeAgentUnavailable(f"Codex {method} timed out.")

    @staticmethod
    def _send(process: subprocess.Popen[bytes], message: dict[str, Any]) -> None:
        if process.stdin is None:
            raise NativeAgentUnavailable("Codex app-server input stream is closed.")
        process.stdin.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))
        process.stdin.flush()

    def _notify(self, process: subprocess.Popen[bytes], method: str, params: dict[str, Any]) -> None:
        self._send(process, {"method": method, "params": params})

    @staticmethod
    def _next_event(events: queue.Queue[str | None], deadline: float) -> dict[str, Any] | None:
        try:
            line = events.get(timeout=max(0.01, deadline - time.monotonic()))
        except queue.Empty as error:
            raise TimeoutError("Timed out waiting for Codex app-server event.") from error
        if line is None:
            return None
        if not line:
            return {}
        value = json.loads(line)
        return value if isinstance(value, dict) else {}


def _toml_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return json.dumps(value, ensure_ascii=False) if isinstance(value, str) else str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{key} = {_toml_literal(item)}" for key, item in value.items()) + " }"
    raise TypeError(f"Unsupported Codex config value: {type(value).__name__}")


def _tool_summary(item: dict[str, Any]) -> dict[str, str]:
    return {
        "server": str(item.get("server") or item.get("serverName") or "kongxing_sketchup"),
        "tool": str(item.get("tool") or item.get("toolName") or item.get("name") or "mcp_tool"),
    }


def _message_text(item: dict[str, Any]) -> str:
    text = item.get("text")
    if isinstance(text, str):
        return text.strip()
    content = item.get("content")
    if isinstance(content, list):
        return "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict)).strip()
    return ""


def _dedupe_calls(calls: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, str]] = []
    for call in calls:
        key = (call.get("server", ""), call.get("tool", ""))
        if key not in seen:
            seen.add(key)
            output.append(call)
    return output
