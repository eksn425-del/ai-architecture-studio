from pathlib import Path

from app.agent_tools import AgentToolSurface
from app.models import AgentSession, ConversationRequest
from app.reference_assets import discover_project_reference_images


def test_reconstruction_request_has_explicit_plan_execute_actions() -> None:
    assert ConversationRequest(message="按图复刻", workflow_mode="image_reconstruction").agent_action == "auto"
    assert ConversationRequest(
        message="先分析",
        workflow_mode="image_reconstruction",
        agent_action="plan",
    ).agent_action == "plan"
    assert ConversationRequest(
        message="批准执行",
        workflow_mode="image_reconstruction",
        agent_action="execute",
    ).agent_action == "execute"


def test_agent_session_tracks_reconstruction_lifecycle() -> None:
    session = AgentSession(project_id="demo")
    assert session.reconstruction_state == "idle"
    session.workflow_mode = "image_reconstruction"
    session.reconstruction_state = "planned"
    assert session.workflow_mode == "image_reconstruction"
    assert session.reconstruction_state == "planned"


def test_reconstruction_reference_scope_excludes_site_and_outputs(tmp_path: Path) -> None:
    project = tmp_path / "project"
    reference = project / "inputs" / "reference" / "target.png"
    site = project / "inputs" / "site" / "site.png"
    output = project / "outputs" / "renders" / "generated.png"
    for path in (reference, site, output):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")

    scoped = discover_project_reference_images(project, categories=("reference",))
    assert scoped == [reference.resolve()]
    assert site.resolve() not in scoped
    assert output.resolve() not in scoped


class _FakeKongxing:
    def list_tools(self):
        return [
            {"name": "sketchup_health", "description": "health", "inputSchema": {"type": "object"}},
            {"name": "sketchup_get_model_context", "description": "context", "inputSchema": {"type": "object"}},
            {"name": "sketchup_export_view_image", "description": "view", "inputSchema": {"type": "object"}},
            {"name": "sketchup_set_camera", "description": "camera", "inputSchema": {"type": "object"}},
            {"name": "sketchup_transform_group", "description": "transform", "inputSchema": {"type": "object"}},
            {"name": "sketchup_undo", "description": "undo", "inputSchema": {"type": "object"}},
            {"name": "sketchup_create_mass", "description": "legacy mass", "inputSchema": {"type": "object"}},
            {"name": "sketchup_create_road", "description": "legacy road", "inputSchema": {"type": "object"}},
            {"name": "sketchup_eval_project_file", "description": "raw eval", "inputSchema": {"type": "object"}},
        ]


class _FakeBackend:
    def __init__(self, names):
        self.names = names

    def list_tools(self):
        return [
            {"name": name, "description": name, "inputSchema": {"type": "object"}}
            for name in self.names
        ]


def test_reconstruction_tool_profile_is_small_and_coding_first(tmp_path: Path) -> None:
    surface = AgentToolSurface(
        tmp_path / "runtime",
        _FakeKongxing(),  # type: ignore[arg-type]
        oss_backends={
            "saie": _FakeBackend(["scene_summary", "create_wall", "cut_opening", "create_roof", "create_furniture", "view_snapshot"]),
            "archflow": _FakeBackend(["run", "check_project"]),
        },
    )

    names = [
        item["name"]
        for item in surface.dynamic_tools(ruby_enabled=True, tool_profile="reconstruction_coding")
    ]

    assert "sketchup_health" in names
    assert "sketchup_get_model_context" in names
    assert "sketchup_export_view_image" in names
    assert "sketchup_create_mass" not in names
    assert "sketchup_create_road" not in names
    assert "sketchup_eval_project_file" not in names
    assert "saie__scene_summary" in names
    assert "saie__view_snapshot" in names
    assert "saie__create_wall" not in names
    assert "saie__cut_opening" not in names
    assert "saie__create_roof" not in names
    assert "saie__create_furniture" not in names
    assert "sketchup_transform_group" not in names
    assert "sketchup_undo" not in names
    assert not any(name.startswith("archflow__") for name in names)
    assert "sketchup_run_workspace_ruby" in names
    assert "sketchup_capture_canonical_view" in names
    assert "sketchup_submit_visual_review" in names
    all_tools = surface.dynamic_tools(
        ruby_enabled=True, tool_profile="reconstruction_coding"
    )
    capture_tool = next(item for item in all_tools if item["name"] == "sketchup_capture_canonical_view")
    assert capture_tool["inputSchema"]["required"] == ["script_id", "view_name"]
    assert capture_tool["inputSchema"]["properties"]["view_name"]["enum"] == [
        "front", "rear", "left", "right", "roof", "oblique"
    ]
    review_tool = next(item for item in all_tools if item["name"] == "sketchup_submit_visual_review")
    assert review_tool["inputSchema"]["required"] == ["views", "critique"]
    assert "critique" in review_tool["inputSchema"]["properties"]
    assert "sketchup_run_project_ruby" not in names


def test_reconstruction_plan_and_execute_require_structured_facade_schedule():
    from app.workflow_context import workflow_developer_instructions

    plan = workflow_developer_instructions(
        "image_reconstruction", mcp_enabled=False, action="plan"
    )
    execute = workflow_developer_instructions(
        "image_reconstruction", mcp_enabled=True, action="execute"
    )
    assert "notes/facade_schedule.json" in plan
    assert "observed" in plan and "user_confirmed" in plan and "inferred" in plan
    assert "notes/facade_schedule.json" in execute
    assert "hard constraints" in execute
