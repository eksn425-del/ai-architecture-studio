from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.models import AgentSession
from app.store import ProjectStore
from app.workspace_files import workspace_file_call
from app.codex_parity import prepare_codex_parity_workspace
from tests.conftest import FakeBrain, FakeSketchUp
from tests.test_demo import FakeNativeAgent


class PlanningAgent(FakeNativeAgent):
    def respond(self, **kwargs):
        if kwargs["mcp_enabled"]:
            kwargs["ruby_state"]["fixture"] = {"revision": 1, "root_pid": 1}
        if "PARAMETER/PLAN turn" in kwargs["prompt"]:
            workspace = prepare_codex_parity_workspace(kwargs["project_dir"] / "runtime/agent_workspace")
            (workspace / "notes/reconstruction_card.md").write_text(
                "# Parameters\nESTIMATED: width 8m, height 14m, depth 12m.\n"
                "# Plan\nNamed floors, glazing modules, balconies and roof pergola.\n", encoding="utf-8")
        return super().respond(**kwargs)


def setup_project(tmp_path, agent=None):
    runtime = tmp_path / "runtime"
    agent = agent or PlanningAgent()
    su = FakeSketchUp()
    client = TestClient(create_app(runtime, brain=FakeBrain(), sketchup=su, native_agent=agent))
    client.get("/api/projects")
    store = ProjectStore(runtime)
    project = store.project_dir("demo-cultural-center")
    model = project / "outputs/model/blank-disposable-test.skp"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b"disposable fixture")
    su.active_model_path = str(model)
    reference = project / "inputs/reference/house.png"
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_bytes(b"image fixture")
    store.save_state("demo-cultural-center", AgentSession(project_id="demo-cultural-center", status="ready",
                     model_path="outputs/model/blank-disposable-test.skp"), "agent_session.json")
    return client, agent, su, project


def send(client, action="auto"):
    return client.post("/api/projects/demo-cultural-center/conversation", json={
        "message": "还原图片；允许推断，估计尺寸，多角度检查。", "workflow_mode": "image_reconstruction",
        "agent_action": action})


def test_first_api_plan_interruption_resumes_written_card_and_tool_history(tmp_path, monkeypatch):
    import json
    import sys
    from types import ModuleType, SimpleNamespace
    from app.litellm_runtime import LiteLLMRuntime
    client, _, su, project = setup_project(tmp_path)
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda _: True))
    module = ModuleType("litellm")
    calls = []
    def completion(**kwargs):
        calls.append(kwargs["messages"])
        if len(calls) == 1:
            message = {"content": None, "tool_calls": [{"id": "write-card", "function": {
                "name": "workspace_write", "arguments": json.dumps({
                    "relative_path": "notes/reconstruction_card.md",
                    "content": "KNOWN: three floors. ESTIMATED: width 12m. ASSUMED: rear windows."
                })}}]}
        elif len(calls) == 2:
            raise ConnectionError("local simulated provider disconnect")
        else:
            assert any(m["role"] == "tool" and m["tool_call_id"] == "write-card" for m in kwargs["messages"])
            message = {"content": "已保留参数卡，请批准后建模。"}
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage={})
    module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", module)
    assert client.post("/api/model-settings", json={"mode": "byok", "model": "openai/test-model",
                       "api_base": "https://example.invalid/v1", "api_key": "test-only-placeholder"}).status_code == 200
    assert send(client, "plan").status_code == 503
    session = client.get("/api/projects/demo-cultural-center").json()["agent_session"]
    assert session["provider"] == "litellm"
    assert session["model"] == "openai/test-model"
    assert session["reconstruction_state"] == "clarifying"
    thread = session["thread_id"]
    retry = send(client, "plan")
    assert retry.status_code == 200
    assert retry.json()["agent"]["reconstruction_state"] == "planned"
    assert retry.json()["project"]["agent_session"]["thread_id"] == thread
    assert len(list((project / "runtime/provider_sessions").glob("*.json"))) == 1
    assert not su.calls


