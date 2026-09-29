from pathlib import Path

from fastapi.testclient import TestClient
from app.main import create_app
from app.models import AgentSession
from app.store import ProjectStore
from tests.conftest import FakeBrain, FakeSketchUp
from tests.test_demo import FakeNativeAgent

from app.codex_parity import prepare_codex_parity_workspace
from app.image_to_sketchup_skill import MAX_CONTEXT_CHARS, load_image_to_sketchup_skill_context
from app.models import ConversationRequest
from app.workflow_context import (
    load_workflow_skill_context,
    workflow_developer_instructions,
    workflow_prompt_note,
)


def test_image_to_sketchup_skill_is_bounded_and_quality_focused() -> None:
    context = load_image_to_sketchup_skill_context()

    assert len(context) <= MAX_CONTEXT_CHARS
    assert "reconstruction_card.md" in context
    assert "box collection is not an acceptable completion" in context
    assert "Pass 1" in context
    assert "Pass 2" in context
    assert "Pass 3" in context
    assert "source-matched" in context
    assert "cost-efficient model" in context


def test_conversation_request_supports_explicit_reconstruction_mode() -> None:
    request = ConversationRequest(message="按参考图建模", workflow_mode="image_reconstruction")

    assert request.workflow_mode == "image_reconstruction"
    assert ConversationRequest(message="继续").workflow_mode == "architecture_design"


def test_reconstruction_workflow_selects_dedicated_skill_and_target_fidelity() -> None:
    context = load_workflow_skill_context("image_reconstruction", mcp_enabled=True)
    prompt_note = workflow_prompt_note("image_reconstruction")
    developer = workflow_developer_instructions("image_reconstruction", mcp_enabled=True)

    assert "Image → SketchUp reconstruction workflow" in context
    assert "visual target to reconstruct" in prompt_note
    assert "Ignore taskbook" in prompt_note
    assert "reconstruction_card.md" in prompt_note
    assert "rough white-box massing" in prompt_note
    assert "source image is the target appearance" in developer
    assert "SAIE semantic tools" in developer
    assert "persistent workspace Ruby" in developer


def test_architecture_workflow_remains_available_and_tools_can_be_disabled() -> None:
    architecture = load_workflow_skill_context("architecture_design", mcp_enabled=True)
    no_tools = load_workflow_skill_context("image_reconstruction", mcp_enabled=False)
    developer = workflow_developer_instructions("architecture_design", mcp_enabled=False)

    assert "Architecture workflow context" in architecture
    assert no_tools == ""
    assert "SketchUp tools are not enabled" in developer


def test_workspace_seeds_and_preserves_reconstruction_card(tmp_path: Path) -> None:
    workspace = prepare_codex_parity_workspace(tmp_path / "agent_workspace")
    card = workspace / "notes" / "reconstruction_card.md"

    assert card.is_file()
    seeded = card.read_text(encoding="utf-8")
    assert "Source and confidence" in seeded
    assert "Facade depth stack" in seeded
    assert "Pass 1" in seeded

    custom = "# Image reconstruction card\n\n- custom observation survives\n"
    card.write_text(custom, encoding="utf-8")

    prepare_codex_parity_workspace(workspace)

    assert card.read_text(encoding="utf-8") == custom


def test_conversation_routes_reconstruction_and_preserves_session(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    native = FakeNativeAgent()
    sketchup = FakeSketchUp()
    client = TestClient(create_app(runtime, brain=FakeBrain(), sketchup=sketchup, native_agent=native))
    client.get("/api/projects")
    store = ProjectStore(runtime)
    project_id = "demo-cultural-center"
    model = store.project_dir(project_id) / "outputs/model/blank-disposable-test.skp"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b"test disposable")
    sketchup.active_model_path = str(model)
    store.save_state(project_id, AgentSession(project_id=project_id, status="ready",
                     model_path="outputs/model/blank-disposable-test.skp", thread_id="thr-fast-assembly"), "agent_session.json")
    for message in ("按图片复刻", "调整阳台"):
        response = client.post(f"/api/projects/{project_id}/conversation", json={
            "message": message, "workflow_mode": "image_reconstruction"})
        assert response.status_code == 200
        call = native.calls[-1]
        assert "Image → SketchUp reconstruction workflow" in call["prompt"]
        assert "visual target to reconstruct" in call["prompt"]
        assert "source image is the target appearance" in call["developer_instructions"]
        assert call["thread_id"] == "thr-fast-assembly"
        assert response.json()["agent"]["workflow_mode"] == "image_reconstruction"
        assert response.json()["project"]["context"]["conversation"][-1]["metadata"]["workflow_mode"] == "image_reconstruction"
    response = client.post(f"/api/projects/{project_id}/conversation", json={"message": "讨论建筑方案"})
    assert response.status_code == 200
    assert "Architecture workflow context" in native.calls[-1]["prompt"]


def test_ui_sends_workflow_mode_and_defaults_to_reconstruction() -> None:
    static = Path(__file__).resolve().parents[1] / "app/static"
    assert 'value="image_reconstruction" selected' in (static / "index.html").read_text(encoding="utf-8")
    assert 'workflow_mode: $("workflow-mode").value' in (static / "studio.js").read_text(encoding="utf-8")
