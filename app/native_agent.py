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
from typing import Any, Callable

from .agent_tools import AgentToolSurface
from .reference_assets import discover_project_reference_images, reference_image_label
from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError, _toml_load
from .workflow_context import WorkflowMode, ToolProfile, workflow_reference_categories


class NativeAgentUnavailable(RuntimeError):
    pass


_PARENT_CODEX_CONTEXT_ENV = {
    "CODEX_APP_TOOLS_PIPE_PATH",
    "CODEX_SESSION_ID",
    "CODEX_THREAD_ID",
    "CODEX_CI",
}


def _app_server_environment(parent_environment: dict[str, str]) -> dict[str, str]:
    """Detach a nested App Server from the desktop thread's tool/permission context."""
    environment = parent_environment.copy()
    for name in _PARENT_CODEX_CONTEXT_ENV:
        environment.pop(name, None)
    return environment


def _app_server_turn_input(prompt: str, reference_images: list[Path]) -> list[dict[str, str]]:
    """Build App Server input items; its JSON enum is camelCase ``localImage``."""
    turn_input = [{"type": "text", "text": prompt}]
    turn_input.extend({"type": "localImage", "path": str(path)} for path in reference_images)
    return turn_input


def _agent_workspace(project_dir: Path) -> Path:
    """Return the only filesystem location a modeling Codex turn may write."""
    project_root = project_dir.resolve()
    runtime_dir = (project_root / "runtime").resolve()
    workspace = (runtime_dir / "agent_workspace").resolve()
    if not runtime_dir.is_relative_to(project_root) or not workspace.is_relative_to(runtime_dir):
        raise ValueError("Agent workspace resolved outside this project runtime.")
    runtime_dir.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    if runtime_dir.is_symlink() or workspace.is_symlink():
        raise ValueError("Agent workspace directories may not be symbolic links.")
    return workspace


def _workspace_write_policy(workspace: Path) -> dict[str, Any]:
    """Build the current Codex App Server workspace-write policy."""
    return {
        "type": "workspaceWrite",
        "writableRoots": [str(workspace.resolve())],
        "networkAccess": False,
        "excludeTmpdirEnvVar": True,
        "excludeSlashTmp": True,
    }


def _composed_tool_instructions(developer_instructions: str, *, mcp_enabled: bool, tool_profile: str = "full") -> str:
    """Supersede the historical Kongxing-only wording once OSS tools are composed.

    The older web layer still passes a Kongxing-only sentence. Keeping the override
    here lets the runtime migrate safely without a second source of truth for which
    dynamic tools are actually authorized this turn.
    """
    if not mcp_enabled:
        return developer_instructions
    if tool_profile == "reconstruction_coding":
        return developer_instructions + "\nUse persistent workspace Ruby as the primary reconstruction tool. SAIE is a helper library; supplied dynamic tools are the authoritative allowlist."
    return developer_instructions.rstrip() + (
        "\n\nOSS Takeover execution override: the dynamic tools supplied on this turn are the authoritative "
        "allowed SketchUp tool surface. Namespaced reusable OSS tools such as saie__* are allowed when "
        "present, even if an older host sentence mentions Kongxing-only operation. Prefer mature semantic "
        "OSS tools first, existing Kongxing named tools second, and guarded project Ruby only for geometry "
        "the mature tools cannot express. Keep every operation on the already verified disposable model; "
        "do not use whole-document lifecycle tools or arbitrary raw Ruby from imported backends."
    )


@dataclass
class AgentTurnResult:
    thread_id: str
    reply: str
    status: str = "completed"
    tool_calls: list[dict[str, str]] = field(default_factory=list)
    model_name: str = ""
    reasoning_effort: str = "low"
    provider_name: str = "codex-app-server"
    region: str = "codex-managed (not exposed)"
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int = 0
    tool_call_count: int = 0
    failed_tool_calls: int = 0


