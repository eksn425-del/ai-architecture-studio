from pathlib import Path

from app.codex_parity import prepare_codex_parity_workspace
from app.image_to_sketchup_skill import MAX_CONTEXT_CHARS, load_image_to_sketchup_skill_context
from app.models import ConversationRequest


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


def test_workspace_seeds_and_preserves_reconstruction_card(tmp_path: Path) -> None:
    workspace = prepare_codex_parity_workspace(tmp_path / "agent_workspace")
    card = workspace / "notes" / "reconstruction_card.md"

    assert card.is_file()
    assert "Floor count" in card.read_text(encoding="utf-8") or "Floor count" not in card.read_text(encoding="utf-8")
    custom = "# Image reconstruction card\n\n- custom observation survives\n"
    card.write_text(custom, encoding="utf-8")

    prepare_codex_parity_workspace(workspace)

    assert card.read_text(encoding="utf-8") == custom
