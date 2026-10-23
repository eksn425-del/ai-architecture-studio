"""HTTP configuration and selected-runtime dispatch without subprocesses or inference."""
import pytest
from app.native_agent import CodexAppServerRuntime, AgentTurnResult, NativeAgentUnavailable
from app.models import AgentSession
from tests.test_novice_flow import workspace


def configure(client, **updates):
    return client.post('/api/model-settings', json={
        'mode': 'codex-responses', 'model': 'fixture/model',
        'api_base': 'https://api.example.test/v1', 'api_key': 'fixture-only-key',
        'protocol': 'responses', 'compatibility_acknowledged': True,
        'reasoning_effort': 'low', **updates,
    })


@pytest.fixture
def selected(tmp_path, monkeypatch):
    monkeypatch.setattr(CodexAppServerRuntime, 'available', property(lambda _: True))
    monkeypatch.setattr('app.native_agent.subprocess.Popen', lambda *_a, **_k: pytest.fail('No process launch'))
    app, client, project, native, su = workspace(tmp_path)
    monkeypatch.setattr(native, 'respond', lambda **_: pytest.fail('No native login substitution'))
    monkeypatch.setattr(app.state.model_router.china_runtime, 'respond', lambda **_: pytest.fail('No LiteLLM substitution'))
    assert configure(client).status_code == 200
    return app, client, project


def test_http_conversation_dispatches_selected_codex_engine_and_resumes_only_same_identity(selected, monkeypatch):
    app, client, project = selected
    seen = []
    def respond(self, **kwargs):
        assert self.api_provider.api_base == 'https://api.example.test/v1'
        seen.append(kwargs)
        return AgentTurnResult(thread_id='api-thread', reply='Fixture read-only answer.',
            provider_name=self.provider_name, model_name=self.model, reasoning_effort='low',
            input_tokens=12, output_tokens=5)
    monkeypatch.setattr(CodexAppServerRuntime, 'respond', respond)
    url=f'/api/projects/{project}/conversation'
    payload={'message':'先聊一下方案', 'agent_action':'clarify', 'workflow_mode':'image_reconstruction'}
    first=client.post(url, json=payload)
    assert first.status_code == 200, first.text
    assert first.json()['agent']['provider'] == 'codex-responses'
    assert first.json()['agent']['model'] == 'fixture/model'
    assert first.json()['agent']['agent_engine'] == 'codex-app-server'
    assert seen[-1]['thread_id'] is None and callable(seen[-1]['progress_callback'])
    assert client.post(url, json=payload).status_code == 200
    assert seen[-1]['thread_id'] == 'api-thread'
    assert configure(client, api_key='fixture-different-account').status_code == 200
    assert client.post(url, json=payload).status_code == 200
    assert seen[-1]['thread_id'] is None
    # Clearing only this explicit route does not select login or legacy API.
    assert client.delete('/api/model-settings/credential?mode=codex-responses').status_code == 200
    count=len(seen)
    rejected=client.post(url, json=payload)
    assert rejected.status_code == 503 and len(seen) == count
    assert app.state.model_router.economy_route.provider == 'codex-responses'


@pytest.mark.parametrize('changed', ['provider', 'model', 'endpoint', 'credential', 'legacy_unbound'])
def test_route_identity_never_resumes_foreign_provider_thread(selected, changed):
    app, client, project = selected
    router=app.state.model_router
    session=AgentSession(project_id=project, thread_id='foreign-thread', provider='codex-responses',
        model='fixture/model', runtime_identity=router.runtime_identity('economy'))
    assert router.resumable_thread(session, 'economy') == 'foreign-thread'
    if changed == 'provider': session.provider='codex-app-server'
    elif changed == 'model': session.model='other-model'
    elif changed == 'endpoint': assert configure(client, api_base='https://other.example.test/v1').status_code == 200
    elif changed == 'credential': assert configure(client, api_key='other-fixture-key').status_code == 200
    else: session.runtime_identity=''
    assert router.resumable_thread(session, 'economy') is None


def test_new_monetary_guard_blocks_dispatch_without_mutating_existing_selection(selected, monkeypatch):
    app, _, _ = selected
    router=app.state.model_router
    monkeypatch.setenv('K_STUDIO_LOCAL_API_TEST_BUDGET', '/fixture/do-not-read-budget')
    monkeypatch.setattr(router.codex_responses_runtime, 'respond', lambda **_: pytest.fail('Cap must block before dispatch'))
    with pytest.raises(NativeAgentUnavailable, match='monetary budget'):
        router.respond(tier='economy')
    assert router.status()['providers']['codex-responses']['available'] is False
    assert router.route('economy').provider == 'codex-responses'


def test_selected_api_readonly_intent_uses_same_runtime_not_default_login(selected, monkeypatch):
    import app.contextual_turn as subject
    from app.models import ConversationRequest
    app, _, project=selected
    router=app.state.model_router
    session=AgentSession(project_id=project, reconstruction_state='building', model_path='fixture.skp')
    context=app.state.store.load_context(project)
    seen=[]
    monkeypatch.setattr(subject, 'interpret_turn', lambda runtime, **kw: seen.append(runtime) or ('clarify', {}))
    result=subject.resolve_host_action(router, project=app.state.store.project_dir(project), session=session,
        context=context, request=ConversationRequest(message='先检查当前方案',workflow_mode='image_reconstruction'))
    assert result == ('clarify', {})
    assert seen == [router.codex_responses_runtime]
