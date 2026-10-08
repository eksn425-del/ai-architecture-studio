from app.modeling_quality import (
    CANONICAL_REVIEW_VIEWS,
    build_visual_critic_prompt,
    parse_visual_critique_response,
    require_post_write_verification,
)


def test_visual_critic_prompt_is_bounded_and_read_only():
    prompt = build_visual_critic_prompt(["source.png"], CANONICAL_REVIEW_VIEWS)
    assert "at most 3" in prompt
    assert "Do not write Ruby" in prompt
    assert "NEEDS_FIX: YES|NO" in prompt
    for view in CANONICAL_REVIEW_VIEWS:
        assert view in prompt


def test_visual_critique_parser_keeps_top_three_and_keep_list():
    result = parse_visual_critique_response(
        """NEEDS_FIX: YES
<assessment>Facade is close but three large mismatches remain.</assessment>
<issue priority="2" view="roof">problem: roof grid is too coarse
action: refine the current roof group only</issue>
<issue priority="1" view="front">problem: upper opening count is wrong
action: patch the named opening group</issue>
<issue priority="4" view="left">problem: tiny trim mismatch
action: defer</issue>
<issue priority="3" view="rear">problem: rear recess is too shallow
action: deepen only the rear recess</issue>
<keep>
overall massing
balcony slab positions
</keep>"""
    )
    assert result.needs_fix is True
    assert result.malformed is False
    assert [issue.priority for issue in result.issues] == [1, 2, 3]
    assert result.issues[0].view == "front"
    assert result.keep == ("overall massing", "balcony slab positions")


def test_visual_critique_done_does_not_require_issues():
    result = parse_visual_critique_response(
        "NEEDS_FIX: NO\n<assessment>No blocking mismatch remains.</assessment>\n<keep>roof\nopenings</keep>"
    )
    assert result.needs_fix is False
    assert result.malformed is False
    assert not result.issues


def test_post_write_verification_returns_expected_actual_receipt():
    transaction = {
        "status": "committed",
        "owned_after": {
            "objects_total": 4,
            "bounds_mm": {"min": [0, 0, 0], "max": [12000, 8000, 6800]},
        },
    }
    readback = {
        "persistent_id": 701,
        "revision": 3,
        "objects_total": 4,
        "bounds_mm": {"min": [0.0, 0.0, 0.0], "max": [12000.005, 8000.0, 6800.0]},
    }
    receipt = require_post_write_verification(
        transaction, readback, expected_root_pid=701, expected_revision=3
    )
    assert receipt["verified"] is True
    assert all("expected" in check and "actual" in check for check in receipt["checks"])


def test_post_write_verification_rejects_silent_mismatch():
    transaction = {"status": "committed", "owned_after": {"objects_total": 4}}
    readback = {"persistent_id": 701, "revision": 3, "objects_total": 3}
    try:
        require_post_write_verification(
            transaction, readback, expected_root_pid=701, expected_revision=3
        )
    except ValueError as error:
        assert "objects_total" in str(error)
    else:
        raise AssertionError("A mismatched post-write readback must fail.")


def test_verification_rejects_missing_expected_readback_fields():
    import pytest
    for field, expected in (("objects_total", 4), ("bounds_mm", {"min": [0, 0, 0], "max": [1, 1, 1]})):
        with pytest.raises(ValueError, match=field):
            require_post_write_verification(
                {"status": "committed", "owned_after": {field: expected}},
                {"persistent_id": 701, "revision": 3},
                expected_root_pid=701, expected_revision=3,
            )


def test_runtime_write_budget_counts_commits_and_keeps_review_available(tmp_path, monkeypatch):
    import pytest
    from app.agent_tools import AgentToolSurface
    from app.sketchup_mcp import MCPCallError
    class Executor:
        def __init__(self, *args, **kwargs):
            self.ruby_state = kwargs["ruby_state"]
    monkeypatch.setattr("app.agent_tools.ProjectRubyExecutor", Executor)
    surface = AgentToolSurface(tmp_path, object(), oss_backends={})
    monkeypatch.setattr(surface, "dynamic_tools", lambda **kwargs: [])
    def run(name, args, **kwargs):
        if name != "sketchup_run_workspace_ruby":
            return {"success": True}
        state = kwargs["project_ruby"].ruby_state
        key = args.get("script_id", "villa")
        state[key] = {"revision": state.get(key, {}).get("revision", 0) + 1}
        if args.get("capture_failure"):
            raise OSError("capture failed after commit")
        return {"success": True}
    monkeypatch.setattr(surface, "dispatch", run)
    for state, limit in (({}, 3), ({"villa": {"revision": 5}}, 2)):
        context = surface.prepare(project_dir=tmp_path / "projects" / "budget",
            mcp_enabled=True, model_path=tmp_path / "blank.skp", model_guid="fixture",
            ruby_enabled=True, ruby_state=state, tool_profile="reconstruction_coding")
        with pytest.raises(OSError):
            context.dispatch("sketchup_run_workspace_ruby", {"capture_failure": True})
        for _ in range(limit - 1):
            context.dispatch("sketchup_run_workspace_ruby", {})
        with pytest.raises(MCPCallError, match="预算"):
            context.dispatch("sketchup_run_workspace_ruby", {"script_id": "bypass"})
        assert context.dispatch("sketchup_inspect_owned", {})["success"]
        assert "bypass" not in state