def test_lifecycle_requires_explicit_approval_and_preserves_thread(tmp_path):
    client, agent, su, project = setup_project(tmp_path)
    assert send(client, "execute").status_code == 409
    assert not agent.calls
    first = send(client)
    assert first.json()["agent"]["reconstruction_state"] == "clarifying"
    assert first.json()["project"]["agent_session"]["clarification_rounds"] == 1
    assert not su.calls
    assert send(client).json()["agent"]["reconstruction_state"] == "planned"
    second = send(client, "plan")
    assert second.json()["agent"]["reconstruction_state"] == "planned"
    assert not su.calls
    assert send(client).json()["agent"]["agent_action"] == "plan"
    assert not su.calls
    approved = send(client, "execute")
    assert approved.status_code == 200
    assert approved.json()["agent"]["reconstruction_state"] == "building"
    assert send(client).json()["agent"]["agent_action"] == "execute"
    assert all(call["tool_profile"] == "reconstruction_coding" for call in agent.calls)
    assert all(call["thread_id"] == "thr-fast-assembly" for call in agent.calls[1:])
    assert all(call["project_dir"] == project for call in agent.calls)


def test_missing_reference_and_missing_card_are_rejected(tmp_path):
    client, agent, su, project = setup_project(tmp_path, FakeNativeAgent())
    assert send(client, "plan").status_code == 422
    assert not su.calls
    (project / "inputs/reference/house.png").unlink()
    count = len(agent.calls)
    assert send(client, "clarify").status_code == 200
    assert len(agent.calls) == count + 1


def test_new_input_invalidates_plan_and_blocks_execution(tmp_path):
    client, agent, su, project = setup_project(tmp_path)
    assert send(client, "plan").status_code == 200
    before = len(agent.calls)
    response = client.post("/api/projects/demo-cultural-center/inputs/brief?filename=dimensions.txt", content="宽度改为12米".encode())
    assert response.status_code == 200
    session = client.get("/api/projects/demo-cultural-center").json()["agent_session"]
    assert session["reconstruction_state"] == "clarifying"
    assert session["thread_id"] == ""
    assert send(client, "execute").status_code == 409
    assert len(agent.calls) == before and not su.calls


def test_failed_plan_update_cannot_reuse_old_saved_card(tmp_path):
    client, agent, su, project = setup_project(tmp_path)
    assert send(client, "plan").status_code == 200
    agent.respond = FakeNativeAgent().respond  # Replies without updating the card.
    update = client.post("/api/projects/demo-cultural-center/conversation", json={
        "message": "宽度改为12米，请更新计划", "workflow_mode": "image_reconstruction", "agent_action": "plan"})
    assert update.status_code == 422
    assert "本次更新" in update.json()["detail"]
    assert client.get("/api/projects/demo-cultural-center").json()["agent_session"]["reconstruction_state"] == "clarifying"
    assert send(client, "execute").status_code == 409
    assert not su.calls


@pytest.mark.parametrize("state", ["planned", "building"])
@pytest.mark.parametrize("message", ["为什么要估算背面？", "修改窗子会影响阳台吗？", "能不能只聊一下尺寸"])
def test_plan_questions_preserve_stage_and_do_not_edit_model(tmp_path, state, message):
    client, agent, su, project = setup_project(tmp_path)
    assert send(client, "plan").status_code == 200
    store = ProjectStore(project.parents[1])
    session = store.load_state("demo-cultural-center", "agent_session.json", AgentSession)
    session.reconstruction_state = state
    store.save_state("demo-cultural-center", session, "agent_session.json")
    before = (project / "runtime/agent_workspace/notes/reconstruction_card.md").read_bytes()
    response = client.post("/api/projects/demo-cultural-center/conversation", json={
        "message": message, "workflow_mode": "image_reconstruction"})
    assert response.status_code == 200
    assert response.json()["agent"]["agent_action"] == "clarify"
    assert response.json()["agent"]["reconstruction_state"] == state
    assert not agent.calls[-1]["mcp_enabled"] and not su.calls
    assert (project / "runtime/agent_workspace/notes/reconstruction_card.md").read_bytes() == before


