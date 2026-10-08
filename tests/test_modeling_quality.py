from app.modeling_quality import (
    CANONICAL_REVIEW_VIEWS,
    build_visual_critic_prompt,
    parse_visual_critique_response,
    require_post_write_verification,
    submit_visual_review,
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
    monkeypatch.setattr(
        "app.agent_tools.submit_visual_review",
        lambda project_dir, ruby_state, arguments: {"needs_fix": True, "quality_status": "needs_fix"},
    )
    for state, limit in (({}, 3), ({"villa": {"revision": 5}}, 2)):
        context = surface.prepare(project_dir=tmp_path / "projects" / "budget",
            mcp_enabled=True, model_path=tmp_path / "blank.skp", model_guid="fixture",
            ruby_enabled=True, ruby_state=state, tool_profile="reconstruction_coding")
        with pytest.raises(OSError):
            context.dispatch("sketchup_run_workspace_ruby", {"capture_failure": True})
        for _ in range(limit - 1):
            context.dispatch("sketchup_submit_visual_review", {"views": {}, "critique": "fixture"})
            context.dispatch("sketchup_run_workspace_ruby", {})
        with pytest.raises(MCPCallError, match="预算"):
            context.dispatch("sketchup_run_workspace_ruby", {"script_id": "bypass"})
        assert context.dispatch("sketchup_inspect_owned", {})["success"]
        assert "bypass" not in state



def _current_review_fixture(tmp_path):
    project = tmp_path / "project"
    render_dir = project / "outputs" / "renders"
    render_dir.mkdir(parents=True)
    revisions = {"villa": 3}
    views = {}
    for index, view in enumerate(CANONICAL_REVIEW_VIEWS):
        image = render_dir / f"agent-view-{index:010d}.png"
        image.write_bytes(b"current-png-evidence")
        image.with_suffix(".evidence.json").write_text(
            __import__("json").dumps({
                "path": image.relative_to(project).as_posix(),
                "width": 1200,
                "height": 800,
                "quality_status": "not_accepted",
                "model_revisions": revisions,
            }),
            encoding="utf-8",
        )
        views[view] = image.relative_to(project).as_posix()
    state = {
        "villa": {
            "revision": 3,
            "last_verification": {
                "verified": True,
                "checks": [{"check": "revision", "expected": 3, "actual": 3}],
            },
        }
    }
    return project, state, views


def test_visual_review_receipt_requires_all_current_six_views(tmp_path):
    project, state, views = _current_review_fixture(tmp_path)
    receipt = submit_visual_review(project, state, {
        "views": views,
        "reviewer": {"kind": "independent_host_critic", "status": "ok", "provider": "fixture", "model": "fixture-vl"},
        "critique": (
            "NEEDS_FIX: YES\n"
            "<assessment>Roof remains too heavy.</assessment>\n"
            "<issue priority=\"1\" view=\"roof\">problem: parapet too bulky\n"
            "action: patch roof/parapet only</issue>\n"
            "<keep>front balcony\ncorner louvers</keep>"
        ),
    })
    assert receipt["needs_fix"] is True
    assert receipt["quality_status"] == "needs_fix"
    assert set(receipt["views"]) == set(CANONICAL_REVIEW_VIEWS)
    assert receipt["model_revisions"] == {"villa": 3}
    assert receipt["reviewer"]["kind"] == "independent_host_critic"
    assert receipt["reviewer"]["status"] == "ok"
    assert (project / "runtime/agent_workspace/qa/visual_review.json").is_file()
    assert "NEEDS_FIX: YES" in (project / "runtime/agent_workspace/qa/visual_qa.md").read_text(encoding="utf-8")


def test_visual_review_rejects_stale_revision_and_missing_writer_receipt(tmp_path):
    import json
    import pytest

    project, state, views = _current_review_fixture(tmp_path)
    stale = project / views["rear"]
    sidecar = stale.with_suffix(".evidence.json")
    evidence = json.loads(sidecar.read_text(encoding="utf-8"))
    evidence["model_revisions"] = {"villa": 2}
    sidecar.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError, match="stale"):
        submit_visual_review(project, state, {
            "views": views,
            "critique": "NEEDS_FIX: NO\n<assessment>Current views match.</assessment>",
        })

    evidence["model_revisions"] = {"villa": 3}
    sidecar.write_text(json.dumps(evidence), encoding="utf-8")
    state["villa"].pop("last_verification")
    with pytest.raises(ValueError, match="no verified"):
        submit_visual_review(project, state, {
            "views": views,
            "critique": "NEEDS_FIX: NO\n<assessment>Current views match.</assessment>",
        })


def test_visual_review_rejects_duplicate_or_non_agent_view_paths(tmp_path):
    import pytest

    project, state, views = _current_review_fixture(tmp_path)
    duplicate = dict(views)
    duplicate["rear"] = duplicate["front"]
    with pytest.raises(ValueError, match="distinct"):
        submit_visual_review(project, state, {
            "views": duplicate,
            "critique": "NEEDS_FIX: NO\n<assessment>Current views match.</assessment>",
        })



