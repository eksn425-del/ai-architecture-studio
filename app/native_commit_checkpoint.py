"""Save a guarded native recovery checkpoint at a committed write boundary."""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .sketchup_mcp import MCPCallError, _generated_script_dir


def _ruby_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("#", "\\#")


def persist_committed_revision(*, project_dir: Path, project_id: str, model_path: Path,
                               model_guid: str, script_id: str, revision: int,
                               root_pid: int, mcp: Any) -> dict[str, Any]:
    """Save the committed model, without moving or overwriting old checkpoints.

    SU checks identity and root metadata on its main thread immediately before
    saving. The immutable copy comes first so it survives a later bound-save
    failure. A failed/ambiguous RPC is never retried as a geometry operation.
    This is a recovery checkpoint, not proof of a native reopen or visual QA.
    """
    project_dir = project_dir.resolve()
    model_dir = project_dir / "outputs" / "model"
    if any(path.is_symlink() for path in (project_dir / "outputs", model_dir)) or not model_dir.resolve().is_relative_to(project_dir):
        raise MCPCallError("Project model directory is not a safe local directory; no save was attempted.")
    model_path = model_path.resolve()
    if (not model_path.is_relative_to(model_dir.resolve()) or
            not model_path.name.lower().startswith("blank-disposable-") or
            model_path.suffix.lower() != ".skp" or not model_path.is_file()):
        raise MCPCallError("Committed geometry exists, but the project model path is not a valid disposable SKP; no save was attempted.")
    if (not model_guid or not re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", script_id) or
            type(revision) is not int or revision < 1 or type(root_pid) is not int or root_pid < 1):
        raise MCPCallError("Committed geometry exists, but checkpoint identity is incomplete; no save was attempted.")
    recovery_dir = model_dir / "committed-revisions"
    if recovery_dir.is_symlink():
        raise MCPCallError("Recovery checkpoint directory is a symbolic link; no save was attempted.")
    recovery_dir.mkdir(parents=True, exist_ok=True)
    if not recovery_dir.resolve().is_relative_to(model_dir.resolve()):
        raise MCPCallError("Recovery checkpoint directory is outside this project; no save was attempted.")
    target = recovery_dir / f"{script_id}-r{revision}-{uuid.uuid4().hex}.skp"
    if target.exists() or target.is_symlink():
        raise MCPCallError("Recovery checkpoint already exists; no save was attempted.")
    transport_dir = _generated_script_dir().expanduser().resolve()
    transport_dir.mkdir(parents=True, exist_ok=True)
    transport = transport_dir / f"studio-commit-checkpoint-{uuid.uuid4().hex}.rb"
    status = target.with_suffix(".status.json")
    cancel = target.with_suffix(".cancel")
    # The bridge wraps each generated script in a SketchUp operation. Schedule
    # the actual save only after that operation returns/commits, then repeat
    # all identity checks in the native timer before touching disk.
    guards = [
        "model = Sketchup.active_model",
        f"raise 'Active model path changed' unless File.expand_path(model.path) == File.expand_path({_ruby_string(str(model_path))})",
        f"raise 'Active model GUID changed' unless model.guid == {_ruby_string(model_guid)}",
        "raise 'Active edit context changed' unless model.active_path.nil?",
        f"root = model.find_entity_by_persistent_id({root_pid})",
        "raise 'Owned root missing or empty' unless root.is_a?(Sketchup::Group) && root.valid? && root.entities.length > 0",
        f"raise 'Owned project changed' unless root.get_attribute('sketchup_architect', 'project_id') == {_ruby_string(project_id)}",
        f"raise 'Owned revision changed' unless root.get_attribute('sketchup_architect', 'revision') == {revision}",
    ]
    code = "\n".join([
        "# ARCHFLOW_GENERATED_SCRIPT",
        *guards,
        "UI.start_timer(0.1, false) do",
        "begin",
        f"raise 'Checkpoint cancelled before save' if File.exist?({_ruby_string(str(cancel))})",
        *guards,
        f"target = {_ruby_string(str(target))}",
        "raise 'Checkpoint already exists' if File.exist?(target)",
        "raise 'Recovery copy save failed' unless model.save_copy(target)",
        "raise 'Bound model save failed; recovery copy may exist' unless model.save",
        f"File.write({_ruby_string(str(status))}, JSON.generate({{finished: true, ok: true}}))",
        "rescue StandardError => error",
        f"File.write({_ruby_string(str(status))}, JSON.generate({{finished: true, ok: false, error: error.message}}))",
        "end",
        "end",
        "{checkpoint_scheduled: true}",
    ]) + "\n"
    transport.write_text(code, encoding="utf-8", newline="\n")
    try:
        result = mcp.call("sketchup_eval_project_file", {
            "script_path": str(transport), "operation_name": "Persist verified project commit",
        })
    except Exception as error:
        cancel.touch()
        raise MCPCallError("Native geometry committed, but checkpoint save is unconfirmed. Keep SketchUp open and recover; do not automatically repeat the write.") from error
    finally:
        transport.unlink(missing_ok=True)
    proof = result.get("result") if isinstance(result, dict) else None
    if not isinstance(proof, dict) or proof.get("checkpoint_scheduled") is not True:
        cancel.touch()
        raise MCPCallError("Native geometry committed, but checkpoint save is unconfirmed. Keep SketchUp open and recover; do not automatically repeat the write.")
    deadline = time.monotonic() + 20
    outcome: dict[str, Any] = {}
    while time.monotonic() < deadline:
        if status.is_file():
            try:
                candidate = json.loads(status.read_text(encoding="utf-8"))
                if isinstance(candidate, dict) and candidate.get("finished") is True:
                    outcome = candidate
                    break
            except (OSError, ValueError):
                pass
        time.sleep(0.1)
    if outcome.get("ok") is not True or not target.is_file() or target.stat().st_size <= 0:
        cancel.touch()
        raise MCPCallError("Native geometry committed, but checkpoint save is unconfirmed. Keep SketchUp open and recover; do not automatically repeat the write.")
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"status": "saved_unverified_reopen", "path": target.relative_to(project_dir).as_posix(),
            "sha256": digest.hexdigest(), "revision": revision, "root_pid": root_pid}
