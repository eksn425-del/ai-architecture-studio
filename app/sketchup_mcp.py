from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


class ConnectorUnavailable(RuntimeError):
    pass


class MCPCallError(RuntimeError):
    pass


class UnsavedModelError(MCPCallError):
    def __init__(self, identity: dict[str, Any]):
        super().__init__("SketchUp 当前是未保存的无标题模型；需要先打开项目专属副本。")
        self.identity = identity


def _toml_load(path: Path) -> dict[str, Any]:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _resolve_server() -> tuple[list[str], dict[str, str], str | None]:
    standalone = os.environ.get("ARCH_STUDIO_MCP_CONFIG", "")
    if standalone:
        try:
            server = json.loads(Path(standalone).read_text(encoding="utf-8"))
            command = str(server.get("command", ""))
            resolved = shutil.which(command) or (command if Path(command).is_file() else "")
            if not resolved or not isinstance(server.get("args", []), list):
                raise ValueError("invalid executable/arguments")
            return [resolved, *map(str, server.get("args", []))], {str(k):str(v) for k,v in server.get("env", {}).items()}, server.get("cwd")
        except (OSError, ValueError, AttributeError, TypeError) as error:
            raise ConnectorUnavailable("The standalone SketchUp connector configuration is unavailable or invalid.") from error
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    config_path = codex_home / "config.toml"
    if not config_path.exists():
        raise ConnectorUnavailable("Codex config.toml was not found; the existing SketchUp MCP is not configured.")
    try:
        config = _toml_load(config_path)
        server = config.get("mcp_servers", {}).get("kongxing_sketchup")
    except Exception as error:
        raise ConnectorUnavailable(f"Could not read the configured SketchUp MCP entry: {error}") from error
    if not isinstance(server, dict) or server.get("enabled", True) is False:
        raise ConnectorUnavailable("The existing kongxing_sketchup MCP server is not enabled in Codex config.")
    command = str(server.get("command", ""))
    if not command:
        raise ConnectorUnavailable("The existing SketchUp MCP config has no command.")
    resolved = shutil.which(command) or (command if Path(command).is_file() else "")
    if not resolved:
        raise ConnectorUnavailable(f"The configured SketchUp MCP command is unavailable: {command}")
    arguments = [str(item) for item in server.get("args", [])]
    environment = {str(key): str(value) for key, value in server.get("env", {}).items()}
    cwd = str(server.get("cwd")) if server.get("cwd") else None
    return [resolved, *arguments], environment, cwd


def _generated_script_dir() -> Path:
    configured = os.environ.get("ARCHFLOW_GENERATED_SCRIPT_DIR")
    if configured:
        return Path(configured).expanduser()
    program_data = os.environ.get("PROGRAMDATA")
    if program_data:
        return Path(program_data) / "archflow-mcp" / "generated_scripts"
    return Path.home() / ".local" / "share" / "archflow-mcp" / "generated_scripts"


def _frame(message: dict[str, Any]) -> bytes:
    body = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _read_frames(data: bytes) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    remaining = data
    while remaining:
        boundary = remaining.find(b"\r\n\r\n")
        if boundary < 0:
            break
        header = remaining[:boundary].decode("ascii", errors="replace")
        match = re.search(r"(?im)^Content-Length:\s*(\d+)\s*$", header)
        if not match:
            remaining = remaining[boundary + 4 :]
            continue
        size = int(match.group(1))
        start = boundary + 4
        end = start + size
        if len(remaining) < end:
            break
        try:
            message = json.loads(remaining[start:end].decode("utf-8"))
            if isinstance(message, dict):
                messages.append(message)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        remaining = remaining[end:]
    return messages


