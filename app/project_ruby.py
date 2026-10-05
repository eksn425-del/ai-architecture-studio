from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from .sketchup_mcp import (
    ConfiguredSketchUpMCP,
    MCPCallError,
    SketchUpAdapter,
    _generated_script_dir,
)
from .store import safe_project_id


SCRIPT_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,47}$")
MAX_RUBY_SOURCE_BYTES = 120_000
_FORBIDDEN_SOURCE = re.compile(
    # Reject host/process/reflection namespaces and dispatch primitives even when
    # the source tries to reference them indirectly (for example Object::File,
    # :system, or receiver.public_send(...)). This is a guardrail, not a Ruby VM
    # sandbox; the only trusted execution boundary remains the disposable model.
    r"\b(?:File|Dir|IO|Process|Kernel|Object|BasicObject|Module|RubyVM|ObjectSpace|Marshal|ENV|ARGV|Socket|BasicSocket|TCPSocket|UDPSocket|IPSocket|Thread|Gem|URI|Net|OpenURI|UI)\b"
    r"|\b(?:class|require|load|eval|class_eval|module_eval|instance_eval|system|exec|spawn|fork|exit|abort|at_exit|trap|send|public_send|__send__|method_missing|method|const_get|const_set|autoload|define_method|binding|instance_variable_get|instance_variable_set|instance_variables|singleton_class)\b"
    r"|Sketchup\s*\.\s*(?:active_model|open_models|open_file|exit|send)"
    # Scripts receive the full model for materials/camera, but may only mutate
    # geometry in the injected owned root. Block root-to-model traversal and
    # whole-document edit/save operations from agent-provided source.
    r"|\bmodel\s*\.\s*(?:entities|save|save_copy|close|start_operation|commit_operation|abort_operation)\b"
    r"|\.\s*(?:parent|erase!|erase_entities|clear!|explode|save|save_copy|save_as|close|start_operation|commit_operation|abort_operation|write_image|write_to_file|export|import|open_file|popen|download)\b"
    r"|(?<![A-Za-z0-9_])\$[A-Za-z_][A-Za-z0-9_]*"
    r"|`|%x\s*[({]",
)


def validate_project_ruby_source(script_id: str, ruby_source: str) -> str:
    if not SCRIPT_ID_RE.fullmatch(script_id):
        raise ValueError("script_id must start with a lowercase letter and contain only lowercase letters, numbers, _ or -.")
    if not isinstance(ruby_source, str) or not ruby_source.strip():
        raise ValueError("ruby_source must contain SketchUp Ruby code.")
    if len(ruby_source.encode("utf-8")) > MAX_RUBY_SOURCE_BYTES:
        raise ValueError("ruby_source exceeds the 120 KB project-script limit.")
    match = _FORBIDDEN_SOURCE.search(ruby_source)
    if match:
        raise ValueError(
            f"Ruby source contains a blocked host, reflection, whole-model, or process operation: {match.group(0)!r}. "
            "The host already injects model and root (Sketchup::Group) and owns the transaction/save. "
            "Remove all active_model and start/commit/abort_operation calls, including conditional ones. "
            "Use root.entities for geometry; keep the injected root. Helpers must receive model/root explicitly "
            "or be lambdas capturing them, because Ruby def does not capture local variables."
        )
    return ruby_source


