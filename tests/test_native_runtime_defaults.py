"""Regression for real runtime routing semantics, without any model calls."""
from app.native_agent import CodexAppServerRuntime, _composed_tool_instructions
from app.workflow_context import load_workflow_skill_context, workflow_developer_instructions


def test_native_continuity_is_default_and_legacy_is_explicit(tmp_path, monkeypatch):
    monkeypatch.delenv("ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE", raising=False)
    assert CodexAppServerRuntime(tmp_path).reconstruction_thread_mode == "native"
    monkeypatch.setenv("ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE", "compact")
    assert CodexAppServerRuntime(tmp_path).reconstruction_thread_mode == "compact"


def test_blender_does_not_receive_sketchup_execution_override():
    instruction = "Operate the selected Blender model with the supplied tools."
    for profile in ("full", "reconstruction_coding"):
        assert _composed_tool_instructions(instruction, mcp_enabled=True,
            tool_profile=profile, backend="blender") == instruction
    assert "allowed SketchUp tool surface" in _composed_tool_instructions(
        instruction, mcp_enabled=True, backend="sketchup")


def test_native_prompt_defaults_do_not_change_api_route_or_write_authority(monkeypatch):
    monkeypatch.delenv("ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE", raising=False)
    native = load_workflow_skill_context("image_reconstruction", mcp_enabled=False, native_harness=True)
    legacy = load_workflow_skill_context("image_reconstruction", mcp_enabled=False)
    assert len(native) < len(legacy)
    for action in ("clarify", "plan"):
        text = workflow_developer_instructions("image_reconstruction", mcp_enabled=False,
            action=action, native_harness=True)
        assert "writer tools are withheld" in text
    monkeypatch.setenv("ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE", "full")
    assert load_workflow_skill_context("image_reconstruction", mcp_enabled=False,
        native_harness=True).split("\n\n", 1)[1] == legacy.split("\n\n", 1)[1]


def test_environment_prompt_profile_does_not_impersonate_native_runtime(monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE", "harness")
    api = load_workflow_skill_context("image_reconstruction", mcp_enabled=True, native_harness=False)
    native = load_workflow_skill_context("image_reconstruction", mcp_enabled=True, native_harness=True)
    assert "Runtime engine: the host-selected API tool loop" in api
    assert "powered by" not in api and "autonomy of native Codex" not in api
    assert "Runtime engine: Codex App Server, selected by the host" in native


def test_workspace_skill_change_rebinds_but_normal_note_change_does_not(tmp_path):
    from app.native_agent import _workspace_instruction_fingerprint
    agents = tmp_path / "AGENTS.md"; agents.write_text("project rules", encoding="utf-8")
    skill = tmp_path / ".agents/skills/build/SKILL.md"
    skill.parent.mkdir(parents=True); skill.write_text("method version1", encoding="utf-8")
    initial = _workspace_instruction_fingerprint(tmp_path, "developer")
    assert initial == _workspace_instruction_fingerprint(tmp_path, "developer")
    (tmp_path / "ordinary-note.txt").write_text("current geometry", encoding="utf-8")
    assert initial == _workspace_instruction_fingerprint(tmp_path, "developer")
    skill.write_text("method version2", encoding="utf-8")
    assert initial != _workspace_instruction_fingerprint(tmp_path, "developer")
    before = _workspace_instruction_fingerprint(tmp_path, "developer")
    agents.write_text("changed rules", encoding="utf-8")
    assert before != _workspace_instruction_fingerprint(tmp_path, "developer")


def test_deepseek_responses_disables_unsupported_web_search(tmp_path):
    import tomllib
    from app.codex_provider import CodexResponsesProvider
    runtime = CodexAppServerRuntime(tmp_path / "runtime", home_root=tmp_path / "home",
        model="deepseek-v4.1-flash", api_provider=CodexResponsesProvider(
            "https://api.b.ai/v1", "synthetic-test-token", compatibility_acknowledged=True))
    runtime._prepare_home(mcp_enabled=False)
    config = tomllib.loads((runtime.home / "config.toml").read_text(encoding="utf-8"))
    assert config["web_search"] == "disabled"
    assert config["sandbox_mode"] == "workspace-write"


def test_uncertain_native_commit_cannot_use_generic_rollback(tmp_path):
    import json
    from tests.test_novice_flow import workspace
    app, client, project_id, native, su = workspace(tmp_path)
    project = app.state.store.project_dir(project_id)
    path = project / "runtime/project_ruby_state.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"scripts":{"building":{"revision":1,"durability_status":"unconfirmed"}}}), encoding="utf-8")
    before = path.read_bytes()
    response = client.post(f"/api/projects/{project_id}/agent/recover")
    assert response.status_code == 409
    assert "自动恢复已禁用" in response.json()["detail"]
    assert path.read_bytes() == before


def test_unverified_python_candidate_mode_is_disabled_before_filesystem_changes(tmp_path):
    import pytest
    from app.blender_python_jobs import BlenderPythonJobs
    with pytest.raises(RuntimeError, match="mode is disabled"):
        BlenderPythonJobs(tmp_path / "absent-project", "not-used")
    assert not (tmp_path / "absent-project").exists()


def test_named_profile_config_binds_exact_workspace_without_unsupported_rpc_root(tmp_path):
    import tomllib
    from app.codex_provider import CodexResponsesProvider
    from app.native_agent import _native_permission_params
    workspace = tmp_path / "job"; workspace.mkdir()
    runtime_dir = tmp_path / "blender"; runtime_dir.mkdir()
    rt = CodexAppServerRuntime(tmp_path / "runtime", home_root=tmp_path / "home",
        api_provider=CodexResponsesProvider("https://fixture.invalid/v1", "synthetic", compatibility_acknowledged=True),
        execution_read_roots=(runtime_dir,))
    rt._prepare_home(mcp_enabled=False,agent_workspace=workspace)
    config=tomllib.loads((rt.home / "config.toml").read_text(encoding="utf-8"))
    fs=config["permissions"]["kstudio_blender"]["filesystem"]
    assert fs[str(workspace.resolve())] == "write"
    assert ":workspace_roots" not in fs
    assert config["permissions"]["kstudio_blender"]["network"]["enabled"] is False
    assert config["approval_policy"] == "never"  # no policy relaxation
    assert "sandbox_mode" not in config and "sandbox_workspace_write" not in config
    assert _native_permission_params(workspace,named=True,read_only=False,turn=False) == _native_permission_params(workspace,named=True,read_only=False,turn=True)


def test_permission_wire_fields_match_installed_experimental_protocol(tmp_path):
    import json
    from pathlib import Path
    from app.native_agent import _native_permission_params
    snapshots=Path(__file__).parent / "fixtures/codex-protocol-0.130-alpha5"
    for method in ("ThreadStartParams", "ThreadResumeParams", "TurnStartParams"):
        schema=json.loads((snapshots / (method+".json")).read_text(encoding="utf-8"))
        assert "runtimeWorkspaceRoots" not in schema["properties"]
        for named in (False,True):
            for read_only in (False,True):
                params=_native_permission_params(tmp_path,named=named,read_only=read_only,turn=method=="TurnStartParams")
                assert set(params) <= set(schema["properties"])
                assert not ({"sandbox", "sandboxPolicy"} & set(params) and "permissions" in params)