class ConfiguredSketchUpMCP:
    """Small stdio client for the existing, user-configured Kongxing MCP server."""

    def __init__(self, timeout_seconds: int = 15):
        self.timeout_seconds = timeout_seconds

    def _request(self, requests: list[dict[str, Any]], response_id: int) -> dict[str, Any]:
        command, configured_env, configured_cwd = _resolve_server()
        environment = os.environ.copy()
        environment.update(configured_env)
        payload = b"".join(_frame(message) for message in requests)
        try:
            completed = subprocess.run(
                command,
                input=payload,
                capture_output=True,
                timeout=self.timeout_seconds,
                cwd=configured_cwd or str(Path(__file__).resolve().parents[1]),
                env=environment,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as error:
            raise MCPCallError(f"The existing SketchUp MCP did not respond within {self.timeout_seconds} seconds.") from error
        except OSError as error:
            raise ConnectorUnavailable(f"The existing SketchUp MCP could not be started: {error}") from error

        responses = {item.get("id"): item for item in _read_frames(completed.stdout) if "id" in item}
        response = responses.get(response_id)
        if response is None:
            detail = completed.stderr.decode("utf-8", errors="replace")[-1200:].strip()
            raise MCPCallError(detail or "The existing SketchUp MCP returned no tool response.")
        if response.get("error"):
            raise MCPCallError(str(response["error"].get("message", "MCP tool call failed")))
        result = response.get("result")
        if not isinstance(result, dict):
            raise MCPCallError("The existing SketchUp MCP returned an invalid response.")
        if result.get("isError"):
            content = result.get("content", [])
            message = " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
            raise MCPCallError(message or "The SketchUp MCP tool returned an error.")
        return result

    @staticmethod
    def _initialize_requests() -> list[dict[str, Any]]:
        return [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ai-architecture-studio", "version": "0.1.0"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        ]

    def list_tools(self) -> list[dict[str, Any]]:
        requests = self._initialize_requests() + [{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
        result = self._request(requests, 2)
        tools = result.get("tools", [])
        if not isinstance(tools, list):
            raise MCPCallError("The configured SketchUp MCP returned an invalid tool list.")
        return [tool for tool in tools if isinstance(tool, dict) and isinstance(tool.get("name"), str)]

    def call_raw(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        requests = self._initialize_requests() + [
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": tool_name,
                "arguments": arguments or {},
            }},
        ]
        return self._request(requests, 3)

    def call_for_agent(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        result = self.call_raw(tool_name, arguments)
        output: list[dict[str, str]] = []
        for part in result.get("content", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                output.append({"type": "inputText", "text": str(part.get("text", ""))})
            elif part.get("type") == "image" and isinstance(part.get("data"), str):
                mime_type = str(part.get("mimeType") or "image/png")
                output.append({"type": "inputImage", "imageUrl": f"data:{mime_type};base64,{part['data']}"})
            elif part.get("type") == "resource" and isinstance(part.get("resource"), dict):
                text = part["resource"].get("text")
                if isinstance(text, str):
                    output.append({"type": "inputText", "text": text})
        return {"success": not bool(result.get("isError")), "contentItems": output}

    def call(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        result = self.call_raw(tool_name, arguments)
        content = result.get("content", [])
        text = next((part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"), "")
        if not text:
            return result
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}


class SketchUpAdapter:
    def __init__(self, client: ConfiguredSketchUpMCP | None = None):
        self.client = client or ConfiguredSketchUpMCP()

    def ping(self) -> dict[str, Any]:
        return self.client.call("sketchup_health")

    def get_model_info(self) -> dict[str, Any]:
        return self.client.call("sketchup_get_model_context")

    def create_mass(self, *, stable_id: str, name: str, origin_m: list[float], width_m: float,
                    depth_m: float, height_m: float, color: str = "#D9D9D9") -> dict[str, Any]:
        result = self.client.call("sketchup_create_mass", {
            "name": f"[{stable_id}] {name}",
            "origin_m": origin_m,
            "width_m": width_m,
            "depth_m": depth_m,
            "height_m": height_m,
            "material": {"color": color},
        })
        return result if isinstance(result, dict) else {"result": result}

    def create_circulation(self, *, stable_id: str, name: str, start_m: list[float], end_m: list[float],
                           width_m: float) -> dict[str, Any]:
        result = self.client.call("sketchup_create_road", {
            "name": f"[{stable_id}] {name}",
            "start_m": start_m,
            "end_m": end_m,
            "width_m": width_m,
        })
        return result if isinstance(result, dict) else {"result": result}

    def modify_object(self, *, connector_ref: str, translate_m: list[float] | None = None,
                      scale: list[float] | None = None) -> dict[str, Any]:
        if not connector_ref.isdigit():
            raise MCPCallError("This object has no numeric Kongxing entity ID and cannot be edited through the existing connector.")
        result = self.client.call("sketchup_transform_group", {
            "entity_id": int(connector_ref),
            "translate_m": translate_m or [0, 0, 0],
            "scale": scale or [1, 1, 1],
        })
        return result if isinstance(result, dict) else {"result": result}

    def capture_view(self, output_path: Path, width: int = 1500, height: int = 950,
                     zoom_extents: bool = True) -> dict[str, Any]:
        result = self.client.call("sketchup_export_view_image", {
            "output_path": str(output_path.resolve()),
            "width": width,
            "height": height,
            "zoom_extents": zoom_extents,
        })
        return result if isinstance(result, dict) else {"result": result}

    def set_camera(self, eye_m: list[float], target_m: list[float],
                   up_m: list[float] | None = None) -> dict[str, Any]:
        result = self.client.call("sketchup_set_camera", {
            "eye_m": eye_m,
            "target_m": target_m,
            "up": up_m or [0, 0, 1],
        })
        return result if isinstance(result, dict) else {"result": result}

    def get_active_model_identity(self) -> dict[str, Any]:
        generated_dir = _generated_script_dir()
        generated_dir.mkdir(parents=True, exist_ok=True)
        script_path = generated_dir / f"studio-model-path-{os.urandom(6).hex()}.rb"
        script = (
            "# ARCHFLOW_GENERATED_SCRIPT\n"
            "model = Sketchup.active_model\n"
            "{ model_path: model.path, model_name: model.title, model_guid: model.guid, "
            "modified: model.modified?, active_context: !model.active_path.nil?, main_thread: Thread.current == Thread.main }\n"
        )
        script_path.write_text(script, encoding="utf-8")
        try:
            result = self.client.call("sketchup_eval_project_file", {
                "script_path": str(script_path.resolve()),
                "operation_name": "AI Architecture Studio disposable-model safety check",
            })
        finally:
            script_path.unlink(missing_ok=True)
        candidates = [result]
        if isinstance(result, dict):
            candidates.append(result.get("result"))
            text = result.get("text")
            if isinstance(text, str):
                try:
                    candidates.append(json.loads(text))
                except json.JSONDecodeError:
                    pass
        for candidate in candidates:
            if isinstance(candidate, dict):
                if candidate.get("model_path") == "" and candidate.get("model_guid"):
                    raise UnsavedModelError(candidate)
                path = candidate.get("model_path") or candidate.get("path")
                guid = candidate.get("model_guid")
                if isinstance(path, str) and path and isinstance(guid, str) and guid:
                    if candidate.get("main_thread") is False:
                        raise MCPCallError("SketchUp Ruby evaluation did not run on the main thread.")
                    return {
                        "model_path": path,
                        "model_name": str(candidate.get("model_name") or Path(path).name),
                        "model_guid": guid,
                        "active_context": bool(candidate.get("active_context", False)),
                        "main_thread": bool(candidate.get("main_thread", True)),
                    }
        raise MCPCallError("The SketchUp MCP did not return the active model path and GUID, so the disposable-model safety check cannot pass.")

    def get_active_model_path(self) -> str:
        identity = self.get_active_model_identity()
        return str(identity["model_path"])

    def open_copy_from_unsaved_model(self, target_path: Path, expected_guid: str, *, expected_saved_path: str | None = None) -> None:
        """Host lifecycle only: preserve current work, then open a prepared copy.

        Save to a new recovery path, never overwrite the source. This also clears
        SketchUp's modified flag so opening the copy cannot hang on a save dialog.
        """
        if not target_path.is_file() or not target_path.name.startswith("blank-disposable-"):
            raise MCPCallError("Project disposable copy is missing.")
        scripts = _generated_script_dir()
        scripts.mkdir(parents=True, exist_ok=True)
        path = scripts / f"studio-open-{os.urandom(6).hex()}.rb"
        path_guard = (f"m.path == {json.dumps(expected_saved_path, ensure_ascii=False)}" if expected_saved_path else "m.path.empty?")
        guard = ("m = Sketchup.active_model\n"
                 f"raise 'Active model changed' unless m.guid == {json.dumps(expected_guid)}\n"
                 f"raise 'Active path or edit context changed' unless {path_guard} && m.active_path.nil?\n")
        backup = target_path.parent / f"unsaved-before-connect-{os.urandom(6).hex()}.skp"
        status_path = backup.with_suffix(".json")
        status_literal = json.dumps(str(status_path.resolve()), ensure_ascii=False)
        path.write_text("# ARCHFLOW_GENERATED_SCRIPT\n" + guard +
                        "UI.start_timer(0.1, false) do\nbegin\n" + guard +
                        f"raise 'Could not preserve current work' unless m.save({json.dumps(str(backup.resolve()), ensure_ascii=False)})\n" +
                        f"raise 'Could not open project copy' unless Sketchup.open_file({json.dumps(str(target_path.resolve()), ensure_ascii=False)})\n" +
                        f"File.write({status_literal}, JSON.generate({{ok: true}}))\nrescue StandardError => error\n" +
                        f"File.write({status_literal}, JSON.generate({{ok: false, error: error.message}}))\nend\nend\n"
                        "{ open_scheduled: true }\n", encoding="utf-8")
        try:
            self.client.call("sketchup_eval_project_file", {"script_path": str(path.resolve()),
                             "operation_name": "Open project disposable model"})
            deadline = time.monotonic() + 20
            while not status_path.is_file():
                if time.monotonic() >= deadline:
                    raise MCPCallError("SketchUp 项目副本打开操作尚未响应，请关闭弹窗后重试。")
                time.sleep(0.1)
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if not status.get("ok"):
                raise MCPCallError("SketchUp 项目副本打开失败：" + str(status.get("error", "unknown")))
        finally:
            path.unlink(missing_ok=True)

    def restore_disposable_model(self, target_path: Path, expected_path: Path) -> None:
        """Host-owned lifecycle action, never exposed as an agent execution tool."""
        identity = self.get_active_model_identity()
        if Path(str(identity.get("model_path") or "")).resolve() != expected_path.resolve():
            raise MCPCallError("The active model changed before recovery.")
        if identity.get("active_context"):
            raise MCPCallError("Exit the active edit context before recovering a checkpoint.")
        if target_path.parent.resolve() != expected_path.parent.resolve() or not target_path.name.startswith("blank-disposable-"):
            raise MCPCallError("Recovery must stay in the same disposable project folder.")
        scripts = _generated_script_dir()
        scripts.mkdir(parents=True, exist_ok=True)
        script_path = scripts / f"studio-recover-{os.urandom(6).hex()}.rb"
        target = json.dumps(str(target_path.resolve()), ensure_ascii=False)
        expected = json.dumps(str(expected_path.resolve()), ensure_ascii=False)
        script_path.write_text(
            "# ARCHFLOW_GENERATED_SCRIPT\n"
            f"raise 'Active recovery model changed' unless Sketchup.active_model.path == {expected}\n"
            "raise 'Could not save the disposable recovery source' unless Sketchup.active_model.save\n"
            f"UI.start_timer(0.1, false) {{ raise 'Active recovery model changed' unless Sketchup.active_model.path == {expected}; Sketchup.open_file({target}) }}\n"
            "{ recovery_scheduled: true }\n", encoding="utf-8")
        try:
            self.client.call("sketchup_eval_project_file", {"script_path": str(script_path.resolve()),
                             "operation_name": "Restore generated model checkpoint"})
        finally:
            script_path.unlink(missing_ok=True)

    def save_model(self, target_path: Path, operation_name: str = "AI Architecture Studio Demo checkpoint", expected_root_ids: list[int] | None = None) -> dict[str, Any]:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        generated_dir = _generated_script_dir()
        generated_dir.mkdir(parents=True, exist_ok=True)
        script_path = generated_dir / f"studio-save-{os.urandom(6).hex()}.rb"
        # JSON string literals are valid Ruby string literals for Windows paths.
        ruby_target = json.dumps(str(target_path.resolve()), ensure_ascii=False)
        root_guard = ""
        if expected_root_ids:
            ids = json.dumps([int(pid) for pid in expected_root_ids])
            root_guard = (f"roots = {ids}.map {{ |pid| model.find_entity_by_persistent_id(pid) }}\n"
                          "raise 'Owned model root is missing or empty; previous checkpoint retained' unless roots.any? { |r| r.is_a?(Sketchup::Group) && r.valid? && r.entities.length > 0 }\n")
        script = (
            "# ARCHFLOW_GENERATED_SCRIPT\n"
            "model = Sketchup.active_model\n"
            + root_guard +
            # SketchUp 2024 rejects save_copy to its own active filename.
            # The guarded host owns saving that bound disposable document.
            f"target = {ruby_target}\n"
            "saved = if File.expand_path(model.path) == File.expand_path(target)\n"
            "  model.save\n"
            "else\n"
            "  model.save_copy(target)\n"
            "end\n"
            "raise 'SketchUp checkpoint save failed' unless saved\n"
            f"{{ saved: true, path: model.path, operation: {json.dumps(operation_name)} }}\n"
        )
        script_path.write_text(script, encoding="utf-8")
        try:
            result = self.client.call("sketchup_eval_project_file", {
                "script_path": str(script_path.resolve()),
                "operation_name": operation_name,
            })
            return result if isinstance(result, dict) else {"result": result}
        finally:
            script_path.unlink(missing_ok=True)
