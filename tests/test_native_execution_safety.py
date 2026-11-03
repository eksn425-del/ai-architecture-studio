import pytest
from app.native_execution_safety import execution_readiness
from app.native_agent import CodexAppServerRuntime, NativeAgentUnavailable
from app.codex_provider import CodexResponsesProvider


def test_windows_profile_or_environment_cannot_certify_execution(monkeypatch):
    monkeypatch.setenv("KSTUDIO_WINDOWS_ISOLATION_VERIFIED", "1")
    state=execution_readiness("win32")
    assert state["execution_allowed"] is False
    assert state["policy_text_is_proof"] is False
    assert state["verification_enable_path_implemented"] is False


def test_windows_guard_blocks_public_and_internal_paths_before_any_process(tmp_path,monkeypatch):
    rt=CodexAppServerRuntime(tmp_path/'runtime',codex_executable='fixture',home_root=tmp_path/'home',
        api_provider=CodexResponsesProvider('https://fixture.invalid/v1','synthetic',compatibility_acknowledged=True))
    monkeypatch.setattr(rt,'execution_readiness',lambda:execution_readiness('win32'))
    monkeypatch.setattr('app.native_agent.subprocess.Popen',lambda *_a,**_k:pytest.fail('Unverified environment launched a process'))
    monkeypatch.setattr(rt.tool_surface,'prepare',lambda **_k:pytest.fail('Unverified execution prepared host tools'))
    with pytest.raises(NativeAgentUnavailable,match='Windows'):
        rt.respond(project_dir=tmp_path/'project',thread_id=None,prompt='test',mcp_enabled=True,developer_instructions='test')
    with pytest.raises(NativeAgentUnavailable,match='Windows'):
        rt._run_turn(project_dir=tmp_path/'project',agent_workspace=tmp_path/'workspace',thread_id=None,prompt='test',
            mcp_enabled=True,developer_instructions='test',dynamic_tools=[],tool_handler=lambda *_:None,
            model='fixture',reasoning_effort='low',reference_images=[])
    assert not rt.home.exists()


def test_binary_installation_is_not_execution_readiness(tmp_path,monkeypatch):
    rt=CodexAppServerRuntime(tmp_path,codex_executable='fixture')
    monkeypatch.setattr('app.native_agent.shutil.which',lambda _: 'fixture.exe')
    monkeypatch.setattr(rt,'execution_readiness',lambda:execution_readiness('win32'))
    assert rt.binary_available is True
    assert rt.available is False
