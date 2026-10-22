import pytest
from app.agent_tools import AgentToolSurface, canonical_camera_from_bounds_mm
from app.modeling_quality import (
    CANONICAL_REVIEW_VIEWS,
    build_visual_critic_prompt,
    owned_inspection_fingerprint,
    parse_visual_critique_response,
    require_post_write_verification,
    verify_preserved_owned_paths,
    submit_visual_review,
    validate_facade_schedule_payload,
)


def test_visual_critic_prompt_is_bounded_and_read_only():
    prompt = build_visual_critic_prompt(["source.png"], CANONICAL_REVIEW_VIEWS)
    assert "at most 3" in prompt
    assert "Do not write Ruby" in prompt
    assert "NEEDS_FIX: YES|NO" in prompt
    for view in CANONICAL_REVIEW_VIEWS:
        assert view in prompt


def test_new_building_critic_has_no_old_cafe_project_requirements():
    prompt = build_visual_critic_prompt(["new-user-building.png"], CANONICAL_REVIEW_VIEWS)
    assert "ONLY elements genuinely visible" in prompt
    assert "Do not hallucinate" in prompt
    assert "source-matched views take priority" in prompt
    assert "including canopy/supports, cladding and open bays when visible" not in prompt
    assert "Missing lower annex" not in prompt
    assert "source-versus-current" in prompt


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


def test_visual_critique_rejects_missing_assessment_and_retains_all_keep_blocks():
    result = parse_visual_critique_response(
        "NEEDS_FIX: NO\nUnstructured comparison.\n<keep>glass</keep>\n<keep>roof</keep>"
    )
    assert result.malformed
    assert result.keep == ("glass", "roof")


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


def test_keep_fingerprint_and_preservation_receipt():
    before = {
        "SHELL/LEFT_WALL": {
            "persistent_id": 101,
            "objects_total": 7,
            "bounds_mm": {"min": [0, 0, 0], "max": [200, 8000, 6400]},
        },
        "BALCONY": {
            "persistent_id": 202,
            "objects_total": 4,
            "bounds_mm": {"min": [2500, -1200, 3000], "max": [7000, 0, 3600]},
        },
    }
    after = {
        key: {
            **value,
            "bounds_mm": {
                "min": [float(number) for number in value["bounds_mm"]["min"]],
                "max": [float(number) for number in value["bounds_mm"]["max"]],
            },
        }
        for key, value in before.items()
    }
    receipt = verify_preserved_owned_paths(before, after)
    assert receipt["verified"] is True
    assert receipt["paths"] == ["BALCONY", "SHELL/LEFT_WALL"]
    assert owned_inspection_fingerprint(before["BALCONY"])["persistent_id"] == 202


def test_keep_preservation_rejects_id_count_or_bounds_regression():
    import pytest
    before = {
        "FACADE/LOUVERS": {
            "persistent_id": 301,
            "objects_total": 12,
            "bounds_mm": {"min": [0, 0, 0], "max": [1200, 250, 3200]},
        },
    }
    for field, replacement in (
        ("persistent_id", 999),
        ("objects_total", 11),
        ("bounds_mm", {"min": [0, 0, 0], "max": [1300, 250, 3200]}),
    ):
        changed = {"FACADE/LOUVERS": dict(before["FACADE/LOUVERS"])}
        changed["FACADE/LOUVERS"][field] = replacement
        with pytest.raises(ValueError, match="Protected KEEP path"):
            verify_preserved_owned_paths(before, changed)


def test_deep_keep_binds_collector_even_if_digest_is_identical():
    entry = {'persistent_id': 301, 'objects_total': 12,
             'bounds_mm': {'min': [0,0,0], 'max': [1200,250,3200]},
             'deep_geometry_material_sha256': 'a'*64}
    assert owned_inspection_fingerprint(entry)['deep_fingerprint_collector'] == 'KStudioNativeDeepFingerprint/1'
    graph = {**entry, 'deep_fingerprint_collector': 'KStudioNativeDefinitionGraph/1'}
    assert verify_preserved_owned_paths({'GRID': graph}, {'GRID': graph})['verified']
    with pytest.raises(ValueError, match='deep_fingerprint_collector'):
        verify_preserved_owned_paths({'GRID': entry}, {'GRID': graph})
    with pytest.raises(ValueError, match='Unknown'):
        owned_inspection_fingerprint({**entry, 'deep_fingerprint_collector': 'invented'})


