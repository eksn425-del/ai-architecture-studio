"""Offline recovery contract; not a native geometry or visual-quality verdict."""
import json

import pytest

from app.agent_tools import AgentToolSurface
from app.sketchup_mcp import MCPCallError


@pytest.mark.parametrize("failure", ["preflight", "postflight", "after_commit", "rollback", "oversized"])
def test_writer_errors_distinguish_committed_geometry(tmp_path, monkeypatch, failure):
    state = {"case": {"revision": 3, "root_pid": 19}}
    calls = []

    class Executor:
        def __init__(self, *args, **kwargs):
            self.ruby_state = kwargs["ruby_state"]

        def inspect_owned(self, arguments):
            calls.append("inspect")
            if failure == "preflight" or (failure == "postflight" and len(calls) > 1):
                raise MCPCallError('Missing exact owned path ["KEEP","leaf"]')
            return {"success": True, "contentItems": [{"type": "inputText", "text": json.dumps({
                "persistent_id": 501, "objects_total": 4,
                "bounds_mm": {"min": [0, 0, 0], "max": [1, 1, 1]},
            })}]}

    monkeypatch.setattr("app.agent_tools.ProjectRubyExecutor", Executor)
    monkeypatch.setattr("app.agent_tools.submit_visual_review", lambda *args: {
        "needs_fix": True, "quality_status": "needs_fix", "keep": ["KEEP"],
    })
    surface = AgentToolSurface(tmp_path, object(), oss_backends={})
    monkeypatch.setattr(surface, "dynamic_tools", lambda **kwargs: [])

    def write(*args, **kwargs):
        calls.append("write")
        if failure == "rollback":
            raise MCPCallError("Precommit guard aborted transaction")
        state["case"]["revision"] = 4
        if failure == "after_commit":
            raise MCPCallError("Screenshot unavailable after commit")
        return {"success": True, "contentItems": []}

    monkeypatch.setattr(surface, "dispatch", write)
    context = surface.prepare(project_dir=tmp_path / "case", mcp_enabled=True,
                              model_path=tmp_path / "blank.skp", model_guid="fixture",
                              ruby_enabled=True, ruby_state=state, tool_profile="reconstruction_coding")
    context.dispatch("sketchup_submit_visual_review", {"views": {}, "critique": "fixture"})
    paths = [[f"KEEP{i}"] for i in range(257)] if failure == "oversized" else [["KEEP"]]
    with pytest.raises(MCPCallError) as caught:
        context.dispatch("sketchup_run_workspace_ruby", {
            "script_id": "case", "update_mode": "edit",
            "allowed_mutation_paths": [["EDIT"]], "preserve_paths": paths,
        })
    text = str(caught.value)
    if failure in {"postflight", "after_commit"}:
        assert "POST_COMMIT_VERIFICATION_FAILED" in text and "Do not repeat this writer" in text
        assert state["case"]["revision"] == 4
        assert context.quality_state["post_commit_error"]["geometry_already_committed"] is True
        assert context.quality_state["writes"] == 1 and context.quality_state["review"] is None
        assert calls.count("write") == 1
    else:
        assert "POST_COMMIT" not in text and state["case"]["revision"] == 3
        assert context.quality_state["writes"] == 0
        if failure != "rollback":
            assert "KEEP_PREFLIGHT_FAILED" in text and "no geometry was attempted" in text
            assert "write" not in calls
        if failure == "oversized":
            assert "received 257" in text and not calls
