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


def test_lifecycle_requires_explicit_approval_and_preserves_thread(tmp_path):
    client, agent, su, project = setup_project(tmp_path)
    assert send(client, "execute").status_code == 409
    assert not agent.calls
    first = send(client)
    assert first.json()["agent"]["reconstruction_state"] == "clarifying"
    assert first.json()["project"]["agent_session"]["clarification_rounds"] == 1
    assert not su.calls
    second = send(client)
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
    assert send(client).status_code == 409
    assert len(agent.calls) == count


def test_workspace_tools_allow_notes_ruby_and_reject_escape(tmp_path):
    root = prepare_codex_parity_workspace(tmp_path / "workspace")
    workspace_file_call(root, "workspace_write", {"relative_path": "scripts/house.rb", "content": "revision=1"})
    assert workspace_file_call(root, "workspace_read", {"relative_path": "scripts/house.rb"})["content"] == "revision=1"
    assert "scripts/house.rb" in workspace_file_call(root, "workspace_read", {})["files"]
    for path in ("../input.md", "C:/secrets.md", "notes/../a.md", "scripts/a.py"):
        with pytest.raises(ValueError):
            workspace_file_call(root, "workspace_write", {"relative_path": path, "content": "x"})


def test_litellm_reconstruction_retains_history_and_only_reference(tmp_path, monkeypatch):
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
    assert "reference.png" in text and "site.png" not in text and "brief.png" not in text
    assert len(seen[0]["messages"][1]["content"]) == 2


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
