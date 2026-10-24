"""Existing-model inspection must not require approving geometry writes."""
import pytest
from app.agent_tools import AgentToolSurface
from app.blender_backend import BlenderBackend


@pytest.mark.parametrize('revision,requested', [(0, True), (1, False), (1, True)])
def test_reader_capability_is_explicit_existing_model_only(tmp_path, monkeypatch, revision, requested):
    (tmp_path / 'state').mkdir()
    (tmp_path / 'state/modeling_backend.json').write_text('{"backend":"blender"}')
    monkeypatch.setattr('app.blender_backend.shutil.which', lambda _: 'fixture-not-launched')
    calls = []
    def dispatch(self, name, arguments):
        calls.append(name)
        assert name != 'blender_apply_objects', 'Write reached the native backend'
        return {'revision': revision, 'objects': {}}
    monkeypatch.setattr(BlenderBackend, 'dispatch', dispatch)
    context = AgentToolSurface(tmp_path, None, oss_backends={}).prepare(
        project_dir=tmp_path, mcp_enabled=False, model_path=None, model_guid='',
        ruby_enabled=False, ruby_state={}, blender_readonly_tools=requested)
    names = {spec['name'] for spec in context.dynamic_tools}
    expected = {'blender_inspect_scene', 'blender_render_scene',
                'blender_audit_connections', 'blender_audit_clearance'}
    assert names == (expected if requested and revision else set())
    if names:
        assert context.dispatch('blender_inspect_scene', {})['revision'] == revision
        context.dispatch('blender_render_scene', {'view': 'front'})
    for name in ['blender_apply_objects', 'blender_prepare_component', 'execute_python']:
        with pytest.raises(ValueError, match='approved execution'):
            context.dispatch(name, {'objects': []})
    assert 'blender_apply_objects' not in calls


def test_existing_blender_conversation_requests_readers_without_write_permission(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.native_agent import AgentTurnResult
    seen = []
    class ReaderFixture:
        available = True
        model = 'reader-fixture'
        reasoning_effort = 'medium'
        def respond(self, **kw):
            seen.append(kw)
            return AgentTurnResult(thread_id='reader-fixture', reply='只读检查。',
                                   model_name=self.model, provider_name='codex-app-server')
    monkeypatch.setattr('app.blender_backend.shutil.which', lambda _: 'fixture-not-launched')
    monkeypatch.setattr(BlenderBackend, 'dispatch', lambda *_: {'revision': 1, 'objects': {}})
    monkeypatch.setattr('app.contextual_turn.resolve_host_action',
                        lambda *a, **kw: ('clarify', {'user_message_id': 'fixture-user-message'}))
    app = create_app(runtime_root=tmp_path, native_agent=ReaderFixture())
    client = TestClient(app)
    pid = client.post('/api/projects', json={'project_name': 'Read-only review'}).json()['project_id']
    assert client.post(f'/api/projects/{pid}/blender/session').status_code == 200
    response = client.post(f'/api/projects/{pid}/conversation', json={'message': '只检查尺寸，不修改模型。'})
    assert response.status_code == 200, response.text
    assert seen[-1]['blender_readonly_tools'] is True
    assert seen[-1]['mcp_enabled'] is False
