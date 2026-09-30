from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .models import AgentSession, ConversationRequest, ProjectContext
from .reference_assets import discover_project_reference_images


ResolvedAction = Literal["plan", "execute"]


@dataclass(frozen=True)
class ReconstructionTurnPolicy:
    action: ResolvedAction
    tools_enabled: bool
    tool_profile: Literal["reconstruction_coding"]
    reference_categories: tuple[str, ...]
    reasoning_effort_preference: Literal["low"]


def resolve_reconstruction_action(session: AgentSession, request: ConversationRequest) -> ResolvedAction:
    """Resolve the Building-Xuezhang-style plan -> approval -> execution lifecycle.

    ``auto`` means plan until the user has a confirmed plan, then keep editing the
    same model. Explicit ``execute`` is rejected by the host unless a plan already
    exists; this function only resolves intent and does not perform that validation.
    """
    if request.agent_action == "plan":
        return "plan"
    if request.agent_action == "execute":
        return "execute"
    return "execute" if session.reconstruction_state in {"planned", "building"} else "plan"


def build_reconstruction_turn_policy(
    session: AgentSession,
    request: ConversationRequest,
    *,
    sketchup_session_ready: bool,
) -> ReconstructionTurnPolicy:
    action = resolve_reconstruction_action(session, request)
    return ReconstructionTurnPolicy(
        action=action,
        tools_enabled=bool(action == "execute" and sketchup_session_ready),
        tool_profile="reconstruction_coding",
        reference_categories=("reference",),
        reasoning_effort_preference="low",
    )


def reconstruction_reference_images(project_dir: Path) -> list[Path]:
    """Return only user reference images; never site/brief/output images."""
    return discover_project_reference_images(project_dir, categories=("reference",))


def require_reconstruction_reference(project_dir: Path) -> list[Path]:
    images = reconstruction_reference_images(project_dir)
    if not images:
        raise ValueError("图片复刻模式至少需要一张 inputs/reference 参考图片。")
    return images


def reconstruction_context_payload(context: ProjectContext) -> dict[str, object]:
    """Keep cheap-model reconstruction context deliberately small.

    Taskbook/site/program fields are intentionally excluded. The model gets the
    source image as multimodal input, the current reconstruction Skill, and only the
    recent conversation needed to preserve revision continuity.
    """
    recent = [
        {
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
            "metadata": {
                key: value
                for key, value in message.metadata.items()
                if key in {"workflow_mode", "agent_action", "reconstruction_state"}
            },
        }
        for message in context.conversation[-8:]
    ]
    references = [
        {
            "type": reference.type,
            "source": Path(reference.source).name if reference.source else "",
            "title": reference.title,
            "status": reference.status,
        }
        for reference in context.references
        if reference.type == "image"
    ]
    return {
        "project_id": context.project_id,
        "project_name": context.project_name,
        "reference_images": references,
        "recent_conversation": recent,
    }