def test_upload_cannot_race_running_turn(tmp_path):
    client, agent, su, project = setup_project(tmp_path)
    app = client.app
    app.state.agent_lock.acquire()
    try:
        response = client.post("/api/projects/demo-cultural-center/inputs/brief?filename=note.txt", content=b"new requirements")
        assert response.status_code == 409
        assert not list((project / "inputs/brief").glob("*note.txt"))
    finally:
        app.state.agent_lock.release()


def test_file_writes_alone_cannot_be_reported_as_building(tmp_path):
    client, agent, su, project = setup_project(tmp_path, FakeNativeAgent())
    store = ProjectStore(project.parents[1])
    session = store.load_state("demo-cultural-center", "agent_session.json", AgentSession)
    session.reconstruction_state = "planned"
    store.save_state("demo-cultural-center", session, "agent_session.json")
    result = send(client, "execute")
    assert result.status_code == 422
    assert "已提交" in result.json()["detail"]


def test_workspace_tools_allow_notes_ruby_and_reject_escape(tmp_path):
    root = prepare_codex_parity_workspace(tmp_path / "workspace")
    workspace_file_call(root, "workspace_write", {"relative_path": "scripts/house.rb", "content": "revision=1"})
    assert workspace_file_call(root, "workspace_read", {"relative_path": "scripts/house.rb"})["content"] == "revision=1"
    assert "scripts/house.rb" in workspace_file_call(root, "workspace_read", {})["files"]
    for path in ("../input.md", "C:/secrets.md", "notes/../a.md", "scripts/a.py"):
        with pytest.raises(ValueError):
            workspace_file_call(root, "workspace_write", {"relative_path": path, "content": "x"})


def test_workspace_read_lists_normal_directory_requests_without_path_escape(tmp_path):
    root = prepare_codex_parity_workspace(tmp_path / "workspace")
    workspace_file_call(root, "workspace_write", {"relative_path": "scripts/house.rb", "content": "revision=1"})
    workspace_file_call(root, "workspace_write", {"relative_path": "notes/test.md", "content": "note"})
    all_files = workspace_file_call(root, "workspace_read", {"relative_path": "."})["files"]
    assert "scripts/house.rb" in all_files and "notes/test.md" in all_files
    notes = workspace_file_call(root, "workspace_read", {"relative_path": "notes/"})["files"]
    assert "notes/test.md" in notes and "scripts/house.rb" not in notes
    for invalid in ("../", [], None):
        with pytest.raises(ValueError):
            workspace_file_call(root, "workspace_read", {"relative_path": invalid})


def test_reconstruction_planning_file_failures_do_not_suggest_stronger_model(tmp_path):
    class FileFailureAgent(PlanningAgent):
        failed_tool_calls = 2
    client, _, su, _ = setup_project(tmp_path, FileFailureAgent())
    result = send(client, "clarify")
    assert result.status_code == 200
    assert result.json()["agent"]["failed_tool_calls"] == 2
    assert result.json()["agent"]["premium_rescue_pending"] is False
    assert not su.calls


def test_litellm_reconstruction_retains_history_and_uploaded_evidence(tmp_path, monkeypatch):
    import sys
    from types import ModuleType, SimpleNamespace
    from app.litellm_runtime import LiteLLMRuntime
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-only-key")
    for category in ("reference", "site", "brief"):
        path = tmp_path / "inputs" / category / f"{category}.png"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"fixture")
    seen = []
    def completion(**kwargs):
        seen.append(kwargs)
        assert {t["function"]["name"] for t in kwargs["tools"]} == {"workspace_read", "workspace_write"}
        return SimpleNamespace(choices=[SimpleNamespace(message={"content": "plan", "tool_calls": None})], usage={})
    module = ModuleType("litellm")
    module.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", module)
    runtime = LiteLLMRuntime(tmp_path)
    arguments = dict(project_dir=tmp_path, prompt="plan", mcp_enabled=False, developer_instructions="planner",
                     workflow_mode="image_reconstruction", tool_profile="reconstruction_coding")
    first = runtime.respond(thread_id=None, **arguments)
    second = runtime.respond(thread_id=first.thread_id, **arguments)
    assert second.thread_id == first.thread_id
    assert any(m["role"] == "assistant" for m in seen[1]["messages"])
    text = seen[0]["messages"][1]["content"][0]["text"]
    assert "reference.png" in text and "site.png" in text and "brief.png" in text
    assert len(seen[0]["messages"][1]["content"]) == 7
    blocks = seen[0]["messages"][1]["content"]
    assert all(blocks[i - 1]["type"] == "text" and ".png" in blocks[i - 1]["text"]
               for i, block in enumerate(blocks) if block["type"] == "image_url")


