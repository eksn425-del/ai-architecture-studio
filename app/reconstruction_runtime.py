from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .models import AgentSession, ConversationRequest, ProjectContext
from .reference_assets import discover_project_reference_images


ResolvedAction = Literal["clarify", "plan", "execute"]
ReconstructionState = Literal["idle", "clarifying", "planned", "building"]


@dataclass(frozen=True)
class ReconstructionTurnPolicy:
    action: ResolvedAction
    tools_enabled: bool
    tool_profile: Literal["reconstruction_coding"]
    reference_categories: tuple[str, ...]
    reasoning_effort_preference: Literal["low"]
    user_gate: Literal["clarification", "approval", "none"]


def resolve_reconstruction_action(session: AgentSession, request: ConversationRequest) -> ResolvedAction:
    """Resolve the reconstruction dialogue without asking the coding host to improvise policy.

    Default flow:

    idle -> clarify
    clarifying -> clarify until the user requests a plan
    planned -> plan until explicit approval; building -> execute

    The user/host may explicitly request clarify/plan/execute. Execution is validated
    separately and must never occur before an approved plan exists.
    """
    if request.agent_action in {"clarify", "plan", "execute"}:
        return request.agent_action
    if session.reconstruction_state == "idle":
        return "clarify"
    if session.reconstruction_state == "clarifying":
        return "clarify"
    return "execute" if session.reconstruction_state == "building" else "plan"


def validate_reconstruction_action(session: AgentSession, action: ResolvedAction) -> None:
    """Reject only transitions that could modify SketchUp before user approval."""
    if action == "execute" and session.reconstruction_state not in {"planned", "building"}:
        raise ValueError("图片复刻必须先完成澄清和建模参数/计划确认，之后才能执行 SketchUp 建模。")


def next_reconstruction_state(session: AgentSession, action: ResolvedAction) -> ReconstructionState:
    if action == "clarify":
        return "clarifying"
    if action == "plan":
        return "planned"
    return "building"


def build_reconstruction_turn_policy(
    session: AgentSession,
    request: ConversationRequest,
    *,
    sketchup_session_ready: bool,
) -> ReconstructionTurnPolicy:
    action = resolve_reconstruction_action(session, request)
    validate_reconstruction_action(session, action)
    if action == "execute" and not sketchup_session_ready:
        raise ValueError("请先打开当前项目的 SketchUp 空白副本，再批准执行。")
    user_gate: Literal["clarification", "approval", "none"] = (
        "clarification" if action == "clarify" else
        "approval" if action == "plan" else
        "none"
    )
    return ReconstructionTurnPolicy(
        action=action,
        tools_enabled=bool(action == "execute" and sketchup_session_ready),
        tool_profile="reconstruction_coding",
        reference_categories=("reference", "brief", "site"),
        reasoning_effort_preference="low",
        user_gate=user_gate,
    )


def reconstruction_reference_images(project_dir: Path) -> list[Path]:
    """Return only user reference images; never site/brief/output images."""
    return discover_project_reference_images(project_dir, categories=("reference",))


def require_reconstruction_reference(project_dir: Path) -> list[Path]:
    images = reconstruction_reference_images(project_dir)
    if not images:
        raise ValueError("图片复刻模式至少需要一张 inputs/reference 参考图片。")
    return images


def reconstruction_context_payload(context: ProjectContext, session: AgentSession | None = None) -> dict[str, object]:
    """Keep cheap-model reconstruction context deliberately small.

    Include explicitly uploaded document/site/URL evidence and recent dialogue.
    Historical outputs and unprovided synthetic project briefs remain excluded;
    the actual target image is supplied separately as multimodal input.
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
        for message in context.conversation[-10:]
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
    payload: dict[str, object] = {
        "project_id": context.project_id,
        "project_name": context.project_name,
        "reference_images": references,
        "recent_conversation": recent,
    }
    # Include only explicitly supplied project inputs, never historical outputs.
    payload["provided_documents"] = context.brief.summary[:30000] if context.brief.source_files or context.site.source_files or any(ref.type == "note" and ref.source.startswith("inputs/") for ref in context.references) else ""
    payload["provided_site"] = {"summary": context.site.summary[:8000], "boundary": context.site.boundary} if context.site.source_files else {}
    payload["provided_urls"] = [reference.model_dump(mode="json") for reference in context.references if reference.type == "url"]
    if session is not None:
        payload["reconstruction_state"] = session.reconstruction_state
        payload["clarification_rounds"] = session.clarification_rounds
    return payload