class CodexAppServerRuntime:
    """Runs Codex app-server with project-local tools and an isolated writable workspace."""

    def __init__(self, runtime_root: Path, *, codex_executable: str | None = None,
                 model: str | None = None, timeout_seconds: int = 300,
                 sketchup_mcp: ConfiguredSketchUpMCP | None = None,
                 home_root: Path | None = None,
                 reasoning_effort: str | None = None):
        self.runtime_root = runtime_root.resolve()
        self.codex_executable = codex_executable or os.environ.get("CODEX_CLI_PATH") or shutil.which("codex")
        self.model = model or os.environ.get("ARCH_STUDIO_ECONOMY_MODEL", "gpt-6.1-sol")
        effort = reasoning_effort or os.environ.get("ARCH_STUDIO_CODEX_REASONING_EFFORT", "low")
        if effort not in {"low", "medium", "high", "xhigh", "max"}:
            raise ValueError("ARCH_STUDIO_CODEX_REASONING_EFFORT must be one of low, medium, high, xhigh, or max.")
        self.reasoning_effort = effort
        self.timeout_seconds = timeout_seconds
        configured_home = home_root
        if configured_home is None and os.environ.get("ARCH_STUDIO_CODEX_HOME"):
            configured_home = Path(os.environ["ARCH_STUDIO_CODEX_HOME"])
        if configured_home is None:
            user_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
            configured_home = user_data / "AI Architecture Studio" / "CodexHome"
        self.home = configured_home.expanduser().resolve()
        self.sketchup_mcp = sketchup_mcp or ConfiguredSketchUpMCP(timeout_seconds=180)
        self.tool_surface = AgentToolSurface(self.runtime_root, self.sketchup_mcp)
        self._lock = threading.RLock()

    @property
    def available(self) -> bool:
        return bool(self.codex_executable)

    def respond(self, *, project_dir: Path, thread_id: str | None, prompt: str,
                mcp_enabled: bool, developer_instructions: str,
                model_path: Path | None = None, model_guid: str = "",
                ruby_enabled: bool = True, ruby_state: dict[str, dict[str, Any]] | None = None,
                architecture_skill_context: str = "", model: str | None = None,
                reasoning_effort: str | None = None, workflow_mode: WorkflowMode = "architecture_design",
                tool_profile: ToolProfile = "full") -> AgentTurnResult:
        if not self.codex_executable:
            raise NativeAgentUnavailable("Codex CLI is unavailable; install/sign in to Codex CLI to start the native agent.")
        with self._lock:
            selected_model = model or self.model
            selected_effort = reasoning_effort or self.reasoning_effort
            if selected_effort not in {"low", "medium", "high", "xhigh", "max"}:
                raise ValueError("reasoning_effort must be one of low, medium, high, xhigh, or max.")
            try:
                tools = self.tool_surface.prepare(
                    project_dir=project_dir, mcp_enabled=mcp_enabled, model_path=model_path,
                    model_guid=model_guid, ruby_enabled=ruby_enabled, ruby_state=ruby_state,
                    tool_profile=tool_profile,
                )
                agent_workspace = _agent_workspace(project_dir)
            except (RuntimeError, ValueError) as error:
                raise NativeAgentUnavailable(str(error)) from error
            self._prepare_home(
                mcp_enabled=mcp_enabled, model=selected_model,
                reasoning_effort=selected_effort, agent_workspace=agent_workspace,
            )
            full_prompt = prompt.rstrip()
            if architecture_skill_context:
                full_prompt += "\n\n" + architecture_skill_context.strip()
            reference_images = discover_project_reference_images(project_dir, categories=workflow_reference_categories(workflow_mode))
            if reference_images:
                full_prompt += "\n\n" + reference_image_label(reference_images, reconstruction=workflow_mode == "image_reconstruction")
            effective_developer_instructions = _composed_tool_instructions(
                developer_instructions, mcp_enabled=mcp_enabled, tool_profile=tool_profile,
            )
            return self._run_turn(
                project_dir=project_dir.resolve(), agent_workspace=agent_workspace,
                thread_id=thread_id, prompt=full_prompt, mcp_enabled=mcp_enabled,
                developer_instructions=effective_developer_instructions,
                dynamic_tools=tools.dynamic_tools, tool_handler=tools.dispatch,
                model=selected_model, reasoning_effort=selected_effort,
                reference_images=reference_images,
                workflow_mode=workflow_mode, tool_profile=tool_profile,
            )

    def _dynamic_tools(self, *, ruby_enabled: bool = False) -> list[dict[str, Any]]:
        try:
            return self.tool_surface.dynamic_tools(ruby_enabled=ruby_enabled)
        except RuntimeError as error:
            raise NativeAgentUnavailable(str(error)) from error

    def _dispatch_tool(self, name: str, arguments: dict[str, Any], *, project_dir: Path,
                       project_ruby: Any | None) -> dict[str, Any]:
        return self.tool_surface.dispatch(name, arguments, project_dir=project_dir, project_ruby=project_ruby)

    def _prepare_home(self, *, mcp_enabled: bool, model: str | None = None,
                      reasoning_effort: str | None = None,
                      agent_workspace: Path | None = None) -> None:
        source_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
        source_config = source_home / "config.toml"
        if not source_config.is_file():
            raise NativeAgentUnavailable("Codex config.toml was not found; the local native agent is not configured.")
        try:
            user_config = _toml_load(source_config)
        except Exception as error:
            raise NativeAgentUnavailable(f"Could not read Codex configuration: {error}") from error
        self.home.mkdir(parents=True, exist_ok=True)
        source_auth = source_home / "auth.json"
        target_auth = self.home / "auth.json"
        if source_auth.is_file() and not target_auth.exists():
            try:
                os.link(source_auth, target_auth)
            except OSError:
                shutil.copy2(source_auth, target_auth)
        if not target_auth.is_file():
            raise NativeAgentUnavailable("Codex login cache is unavailable. Sign in to Codex CLI on this computer first.")

        workspace = agent_workspace.resolve() if agent_workspace is not None else self.runtime_root
        lines = [
            f"model = {json.dumps(model or self.model)}",
            f"model_reasoning_effort = {json.dumps(reasoning_effort or self.reasoning_effort)}",
            'approval_policy = "never"',
            'sandbox_mode = "workspace-write"',
            "mcp_optional_startup_grace_ms = 0",
            "",
            "[sandbox_workspace_write]",
            "network_access = false",
            f"writable_roots = [{json.dumps(str(workspace))}]",
        ]
        # Preserve the user's supported Windows sandbox implementation selection.
        # The project still uses workspace-write, never full access.
        windows = user_config.get("windows", {})
        if isinstance(windows, dict) and windows.get("sandbox") in {"elevated", "unelevated"}:
            lines.extend(["", "[windows]", f"sandbox = {json.dumps(windows['sandbox'])}"])
        temp_config = self.home / f"config.{uuid.uuid4().hex}.tmp"
        config_path = self.home / "config.toml"
        temp_config.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temp_config.replace(config_path)

    def _run_turn(self, *, project_dir: Path, agent_workspace: Path,
                  thread_id: str | None, prompt: str,
                  mcp_enabled: bool, developer_instructions: str,
                  dynamic_tools: list[dict[str, Any]],
                  tool_handler: Callable[[str, dict[str, Any]], dict[str, Any]],
                  model: str, reasoning_effort: str,
                  reference_images: list[Path], workflow_mode: WorkflowMode = "architecture_design",
                  tool_profile: ToolProfile = "full") -> AgentTurnResult:
        started = time.monotonic()
        environment = _app_server_environment(dict(os.environ))
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
                cwd=agent_workspace,
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
            self._request(process, events, request_id, "initialize", {
                "clientInfo": {"name": "ai-architecture-studio", "title": "AI Architecture Studio", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True},
            }, buffered)
            request_id += 1
            self._notify(process, "initialized", {})
            thread_params: dict[str, Any] = {
                "model": model,
                "cwd": str(agent_workspace),
                "runtimeWorkspaceRoots": [str(agent_workspace)],
                "sandbox": "workspace-write",
                "approvalPolicy": "never",
                "serviceName": "ai_architecture_studio_oss_takeover_v1",
                "developerInstructions": developer_instructions,
            }
            thread_params["dynamicTools"] = dynamic_tools if mcp_enabled else []
            if thread_id:
                thread_params = {"threadId": thread_id, "developerInstructions": developer_instructions}
                thread_params["dynamicTools"] = dynamic_tools if mcp_enabled else []
                thread = self._request(process, events, request_id, "thread/resume", thread_params, buffered)
            else:
                thread = self._request(process, events, request_id, "thread/start", thread_params, buffered)
            request_id += 1
            resolved_thread_id = str((thread.get("thread") or {}).get("id") or thread_id or "")
            if not resolved_thread_id:
                raise NativeAgentUnavailable("Codex app-server returned no thread id.")

            turn_input = _app_server_turn_input(prompt, reference_images)
            evidence_dir = project_dir / "runtime" / "agent_events"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence_path = evidence_dir / f"{uuid.uuid4().hex}.jsonl"

            def record(event: dict[str, Any]) -> None:
                with evidence_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")

            record({"event": "turn_input", "thread_id": resolved_thread_id,
                    "model": model, "reasoning_effort": reasoning_effort,
                    "workflow_mode": workflow_mode, "tool_profile": tool_profile,
                    "reference_categories": list(workflow_reference_categories(workflow_mode)),
                    "input_types": [item["type"] for item in turn_input],
                    "reference_files": [path.relative_to(project_dir).as_posix() for path in reference_images],
                    "sandbox_policy": {"type": "workspaceWrite", "networkAccess": False},
                    "tool_names": [tool["name"] for tool in dynamic_tools]})
            self._send(process, {
                "id": request_id,
                "method": "turn/start",
                "params": {
                    "threadId": resolved_thread_id,
                    "input": turn_input,
                    "cwd": str(agent_workspace),
                    "runtimeWorkspaceRoots": [str(agent_workspace)],
                    "model": model,
                    "effort": reasoning_effort,
                    "approvalPolicy": "never",
                    "sandboxPolicy": _workspace_write_policy(agent_workspace),
                },
            })
            deadline = time.monotonic() + self.timeout_seconds
            tool_calls: list[dict[str, str]] = []
            tool_call_count = 0
            failed_tool_calls = 0
            input_tokens: int | None = None
            output_tokens: int | None = None
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
                if method in {"item/started", "item/completed", "turn/completed"}:
                    event_item = params.get("item") or {}
                    record({"event": method, "item_type": event_item.get("type"),
                            "status": event_item.get("status") or (params.get("turn") or {}).get("status"),
                            "text": _message_text(event_item) if event_item.get("type") in {"agentMessage", "agent_message"} else ""})
                usage = _extract_token_usage(params)
                input_tokens = usage[0] if usage[0] is not None else input_tokens
                output_tokens = usage[1] if usage[1] is not None else output_tokens
                if method in {"item/tool/call", "dynamicToolCall"} and message.get("id") is not None:
                    call = _tool_summary(params)
                    tool_calls.append(call)
                    tool_call_count += 1
                    try:
                        if call["tool"] not in {str(tool.get("name", "")) for tool in dynamic_tools}:
                            raise MCPCallError("The agent requested a tool that is not in this turn's active composed SketchUp tool allowlist.")
                        output = tool_handler(call["tool"], params.get("arguments") or {})
                        if output.get("success") is False or output.get("isError") is True:
                            failed_tool_calls += 1
                    except (ConnectorUnavailable, MCPCallError, OSError, RuntimeError, ValueError) as error:
                        failed_tool_calls += 1
                        output = {"success": False, "contentItems": [{"type": "inputText", "text": str(error)}]}
                    self._send(process, {"id": message["id"], "result": output})
                    record({"event": "tool_result", "tool": call["tool"],
                            "success": output.get("success", not output.get("isError", False)),
                            "content_types": [part.get("type") for part in output.get("contentItems", [])]})
                    continue
                item = params.get("item") or {}
                if isinstance(item, dict) and item.get("type") in {"mcpToolCall", "mcp_tool_call"}:
                    tool_calls.append(_tool_summary(item))
                elif isinstance(item, dict) and item.get("type") == "dynamicToolCall":
                    tool_calls.append({"server": "sketchup_tool_surface", "tool": str(item.get("tool", "dynamic_tool"))})
                elif method in {"item/started", "item/completed"} and isinstance(item, dict):
                    if item.get("type") in {"mcpToolCall", "mcp_tool_call"}:
                        tool_calls.append(_tool_summary(item))
                    if method == "item/completed" and item.get("type") in {"agentMessage", "agent_message"}:
                        reply = _message_text(item)
                elif "mcpToolCall" in method and isinstance(params, dict):
                    tool_calls.append({
                        "server": str(params.get("server", "sketchup_tool_surface")),
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
                model_name=model,
                reasoning_effort=reasoning_effort,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=round((time.monotonic() - started) * 1000),
                tool_call_count=tool_call_count,
                failed_tool_calls=failed_tool_calls,
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
        "server": str(item.get("server") or item.get("serverName") or "sketchup_tool_surface"),
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


def _extract_token_usage(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    """Read per-turn usage fields without inventing counts when App Server omits them."""
    candidates = [payload]
    for key in ("turn", "usage", "tokenUsage", "token_usage", "last", "total"):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.insert(0, value)
    input_keys = ("inputTokens", "input_tokens", "prompt_tokens", "promptTokens")
    output_keys = ("outputTokens", "output_tokens", "completion_tokens", "completionTokens")

    def first_count(keys: tuple[str, ...]) -> int | None:
        for candidate in candidates:
            for key in keys:
                value = candidate.get(key)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    return value
        return None

    return first_count(input_keys), first_count(output_keys)


def _dedupe_calls(calls: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, str]] = []
    for call in calls:
        key = (call.get("server", ""), call.get("tool", ""))
        if key not in seen:
            seen.add(key)
            output.append(call)
    return output
