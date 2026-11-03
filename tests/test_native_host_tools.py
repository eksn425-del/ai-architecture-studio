"""No model calls: protocol, capability and budget regressions."""
import json
from pathlib import Path
import tomllib
import pytest
from app import native_execution_safety as safety
from app.codex_provider import CodexResponsesProvider
from app.native_agent import CodexAppServerRuntime, NativeAgentUnavailable


def runtime(tmp_path, **kwargs):
    return CodexAppServerRuntime(tmp_path / "runtime", codex_executable="synthetic-not-executed",
        home_root=tmp_path / "home", execution_mode="host_tools",
        api_provider=CodexResponsesProvider("https://fixture.invalid/v1", "synthetic-secret",
            compatibility_acknowledged=True), **kwargs)


def test_host_tools_require_known_binary_not_environment_claim(monkeypatch):
    monkeypatch.setenv("KSTUDIO_WINDOWS_ISOLATION_VERIFIED", "1")
    monkeypatch.setattr(safety, "host_tools_runtime_identity", lambda _: None)
    result=safety.execution_readiness("win32", capability="host_tools", executable="unknown")
    assert not result["execution_allowed"]
    monkeypatch.setattr(safety, "host_tools_runtime_identity", lambda _: {"version":"fixture", "sha256":"fixture"})
    result=safety.execution_readiness("win32", capability="host_tools", executable="fixture")
    assert result["execution_allowed"]
    assert not result["local_execution_allowed"] and not result["os_boundary_verified"]
    assert not safety.execution_readiness("win32")["execution_allowed"]


def test_host_tools_does_not_accept_login_or_local_runtime_roots(tmp_path):
    with pytest.raises(ValueError, match="explicit API"):
        CodexAppServerRuntime(tmp_path, execution_mode="host_tools")
    with pytest.raises(ValueError, match="no local execution"):
        runtime(tmp_path, execution_read_roots=(tmp_path,))


def test_no_environment_is_explicit_on_start_resume_and_turn(tmp_path):
    rt=runtime(tmp_path)
    schemas=Path(__file__).parent / "fixtures/codex-protocol-0.130-alpha5"
    for method in ("ThreadStartParams", "ThreadResumeParams", "TurnStartParams"):
        schema=json.loads((schemas / (method+".json")).read_text(encoding="utf-8"))
        for read_only in (True,False):
            params=rt._permission_params(tmp_path, read_only=read_only, turn=method=="TurnStartParams", resume=method=="ThreadResumeParams")
            if method == "ThreadResumeParams":
                assert "environments" not in params  # unsupported there; sticky + per-turn
            else:
                assert params["environments"] == []
            assert set(params) <= set(schema["properties"])
            assert params.get("sandbox", "read-only") == "read-only"
            assert params.get("sandboxPolicy", {"type":"readOnly"})["type"] == "readOnly"
            assert "permissions" not in params


def test_generated_api_profile_disables_extra_tools_and_copies_no_native_config(tmp_path,monkeypatch):
    rt=runtime(tmp_path)
    monkeypatch.setenv("CODEX_HOME",str(tmp_path / "do-not-read-native-home"))
    monkeypatch.setattr("app.native_agent._toml_load",lambda *_: pytest.fail("Native config read"))
    rt._prepare_home(mcp_enabled=True,agent_workspace=tmp_path / "workspace")
    text=(rt.home / "config.toml").read_text(encoding="utf-8")
    config=tomllib.loads(text)
    assert rt.home.name == "host-tools-v1"
    assert config["sandbox_mode"] == "read-only"
    assert "sandbox_workspace_write" not in config and "windows" not in config
    assert config["web_search"] == "disabled" and config["approval_policy"] == "never"
    assert all(config["features"][key] is False for key in safety.HOST_TOOLS_DISABLED_FEATURES)
    assert "synthetic-secret" not in text and not (rt.home / "auth.json").exists()


@pytest.mark.parametrize("name",["shell", "apply_patch", "sketchup_run_project_ruby", "blender_execute_python", "workspace_write"])
def test_unsafe_host_tools_rejected_before_native_process(tmp_path,monkeypatch,name):
    rt=runtime(tmp_path)
    monkeypatch.setattr(rt,"_assert_execution_ready",lambda: None) # tool validation independently
    monkeypatch.setattr("app.native_agent.subprocess.Popen",lambda *_a,**_k:pytest.fail("Unexpected process"))
    with pytest.raises(NativeAgentUnavailable, match="bounded Blender"):
        rt._run_turn(project_dir=tmp_path,agent_workspace=tmp_path,thread_id=None,prompt="fixture",
            mcp_enabled=True,developer_instructions="fixture",dynamic_tools=[{"name":name}],
            tool_handler=lambda *_:pytest.fail("Unexpected dispatch"),model="fixture",reasoning_effort="low",reference_images=[])


def test_host_tools_preserves_monetary_guard_before_config_or_dispatch(tmp_path,monkeypatch):
    rt=runtime(tmp_path)
    monkeypatch.setenv("K_STUDIO_OPERATOR_MAX_USD","20")
    with pytest.raises(NativeAgentUnavailable,match="monetary"):
        rt._prepare_home(mcp_enabled=False)
    assert not rt.home.exists()


def test_modified_host_profile_rejected_before_process(tmp_path,monkeypatch):
    rt=runtime(tmp_path)
    rt._prepare_home(mcp_enabled=False)
    config=rt.home / "config.toml"
    config.write_text(config.read_text(encoding="utf-8").replace("js_repl = false","js_repl = true"),encoding="utf-8")
    monkeypatch.setattr(rt,"_assert_execution_ready",lambda: None)
    monkeypatch.setattr("app.native_agent.subprocess.Popen",lambda *_a,**_k:pytest.fail("Unexpected process"))
    with pytest.raises(NativeAgentUnavailable,match="configuration changed"):
        rt._run_turn(project_dir=tmp_path,agent_workspace=tmp_path,thread_id=None,prompt="fixture",
            mcp_enabled=False,developer_instructions="fixture",dynamic_tools=[],
            tool_handler=lambda *_:None,model="fixture",reasoning_effort="low",reference_images=[])