def test_provider_configuration_reuses_litellm_without_dashscope_lock(tmp_path, monkeypatch):
    from app.litellm_runtime import LiteLLMRuntime
    monkeypatch.setenv("ARCH_STUDIO_API_MODEL", "openai/test-vision-model")
    monkeypatch.setenv("ARCH_STUDIO_API_KEY_ENV", "TEST_PROVIDER_KEY")
    monkeypatch.setenv("TEST_PROVIDER_KEY", "synthetic-key")
    monkeypatch.setenv("ARCH_STUDIO_API_BASE", "https://example.invalid/v1")
    runtime = LiteLLMRuntime(tmp_path)
    assert runtime.model == "openai/test-vision-model"
    assert runtime.credential_configured
    assert runtime.api_base == "https://example.invalid/v1"


def test_native_home_preserves_supported_windows_sandbox_choice(tmp_path, monkeypatch):
    import tomllib
    from app.native_agent import CodexAppServerRuntime
    source = tmp_path / "source"
    source.mkdir()
    (source / "config.toml").write_text('[windows]\nsandbox="elevated"\n', encoding="utf-8")
    (source / "auth.json").write_text("synthetic-auth", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(source))
    runtime = CodexAppServerRuntime(tmp_path, codex_executable="synthetic", home_root=tmp_path / "isolated")
    workspace = tmp_path / "workspace"
    runtime._prepare_home(mcp_enabled=False, agent_workspace=workspace)
    config = tomllib.loads((runtime.home / "config.toml").read_text(encoding="utf-8"))
    assert config["windows"]["sandbox"] == "elevated"
    assert config["sandbox_mode"] == "workspace-write"
    assert config["sandbox_workspace_write"]["network_access"] is False
    assert config["sandbox_workspace_write"]["writable_roots"] == [str(workspace.resolve())]


def test_native_home_refreshes_older_isolated_login_cache(tmp_path, monkeypatch):
    import os
    from app.native_agent import CodexAppServerRuntime
    source = tmp_path / "source"
    isolated = tmp_path / "isolated"
    source.mkdir()
    isolated.mkdir()
    (source / "config.toml").write_text('', encoding='utf-8')
    (source / "auth.json").write_text('synthetic-new-login', encoding='utf-8')
    (isolated / "auth.json").write_text('synthetic-old-login', encoding='utf-8')
    os.utime(isolated / 'auth.json', (1, 1))
    monkeypatch.setenv('CODEX_HOME', str(source))
    runtime = CodexAppServerRuntime(tmp_path, codex_executable='synthetic', home_root=isolated)
    runtime._prepare_home(mcp_enabled=False, agent_workspace=tmp_path / 'workspace')
    assert (isolated / 'auth.json').read_text() == 'synthetic-new-login'
    (isolated / 'auth.json').write_text('synthetic-runtime-refreshed', encoding='utf-8')
    os.utime(source / 'auth.json', (1, 1))
    runtime._prepare_home(mcp_enabled=False, agent_workspace=tmp_path / 'workspace')
    assert (isolated / 'auth.json').read_text() == 'synthetic-runtime-refreshed'


def test_native_tools_require_registered_execution_thread():
    from app.native_agent import _can_resume_tools, _thread_tool_fingerprint
    tools = [{"name": "sketchup_run_workspace_ruby", "inputSchema": {"type": "object"}}]
    registrations = {"planner": _thread_tool_fingerprint([]), "builder": _thread_tool_fingerprint(tools)}
    assert _can_resume_tools("planner", registrations, [])
    assert not _can_resume_tools("planner", registrations, tools)
    assert _can_resume_tools("builder", registrations, tools)
    assert not _can_resume_tools("builder", registrations, [])
    assert not _can_resume_tools("legacy-untracked", registrations, tools)


