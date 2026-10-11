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
