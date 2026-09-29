from pathlib import Path

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