@pytest.mark.parametrize("resumed", [False, True])
def test_post_review_correction_requires_edit_and_verifies_keep_paths(tmp_path, monkeypatch, resumed):
    import json
    import pytest
    from app.agent_tools import AgentToolSurface
    from app.sketchup_mcp import MCPCallError

    class Executor:
        def __init__(self, *args, **kwargs):
            self.ruby_state = kwargs["ruby_state"]

        def inspect_owned(self, arguments):
            path = "/".join(arguments.get("path") or [])
            payload = {
                "persistent_id": 501 if path == "BALCONY" else 500,
                "revision": self.ruby_state.get(arguments["script_id"], {}).get("revision", 0),
                "objects_total": 4,
                "bounds_mm": {"min": [0, 0, 0], "max": [4000, 1200, 3400]},
                "objects": [],
                "next_offset": None,
            }
            return {
                "success": True,
                "contentItems": [{"type": "inputText", "text": json.dumps(payload)}],
            }

    monkeypatch.setattr("app.agent_tools.ProjectRubyExecutor", Executor)
    surface = AgentToolSurface(tmp_path, object(), oss_backends={})
    monkeypatch.setattr(surface, "dynamic_tools", lambda **kwargs: [])
    monkeypatch.setattr(
        "app.agent_tools.submit_visual_review",
        lambda project_dir, ruby_state, arguments: {
            "needs_fix": True,
            "quality_status": "needs_fix",
            "keep": ["balcony"],
        },
    )

    forwarded_keep = []

    def run(name, args, **kwargs):
        if name == "sketchup_inspect_owned":
            return kwargs["project_ruby"].inspect_owned(args)
        if name == "sketchup_run_workspace_ruby":
            if args.get("_keep_expectations"):
                forwarded_keep.extend(args["_keep_expectations"])
            state = kwargs["project_ruby"].ruby_state
            key = args.get("script_id", "villa")
            state[key] = {"revision": state.get(key, {}).get("revision", 0) + 1}
            return {"success": True, "contentItems": []}
        return {"success": True}

    monkeypatch.setattr(surface, "dispatch", run)
    context = surface.prepare(
        project_dir=tmp_path / "projects" / "preserve",
        mcp_enabled=True,
        model_path=tmp_path / "blank.skp",
        model_guid="fixture",
        ruby_enabled=True,
        ruby_state={"villa": {"revision": 1}} if resumed else {},
        tool_profile="reconstruction_coding",
    )
    if not resumed:
        context.dispatch("sketchup_run_workspace_ruby", {"script_id": "villa"})
    context.dispatch("sketchup_submit_visual_review", {"views": {}, "critique": "fixture"})

    with pytest.raises(MCPCallError, match="preserve_paths"):
        context.dispatch(
            "sketchup_run_workspace_ruby",
            {"script_id": "villa", "update_mode": "edit", "allowed_mutation_paths": [["FACADE"]]},
        )
    with pytest.raises(MCPCallError, match="update_mode=edit"):
        context.dispatch(
            "sketchup_run_workspace_ruby",
            {"script_id": "villa", "update_mode": "replace", "preserve_paths": [["BALCONY"]], "allowed_mutation_paths": [["FACADE"]]},
        )

    result = context.dispatch(
        "sketchup_run_workspace_ruby",
        {"script_id": "villa", "update_mode": "edit", "preserve_paths": [["BALCONY"]], "allowed_mutation_paths": [["FACADE"]]},
    )
    assert result["preservation_verification"]["verified"] is True
    assert context.quality_state["preservation"]["paths"] == ["BALCONY"]
    assert result["repair_memory"]["status"] == "awaiting_review"
    assert forwarded_keep == [{
        "path": ["BALCONY"],
        "persistent_id": 501,
        "objects_total": 4,
        "bounds_mm": {"min": [0.0, 0.0, 0.0], "max": [4000.0, 1200.0, 3400.0]},
    }]

    next_review = context.dispatch(
        "sketchup_submit_visual_review",
        {"views": {}, "critique": "fixture"},
    )
    assert next_review["repair_memory"]["outcome"] == "still_needs_fix"
    repair_history = tmp_path / "projects" / "preserve" / "runtime" / "agent_workspace" / "qa" / "repair_history.json"
    assert repair_history.is_file()
    assert "still_needs_fix" in repair_history.read_text(encoding="utf-8")


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
            context.dispatch("sketchup_run_workspace_ruby", {"update_mode": "edit", "allowed_mutation_paths": [["FACADE"]]})
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
                "camera_contract_version": 1,
                "canonical_view": view,
                "canonical_script_id": "villa",
                "camera": {
                    "eye_m": [0.0, -20.0, 3.0],
                    "target_m": [0.0, 0.0, 3.0],
                    "up_m": [0.0, 0.0, 1.0],
                },
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
    assert (project / "runtime/agent_workspace/qa/visual_review.json").is_file()
    assert "NEEDS_FIX: YES" in (project / "runtime/agent_workspace/qa/visual_qa.md").read_text(encoding="utf-8")


