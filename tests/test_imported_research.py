from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.native_agent import AgentTurnResult
from app.agent_tools import AgentToolSurface
from app.imported_research import imported_research_context, MAX_NOTE_BYTES
from app.models import Reference


def test_upload_reaches_actual_conversation_provider_without_write_tools(tmp_path):
    class Provider:
        available = True
        model = 'deterministic-test-fixture'
        reasoning_effort = 'low'
        calls = []
        def respond(self, **kwargs):
            self.calls.append(kwargs)
            assert not kwargs['mcp_enabled']
            tools = AgentToolSurface(tmp_path, None, oss_backends={}).prepare(
                project_dir=kwargs['project_dir'], mcp_enabled=False, model_path=None,
                model_guid='', ruby_enabled=False, ruby_state={})
            assert tools.dynamic_tools == []
            with pytest.raises(ValueError, match='approved execution'):
                tools.dispatch('blender_apply_objects', {'objects': []})
            return AgentTurnResult(thread_id='fixture', reply='研究计划，尺寸待确认。',
                                   provider_name='fixture', model_name=self.model)
    provider = Provider()
    app = create_app(runtime_root=tmp_path, native_agent=provider)
    client = TestClient(app)
    pid = client.post('/api/projects', json={'project_name': 'Imported research'}).json()['project_id']
    base = f'/api/projects/{pid}'
    assert client.post(base+'/blender/session').status_code == 200
    notes = 'Source: https://example.org/architecture\nManual observation: two curved towers.\nDimensions: unverified.'
    result = client.post(base+'/inputs/reference?filename=research.md', content=notes.encode())
    assert result.status_code == 200, result.text
    assert client.post(base+'/conversation', json={'message': '执行', 'agent_action': 'execute'}).status_code == 409
    brief=client.post(base+'/inputs/brief?filename=brief.txt',content='用户原有任务书'.encode('utf-8'))
    assert brief.status_code==200,brief.text
    result = client.post(base+'/conversation', json={'message': '根据上传研究整理计划', 'agent_action': 'plan'})
    assert result.status_code == 200, result.text
    prompt = provider.calls[-1]['prompt']
    assert 'Manual observation: two curved towers.' in prompt
    assert 'https://example.org/architecture' in prompt
    assert 'external_manual_upload_unverified' in prompt and 'NOT live web search' in prompt
    assert not result.json()['agent']['geometry_committed']


@pytest.mark.parametrize('source', ['../secret.md', 'inputs/reference/../../secret.md', '/tmp/secret.md',
                                    'inputs/reference/../secret.md', 'inputs/reference\\secret.md'])
def test_reject_path_escape(tmp_path, source):
    context = SimpleNamespace(references=[Reference(type='note', source=source)])
    with pytest.raises(ValueError):
        imported_research_context(tmp_path, context)


@pytest.mark.parametrize('data', [b'\xff', b'abc\x00def', b' ', b'a'*(MAX_NOTE_BYTES+1)])
def test_reject_malformed_or_oversized(tmp_path, data):
    path = tmp_path/'inputs/reference/notes.md'
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    context = SimpleNamespace(references=[Reference(type='note', source='inputs/reference/notes.md')])
    with pytest.raises(ValueError):
        imported_research_context(tmp_path, context)


def test_reject_link(tmp_path):
    target = tmp_path/'secret.md'; target.write_text('private')
    folder = tmp_path/'inputs/reference'; folder.mkdir(parents=True)
    (folder/'notes.md').symlink_to(target)
    context = SimpleNamespace(references=[Reference(type='note', source='inputs/reference/notes.md')])
    with pytest.raises(ValueError):
        imported_research_context(tmp_path, context)


def test_bad_note_blocks_provider_and_unknown_image_role_still_blocks(tmp_path):
    class NeverCalled:
        available = True
        model = 'fixture'
        reasoning_effort = 'low'
        def respond(self, **kwargs):
            pytest.fail('invalid evidence must not reach provider')
    app = create_app(runtime_root=tmp_path, native_agent=NeverCalled())
    client = TestClient(app)
    pid = client.post('/api/projects', json={'project_name': 'Bad notes'}).json()['project_id']
    base = f'/api/projects/{pid}'
    assert client.post(base+'/blender/session').status_code == 200
    result = client.post(base+'/inputs/reference?filename=bad.md', content=b'\xff')
    assert result.status_code == 200
    result = client.post(base+'/conversation', json={'message': '整理计划', 'agent_action': 'plan'})
    assert result.status_code == 422
    store = app.state.store
    context = store.load_context(pid)
    context.references = [Reference(type='image', source='inputs/reference/unknown.png', evidence_role='unknown')]
    store.save(context, store.project_dir(pid)/'state/project_context.json')
    result = client.post(base+'/conversation', json={'message': '整理计划', 'agent_action': 'plan'})
    assert result.status_code == 409


def test_total_size_is_bounded(tmp_path):
    folder = tmp_path/'inputs/reference'; folder.mkdir(parents=True)
    refs = []
    for index in range(5):
        name = f'notes-{index}.md'
        (folder/name).write_bytes(b'x'*MAX_NOTE_BYTES)
        refs.append(Reference(type='note', source='inputs/reference/'+name))
    with pytest.raises(ValueError, match='total limit'):
        imported_research_context(tmp_path, SimpleNamespace(references=refs))
