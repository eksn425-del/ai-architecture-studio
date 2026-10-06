import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.models import AgentSession, ConversationRequest
from app.reconstruction_runtime import explicit_build_approval, resolve_reconstruction_action

CASES = [
    ('批准当前计划，请直接执行，检查是否错位，不要执行旧整栋基线，不要修改其他部分。', True),
    ('确认开始建模，不要执行旧脚本，完成后验证是否破碎。', True),
    ('批准执行，但尺寸改为12米。', False),
    ('批准执行，但先别建模。', False),
    ('批准开始建模，但是不要修改模型。', False),
    ('不要执行旧计划，先聊一下。', False),
    ('确认，但修改窗户数量。', False),
    ('你确认后是否开始建模？', False),
]

@pytest.mark.parametrize('message,expected', CASES)
def test_scoped_approval_python(message, expected):
    assert explicit_build_approval(message) is expected
    session = AgentSession(project_id='test', reconstruction_state='planned')
    request = ConversationRequest(message=message, workflow_mode='image_reconstruction')
    assert (resolve_reconstruction_action(session, request) == 'execute') is expected

def test_browser_and_server_use_same_approval_decisions():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required to execute actual frontend approval classifier')
    source = Path('app/static/studio.js').read_text(encoding='utf-8')
    function = source.split('function isBuildApproval(message) {', 1)[1].split('\nfunction renderJourney()', 1)[0]
    script = 'function isBuildApproval(message) {' + function
    script += '\nconsole.log(JSON.stringify(' + json.dumps(CASES, ensure_ascii=False) + '.map(([text]) => isBuildApproval(text))))'
    actual = subprocess.run([node, '-e', script], capture_output=True, text=True, encoding='utf-8', check=True)
    assert json.loads(actual.stdout) == [expected for _, expected in CASES]

def test_licensed_upstream_skill_excerpts_loaded_in_product():
    from app.image_to_sketchup_skill import load_image_to_sketchup_skill_context, _IMAGE_TO_SKETCHUP_CONTEXT
    skill = load_image_to_sketchup_skill_context()
    assert skill == _IMAGE_TO_SKETCHUP_CONTEXT
    assert 'Safe face normal' in skill
    assert 'fake automatic' in skill
    for name in ('API_SKILL_LICENSE', 'HARNESS_LICENSE'):
        assert 'MIT License' in Path('app/vendor/sketchup_runtime_skills', name).read_text(encoding='utf-8')

def test_initial_explicit_plan_skips_redundant_questionnaire_but_not_approval():
    session = AgentSession(project_id='test', reconstruction_state='idle')
    request = ConversationRequest(message='两层，宽10米深8米，其他估算，允许推断。请先给我计划。', workflow_mode='image_reconstruction')
    assert resolve_reconstruction_action(session, request) == 'plan'
    from app.reconstruction_runtime import build_reconstruction_turn_policy
    policy = build_reconstruction_turn_policy(session, request, sketchup_session_ready=True)
    assert not policy.tools_enabled
