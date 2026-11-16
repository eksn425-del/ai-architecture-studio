"""Readiness probes must not launch a provider or inspect authentication."""
from app.native_agent import CodexAppServerRuntime


def test_nonexistent_executable_path_is_unavailable(tmp_path):
    runtime = CodexAppServerRuntime(tmp_path, codex_executable=str(tmp_path / 'not-installed'))
    assert runtime.available is False


def test_executable_detection_uses_path_only(tmp_path, monkeypatch):
    runtime = CodexAppServerRuntime(tmp_path, codex_executable='fixture')
    monkeypatch.setattr('app.native_agent.shutil.which', lambda command: '/installed/fixture' if command == 'fixture' else None)
    assert runtime.available is True
