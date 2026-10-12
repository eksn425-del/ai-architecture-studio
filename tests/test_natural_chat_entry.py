"""The human chat stream must never be an injected engineering test script."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from app.models import AgentSession, ConversationRequest
from app.reconstruction_runtime import build_reconstruction_turn_policy


def test_natural_approval_is_a_valid_approved_model_execution():
    session = AgentSession(project_id="normal-human-dialog", reconstruction_state="planned")
    req = ConversationRequest(message="确认，按当前计划开始建模。", workflow_mode="image_reconstruction")
    policy = build_reconstruction_turn_policy(session, req, sketchup_session_ready=True)
    assert policy.action == "execute"
    assert policy.tools_enabled is True


def test_frontend_approval_keeps_human_words_separate_from_developer_policy():
    source = (Path(__file__).parents[1] / "app/static/studio.js").read_text(encoding="utf8")
    assert "内部步骤连续自动完成，逐视角检查" not in source
    assert "不要只写脚本就停止" not in source
    assert "executionUserMessage(typed)" in source
    start = source.index("function executionUserMessage(")
    end = source.index("\nfunction ", start + 1)
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is needed to execute actual frontend function")
    probe = (source[start:end] +
             "\nconsole.log(JSON.stringify([executionUserMessage(''),"
             "executionUserMessage('我确认，就照刚才说的建模。')]))")
    result = subprocess.run([node, "-e", probe], capture_output=True, text=True,
                            encoding="utf8", check=True)
    messages = json.loads(result.stdout)
    assert messages == ["确认，按当前计划开始建模。", "我确认，就照刚才说的建模。"]
    assert all("sketchup_" not in message and "JSON" not in message for message in messages)


def test_actual_send_handler_builds_natural_message_without_reference_error():
    source = (Path(__file__).parents[1] / "app/static/studio.js").read_text(encoding="utf8")
    start = source.index('async function sendConversation(')
    end = source.index('  saveDraft();', start)
    # Execute the real entry path, not just a detached approval helper. The
    # previous patch commented out const message with literal backslash-n.
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node is needed for actual send entry regression')
    helper_start = source.index('function executionUserMessage(')
    helper_end = source.index('\nfunction ', helper_start + 1)
    probe = "const state={busy:false,project:{agent_session:{status:'ready',reconstruction_state:'idle'}}};\n"
    probe += "let typed='这三张图是同一栋建筑，请先分析不同视角。'; const $=()=>({value:typed}); const sourceImages=()=>[1,2,3]; const isBuildApproval=()=>true;\n"
    probe += source[helper_start:helper_end] + '\n' + source[start:end] + 'return message; }\n'
    probe += "(async()=>{const first=await sendConversation(null);typed='可以，按这个方案开始建模。';const approved=await sendConversation(null,'execute');console.log(JSON.stringify([first,approved]));})().catch(e=>{console.error(e);process.exit(1)});"
    result = subprocess.run([node,'-e',probe],capture_output=True,text=True,encoding='utf8',check=True)
    assert json.loads(result.stdout)==['这三张图是同一栋建筑，请先分析不同视角。','可以，按这个方案开始建模。']

@pytest.mark.parametrize("utterance", [
    "把顶部玻璃房降低一点，其他部分别动。",
    "我觉得这边幕墙比例不对，帮我调整到和图片一致。",
    "左侧楼梯太陡了，改缓一点，其余不变。",
])
def test_existing_model_natural_feedback_executes_without_new_plan(utterance):
    session = AgentSession(project_id="existing-architecture", reconstruction_state="building")
    req = ConversationRequest(message=utterance, workflow_mode="image_reconstruction")
    policy = build_reconstruction_turn_policy(session, req, sketchup_session_ready=True)
    assert policy.action == "execute"
    assert policy.tools_enabled is True


def test_existing_model_question_is_discussion_only():
    session = AgentSession(project_id="existing-architecture", reconstruction_state="building")
    req = ConversationRequest(message="我觉得屋顶玻璃房有点高，你觉得应该怎么改？", workflow_mode="image_reconstruction")
    policy = build_reconstruction_turn_policy(session, req, sketchup_session_ready=True)
    assert policy.action == "clarify"
    assert policy.tools_enabled is False


def test_existing_model_developer_instruction_keeps_edit_local():
    from app.workflow_context import workflow_developer_instructions
    prompt = workflow_developer_instructions("image_reconstruction", mcp_enabled=True, action="execute")
    assert "SAME model" in prompt
    assert "smallest dependent edit" in prompt
    assert "A question or discussion-only message does not authorize geometry" in prompt