def test_visual_review_rejects_invalid_evidence_instead_of_silently_dropping_it(tmp_path):
    import json, pytest
    project, state, views = _current_review_fixture(tmp_path)
    path = project / "runtime/agent_workspace/notes/reconstruction_evidence.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "primary_source": "../../inputs/reference/sheet.png"}))
    with pytest.raises(ValueError, match="Invalid notes/reconstruction_evidence.json"):
        submit_visual_review(project, state, {
            "views": views, "critique": "NEEDS_FIX: NO\n<assessment>Looks correct</assessment>\n<keep>walls</keep>"
        })
    assert not (project / "runtime/agent_workspace/qa/visual_review.json").exists()


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
    with pytest.raises(MCPCallError, match="update_mode=edit"):
        context.dispatch("sketchup_run_workspace_ruby", {})
    context.dispatch("sketchup_run_workspace_ruby", {"update_mode": "edit", "allowed_mutation_paths": [["FACADE"]]})
    assert context.quality_state["writes"] == 2
    assert context.quality_state["review"] is None



def test_litellm_host_requires_visual_review_before_final_reply(tmp_path, monkeypatch):
    import json
    import sys
    from types import ModuleType, SimpleNamespace

    from PIL import Image

    from app.agent_tools import AgentToolContext
    from app.litellm_runtime import LiteLLMRuntime

    reference = tmp_path / "inputs" / "reference" / "source.png"
    reference.parent.mkdir(parents=True)
    Image.new("RGB", (32, 24), "white").save(reference)

    revisions = {"villa": 1}
    view_paths = {}
    render_dir = tmp_path / "outputs" / "renders"
    render_dir.mkdir(parents=True)
    for index, view in enumerate(CANONICAL_REVIEW_VIEWS):
        image = render_dir / f"agent-view-{index:010d}.png"
        Image.new("RGB", (32, 24), "white").save(image)
        image.with_suffix(".evidence.json").write_text(
            json.dumps({
                "path": image.relative_to(tmp_path).as_posix(),
                "width": 32,
                "height": 24,
                "quality_status": "not_accepted",
                "model_revisions": revisions,
                "camera_contract_version": 1,
                "canonical_view": view,
                "canonical_script_id": "villa",
                "camera": {
                    "eye_m": [0.0, -20.0, 3.0],
                    "target_m": [0.0, 0.0, 3.0],
                    "up_m": [0.0, 0.0, 1.0],
                },
            }),
            encoding="utf-8",
        )
        view_paths[view] = image.relative_to(tmp_path).as_posix()

    schedule_dir = tmp_path / "runtime" / "agent_workspace" / "notes"
    schedule_dir.mkdir(parents=True, exist_ok=True)
    (schedule_dir / "facade_schedule.json").write_text(json.dumps({
        "schema_version": 1,
        "views": {
            "front": {"opening_count": 4, "provenance": "observed"},
            "rear": {"opening_count": 3, "provenance": "user_confirmed"},
        },
        "roof": {"parapet": "thin", "provenance": "observed"},
        "user_confirmed": ["rear opening_count=3"],
        "inferred": [],
    }), encoding="utf-8")
    from app.reconstruction_evidence import default_reconstruction_evidence
    evidence = default_reconstruction_evidence()
    evidence["fidelity_mode"] = "single_view_inference"
    evidence["primary_source"] = "inputs/reference/source.png"
    evidence["sources"] = [{
        "path": "inputs/reference/source.png",
        "kind": "exterior_image",
        "provenance": "observed",
        "role": "primary",
    }]
    evidence["exterior_views"]["front"] = {
        "provenance": "observed",
        "source_refs": ["inputs/reference/source.png"],
        "notes": [],
    }
    (schedule_dir / "reconstruction_evidence.json").write_text(
        json.dumps(evidence), encoding="utf-8"
    )

    quality = {"writes": 1, "write_limit": 1, "review": None}
    tool = {
        "type": "function",
        "name": "sketchup_submit_visual_review",
        "description": "read only review",
        "inputSchema": {"type": "object", "properties": {}},
    }

    def dispatch(name, arguments):
        assert name == "sketchup_submit_visual_review"
        assert arguments["_reviewer"]["mode"] == "host_dedicated_read_only"
        assert arguments["critique"].startswith("NEEDS_FIX: YES")
        quality["review"] = {
            "needs_fix": True,
            "quality_status": "needs_fix",
            "reviewer": arguments["_reviewer"],
        }
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
        calls.append(kwargs)
        call_index = len(calls)
        if call_index == 1:
            return SimpleNamespace(
                model=kwargs["model"].split("/", 1)[-1],
                choices=[SimpleNamespace(message={"content": "我完成了。", "tool_calls": None})],
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        if call_index == 2:
            assert any(
                m.get("role") == "user" and "HOST QUALITY GATE" in str(m.get("content"))
                for m in kwargs["messages"]
            )
            return SimpleNamespace(
                model=kwargs["model"].split("/", 1)[-1],
                choices=[SimpleNamespace(message={
                    "content": None,
                    "tool_calls": [{
                        "id": "review-1",
                        "function": {
                            "name": "sketchup_submit_visual_review",
                            "arguments": json.dumps({
                                "views": view_paths,
                                "critique": "NEEDS_FIX: NO\n<assessment>Builder fallback only.</assessment>",
                            }),
                        },
                    }],
                })],
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        if call_index == 3:
            assert "read-only visual critic" in kwargs["messages"][0]["content"]
            assert "tools" not in kwargs
            critic_payload = str(kwargs["messages"][1]["content"])
            assert "FACADE_SCHEDULE" in critic_payload
            assert "RECONSTRUCTION_EVIDENCE" in critic_payload
            assert "single_view_inference" in critic_payload
            assert "hard visual target" in critic_payload
            assert "rear opening_count=3" in critic_payload
            assert '"opening_count": 4' in critic_payload
            return SimpleNamespace(
                model=kwargs["model"].split("/", 1)[-1],
                choices=[SimpleNamespace(message={
                    "content": (
                        "NEEDS_FIX: YES\n"
                        "<assessment>Wall seams remain visible.</assessment>\n"
                        "<issue priority=\"1\" view=\"front\">problem: visible wall seam\n"
                        "action: patch shell only</issue>\n"
                        "<keep>balcony</keep>"
                    ),
                    "tool_calls": None,
                })],
                usage={"prompt_tokens": 100, "completion_tokens": 20},
            )
        return SimpleNamespace(
            model=kwargs["model"].split("/", 1)[-1],
            choices=[SimpleNamespace(message={"content": "仍有问题。", "tool_calls": None})],
            usage={"prompt_tokens": 0, "completion_tokens": 0},
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
        ruby_state={
            "villa": {
                "revision": 1,
                "last_verification": {"verified": True},
            }
        },
        workflow_mode="image_reconstruction",
        tool_profile="reconstruction_coding",
    )
    assert len(calls) == 4
    assert "尚不能判定还原质量通过" in result.reply
    assert quality["review"]["needs_fix"] is True
    assert quality["review"]["reviewer"]["mode"] == "host_dedicated_read_only"
    assert result.input_tokens == 100
    assert result.output_tokens == 20



def test_facade_schedule_validator_accepts_structured_source_facts():
    schedule = validate_facade_schedule_payload({
        "schema_version": 1,
        "dimensions_mm": {
            "overall_width": 10000,
            "overall_depth": 8000,
            "level_height": 3200,
            "floor_count": 2,
        },
        "views": {
            "front": {
                "provenance": "observed",
                "opening_count": 4,
                "door_count": 1,
                "features": ["balcony"],
                "notes": [],
            },
            "rear": {
                "provenance": "user_confirmed",
                "opening_count": 3,
                "door_count": 0,
                "features": [],
                "notes": ["three windows per floor"],
            },
        },
        "roof": {
            "provenance": "observed",
            "type": "flat",
            "parapet": "thin",
            "divisions": ["3x2"],
            "notes": [],
        },
        "global_features": ["corner louvers"],
        "user_confirmed": ["rear opening_count=3"],
        "inferred": [],
    })
    assert schedule["views"]["rear"]["provenance"] == "user_confirmed"


def test_facade_schedule_validator_rejects_unstable_types():
    import pytest

    with pytest.raises(ValueError, match="opening_count"):
        validate_facade_schedule_payload({
            "schema_version": 1,
            "views": {"front": {"provenance": "observed", "opening_count": 3.5}},
        })
    with pytest.raises(ValueError, match="provenance"):
        validate_facade_schedule_payload({
            "schema_version": 1,
            "views": {"front": {"provenance": "hallucinated", "opening_count": 3}},
        })


def test_visual_review_accepts_current_source_matched_pair(tmp_path):
    import json
    from PIL import Image
    from app.modeling_quality import submit_visual_review

    project, state, views = _current_review_fixture(tmp_path)
    source = project / "inputs" / "reference" / "living-room.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 12), "white").save(source)

    current = project / "outputs" / "renders" / "agent-view-interior.png"
    Image.new("RGB", (16, 12), "white").save(current)
    current.with_suffix(".evidence.json").write_text(json.dumps({
        "path": current.relative_to(project).as_posix(),
        "width": 16,
        "height": 12,
        "quality_status": "not_accepted",
        "model_revisions": {"villa": 3},
    }), encoding="utf-8")

    receipt = submit_visual_review(project, state, {
        "views": views,
        "critique": "NEEDS_FIX: NO\n<assessment>Visible evidence is aligned.</assessment>",
        "evidence_pairs": [{
            "source_ref": "inputs/reference/living-room.png",
            "current_view": "outputs/renders/agent-view-interior.png",
            "label": "living room",
        }],
    })
    assert receipt["evidence_pairs"][0]["label"] == "living room"
    assert receipt["evidence_pairs"][0]["model_revisions"] == {"villa": 3}


def test_eight_sheet_panel_coverage_can_exceed_twelve_without_accepting_stale_images(tmp_path):
    import json
    import pytest
    from PIL import Image
    from app.modeling_quality import validate_source_matched_pairs, MAX_SOURCE_MATCHED_PAIRS

    project, _, _ = _current_review_fixture(tmp_path)
    source = project / 'inputs/reference/multi-panel-original.png'
    source.parent.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', (16, 12), 'white').save(source)
    pairs = []
    for n in range(MAX_SOURCE_MATCHED_PAIRS):
        current = project / f'outputs/renders/agent-view-panel-{n}.png'
        Image.new('RGB', (16, 12), 'white').save(current)
        current.with_suffix('.evidence.json').write_text(json.dumps({
            'path': current.relative_to(project).as_posix(),
            'width': 16, 'height': 12, 'model_revisions': {'villa': 3},
        }), encoding='utf-8')
        pairs.append({'source_ref': source.relative_to(project).as_posix(),
                      'current_view': current.relative_to(project).as_posix(),
                      'label': f'actual distinct panel view {n}'})
    assert len(validate_source_matched_pairs(project, {'villa': 3}, pairs)) == 24
    with pytest.raises(ValueError, match='at most 24'):
        validate_source_matched_pairs(project, {'villa': 3}, pairs + [pairs[0]])
    stale = project / pairs[12]['current_view']
    stale.with_suffix('.evidence.json').write_text(json.dumps({'model_revisions': {'villa': 2}}), encoding='utf-8')
    with pytest.raises(ValueError, match='stale'):
        validate_source_matched_pairs(project, {'villa': 3}, pairs)


def test_canonical_camera_contract_is_deterministic_and_axis_aligned():
    bounds = {"min": [0.0, 0.0, 0.0], "max": [10000.0, 8000.0, 6400.0]}
    front = canonical_camera_from_bounds_mm(bounds, "front")
    rear = canonical_camera_from_bounds_mm(bounds, "rear")
    left = canonical_camera_from_bounds_mm(bounds, "left")
    right = canonical_camera_from_bounds_mm(bounds, "right")
    roof = canonical_camera_from_bounds_mm(bounds, "roof")
    oblique = canonical_camera_from_bounds_mm(bounds, "oblique")

    assert front["eye_m"][1] < 0
    assert rear["eye_m"][1] > 8
    assert left["eye_m"][0] < 0
    assert right["eye_m"][0] > 10
    assert roof["eye_m"][2] > 6.4
    assert roof["up_m"] == [0.0, 1.0, 0.0]
    assert oblique["eye_m"][0] > 10 and oblique["eye_m"][1] < 0
    assert front == canonical_camera_from_bounds_mm(bounds, "front")


def test_visual_review_rejects_mislabeled_canonical_camera(tmp_path):
    import json
    import pytest

    project, state, views = _current_review_fixture(tmp_path)
    front = project / views["front"]
    sidecar = front.with_suffix(".evidence.json")
    evidence = json.loads(sidecar.read_text(encoding="utf-8"))
    evidence["canonical_view"] = "rear"
    sidecar.write_text(json.dumps(evidence), encoding="utf-8")

    with pytest.raises(ValueError, match="host-certified canonical front"):
        submit_visual_review(project, state, {
            "views": views,
            "critique": "NEEDS_FIX: NO\n<assessment>Looks aligned.</assessment>",
        })


def test_canonical_capture_dispatch_persists_camera_and_revision_provenance(tmp_path):
    import json
    from PIL import Image

    class Adapter:
        def __init__(self):
            self.camera = None

        def set_camera(self, eye_m, target_m, up_m=None):
            self.camera = {"eye_m": eye_m, "target_m": target_m, "up_m": up_m}

        def capture_view(self, output_path, width=1500, height=950, zoom_extents=True):
            assert zoom_extents is False
            Image.new("RGB", (width, height), "white").save(output_path)
            return {"success": True}

    class ProjectRuby:
        def __init__(self):
            self.ruby_state = {
                "villa": {
                    "revision": 4,
                    "last_verification": {"verified": True},
                }
            }
            self.adapter = Adapter()

        def inspect_owned(self, arguments):
            assert arguments["script_id"] == "villa"
            payload = {
                "script_id": "villa",
                "revision": 4,
                "bounds_mm": {
                    "min": [0.0, 0.0, 0.0],
                    "max": [10000.0, 8000.0, 6400.0],
                },
                "objects": [],
            }
            return {
                "success": True,
                "contentItems": [{"type": "inputText", "text": json.dumps(payload)}],
            }

        def refresh_active_model_snapshot(self):
            return {}

    surface = AgentToolSurface(tmp_path / "runtime", object(), oss_backends={})
    project = tmp_path / "project"
    result = surface.dispatch(
        "sketchup_capture_canonical_view",
        {"script_id": "villa", "view_name": "front"},
        project_dir=project,
        project_ruby=ProjectRuby(),
    )
    evidence = result["visual_evidence"]
    assert evidence["canonical_view"] == "front"
    assert evidence["canonical_script_id"] == "villa"
    assert evidence["model_revisions"] == {"villa": 4}
    assert evidence["camera_contract_version"] == 1
    assert evidence["camera"]["eye_m"][1] < 0
    path = project / evidence["path"]
    assert path.is_file()
    stored = json.loads(path.with_suffix(".evidence.json").read_text(encoding="utf-8"))
    assert stored["camera"] == evidence["camera"]


def test_multi_view_requires_each_observed_source_image_pair(tmp_path):
    from app.modeling_quality import require_observed_source_view_pairs
    project = tmp_path / "project"
    refs = []
    for name in ("front.png", "right.png"):
        path = project / "inputs/reference" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"private source")
        refs.append("inputs/reference/" + name)
    evidence = {"fidelity_mode": "multi_view_reconstruction", "exterior_views": {
        "front": {"provenance": "observed", "source_refs": [refs[0]]},
        "right": {"provenance": "observed", "source_refs": [refs[1]]},
    }}
    with pytest.raises(ValueError, match="missing CURRENT camera pairs"):
        require_observed_source_view_pairs(project, evidence, [{"source_ref": refs[0]}])
    result = require_observed_source_view_pairs(project, evidence, [{"source_ref": r} for r in refs])
    assert result["observed_sources"] == refs
    assert result["required"]


def test_multi_panel_single_source_image_is_not_invented_as_two_files(tmp_path):
    from app.modeling_quality import require_observed_source_view_pairs
    project = tmp_path / "project"
    path = project / "inputs/reference/sheet.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"one collage")
    ref = "inputs/reference/sheet.png"
    evidence = {"fidelity_mode": "multi_view_reconstruction", "exterior_views": {
        "front": {"provenance": "observed", "source_refs": [ref]},
        "right": {"provenance": "observed", "source_refs": [ref]},
    }}
    result = require_observed_source_view_pairs(project, evidence, [{"source_ref": ref}])
    assert result["observed_sources"] == [ref]

def test_harness_parity_restores_only_current_independent_source_review(tmp_path, monkeypatch):
    import json
    from app.modeling_quality import load_current_independent_visual_review
    from app.agent_tools import AgentToolSurface
    from app.sketchup_mcp import MCPCallError
    project, state, views = _current_review_fixture(tmp_path)
    from app.codex_parity import prepare_codex_parity_workspace
    # The actual product seeds its notes/ledger before the independent review.
    prepare_codex_parity_workspace(project / "runtime/agent_workspace")
    source = project / "inputs/reference/source.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"original owner image")
    from app.reference_roles import reference_manifest, manifest_fingerprint
    (project / "state").mkdir(exist_ok=True)
    (project / "state/project_context.json").write_text(json.dumps({"references": [{"source": "inputs/reference/source.png", "evidence_role": "target_building"}]}))
    role_fingerprint = manifest_fingerprint(reference_manifest(project, [source]))
    critique = ("NEEDS_FIX: YES\n<assessment>Roof needs correction.</assessment>\n"
                '<issue priority="1" view="front">problem: folded roof wrong\naction: correct ROOF</issue>\n'
                "<keep>ENTRY</keep>")
    receipt = submit_visual_review(project, state, {
        "views": views, "critique": "".join(critique),
        "_reviewer": {"mode": "dedicated_read_only", "model": "gpt-6.1-sol", "reference_manifest_fingerprint": role_fingerprint},
    })
    assert receipt["evidence_sha256"]
    assert load_current_independent_visual_review(project, state) == receipt

    class Executor:
        def __init__(self, *args, **kwargs):
            self.ruby_state = kwargs["ruby_state"]
    monkeypatch.setattr("app.agent_tools.ProjectRubyExecutor", Executor)
    surface = AgentToolSurface(tmp_path, object(), oss_backends={})
    monkeypatch.setattr(surface, "dynamic_tools", lambda **kwargs: [])
    context = surface.prepare(project_dir=project, mcp_enabled=True,
        model_path=tmp_path / "blank.skp", model_guid="verified",
        ruby_enabled=True, ruby_state=state, tool_profile="reconstruction_coding")
    assert context.quality_state["review_reused"] is True
    assert context.quality_state["review"]["issues"][0]["problem"] == "folded roof wrong"

    # Source, screenshot and sidecar integrity each invalidate a prior verdict.
    source.write_bytes(b"new source image")
    assert load_current_independent_visual_review(project, state) is None
    source.write_bytes(b"original owner image")
    screenshot = project / views["front"]
    screenshot.write_bytes(b"new screenshot")
    assert load_current_independent_visual_review(project, state) is None
    screenshot.write_bytes(b"current-png-evidence")
    sidecar = screenshot.with_suffix(".evidence.json")
    original_sidecar = sidecar.read_bytes()
    sidecar.write_bytes(original_sidecar + b" ")
    assert load_current_independent_visual_review(project, state) is None
    sidecar.write_bytes(original_sidecar)
    assert load_current_independent_visual_review(project, state) == receipt

    # No review survives a new committed revision, even if old views still exist.
    state["villa"]["revision"] = 4
    assert load_current_independent_visual_review(project, state) is None


def test_harness_parity_rejects_self_review_or_old_unhashed_receipt(tmp_path):
    import json
    from app.modeling_quality import load_current_independent_visual_review
    project, state, views = _current_review_fixture(tmp_path)
    arguments = {"views": views, "critique": (
        "NEEDS_FIX: YES\n<assessment>Primary form not aligned.</assessment>\n"
        '<issue priority="1" view="front">problem: wrong roof\naction: change roof</issue>') }
    submit_visual_review(project, state, arguments)
    assert load_current_independent_visual_review(project, state) is None
    arguments["_reviewer"] = {"mode": "dedicated_read_only"}
    receipt = submit_visual_review(project, state, arguments)
    receipt.pop("evidence_sha256")
    qa = project / "runtime/agent_workspace/qa"
    (qa / "visual_review.json").write_text(json.dumps(receipt), encoding="utf8")
    assert load_current_independent_visual_review(project, state) is None


def _feedback_review_fixture(tmp_path, *, accepted=False):
    import json
    from app.models import ProjectContext, Reference
    from app.reference_roles import reference_manifest, manifest_fingerprint
    project, state, views = _current_review_fixture(tmp_path)
    source = project / 'inputs/reference/source.png'
    source.parent.mkdir(parents=True, exist_ok=True); source.write_bytes(b'original target')
    context = ProjectContext(references=[Reference(type='image', source='inputs/reference/source.png',
        evidence_role='target_building', submitted_at='old-turn')])
    (project / 'state').mkdir(exist_ok=True)
    (project / 'state/project_context.json').write_text(context.model_dump_json(), encoding='utf8')
    manifest = reference_manifest(project, [source])
    critique = 'NEEDS_FIX: NO\n<assessment>Source appearance accepted.</assessment>' if accepted else (
        'NEEDS_FIX: YES\n<assessment>Balcony needs depth.</assessment>\n'
        '<issue priority="1" view="front">problem: shallow balcony\naction: recess balcony</issue>')
    receipt = submit_visual_review(project, state, {'views': views, 'critique': critique,
        '_reviewer': {'mode': 'dedicated_read_only', 'reference_manifest': manifest,
            'reference_manifest_fingerprint': manifest_fingerprint(manifest)}})
    return project, state, context, receipt


def _append_feedback(project, state, context, *, role='defect_location', revision=3):
    from app.models import Reference
    image = project / 'inputs/reference/feedback.png'; image.write_bytes(b'current model screenshot')
    context.references.append(Reference(type='image', source='inputs/reference/feedback.png',
        evidence_role=role, role_origin='context_default', evidence_model_revisions={'villa': revision}))
    (project / 'state/project_context.json').write_text(context.model_dump_json(), encoding='utf8')


def test_same_revision_defect_attachment_reuses_verified_source_review_and_restores_only_lifecycle(tmp_path):
    from app.modeling_quality import load_current_independent_visual_review
    from app.contextual_attachments import restore_defect_feedback_state
    from app.models import AgentSession
    project, state, context, receipt = _feedback_review_fixture(tmp_path)
    _append_feedback(project, state, context)
    assert load_current_independent_visual_review(project, state) == receipt
    card = project / 'runtime/agent_workspace/notes/reconstruction_card.md'
    card.parent.mkdir(parents=True, exist_ok=True); card.write_text('Existing approved building.', encoding='utf8')
    session = AgentSession(project_id='fixture', status='ready', model_path='outputs/model/blank.skp', ruby_state=state,
        reconstruction_state='clarifying')
    assert restore_defect_feedback_state(project, session, context)
    assert session.reconstruction_state == 'building'
    # Restoring a lifecycle cannot convert a question/refusal into execution.
    from app.contextual_turn import snapshot_turn, validate_decision
    from app.models import ConversationRequest
    request = ConversationRequest(message='先别修改，只解释阳台的问题。')
    snapshot = snapshot_turn(project, session, request, context)
    raw = dict(action='execute', user_message_id=snapshot['user_message_id'], user_message=request.message,
        plan_sha256=snapshot['plan_sha256'], changes_plan=False, conditional=False, reason='fixture')
    assert validate_decision(raw, snapshot, project=project, session=session, request=request) == 'clarify'


@pytest.mark.parametrize('role,revision', [('target_building',3), ('supporting',3), ('unknown',3), ('defect_location',2)])
def test_appended_target_unknown_supporting_or_stale_defect_cannot_reuse_review(tmp_path, role, revision):
    from app.modeling_quality import load_current_independent_visual_review
    project, state, context, _ = _feedback_review_fixture(tmp_path)
    _append_feedback(project, state, context, role=role, revision=revision)
    assert load_current_independent_visual_review(project, state) is None


def test_accepted_review_only_restores_identity_proof_and_never_becomes_old_writer_veto(tmp_path):
    from app.modeling_quality import load_current_independent_visual_review
    project, state, context, receipt = _feedback_review_fixture(tmp_path, accepted=True)
    _append_feedback(project, state, context)
    assert load_current_independent_visual_review(project, state) is None
    assert load_current_independent_visual_review(project, state, include_accepted=True) == receipt


def test_feedback_cannot_hide_changed_original_or_new_taskbook(tmp_path):
    from app.modeling_quality import load_current_independent_visual_review
    from app.contextual_attachments import restore_defect_feedback_state
    from app.models import AgentSession
    project, state, context, _ = _feedback_review_fixture(tmp_path)
    _append_feedback(project, state, context)
    card = project / 'runtime/agent_workspace/notes/reconstruction_card.md'
    card.parent.mkdir(parents=True, exist_ok=True); card.write_text('Existing building.', encoding='utf8')
    session = AgentSession(project_id='fixture', status='ready', model_path='outputs/model/blank.skp',
        ruby_state=state, reconstruction_state='clarifying')
    context.brief.source_files.append('inputs/brief/new.txt')
    assert not restore_defect_feedback_state(project, session, context)
    context.brief.source_files.clear()
    (project / 'inputs/reference/source.png').write_bytes(b'changed target')
    assert load_current_independent_visual_review(project, state) is None
    assert not restore_defect_feedback_state(project, session, context)
    assert session.reconstruction_state == 'clarifying'

