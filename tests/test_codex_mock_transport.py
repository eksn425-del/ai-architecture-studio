"""Characterize current native provider integration without inference/auth access."""
import json
import tomllib
from unittest.mock import patch

import pytest

from app.native_agent import CodexAppServerRuntime, NativeAgentUnavailable


def test_missing_selected_provider_fails_before_login_or_inference(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'config.toml').write_text('model_provider = "local_fixture"\n')
    runtime = CodexAppServerRuntime(tmp_path / 'runtime', home_root=tmp_path / 'target')
    with patch.dict('os.environ', {'HOME': str(tmp_path), 'CODEX_HOME': str(source)}, clear=True):
        with pytest.raises(NativeAgentUnavailable, match='selected Codex provider configuration'):
            runtime._prepare_home(mcp_enabled=False)


def test_prepare_preserves_only_selected_custom_provider_without_login_or_launching(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'config.toml').write_text('''model_provider = "local_fixture"
[model_providers.local_fixture]
name = "Fixture only"
base_url = "http://127.0.0.1:1/v1"
wire_api = "responses"
requires_openai_auth = false
''')
    # Explicitly fabricated non-secret fixture; never a real user's auth file.
    (source / 'auth.json').write_text(json.dumps({'OPENAI_API_KEY': 'fixture-not-a-real-key'}))
    target = tmp_path / 'target'
    runtime = CodexAppServerRuntime(tmp_path / 'runtime', home_root=target)
    with patch.dict('os.environ', {'HOME': str(tmp_path), 'CODEX_HOME': str(source)}, clear=True):
        with patch('subprocess.Popen', side_effect=AssertionError('Must not launch any process')):
            runtime._prepare_home(mcp_enabled=False)
    effective = tomllib.loads((runtime.home / 'config.toml').read_text())
    assert effective['model_provider'] == 'local_fixture'
    assert effective['model_providers']['local_fixture']['wire_api'] == 'responses'
    assert effective['model_providers']['local_fixture']['requires_openai_auth'] is False
    assert not (runtime.home / 'auth.json').exists()
    assert effective['sandbox_mode'] == 'workspace-write'
    assert effective['sandbox_workspace_write']['network_access'] is False
