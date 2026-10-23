from app.reconstruction_runtime import explicit_build_approval
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


@pytest.mark.parametrize("message,expected", [
    ("检查后墙是否把米当英寸。请直接执行修复，不要只写脚本。", "execute"),
    ("能否修复后墙？请直接执行", "clarify"),
    ("检查是否错位。先别建模，请直接执行检查", "clarify"),
    ("请直接执行检查，但这轮只分析，不执行修复", "clarify"),
    ("请直接执行修复。这只是示例，先讨论如何操作", "clarify"),
])
def test_approved_revision_inspection_is_not_automatically_discussion(message, expected):
    session = AgentSession(project_id="demo", reconstruction_state="building")
    request = ConversationRequest(message=message, workflow_mode="image_reconstruction")
    assert resolve_reconstruction_action(session, request) == expected


def test_auto_reconstruction_plans_after_clarification_answers() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="clarifying", clarification_rounds=1)
    request = ConversationRequest(message="1多角度；2含外部；3无尺寸；4允许推测", workflow_mode="image_reconstruction")

    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)
    assert policy.action == "plan"
    assert policy.tools_enabled is False
    assert policy.user_gate == "approval"
    assert next_reconstruction_state(session, policy.action) == "planned"


def test_auto_reconstruction_executes_after_approved_plan() -> None:
    session = AgentSession(project_id="demo", reconstruction_state="planned")
    request = ConversationRequest(message="批准执行", workflow_mode="image_reconstruction", agent_action="execute")

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
    with pytest.raises(ValueError):
        build_reconstruction_turn_policy(session, request, sketchup_session_ready=False)


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


def test_one_uploaded_sheet_does_not_assert_one_camera_view() -> None:
    context = ProjectContext(project_id="demo", project_name="Six-panel sheet",
                             references=[{"type": "image", "source": "inputs/reference/sheet.png"}])
    payload = reconstruction_context_payload(context)
    assert payload["uploaded_image_count"] == 1
    assert payload["view_count"] is None


@pytest.mark.parametrize("message", ["确认", "开始", "继续", "同意", "已确认", "确认吧！", "已确认，开始建模吧", "批准执行", "开始建模", "已批准计划，请继续建模，不要一次写完全部细节", "确认开始建模，不要反复确认"])
def test_natural_approval_opens_execution_after_plan(message):
    session = AgentSession(project_id="demo", reconstruction_state="planned")
    request = ConversationRequest(message=message, workflow_mode="image_reconstruction")
    assert build_reconstruction_turn_policy(session, request, sketchup_session_ready=True).tools_enabled

@pytest.mark.parametrize("message", ["不要开始建模", "不要现在开始建模", "你开始建模了吗？", "先别执行", "确认但尺寸改为12米再建模", "我不同意开始建模", "如果我说开始建模会怎样", "还未批准执行"])
def test_non_approval_does_not_execute(message):
    session = AgentSession(project_id="demo", reconstruction_state="planned")
    request = ConversationRequest(message=message, workflow_mode="image_reconstruction")
    assert not build_reconstruction_turn_policy(session, request, sketchup_session_ready=True).tools_enabled


@pytest.mark.parametrize("action", ["auto", "execute"])
@pytest.mark.parametrize("message, expected", [
    ("把露台栏杆换成深灰金属竖杆，先给我计划，确认后再执行。", "plan"),
    ("先说明窗户降低20%的衔接方案，等我确认。", "plan"),
    ("暂停，不要修改模型。", "clarify"),
    ("暂不执行，这轮只看现有模型。", "clarify"),
    ("不批准，先别建模。", "clarify"),
])
def test_existing_model_stop_and_plan_override_stale_execute(message, expected, action):
    session=AgentSession(project_id="demo",reconstruction_state="building")
    request=ConversationRequest(message=message,workflow_mode="image_reconstruction",agent_action=action)
    policy=build_reconstruction_turn_policy(session,request,sketchup_session_ready=True)
    assert policy.action==expected
    assert not policy.tools_enabled