class ProjectRubyExecutor:
    """Executes project-owned modeling source through the already configured Kongxing MCP."""

    def __init__(self, runtime_root: Path, project_id: str, *, expected_model_path: Path,
                 expected_model_guid: str, mcp: ConfiguredSketchUpMCP,
                 ruby_state: dict[str, dict[str, Any]] | None = None,
                 adapter: SketchUpAdapter | None = None):
        self.runtime_root = runtime_root.resolve()
        self.project_id = safe_project_id(project_id)
        self.project_dir = (self.runtime_root / "projects" / self.project_id).resolve()
        self.expected_model_path = expected_model_path.resolve()
        self.expected_model_guid = expected_model_guid
        self.adapter = adapter or SketchUpAdapter(mcp)
        self.mcp = mcp
        self.ruby_state = ruby_state if ruby_state is not None else {}
        allowed_model_root = (self.project_dir / "outputs" / "model").resolve()
        if not self.expected_model_path.is_relative_to(allowed_model_root):
            raise ValueError("Ruby tools require this project's own disposable SketchUp model copy.")
        if self.expected_model_path.suffix.lower() != ".skp" or not self.expected_model_path.name.lower().startswith("blank-disposable-"):
            raise ValueError("Ruby tools require a blank-disposable .skp model copy.")
        if not self.expected_model_guid:
            raise ValueError("Ruby tools require a verified active model GUID.")
        self.state_path = self.project_dir / "runtime" / "project_ruby_state.json"
        if self.state_path.is_symlink():
            raise ValueError("Project Ruby state may not be a symbolic link.")
        if self.state_path.is_file():
            saved = json.loads(self.state_path.read_text(encoding="utf-8"))
            if saved.get("model_path") == str(self.expected_model_path):
                for script_id, state in saved.get("scripts", {}).items():
                    if int(state.get("revision", 0)) > int(self.ruby_state.get(script_id, {}).get("revision", 0)):
                        self.ruby_state[script_id] = state

    def _assert_active_model(self) -> dict[str, Any]:
        identity = self.adapter.get_active_model_identity()
        path = identity.get("model_path")
        guid = identity.get("model_guid")
        if not isinstance(path, str) or Path(path).resolve() != self.expected_model_path:
            raise MCPCallError("The active SketchUp document no longer matches this project's disposable model copy.")
        if not isinstance(guid, str) or guid != self.expected_model_guid:
            raise MCPCallError("The active SketchUp model GUID changed; inspect the current document before modeling.")
        if identity.get("active_context"):
            raise MCPCallError("Exit the active SketchUp group/component edit context before running project Ruby.")
        return identity

    def refresh_active_model_snapshot(self) -> dict[str, Any]:
        """Refresh the per-turn GUID token after an existing MCP tool edits the model."""
        identity = self.adapter.get_active_model_identity()
        if Path(str(identity.get("model_path") or "")).resolve() != self.expected_model_path:
            raise MCPCallError("A SketchUp tool changed the active document; project Ruby remains disabled.")
        if identity.get("active_context") or identity.get("main_thread") is False:
            raise MCPCallError("The active model is not at the verified SketchUp main-thread root context.")
        guid = identity.get("model_guid")
        if not isinstance(guid, str) or not guid:
            raise MCPCallError("SketchUp did not return a fresh model GUID after the previous tool call.")
        self.expected_model_guid = guid
        return identity

    def _project_runtime_path(self) -> Path:
        project_runtime = self.project_dir / "runtime"
        scripts = project_runtime / "scripts"
        reports = scripts / "reports"
        for directory in (project_runtime, scripts, reports):
            directory.mkdir(parents=True, exist_ok=True)
            if directory.is_symlink():
                raise ValueError("Project runtime script directories may not be symbolic links.")
            if not directory.resolve().is_relative_to(project_runtime.resolve()):
                raise ValueError("Project Ruby path resolved outside the project runtime.")
        return scripts.resolve()

    @staticmethod
    def _ruby_string(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)

    def _build_transport_script(self, script_path: Path, report_path: Path,
                                expected_revision: int, root_pid: int | None, update_mode: str = "replace") -> str:
        helper_path = Path(__file__).resolve().parent / "vendor" / "sketchup_architect" / "scripts" / "model_session.rb"
        ruby_lines = [
            "# ARCHFLOW_GENERATED_SCRIPT",
            # A read-only audit may already have defined the same module without
            # loading the transaction methods; always load the small helper file.
            f"load {self._ruby_string(str(helper_path.resolve()))}",
            "model = CodexSketchupArchitect.runtime_model",
            f"raise 'Active model path changed' unless File.expand_path(model.path) == File.expand_path({self._ruby_string(str(self.expected_model_path))})",
            f"raise 'Active model GUID changed' unless model.guid == {self._ruby_string(self.expected_model_guid)}",
            f"source_path = {self._ruby_string(str(script_path))}",
            f"source = File.read(source_path, encoding: 'UTF-8')",
            f"CodexSketchupArchitect.run(project_id: {self._ruby_string(self.project_id)}, expected_guid: {self._ruby_string(self.expected_model_guid)}, expected_revision: {expected_revision}, report_path: {self._ruby_string(str(report_path))}, root_pid: {root_pid!r}) do |model, root|",
            *(["  root.entities.to_a.each { |entity| entity.erase! }"] if update_mode == "replace" else []),
            # Scoped lifecycle glue: source still cannot call erase!/clear! or
            # traverse outside its root. Remove one unambiguous direct child
            # instance so small patches can retain all unrelated object IDs.
            "  remove_owned_group = lambda do |name|",
            "    raise 'Expected a nonempty direct-child group name' unless name.is_a?(String) && !name.empty? && name.length <= 200",
            "    matches = root.entities.to_a.select { |e| (e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)) && e.name == name }",
            "    raise 'Owned child name must match exactly one group or component' unless matches.length == 1",
            "    child = matches.first",
            "    raise 'Owned child is locked' if child.locked?",
            "    removed_pid = child.persistent_id",
            "    child.erase!",
            "    removed_pid",
            "  end",
            "  eval(source, binding, File.basename(source_path), 1)",
            f"  root.set_attribute(CodexSketchupArchitect::DICT, 'project_id', {self._ruby_string(self.project_id)})",
            "  root.set_attribute(CodexSketchupArchitect::DICT, 'role', 'project_root')",
            "end",
        ]
        # Ruby uses nil rather than Python's None spelling.
        return "\n".join(ruby_lines).replace("root_pid: None)", "root_pid: nil)") + "\n"

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        script_id = str(arguments.get("script_id") or "")
        ruby_source = validate_project_ruby_source(script_id, arguments.get("ruby_source"))
        update_mode = str(arguments.get("update_mode") or "replace")
        if update_mode not in {"replace", "edit"}:
            raise ValueError("update_mode must be replace or edit.")
        identity_before = self._assert_active_model()
        scripts_dir = self._project_runtime_path()
        script_path = scripts_dir / f"{script_id}.rb"
        if script_path.is_symlink():
            raise MCPCallError("A project script cannot replace a symbolic link.")
        if not script_path.resolve().is_relative_to(scripts_dir):
            raise MCPCallError("Project Ruby path resolved outside this project's runtime scripts directory.")
        old = self.ruby_state.get(script_id, {})
        revision = int(old.get("revision", 0))
        root_pid = old.get("root_pid")
        if update_mode == "edit" and root_pid is None:
            raise ValueError("edit requires an existing script_id and owned root; create it with replace first.")
        if root_pid is not None:
            root_pid = int(root_pid)
        source_hash = hashlib.sha256(ruby_source.encode("utf-8")).hexdigest()
        new_revision = revision + 1
        temporary_source = script_path.with_suffix(f".rb.{uuid.uuid4().hex}.tmp")
        temporary_source.write_text(ruby_source, encoding="utf-8", newline="\n")
        temporary_source.replace(script_path)

        reports_dir = scripts_dir / "reports"
        report_path = reports_dir / f"{script_id}-r{new_revision}-{uuid.uuid4().hex[:8]}.json"
        transport_dir = _generated_script_dir().expanduser().resolve()
        transport_dir.mkdir(parents=True, exist_ok=True)
        transport_path = transport_dir / f"studio-project-ruby-{uuid.uuid4().hex}.rb"
        if transport_path.exists() or transport_path.is_symlink():
            raise MCPCallError("Could not allocate a fresh Kongxing transport shim.")
        transport_script = self._build_transport_script(script_path, report_path, revision, root_pid, update_mode=update_mode)
        transport_path.write_text(transport_script, encoding="utf-8", newline="\n")
        try:
            result = self.mcp.call("sketchup_eval_project_file", {
                "script_path": str(transport_path.resolve()),
                "operation_name": f"AI Architecture Studio project Ruby {script_id} r{new_revision}",
            })
        finally:
            transport_path.unlink(missing_ok=True)

        report: dict[str, Any] = {}
        if report_path.is_file():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                report = {"status": "unreadable", "report_path": str(report_path)}
        if report.get("status") != "committed":
            detail = report.get("error") or (result.get("text") if isinstance(result, dict) else None) or "The transaction did not report a committed revision."
            raise MCPCallError(str(detail))

        root_pid = report.get("root_pid")
        if not isinstance(root_pid, int):
            raise MCPCallError("The SketchUp transaction committed without returning its owned project root id.")
        identity_after = self.adapter.get_active_model_identity()
        if Path(str(identity_after.get("model_path") or "")).resolve() != self.expected_model_path:
            raise MCPCallError("The active SketchUp document changed during the project Ruby transaction.")
        if not isinstance(identity_after.get("model_guid"), str) or not identity_after.get("model_guid"):
            raise MCPCallError("SketchUp did not return the post-transaction model GUID.")
        # SketchUp can refresh a document GUID after a successful edit/save; the path
        # and upstream-owned root/revision are the persistent project identity.
        self.expected_model_guid = str(identity_after["model_guid"])
        # Persist at the transaction boundary, before screenshot/model readback
        # or the model's next inference can fail or the web request is interrupted.
        self.ruby_state[script_id] = {
            "model_guid": self.expected_model_guid,
            "revision": new_revision,
            "root_pid": root_pid,
            "source_sha256": source_hash,
            "last_report": report_path.relative_to(self.project_dir).as_posix(),
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_state = self.state_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        temporary_state.write_text(json.dumps({"model_path": str(self.expected_model_path), "scripts": self.ruby_state}), encoding="utf-8")
        temporary_state.replace(self.state_path)
        model_info = self.adapter.get_model_info()
        image_path = self.project_dir / "outputs" / "renders" / f"ruby-{script_id}-r{new_revision}.png"
        if image_path.is_symlink():
            raise MCPCallError("A screenshot output path cannot be a symbolic link.")
        image_path.parent.mkdir(parents=True, exist_ok=True)
        self.adapter.capture_view(image_path)
        if not image_path.is_file() or image_path.stat().st_size <= 0:
            raise MCPCallError("The project Ruby transaction completed, but SketchUp did not write a review screenshot.")
        if image_path.stat().st_size > 8 * 1024 * 1024:
            raise MCPCallError("The SketchUp review screenshot exceeds the 8 MB agent payload limit.")

        self.ruby_state[script_id] = {
            "model_guid": self.expected_model_guid,
            "revision": new_revision,
            "root_pid": root_pid,
            "source_sha256": source_hash,
            "last_report": report_path.relative_to(self.project_dir).as_posix(),
            "last_screenshot": image_path.relative_to(self.project_dir).as_posix(),
        }
        summary = {
            "script_id": script_id,
            "script_revision": new_revision,
            "source_sha256": source_hash,
            "transaction": report,
            "model_identity": {
                "guid": identity_after.get("model_guid"),
                "model_name": Path(str(identity_before.get("model_path") or "")).name,
            },
            "model_readback": _safe_model_readback(model_info),
            "screenshot": image_path.relative_to(self.project_dir).as_posix(),
            "transport": "existing Kongxing sketchup_eval_project_file",
        }
        return {
            "success": True,
            "contentItems": [
                {"type": "inputText", "text": json.dumps(summary, ensure_ascii=False, indent=2)},
                {"type": "inputImage", "imageUrl": "data:image/png;base64," + base64.b64encode(image_path.read_bytes()).decode("ascii")},
            ],
        }


def _safe_model_readback(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"value": value}
    allowed = {"entity_count", "units", "selection_count", "bounds", "bounds_m", "model_bounds_m", "model_name", "active_entities", "status", "ok", "success"}
    result: dict[str, Any] = {}
    for key, item in value.items():
        if any(term in key.lower() for term in ("token", "secret", "auth")):
            continue
        if "path" in key.lower() and isinstance(item, str):
            result[key] = Path(item).name
        elif key in allowed:
            result[key] = item
    return result
