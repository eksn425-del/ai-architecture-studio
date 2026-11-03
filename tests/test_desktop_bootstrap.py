import os
from pathlib import Path
import pytest
from app.desktop_bootstrap import configure


def bundle(root):
    for name in ('harness/node.exe', 'harness/dsh.cmd', 'harness/node_modules/@deepseek-ai/dsh/lib/bin.js', 'app/dsh_host_tools.mjs'):
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('fixture')
    (root / 'app/architecture_skills').mkdir()
    return root


def test_new_profile_uses_bundle_and_no_inherited_account(tmp_path, monkeypatch):
    monkeypatch.setattr(os, 'environ', dict(os.environ))
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-secret')
    monkeypatch.setenv('ARCH_STUDIO_MCP_CONFIG', 'old-developer-bridge')
    monkeypatch.setenv('KSTUDIO_DSH_MCP_CONFIG', 'old-developer-tools')
    result = configure(bundle(tmp_path / 'install 中文'), tmp_path / 'user data')
    assert 'OPENAI_API_KEY' not in os.environ
    assert 'KSTUDIO_DSH_MCP_CONFIG' not in os.environ
    assert os.environ['KSTUDIO_DSH_CAPABILITIES'] == 'full'
    assert Path(os.environ['ARCH_STUDIO_MCP_CONFIG']).parent == tmp_path / 'user data'
    assert result['node'].is_relative_to(tmp_path / 'install 中文')
    assert not list(result['settings'].iterdir())
    assert os.environ['ARCH_STUDIO_API_MODEL'] == ''


def test_upgrade_preserves_existing_encrypted_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(os, 'environ', dict(os.environ))
    root = bundle(tmp_path / 'install')
    data = tmp_path / 'data'
    settings = data / 'settings'
    settings.mkdir(parents=True)
    vault = settings / 'connections.dpapi'
    vault.write_bytes(b'existing encrypted bytes')
    configure(root, data)
    configure(root, data)
    assert vault.read_bytes() == b'existing encrypted bytes'


def test_incomplete_bundle_fails_before_creating_profile(tmp_path):
    with pytest.raises(RuntimeError, match='安装包缺少'):
        configure(tmp_path / 'missing', tmp_path / 'profile')
    assert not (tmp_path / 'profile').exists()
