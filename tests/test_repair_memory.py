import json

import pytest

from app.repair_memory import (
    finalize_latest_repair_attempt,
    load_repair_history,
    record_repair_attempt,
    repair_history_checkpoint,
)
from app.workspace_files import workspace_file_call


def _review(*, needs_fix=True, problem="roof too heavy", action="thin roof"):
    return {
        "needs_fix": needs_fix,
        "assessment": problem if needs_fix else "blocking mismatch cleared",
        "issues": [] if not needs_fix else [{
            "priority": 1,
            "view": "roof",
            "problem": problem,
            "action": action,
        }],
        "keep": ["front balcony"],
        "model_revisions": {"villa": 3},
        "reviewer": {"mode": "host_dedicated_read_only"},
    }


def _writer(revision=4):
    return {
        "script_id": "villa",
        "revision": revision,
        "relative_path": "scripts/villa.rb",
        "update_mode": "edit",
        "source_sha256": "abc123",
        "precommit_keep_guard": {
            "armed": True,
            "passed": True,
            "paths": ["BALCONY"],
        },
        "preservation_verification": {"verified": True},
    }


def test_repair_memory_records_and_finalizes_still_needs_fix(tmp_path):
    project = tmp_path / "project"
    entry = record_repair_attempt(project, _review(), _writer())
    assert entry["status"] == "awaiting_review"
    assert entry["attempt_id"] == "repair-001"

    finalized = finalize_latest_repair_attempt(
        project,
        _review(problem="roof remains too heavy", action="change construction method"),
    )
    assert finalized["status"] == "reviewed"
    assert finalized["outcome"] == "still_needs_fix"

    stored = load_repair_history(project)
    assert len(stored["entries"]) == 1
    assert stored["entries"][0]["writer"]["precommit_keep_guard"]["armed"] is True
    checkpoint = repair_history_checkpoint(project)
    assert "still_needs_fix" in checkpoint
    assert "roof remains too heavy" in checkpoint


def test_repair_memory_marks_fix_accepted_only_after_next_trusted_review_clears_blockers(tmp_path):
    project = tmp_path / "project"
    record_repair_attempt(project, _review(), _writer())
    finalized = finalize_latest_repair_attempt(project, _review(needs_fix=False))
    assert finalized["outcome"] == "accepted"
    assert finalized["after_review"]["needs_fix"] is False


def test_repair_history_is_readable_but_not_model_writable(tmp_path):
    project = tmp_path / "project"
    workspace = project / "runtime" / "agent_workspace"
    record_repair_attempt(project, _review(), _writer())

    listing = workspace_file_call(workspace, "workspace_read", {"relative_path": "qa/"})
    assert "qa/repair_history.json" in listing["files"]

    readback = workspace_file_call(
        workspace,
        "workspace_read",
        {"relative_path": "qa/repair_history.json"},
    )
    assert "repair-001" in readback["content"]

    with pytest.raises(ValueError, match="host-owned"):
        workspace_file_call(
            workspace,
            "workspace_write",
            {
                "relative_path": "qa/repair_history.json",
                "content": json.dumps({"schema_version": 1, "entries": []}),
            },
        )


def test_finalize_without_pending_attempt_is_noop(tmp_path):
    assert finalize_latest_repair_attempt(tmp_path / "project", _review()) is None