def test_runtime_requires_visual_review_between_committed_writes(tmp_path, monkeypatch):
    import pytest
    from app.agent_tools import AgentToolSurface
    from app.sketchup_mcp import MCPCallError

    class Executor:
        def __init__(self, *args, **kwargs):
            self.ruby_state = kwargs["ruby_state"]

    monkeypatch.setattr("app.agent_tools.ProjectRubyExecutor", Executor)
    monkeypatch.setattr(
        "app.agent_tools.submit_visual_review",
        lambda project_dir, ruby_state, arguments: {"needs_fix": True, "quality_status": "needs_fix"},
    )
    surface = AgentToolSurface(tmp_path, object(), oss_backends={})
    monkeypatch.setattr(surface, "dynamic_tools", lambda **kwargs: [])

    def run(name, args, **kwargs):
        if name == "sketchup_inspect_owned":
            return {"success": True}
        state = kwargs["project_ruby"].ruby_state
        state["villa"] = {"revision": state.get("villa", {}).get("revision", 0) + 1}
        return {"success": True}

    monkeypatch.setattr(surface, "dispatch", run)
    context = surface.prepare(
        project_dir=tmp_path / "projects" / "review-gate",
        mcp_enabled=True,
        model_path=tmp_path / "blank.skp",
        model_guid="fixture",
        ruby_enabled=True,
        ruby_state={},
        tool_profile="reconstruction_coding",
    )
    context.dispatch("sketchup_run_workspace_ruby", {})
    with pytest.raises(MCPCallError, match="六视图视觉审查"):
        context.dispatch("sketchup_run_workspace_ruby", {})
    context.dispatch("sketchup_submit_visual_review", {"views": {}, "critique": "fixture"})
    context.dispatch("sketchup_run_workspace_ruby", {})
    assert context.quality_state["writes"] == 2
    assert context.quality_state["review"] is None



def test_litellm_host_requires_visual_review_before_final_reply(tmp_path, monkeypatch):
    import json
    import sys
    from types import ModuleType, SimpleNamespace

    from app.agent_tools import AgentToolContext
    from app.litellm_runtime import LiteLLMRuntime

    quality = {"writes": 1, "write_limit": 1, "review": None}
    tool = {
        "type": "function",
        "name": "sketchup_submit_visual_review",
        "description": "read only review",
        "inputSchema": {"type": "object", "properties": {}},
    }

    def dispatch(name, arguments):
        assert name == "sketchup_submit_visual_review"
        quality["review"] = {"needs_fix": True, "quality_status": "needs_fix"}
        return {"success": True, "contentItems": [{"type": "inputText", "text": "review stored"}]}

    runtime = LiteLLMRuntime(tmp_path, model="openai/test-model")
    runtime.session_api_key = "test-only"
    monkeypatch.setattr(
        runtime.tool_surface,
        "prepare",
        lambda **kwargs: AgentToolContext([tool], dispatch, quality),
    )

    calls = []
    module = ModuleType("litellm")

    def completion(**kwargs):
        calls.append(kwargs["messages"])
        if len(calls) == 1:
            return SimpleNamespace(
                choices=[SimpleNamespace(message={"content": "我完成了。", "tool_calls": None})],
                usage={},
            )
        if len(calls) == 2:
            assert any(
                m.get("role") == "user" and "HOST QUALITY GATE" in str(m.get("content"))
                for m in kwargs["messages"]
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(message={
                    "content": None,
                    "tool_calls": [{
                        "id": "review-1",
                        "function": {
                            "name": "sketchup_submit_visual_review",
                            "arguments": json.dumps({}),
                        },
                    }],
                })],
                usage={},
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message={"content": "仍有问题。", "tool_calls": None})],
            usage={},
        )

    module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", module)
    result = runtime.respond(
        project_dir=tmp_path,
        thread_id=None,
        prompt="execute",
        mcp_enabled=True,
        developer_instructions="builder",
        model_path=tmp_path / "blank.skp",
        model_guid="fixture",
        ruby_state={"villa": {"revision": 1}},
        workflow_mode="image_reconstruction",
        tool_profile="reconstruction_coding",
    )
    assert len(calls) == 3
    assert "PARTIAL" in result.reply
    assert quality["review"]["needs_fix"] is True


