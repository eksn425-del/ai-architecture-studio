from pathlib import Path

from fastapi.testclient import TestClient

from app.codex_parity import prepare_codex_parity_workspace
from app.image_to_sketchup_skill import MAX_CONTEXT_CHARS, load_image_to_sketchup_skill_context
from app.main import create_app
from app.models import AgentSession, ConversationRequest
from app.store import ProjectStore
from app.workflow_context import (
    load_workflow_skill_context,
    workflow_developer_instructions,
    workflow_prompt_note,
    workflow_reference_categories,
    workflow_tool_profile,
)
from tests.conftest import FakeBrain, FakeSketchUp
from tests.test_demo import FakeNativeAgent


def test_image_to_sketchup_skill_is_bounded_and_quality_focused() -> None:
    context = load_image_to_sketchup_skill_context()

    assert len(context) <= MAX_CONTEXT_CHARS
    assert "reconstruction_card.md" in context
    assert "white boxes are an automatic failure" in context
    assert "clarify" in context.lower()
    assert "KNOWN / ESTIMATED / ASSUMED" in context
    assert "Pass 1" in context
    assert "Pass 2" in context
    assert "Pass 3" in context
    assert "NEEDS_FIX" in context
    assert "at most THREE" in context
    assert "KEEP list" in context
    assert "persistent workspace Ruby" in context
    assert "approval" in context.lower()


def test_conversation_request_supports_reconstruction_actions() -> None:
    for action in ("auto", "clarify", "plan", "execute"):
        request = ConversationRequest(
            message="按参考图建模",
            workflow_mode="image_reconstruction",
            agent_action=action,
        )
        assert request.agent_action == action
    assert ConversationRequest(message="继续").workflow_mode == "architecture_design"


def test_reconstruction_clarification_has_no_geometry_tools() -> None:
    context = load_workflow_skill_context("image_reconstruction", mcp_enabled=False)
    prompt_note = workflow_prompt_note("image_reconstruction", "clarify")
    developer = workflow_developer_instructions("image_reconstruction", mcp_enabled=False, action="clarify")

    assert "Image → SketchUp reconstruction skill" in context
    assert "inputs/reference" in prompt_note
    assert "CLARIFICATION turn" in prompt_note
    assert "at most four" in developer
    assert "Do not edit SketchUp geometry" in developer


def test_reconstruction_plan_parameterizes_before_execution() -> None:
    prompt_note = workflow_prompt_note("image_reconstruction", "plan")
    developer = workflow_developer_instructions("image_reconstruction", mcp_enabled=False, action="plan")

    assert "PARAMETER/PLAN turn" in prompt_note
    assert "KNOWN" not in prompt_note or "plan" in prompt_note.lower()
    assert "parameter card" in developer
    assert "estimates" in developer.lower()
    assert "write 无" in developer
    assert "not separate approvals" in developer
    assert "Do not edit SketchUp geometry" in developer
    assert workflow_tool_profile("image_reconstruction") == "reconstruction_coding"
    assert workflow_reference_categories("image_reconstruction") == ("reference", "site", "brief")


def test_reconstruction_execution_is_coding_first() -> None:
    developer = workflow_developer_instructions("image_reconstruction", mcp_enabled=True, action="execute")
    prompt_note = workflow_prompt_note("image_reconstruction", "execute")

    assert "reconstruction coding agent" in developer
    assert "persistent workspace Ruby" in developer
    assert "SAIE only as a helper" in developer
    assert "Do not ask for approval again" in developer
    assert "Execute the persistent Ruby now" in developer
    assert "never separate user approval gates" in developer
    assert "EXECUTION turn" in prompt_note
    assert "correct visible mismatches" in prompt_note


def test_architecture_workflow_remains_available_and_tools_can_be_disabled() -> None:
    architecture = load_workflow_skill_context("architecture_design", mcp_enabled=True)
    no_tools = load_workflow_skill_context("architecture_design", mcp_enabled=False)
    developer = workflow_developer_instructions("architecture_design", mcp_enabled=False)

    assert "Architecture workflow context" in architecture
    assert no_tools == ""
    assert "SketchUp geometry tools are withheld" in developer
    assert workflow_tool_profile("architecture_design") == "full"


def test_workspace_seeds_and_preserves_parameter_card(tmp_path: Path) -> None:
    workspace = prepare_codex_parity_workspace(tmp_path / "agent_workspace")
    card = workspace / "notes" / "reconstruction_card.md"

    assert card.is_file()
    seeded = card.read_text(encoding="utf-8")
    assert "Intended use / required views" in seeded
    assert "Scale anchors" in seeded
    assert "Unseen geometry policy" in seeded
    assert "Estimated modeling dimensions" in seeded
    assert "Persistent build plan" in seeded
    assert "Approval" in seeded

    custom = "# Image reconstruction parameter card\n\n- custom observation survives\n"
    card.write_text(custom, encoding="utf-8")

    prepare_codex_parity_workspace(workspace)

    assert card.read_text(encoding="utf-8") == custom


def test_conversation_integration_contract_is_clarification_first(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    native = FakeNativeAgent()
    sketchup = FakeSketchUp()
    client = TestClient(create_app(runtime, brain=FakeBrain(), sketchup=sketchup, native_agent=native))
    client.get("/api/projects")
    store = ProjectStore(runtime)
    project_id = "demo-cultural-center"
    project_dir = store.project_dir(project_id)
    model = project_dir / "outputs/model/blank-disposable-test.skp"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b"test disposable")
    reference = project_dir / "inputs/reference/test-house.png"
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_bytes(b"fake-image-fixture")
    sketchup.active_model_path = str(model)
    store.save_state(
        project_id,
        AgentSession(
            project_id=project_id,
            status="ready",
            model_path="outputs/model/blank-disposable-test.skp",
            thread_id="thr-fast-assembly",
            workflow_mode="image_reconstruction",
            reconstruction_state="idle",
        ),
        "agent_session.json",
    )

    response = client.post(
        f"/api/projects/{project_id}/conversation",
        json={"message": "按图片复刻", "workflow_mode": "image_reconstruction", "agent_action": "auto"},
    )
    assert response.status_code == 200
    call = native.calls[-1]
    assert "CLARIFICATION turn" in call["prompt"]
    assert "requirements agent" in call["developer_instructions"]
    assert response.json()["agent"]["reconstruction_state"] == "clarifying"


def test_ui_contract_exposes_reconstruction_action_and_approval() -> None:
    static = Path(__file__).resolve().parents[1] / "app/static"
    index = (static / "index.html").read_text(encoding="utf-8")
    studio = (static / "studio.js").read_text(encoding="utf-8")
    assert 'value="image_reconstruction" selected' in index
    assert 'workflow_mode: $("workflow-mode").value' in studio
    assert "agent_action" in studio
    assert "批准" in index or "批准" in studio
