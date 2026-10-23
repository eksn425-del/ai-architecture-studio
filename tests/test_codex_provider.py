"""Synthetic provider configuration and shared-runtime contracts; no paid inference."""
import io
import json
import os
import tomllib
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.codex_provider import CodexResponsesProvider, API_KEY_ENV, api_environment, selected_native_provider
from app import native_agent as native


def provider(**kwargs):
    return CodexResponsesProvider('https://fixture.invalid/v1', 'synthetic-secret-A',
                                  compatibility_acknowledged=True, **kwargs)


def runtime(tmp_path, **kwargs):
    return native.CodexAppServerRuntime(tmp_path/'runtime', codex_executable='fixture',
        model='fixture-model', home_root=tmp_path/'codex', api_provider=provider(), **kwargs)


@pytest.mark.parametrize('url', ['http://fixture.invalid/v1', 'https://u:password@fixture.invalid',
    'https://fixture.invalid/v1?key=secret', 'https://fixture.invalid/v1#token',
    'https://fixture.invalid/v1/responses', 'https://fixture.invalid/v1/chat/completions'])
def test_rejects_unsafe_or_wrong_base(url):
    with pytest.raises(ValueError):
        replace(provider(), api_base=url)


def test_protocol_requires_explicit_opt_in():
    with pytest.raises(ValueError, match='acknowledgement'):
        CodexResponsesProvider('https://fixture.invalid', 'synthetic')
    with pytest.raises(ValueError, match='Chat Completions'):
        replace(provider(), protocol='chat')
    assert 'synthetic-secret' not in repr(provider())


def test_api_home_config_never_reads_native_source_or_auth(tmp_path, monkeypatch):
    rt = runtime(tmp_path)
    monkeypatch.setenv('CODEX_HOME', str(tmp_path/'missing-native-home'))
    monkeypatch.setattr(native, '_toml_load', lambda *_: pytest.fail('Native config must not be read'))
    rt._prepare_home(mcp_enabled=True, agent_workspace=tmp_path/'workspace')
    cfg = tomllib.loads((rt.home/'config.toml').read_text())
    assert cfg['model_provider'] == 'kstudio_api'
    assert cfg['model_providers']['kstudio_api']['env_key'] == API_KEY_ENV
    assert cfg['model_providers']['kstudio_api']['requires_openai_auth'] is False
    assert cfg['shell_environment_policy']['exclude'] == [API_KEY_ENV]
    assert cfg['shell_environment_policy']['ignore_default_excludes'] is False
    assert cfg['sandbox_mode'] == 'workspace-write'
    assert cfg['sandbox_workspace_write']['network_access'] is False
    assert cfg['sandbox_workspace_write']['writable_roots'] == [str(tmp_path/'workspace')]
    assert not (rt.home/'auth.json').exists()
    assert provider().api_key not in (rt.home/'config.toml').read_text()
    assert rt.provider_name == 'codex-responses'


def test_explicit_child_environment_drops_native_credentials():
    env = api_environment({'PATH': '/bin', 'HOME': '/home/fixture', 'CODEX_SESSION_ID': 'outer',
        'CODEX_HOME': '/outer', 'OPENAI_API_KEY': 'opposite-secret', 'ANTHROPIC_API_KEY': 'unrelated',
        'CUSTOM_AUTH': 'unrelated', 'HTTP_PROXY': 'http://127.0.0.1:1234'}, provider())
    assert env == {'PATH': '/bin', 'HOME': '/home/fixture', 'HTTP_PROXY': 'http://127.0.0.1:1234',
                   API_KEY_ENV: provider().api_key}


def test_provider_model_key_and_endpoint_isolate_sessions(tmp_path):
    rt = runtime(tmp_path)
    for p in [replace(provider(), api_key='synthetic-secret-B'),
              replace(provider(), api_base='https://another.invalid/v1'),
              replace(provider(), provider_id='another')]:
        other = native.CodexAppServerRuntime(tmp_path/'runtime', home_root=tmp_path/'codex',
            model='fixture-model', api_provider=p)
        assert other.home != rt.home and other.session_identity != rt.session_identity
    assert provider().identity('other-model') != rt.session_identity


@pytest.mark.parametrize('budget', ['K_STUDIO_LOCAL_API_TEST_BUDGET', 'K_STUDIO_OPERATOR_MAX_USD'])
def test_budgeted_api_profiles_fail_before_config_or_process(tmp_path, monkeypatch, budget):
    rt = runtime(tmp_path)
    monkeypatch.setenv(budget, 'fixture-existing-liability-ledger')
    monkeypatch.setattr(native.subprocess, 'Popen', lambda *_a, **_k: pytest.fail('No process'))
    with pytest.raises(native.NativeAgentUnavailable, match='monetary reservation'):
        rt._prepare_home(mcp_enabled=False)
    assert not rt.home.exists()


