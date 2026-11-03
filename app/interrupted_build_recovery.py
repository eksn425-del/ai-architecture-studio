"""Reconcile an interrupted first build only after native owned-root proof.

This never authorizes a writer or retries a model operation.  The caller still
routes the current user message through the normal intent and approval gates.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .design_scope_approval import current_reference_fingerprint
from .reference_roles import canonical_plan_text
from .sketchup_mcp import ConnectorUnavailable, MCPCallError


def recover_interrupted_first_build(project_dir: Path, session, adapter, make_executor):
    if session.reconstruction_state != "planned" or not session.model_path:
        return False
    root = project_dir.resolve()
    model = (root / session.model_path).resolve()
    if not model.is_relative_to(root / "outputs" / "model") or not model.is_file():
        return False
    pending_path = root / "runtime" / "pending_design_scope.json"
    epoch_path = root / "runtime" / "relation_execution_epoch.json"
    state_path = root / "runtime" / "project_ruby_state.json"
    card = root / "runtime" / "agent_workspace" / "notes" / "reconstruction_card.md"
    if any(p.is_symlink() or not p.is_file() for p in (pending_path, epoch_path, state_path, card)):
        return False
    try:
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        epoch = json.loads(epoch_path.read_text(encoding="utf-8"))
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        if not all(isinstance(value, dict) for value in (pending, epoch, saved)):
            return False
        scripts = saved.get("scripts")
        if (pending.get("project_identity") != str(root) or pending.get("consumed") is not True
                or pending.get("is_followup") is not False or pending.get("model_revisions")
                or not pending.get("pending_plan_id")
                or epoch.get("pending_plan_id") != pending.get("pending_plan_id")
                or pending.get("reference_manifest_fingerprint") != current_reference_fingerprint(root)
                or pending.get("plan_sha256") != hashlib.sha256(canonical_plan_text(card.read_text(encoding="utf-8")).encode()).hexdigest()
                or saved.get("model_path") != str(model) or not isinstance(scripts, dict) or not scripts):
            return False
        for script_id, state in scripts.items():
            if (not isinstance(script_id, str) or not isinstance(state, dict)
                    or type(state.get("revision")) is not int or state["revision"] < 1
                    or type(state.get("root_pid")) is not int or state["root_pid"] < 1
                    or state.get("durability_status") == "unconfirmed"
                    or not isinstance(state.get("last_verification"), dict)
                    or state["last_verification"].get("verified") is not True):
                return False
            report = (root / str(state.get("last_report") or "")).resolve()
            if not report.is_relative_to(root / "runtime" / "scripts" / "reports") or not report.is_file():
                return False
            record = json.loads(report.read_text(encoding="utf-8"))
            if (not isinstance(record, dict) or record.get("status") != "committed" or record.get("project_id") != root.name
                    or record.get("model_path") != str(model)
                    or record.get("root_pid") != state["root_pid"]
                    or record.get("revision") != state["revision"]):
                return False
        identity = adapter.get_active_model_identity()
        if (not isinstance(identity, dict) or Path(str(identity.get("model_path") or "")).resolve() != model
                or not identity.get("model_guid") or identity.get("active_context")
                or identity.get("main_thread") is False):
            return False
        executor = make_executor(model, identity["model_guid"])
        # inspect_owned validates native path, GUID, project ownership, persistent
        # ID and exact revision inside SketchUp. No code or geometry is replayed.
        for script_id, expected in scripts.items():
            response = executor.inspect_owned({"script_id": script_id, "path": [], "offset": 0, "limit": 1})
            items = response.get("contentItems") if isinstance(response, dict) else None
            if not isinstance(items, list) or not items or not isinstance(items[0], dict):
                return False
            data = json.loads(items[0].get("text", ""))
            if not isinstance(data, dict) or data.get("revision") != expected["revision"] or data.get("read_only") is not True:
                return False
        if adapter.get_active_model_identity() != identity:
            return False
    except (ValueError, OSError, KeyError, TypeError, ConnectorUnavailable, MCPCallError):
        return False
    session.ruby_state = executor.ruby_state
    session.model_guid = identity["model_guid"]
    session.reconstruction_state = "building"
    return True
