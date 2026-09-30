import pytest

from app.models import AgentSession, ConversationRequest, ProjectContext
from app.reconstruction_runtime import (
    build_reconstruction_turn_policy,
    next_reconstruction_state,
    reconstruction_context_payload,
    resolve_reconstruction_action,
    validate_reconstruction_action,
)


def test_auto_reconstruction_clarifies_before_planning() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="idle")
    request = ConversationRequest(message="按图建模", workflow_mode="image_reconstruction")

    assert resolve_reconstruction_action(session, request) == "clarify"
    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)
    assert policy.action == "clarify"
    assert policy.tools_enabled is False
    assert policy.user_gate == "clarification"
    assert policy.tool_profile == "reconstruction_coding"
    assert policy.reasoning_effort_preference == "low"
    assert next_reconstruction_state(session, policy.action) == "clarifying"


def test_auto_reconstruction_plans_after_clarification() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="clarifying", clarification_rounds=1)
    request = ConversationRequest(message="1多角度；2含外部；3无尺寸；4允许推测", workflow_mode="image_reconstruction")

    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)
    assert policy.action == "plan"
    assert policy.tools_enabled is False
    assert policy.user_gate == "approval"
    assert next_reconstruction_state(session, policy.action) == "planned"


def test_auto_reconstruction_executes_after_approved_plan() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="planned")
    request = ConversationRequest(message="批准执行", workflow_mode="image_reconstruction")

    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)
    assert policy.action == "execute"
    assert policy.tools_enabled is True
    assert policy.user_gate == "none"
    assert next_reconstruction_state(session, policy.action) == "building"


def test_explicit_execute_is_rejected_before_plan() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="clarifying")
    request = ConversationRequest(
        message="直接开始",
        workflow_mode="image_reconstruction",
        agent_action="execute",
    )

    with pytest.raises(ValueError):
        build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)


def test_explicit_execute_still_requires_ready_sketchup_session() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="planned")
    request = ConversationRequest(
        message="批准执行",
        workflow_mode="image_reconstruction",
        agent_action="execute",
    )

    validate_reconstruction_action(session, "execute")
    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=False)
    assert policy.action == "execute"
    assert policy.tools_enabled is False


def test_reconstruction_context_excludes_brief_and_site() -> None:
    context = ProjectContext(
        project_id="demo",
        project_name="Image reconstruction",
        brief={"summary": "SHOULD NOT LEAK"},
        site={"summary": "SHOULD NOT LEAK"},
        user_intent="SHOULD NOT LEAK",
        references=[{"type": "image", "source": "inputs/reference/house.png"}],
    )
    session = AgentSession(project_id="demo", reconstruction_state="clarifying", clarification_rounds=1)

    payload = reconstruction_context_payload(context, session)
    serialized = str(payload)
    assert "SHOULD NOT LEAK" not in serialized
    assert "house.png" in serialized
    assert payload["reconstruction_state"] == "clarifying"
    assert payload["clarification_rounds"] == 1
