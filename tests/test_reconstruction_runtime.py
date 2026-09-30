from app.models import AgentSession, ConversationRequest, ProjectContext
from app.reconstruction_runtime import (
    build_reconstruction_turn_policy,
    reconstruction_context_payload,
    resolve_reconstruction_action,
)


def test_auto_reconstruction_plans_before_execution() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="idle")
    request = ConversationRequest(message="按图建模", workflow_mode="image_reconstruction")

    assert resolve_reconstruction_action(session, request) == "plan"
    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)
    assert policy.action == "plan"
    assert policy.tools_enabled is False
    assert policy.tool_profile == "reconstruction_coding"
    assert policy.reasoning_effort_preference == "low"


def test_auto_reconstruction_executes_after_plan() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="planned")
    request = ConversationRequest(message="批准执行", workflow_mode="image_reconstruction")

    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)
    assert policy.action == "execute"
    assert policy.tools_enabled is True


def test_explicit_execute_still_requires_ready_sketchup_session() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="planned")
    request = ConversationRequest(
        message="批准执行",
        workflow_mode="image_reconstruction",
        agent_action="execute",
    )

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

    payload = reconstruction_context_payload(context)
    serialized = str(payload)
    assert "SHOULD NOT LEAK" not in serialized
    assert "house.png" in serialized
