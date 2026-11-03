"""Readiness probes must not launch a provider or inspect authentication."""
from app.native_agent import CodexAppServerRuntime


def test_nonexistent_executable_path_is_unavailable(tmp_path):
    runtime = CodexAppServerRuntime(tmp_path, codex_executable=str(tmp_path / 'not-installed'))
    assert runtime.available is False


def test_executable_detection_uses_path_only(tmp_path, monkeypatch):
    runtime = CodexAppServerRuntime(tmp_path, codex_executable='fixture')
    monkeypatch.setattr('app.native_agent.shutil.which', lambda command: '/installed/fixture' if command == 'fixture' else None)
    assert runtime.binary_available is True
    assert runtime.available is runtime.execution_readiness()["execution_allowed"]


def test_explicit_missing_pin_is_never_replaced(tmp_path, monkeypatch):
    from app.native_agent import resolve_codex_executable
    monkeypatch.setattr("app.native_agent.shutil.which", lambda _: "another-codex")
    pin = str(tmp_path / "missing-codex.exe")
    assert resolve_codex_executable(pin) == pin


def test_windows_bundle_discovery_without_path_entry(tmp_path, monkeypatch):
    import os
    import pytest
    from app.native_agent import resolve_codex_executable
    if os.name != "nt":
        pytest.skip("Windows desktop bundle")
    monkeypatch.delenv("CODEX_CLI_PATH", raising=False)
    monkeypatch.setattr("app.native_agent.shutil.which", lambda _: None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    executable = tmp_path / "OpenAI/Codex/bin/codex.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"fixture; never executed")
    assert resolve_codex_executable() == str(executable)