def test_litellm_independent_critic_overrides_builder_self_review(tmp_path, monkeypatch):
    import json
    import sys
    from types import ModuleType, SimpleNamespace

    from PIL import Image

    from app.agent_tools import AgentToolContext
    from app.litellm_runtime import LiteLLMRuntime

    project = tmp_path / "project"
    source = project / "inputs" / "reference" / "source.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (20, 20), (200, 200, 200)).save(source)

    render_dir = project / "outputs" / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "villa": {
            "revision": 1,
            "last_verification": {
                "verified": True,
                "checks": [{"check": "revision", "expected": 1, "actual": 1}],
            },
        }
    }
    views = {}
    for index, view in enumerate(CANONICAL_REVIEW_VIEWS):
        image = render_dir / f"agent-view-{index:010d}.png"
        Image.new("RGB", (20, 20), (10 + index, 20, 30)).save(image)
        image.with_suffix(".evidence.json").write_text(json.dumps({
            "path": image.relative_to(project).as_posix(),
            "width": 20,
            "height": 20,
            "quality_status": "not_accepted",
            "model_revisions": {"villa": 1},
        }), encoding="utf-8")
        views[view] = image.relative_to(project).as_posix()

    quality = {"writes": 1, "write_limit": 3, "review": None}
    review_tool = {
        "type": "function",
        "name": "sketchup_submit_visual_review",
        "description": "submit current views",
        "inputSchema": {"type": "object", "properties": {}},
    }

    def dispatch(name, arguments):
        assert name == "sketchup_submit_visual_review"
        builder = submit_visual_review(project, state, arguments)
        quality["review"] = builder
        return {
            "success": True,
            "visual_review": builder,
            "contentItems": [{"type": "inputText", "text": json.dumps({"visual_review": builder})}],
        }

    runtime = LiteLLMRuntime(tmp_path, model="openai/test-model")
    runtime.session_api_key = "test-only"
    monkeypatch.setattr(
        runtime.tool_surface,
        "prepare",
        lambda **kwargs: AgentToolContext([review_tool], dispatch, quality),
    )

    calls = []
    module = ModuleType("litellm")

    def completion(**kwargs):
        calls.append(kwargs)
        system = str(kwargs["messages"][0].get("content", ""))
        if "INDEPENDENT host critic" in system:
            assert "tools" not in kwargs
            return SimpleNamespace(
                choices=[SimpleNamespace(message={
                    "content": (
                        "NEEDS_FIX: NO\n"
                        "<assessment>Independent source-to-current review finds no blocking mismatch.</assessment>\n"
                        "<keep>overall massing\nopenings</keep>"
                    )
                })],
                usage={"prompt_tokens": 11, "completion_tokens": 7},
            )
        if len([call for call in calls if "INDEPENDENT host critic" not in str(call["messages"][0].get("content", ""))]) == 1:
            return SimpleNamespace(
                choices=[SimpleNamespace(message={
                    "content": None,
                    "tool_calls": [{
                        "id": "review-builder",
                        "function": {
                            "name": "sketchup_submit_visual_review",
                            "arguments": json.dumps({
                                "views": views,
                                "critique": (
                                    "NEEDS_FIX: YES\n"
                                    "<assessment>Builder thinks roof is wrong.</assessment>\n"
                                    "<issue priority=\"1\" view=\"roof\">problem: roof wrong\n"
                                    "action: change roof</issue>\n"
                                    "<keep>massing</keep>"
                                ),
                            }),
                        },
                    }],
                })],
                usage={"prompt_tokens": 5, "completion_tokens": 3},
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message={"content": "完成独立审查。", "tool_calls": None})],
            usage={"prompt_tokens": 4, "completion_tokens": 2},
        )

    module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", module)

    result = runtime.respond(
        project_dir=project,
        thread_id=None,
        prompt="execute",
        mcp_enabled=True,
        developer_instructions="builder",
        model_path=project / "outputs/model/blank-disposable-fixture.skp",
        model_guid="fixture",
        ruby_state=state,
        workflow_mode="image_reconstruction",
        tool_profile="reconstruction_coding",
    )
    review = json.loads((project / "runtime/agent_workspace/qa/visual_review.json").read_text(encoding="utf-8"))
    assert result.reply == "完成独立审查。"
    assert review["needs_fix"] is False
    assert review["reviewer"]["kind"] == "independent_host_critic"
    assert review["reviewer"]["status"] == "ok"
    assert review["builder_self_review"]["needs_fix"] is True
    assert quality["review"]["needs_fix"] is False
    assert result.input_tokens == 20
    assert result.output_tokens == 12


def test_failed_independent_review_cannot_unlock_writer(tmp_path, monkeypatch):
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
        if name == "sketchup_inspect_owned":
            return {"success": True}
        state = kwargs["project_ruby"].ruby_state
        state["villa"] = {"revision": state.get("villa", {}).get("revision", 0) + 1}
        return {"success": True}

    monkeypatch.setattr(surface, "dispatch", run)
    context = surface.prepare(
        project_dir=tmp_path / "projects" / "critic-fail",
        mcp_enabled=True,
        model_path=tmp_path / "blank.skp",
        model_guid="fixture",
        ruby_enabled=True,
        ruby_state={},
        tool_profile="reconstruction_coding",
    )
    context.dispatch("sketchup_run_workspace_ruby", {})
    context.quality_state["review"] = {
        "needs_fix": True,
        "reviewer": {"kind": "independent_host_critic", "status": "failed"},
    }
    with pytest.raises(MCPCallError, match="独立只读视觉审查"):
        context.dispatch("sketchup_run_workspace_ruby", {})