def test_public_respond_uses_same_surface_and_turn_loop(tmp_path, monkeypatch):
    rt = runtime(tmp_path)
    project = tmp_path/'project'; project.mkdir()
    tools = SimpleNamespace(dynamic_tools=[{'name':'fixture','inputSchema':{'type':'object'}}],
                            quality_state={}, dispatch=lambda *_: {'success':True})
    monkeypatch.setattr(rt.tool_surface, 'prepare', lambda **_: tools)
    turns = []
    monkeypatch.setattr(rt, '_run_turn', lambda **kw: turns.append(kw) or native.AgentTurnResult('fixture','done'))
    rt.respond(project_dir=project, thread_id=None, prompt='fixture task', mcp_enabled=True,
               developer_instructions='fixture policy')
    assert turns[0]['dynamic_tools'] is tools.dynamic_tools
    assert turns[0]['tool_handler']('fixture', {}) == {'success':True}
    assert (rt.home/'config.toml').exists() and not (rt.home/'auth.json').exists()


def prepared_turn(tmp_path, monkeypatch, rt):
    class Process:
        stdout = io.BytesIO(); stdin = io.BytesIO(); stderr = io.BytesIO()
        def poll(self): return 0
    monkeypatch.setattr(native.subprocess, 'Popen', lambda *_a, **_kw: Process())
    requested = []
    def request(_process, _events, _id, method, params, _buffered):
        requested.append((method, params))
        if method == 'turn/start': return {'turn': {'id':'fixture-turn'}}
        return {'thread': {'id':'fixture-thread'}, 'model':'fixture-model', 'modelProvider':'kstudio_api'}
    monkeypatch.setattr(rt, '_request', request)
    monkeypatch.setattr(rt, '_send', lambda *_: None)
    monkeypatch.setattr(rt, '_next_event', lambda *_: {'method':'turn/completed', 'params':{
        'threadId':'fixture-thread', 'turn': {'id':'fixture-turn','status':'completed'}}})
    project = tmp_path/'project'; workspace = project/'runtime/agent_workspace'; workspace.mkdir(parents=True, exist_ok=True)
    args = dict(project_dir=project, agent_workspace=workspace, prompt='fixture', mcp_enabled=True,
        developer_instructions='same', dynamic_tools=[], tool_handler=lambda *_: {}, model='fixture-model',
        reasoning_effort='low', reference_images=[])
    return requested, args


def test_thread_resume_binds_provider_endpoint_and_account(tmp_path, monkeypatch):
    rt = runtime(tmp_path)
    requested, args = prepared_turn(tmp_path, monkeypatch, rt)
    result = rt._run_turn(thread_id=None, **args)
    assert result.provider_name == 'codex-responses'
    rt._run_turn(thread_id=result.thread_id, **args)
    assert requested[-2][0] == 'thread/resume'
    other = native.CodexAppServerRuntime(tmp_path/'runtime', home_root=tmp_path/'codex', model='fixture-model',
        api_provider=replace(provider(), api_key='different-synthetic-account'))
    requested2, args2 = prepared_turn(tmp_path, monkeypatch, other)
    other._run_turn(thread_id=result.thread_id, **args2)
    assert requested2[-2][0] == 'thread/start'


@pytest.mark.parametrize('reported', [{'model':'fixture-model'}, {'model':'wrong', 'modelProvider':'kstudio_api'},
                                     {'model':'fixture-model','modelProvider':'openai'}])
def test_missing_or_wrong_provider_model_identity_blocks_inference(tmp_path, monkeypatch, reported):
    rt = runtime(tmp_path)
    requested, args = prepared_turn(tmp_path, monkeypatch, rt)
    calls=[]
    def wrong(_p, _q, _i, method, _params, _b):
        calls.append(method)
        return {**reported, 'thread': {'id':'fixture'}}
    monkeypatch.setattr(rt, '_request', wrong)
    with pytest.raises(native.NativeAgentUnavailable, match='did not confirm'):
        rt._run_turn(thread_id=None, **args)
    assert 'turn/start' not in calls


def test_native_env_key_configuration_needs_no_login_and_omits_other_providers(tmp_path, monkeypatch):
    source = tmp_path/'source'; source.mkdir()
    (source/'config.toml').write_text('''model_provider = "external"
+[model_providers.external]
+name = "External fixture"
+base_url = "https://fixture.invalid/v1"
+wire_api = "responses"
+requires_openai_auth = false
+env_key = "SYNTHETIC_API_KEY"
+[model_providers.unrelated]
+name = "Never copied"
+base_url = "https://unrelated.invalid/v1"
+[mcp_servers.not_allowed]
+command = "do-not-copy"
+'''.replace('\n+', '\n'))
    monkeypatch.setenv('CODEX_HOME', str(source)); monkeypatch.setenv('SYNTHETIC_API_KEY', 'synthetic-fixture')
    rt = native.CodexAppServerRuntime(tmp_path/'runtime', home_root=tmp_path/'generated')
    rt._prepare_home(mcp_enabled=False)
    cfg = tomllib.loads((rt.home/'config.toml').read_text())
    assert set(cfg['model_providers']) == {'external'} and 'mcp_servers' not in cfg
    assert not (rt.home/'auth.json').exists()
    monkeypatch.delenv('SYNTHETIC_API_KEY')
    with pytest.raises(native.NativeAgentUnavailable, match='no login fallback'):
        rt._prepare_home(mcp_enabled=False)