@pytest.mark.parametrize("message,expected", [
 ("还没有批准执行，等我看完。","clarify"),
 ("未确认，不要现在开始建模。","clarify"),
 ("请直接修复这扇窗，不要修改其他构件。","execute"),
 ("先按已经批准的方案直接修复这扇窗。","execute"),
])
def test_followup_stop_and_scoped_keep_counterexamples(message,expected):
 session=AgentSession(project_id="demo",reconstruction_state="building")
 request=ConversationRequest(message=message,workflow_mode="image_reconstruction")
 assert resolve_reconstruction_action(session,request)==expected

@pytest.mark.parametrize("action",["auto","execute"])
@pytest.mark.parametrize("message,expected",[("还没有确认，等我看完。","clarify"),("先只出方案，不要实际操作。","plan"),("这次仅提供计划。","plan")])
def test_only_plan_and_unconfirmed_followups(message,expected,action):
 session=AgentSession(project_id="demo",reconstruction_state="building")
 assert resolve_reconstruction_action(session,ConversationRequest(message=message,agent_action=action))==expected

@pytest.mark.parametrize("state",["planned","building"])
@pytest.mark.parametrize("message",["先讨论一下窗户为什么错位。","只分析，不做任何改动。"])
def test_readonly_intent_overrides_stale_execute(state,message):
 assert resolve_reconstruction_action(AgentSession(project_id="demo",reconstruction_state=state),ConversationRequest(message=message,agent_action="execute"))=="clarify"

@pytest.mark.parametrize("action",["auto","execute"])
@pytest.mark.parametrize("message",["停止建模。","停止操作模型。","不要实际操作模型。","禁止修改模型。"])
def test_global_stop_synonyms(message,action):
 assert resolve_reconstruction_action(AgentSession(project_id="demo",reconstruction_state="building"),ConversationRequest(message=message,agent_action=action))=="clarify"

@pytest.mark.parametrize("state",["planned","building"])
@pytest.mark.parametrize("message",["确认停止建模。","确认禁止执行。"])
def test_confirm_stop_is_not_execution_approval(state,message):
 assert not explicit_build_approval(message)
 assert resolve_reconstruction_action(AgentSession(project_id="demo",reconstruction_state=state),ConversationRequest(message=message,agent_action="execute"))=="clarify"


@pytest.mark.parametrize("message", [
    "为什么要拦截？我没有限制的，你全部完成",
    "为什么停了？请继续完成剩余部分。",
])
def test_question_then_explicit_completion_keeps_approved_writer(message):
    session = AgentSession(project_id="demo", reconstruction_state="building")
    request = ConversationRequest(message=message, workflow_mode="image_reconstruction")
    assert build_reconstruction_turn_policy(session, request, sketchup_session_ready=True).tools_enabled


@pytest.mark.parametrize("message", [
    "为什么要拦截？", "你全部完成了吗？", "请继续完成？", "请继续完成，先只给计划，等我批准。",
    "暂停，不要修改模型。请继续完成。", "为什么不继续完成？", "如果可以，你全部完成。",
    "我想知道，你全部完成是什么意思", "只解释为什么停了，你全部完成。",
    "为什么停止建模？请继续建模。",
])
def test_completion_question_or_explicit_nonwrite_still_has_no_writer(message):
    session = AgentSession(project_id="demo", reconstruction_state="building")
    request = ConversationRequest(message=message, workflow_mode="image_reconstruction")
    assert not build_reconstruction_turn_policy(session, request, sketchup_session_ready=True).tools_enabled


def test_completion_does_not_skip_initial_approval():
    session = AgentSession(project_id="demo", reconstruction_state="idle")
    request = ConversationRequest(message="为什么没建？你全部完成。", workflow_mode="image_reconstruction")
    assert not build_reconstruction_turn_policy(session, request, sketchup_session_ready=True).tools_enabled