def test_execution_without_actual_tool_calls_is_not_building(tmp_path):
    class NoToolsAgent(PlanningAgent):
        def respond(self, **kwargs):
            result = super().respond(**kwargs)
            result.tool_calls = []
            result.tool_call_count = 0
            return result
    client, agent, su, project = setup_project(tmp_path, NoToolsAgent())
    assert send(client, "plan").status_code == 200
    result = send(client, "execute")
    assert result.status_code == 422
    session = ProjectStore(tmp_path / "runtime").load_state("demo-cultural-center", "agent_session.json", AgentSession)
    assert session.reconstruction_state == "planned"


def test_interrupted_committed_build_checkpoints_and_retains_execution_thread(tmp_path):
    from app.native_agent import AgentTurnResult, NativeAgentUnavailable
    import json

    class InterruptedAgent(PlanningAgent):
        def respond(self, **kwargs):
            if kwargs["mcp_enabled"]:
                kwargs["ruby_state"]["house"] = {"revision": 2, "root_pid": 123}
                error = NativeAgentUnavailable("Timed out waiting for Codex app-server event.")
                error.partial_result = AgentTurnResult(
                    thread_id="execution-thread", reply="", status="interrupted",
                    tool_call_count=4, failed_tool_calls=1, latency_ms=900000)
                raise error
            return super().respond(**kwargs)

    client, agent, su, project = setup_project(tmp_path, InterruptedAgent())
    send(client)
    send(client, "plan")
    assert send(client, "execute").status_code == 503
    session = json.loads((project / "state/agent_session.json").read_text(encoding="utf-8"))
    assert session["thread_id"] == "execution-thread"
    assert session["reconstruction_state"] == "building"
    assert session["tool_call_count"] == 4
    assert session["failed_tool_calls"] == 1
    assert "尚未完成" in session["last_reply"]
    state = json.loads((project / "state/model_state.json").read_text(encoding="utf-8"))
    assert state["last_operation"]["status"] == "interrupted"
    assert state["model_path"].endswith("fast-assembly-agent.skp")
    assert any(name == "save_model" and args["operation_name"] == "Persist bound agent document"
               for name, args in su.calls)
    assert send(client).status_code == 503


def test_checkpoint_recovery_is_confined_to_generated_project_copy(tmp_path):
    client, agent, su, project = setup_project(tmp_path)
    assert client.post("/api/projects/demo-cultural-center/agent/recover").status_code == 409
    snapshot = project / "outputs/model/previous-agent-checkpoint.skp"
    snapshot.write_bytes(b"owned checkpoint")
    import json
    (project / "runtime/previous-agent-ruby-state.json").parent.mkdir(parents=True, exist_ok=True)
    (project / "runtime/previous-agent-ruby-state.json").write_text(json.dumps({"house": {"revision": 1, "root_pid": 123}}), encoding="utf-8")
    def restore(target, expected):
        assert expected.name == "blank-disposable-test.skp"
        assert target.parent == snapshot.parent
        assert target.read_bytes() == b"owned checkpoint"
        su.active_model_path = str(target)
    su.restore_disposable_model = restore
    result = client.post("/api/projects/demo-cultural-center/agent/recover")
    assert result.status_code == 200
    assert result.json()["project"]["agent_session"]["ruby_state"]["house"]["revision"] == 1
    assert result.json()["project"]["agent_session"]["model_path"].startswith("outputs/model/blank-disposable-recovery-")
    note = result.json()["project"]["context"]["conversation"][-1]
    assert note["metadata"]["agent_action"] == "recovery"
    assert '"house": 1' in note["content"]
    assert "失败轮的笔记和脚本仍保留" in note["content"]


def test_agent_turn_and_recovery_cannot_overlap(tmp_path):
    client, agent, su, project = setup_project(tmp_path)
    lock = client.app.state.agent_lock
    lock.acquire()
    try:
        assert send(client).status_code == 409
        assert client.post("/api/projects/demo-cultural-center/agent/recover").status_code == 409
        assert not agent.calls
    finally:
        lock.release()
    assert send(client).status_code == 200
