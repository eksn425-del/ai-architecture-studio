import io
import json
import time
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from tests.conftest import FakeBrain, FakeSketchUp
from tests.test_demo import FakeNativeAgent


def workspace(tmp_path):
    agent = FakeNativeAgent()
    su = FakeSketchUp()
    app = create_app(tmp_path / "runtime", brain=FakeBrain(), native_agent=agent, sketchup=su)
    client = TestClient(app)
    project = client.post("/api/projects", json={"project_name": "Novice"}).json()["project_id"]
    return app, client, project, agent, su


def test_deepseek_preset_is_api_only_and_credential_not_returned(tmp_path, monkeypatch):
    from app.litellm_runtime import LiteLLMRuntime
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, _, _, _ = workspace(tmp_path)
    result = client.post("/api/model-settings", json={"mode": "deepseek", "api_key": "test-secret-not-real"})
    assert result.status_code == 200
    assert result.json()["economy"]["provider"] == "litellm"
    assert result.json()["economy"]["model"] == "deepseek/deepseek-flash"
    assert result.json()["economy"]["reasoning_effort"] == "low"
    assert "test-secret-not-real" not in result.text
    assert app.state.model_router.china_runtime.api_base == "https://api.deepseek.com"


def test_standalone_profile_rejects_codex_and_premium(tmp_path, monkeypatch):
    import pytest
    from app.native_agent import NativeAgentUnavailable
    monkeypatch.setenv("ARCH_STUDIO_STANDALONE", "1")
    monkeypatch.setenv("ARCH_STUDIO_ECONOMY_PROVIDER", "litellm")
    monkeypatch.setenv("ARCH_STUDIO_API_MODEL", "deepseek/deepseek-flash")
    monkeypatch.setenv("ARCH_STUDIO_ECONOMY_REASONING_EFFORT", "low")
    app, client, _, _, _ = workspace(tmp_path)
    assert client.post("/api/model-settings", json={"mode":"preset"}).status_code == 409
    assert app.state.model_router.route("economy").model == "deepseek/deepseek-flash"
    assert app.state.model_router.route("economy").reasoning_effort == "low"
    with pytest.raises(NativeAgentUnavailable, match="cannot invoke Codex"):
        app.state.model_router.route("premium")


def test_custom_deepseek_official_model_name_gets_provider_prefix(tmp_path, monkeypatch):
    from app.litellm_runtime import LiteLLMRuntime
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, _, _, _ = workspace(tmp_path)
    settings = {"mode": "byok", "model": "deepseek-flash", "api_base": "https://api.deepseek.com",
                "api_key": "test-only-key", "reasoning_effort": "provider-default"}
    result = client.post("/api/model-settings", json=settings)
    assert result.status_code == 200
    assert result.json()["economy"]["model"] == "deepseek/deepseek-flash"
    settings.pop("api_key")
    settings["reasoning_effort"] = "low"
    assert client.post("/api/model-settings", json=settings).status_code == 200
    assert app.state.model_router.china_runtime.session_api_key == "test-only-key"


def test_glm_domestic_preset_uses_exact_endpoint_and_high(tmp_path, monkeypatch):
    from app.litellm_runtime import LiteLLMRuntime
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, _, _, _ = workspace(tmp_path)
    result = client.post("/api/model-settings", json={"mode":"glm", "api_key":"test-only-glm-key"})
    assert result.status_code == 200
    assert result.json()["economy"]["model"] == "zai/glm-5.3-flash"
    assert result.json()["economy"]["reasoning_effort"] == "high"
    assert app.state.model_router.china_runtime.api_base == "https://open.bigmodel.cn/api/paas/v4"
    assert "test-only-glm-key" not in result.text
    changed = client.post("/api/model-settings", json={"mode":"glm", "reasoning_effort":"max"})
    assert changed.status_code == 200
    assert changed.json()["economy"]["reasoning_effort"] == "max"
    assert app.state.model_router.china_runtime.session_api_key == "test-only-glm-key"
    assert client.post("/api/model-settings", json={"mode":"glm", "reasoning_effort":"medium"}).status_code == 400


def test_uploaded_images_bind_once_to_conversation_and_remain_model_evidence(tmp_path):
    app, client, project, agent, _ = workspace(tmp_path)
    image = io.BytesIO()
    Image.new("RGB", (12, 12), "white").save(image, "PNG")
    uploaded = client.post(f"/api/projects/{project}/inputs/reference?filename=front.png", content=image.getvalue()).json()["path"]
    first = client.post(f"/api/projects/{project}/conversation", json={"message":"先看看图片", "workflow_mode":"image_reconstruction"}).json()
    assert first["project"]["context"]["conversation"][0]["metadata"]["attachments"] == [uploaded]
    assert first["project"]["context"]["references"][0]["submitted_at"]
    second = client.post(f"/api/projects/{project}/conversation", json={"message":"先聊一下", "workflow_mode":"image_reconstruction"}).json()
    assert second["project"]["context"]["conversation"][-2]["metadata"]["attachments"] == []
    other = client.post(f"/api/projects/{project}/inputs/reference?filename=rear.png", content=image.getvalue()).json()["path"]
    third = client.post(f"/api/projects/{project}/conversation", json={"message":"先聊一下", "workflow_mode":"image_reconstruction"}).json()
    assert third["project"]["context"]["conversation"][-2]["metadata"]["attachments"] == [other]
    assert len(third["project"]["context"]["references"]) == 2


def test_text_first_and_repeated_chat_do_not_edit_su(tmp_path):
    app, client, project, agent, su = workspace(tmp_path)
    for _ in range(10):
        result = client.post(f"/api/projects/{project}/conversation", json={"message": "先聊一下我的想法", "workflow_mode": "image_reconstruction"})
        assert result.status_code == 200
        assert result.json()["agent"]["agent_action"] == "clarify"
    assert all(not call["mcp_enabled"] for call in agent.calls)
    assert not su.calls
    assert client.post(f"/api/projects/{project}/conversation", json={"message": "开始", "workflow_mode": "image_reconstruction", "agent_action": "execute"}).status_code == 409


def test_real_document_and_cad_are_evidence_not_silent_uploads(tmp_path):
    app, client, project, agent, su = workspace(tmp_path)
    document = Document()
    document.add_paragraph("任务资料：三层住宅，入口面向南侧。")
    buffer = io.BytesIO()
    document.save(buffer)
    response = client.post(f"/api/projects/{project}/inputs/brief?filename=任务书.docx", content=buffer.getvalue())
    assert response.status_code == 200 and "已读取" in response.json()["read_status"]
    assert client.post(f"/api/projects/{project}/inputs/site?filename=原始场地.dwg", content=b"test-only unsupported CAD fixture").status_code == 200
    client.post(f"/api/projects/{project}/conversation", json={"message": "综合资料看看", "workflow_mode": "image_reconstruction"})
    prompt = agent.calls[-1]["prompt"]
    assert "三层住宅" in prompt and "未提取到可读文本" in prompt
    assert "不得声称已读懂该文件" in prompt
    assert not su.calls


def test_image_normalization_and_unsupported_upload(tmp_path):
    app, client, project, _, _ = workspace(tmp_path)
    image = io.BytesIO()
    Image.new("RGB", (12, 12), "white").save(image, "BMP")
    result = client.post(f"/api/projects/{project}/inputs/reference?filename=photo.bmp", content=image.getvalue())
    assert result.status_code == 200
    assert result.json()["path"].endswith(".png")
    assert "视觉分析" in result.json()["read_status"]
    assert client.post(f"/api/projects/{project}/inputs/brief?filename=macro.exe", content=b"not executable").status_code == 415
    assert client.post(f"/api/projects/{project}/inputs/reference?filename=bad.png", content=b"invalid image").status_code == 415


def test_progress_reports_current_evidence_without_transcripts(tmp_path):
    app, client, project, _, _ = workspace(tmp_path)
    root = app.state.store.project_dir(project)
    assert client.get(f"/api/projects/{project}/agent/progress").json() == {"running": False}
    app.state.active_turns[project] = {"started": time.time()-1, "action": "execute", "baseline": {}}
    events = root / "runtime/agent_events"
    events.mkdir(parents=True)
    (events / "test.jsonl").write_text(json.dumps({"event":"tool_result", "tool":"sketchup_run_workspace_ruby", "success":False, "error":"PRIVATE TEXT"})+"\n{partial", encoding="utf-8")
    (root / "runtime/project_ruby_state.json").write_text(json.dumps({"scripts":{"house":{"revision":2}}}), encoding="utf-8")
    result = client.get(f"/api/projects/{project}/agent/progress")
    assert result.json()["tool_calls"] == 1 and result.json()["failed_tool_calls"] == 1
    assert result.json()["committed_revisions"] == [2]
    assert "PRIVATE TEXT" not in result.text


def test_byok_uses_litellm_and_never_serializes_key(tmp_path, monkeypatch):
    app, client, _, _, _ = workspace(tmp_path)
    from app.litellm_runtime import LiteLLMRuntime
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda _: True))
    key = "test-only-not-a-real-credential"
    result = client.post("/api/model-settings", json={"mode":"byok", "model":"openai/user-selected-model", "api_key":key, "api_base":"https://example.com/v1"})
    assert result.status_code == 200 and result.json()["economy"]["provider"] == "litellm"
    assert key not in result.text
    assert app.state.model_router.china_runtime.session_api_key == key
    assert not list((tmp_path / "runtime").glob("**/*credential*"))
    assert client.post("/api/model-settings", headers={"Origin":"https://foreign.example"}, json={"mode":"preset"}).status_code == 403
    assert client.post("/api/model-settings", json={"mode":"preset"}).json()["economy"]["provider"] == "codex-app-server"
    assert not app.state.model_router.china_runtime.session_api_key


def test_standalone_bridge_configuration_needs_no_codex(tmp_path, monkeypatch):
    from app.sketchup_mcp import _resolve_server
    config = tmp_path / "bridge.json"
    config.write_text(json.dumps({"command":"python", "args":["existing-mcp.py"]}), encoding="utf-8")
    monkeypatch.setenv("ARCH_STUDIO_MCP_CONFIG", str(config))
    command, env, cwd = _resolve_server()
    assert command[-1] == "existing-mcp.py" and not env


def test_desktop_fresh_runtime_without_example_files(tmp_path):
    from app.store import ProjectStore
    store = ProjectStore(tmp_path / "runtime", examples_root=tmp_path / "not-distributed")
    context = store.ensure_seed_project()
    assert context.project_name == "我的第一个建模会话"
    assert store.load_project(context.project_id)["agent_session"].reconstruction_state == "idle"


def test_local_workspace_rejects_foreign_origin_and_host(tmp_path):
    _, client, _, _, _ = workspace(tmp_path)
    assert client.post("/api/projects", headers={"Origin":"https://foreign.example"}, json={"project_name":"No"}).status_code == 403
    assert client.get("/api/status", headers={"Host":"foreign.example"}).status_code == 400


def test_novice_frontend_uses_licensed_safe_markdown_and_real_progress():
    root = Path(__file__).resolve().parents[1]
    js = (root / "app/static/studio.js").read_text(encoding="utf-8")
    assert "html: false" in js and "md.renderer.rules.image" in js
    assert "clipboardData" in js and "dataTransfer" in js
    assert "committed_revisions" in js and "尚无新的模型提交" in js
    assert "item.type !== \"skp\" || hasGeometry" in js
    assert (root / "app/static/vendor/markdown-it/LICENSE").is_file()


def test_url_in_normal_chat_uses_existing_ingestor(tmp_path):
    app, client, project, agent, _ = workspace(tmp_path)
    class ReadableFixture:
        def ingest(self, source):
            return {"type":"url", "source":source, "status":"readable", "title":"Fixture reference", "excerpt":"A test-only public reference description with deep balconies."}
    app.state.reference_ingestor = ReadableFixture()
    response = client.post(f"/api/projects/{project}/conversation", json={"message":"参考 https://example.com/building 帮我分析", "workflow_mode":"image_reconstruction"})
    assert response.status_code == 200
    assert "deep balconies" in agent.calls[-1]["prompt"]


def test_readable_dxf_site_reaches_reconstruction_context(tmp_path):
    import ezdxf
    _, client, project, agent, _ = workspace(tmp_path)
    drawing = ezdxf.new("R2010")
    drawing.header["$INSUNITS"] = 6
    drawing.modelspace().add_lwpolyline([(0,0),(30,0),(30,30),(0,30)], close=True)
    output = io.StringIO()
    drawing.write(output)
    assert client.post(f"/api/projects/{project}/inputs/site?filename=site.dxf", content=output.getvalue().encode()).status_code == 200
    response = client.post(f"/api/projects/{project}/conversation", json={"message":"结合上传的场地分析", "workflow_mode":"image_reconstruction"})
    assert response.status_code == 200
    assert "provided_site" in agent.calls[-1]["prompt"] and "30.0" in agent.calls[-1]["prompt"]


def test_image_delete_restore_invalidates_plan_without_editing_model(tmp_path):
    app, client, project, _, su = workspace(tmp_path)
    buffer = io.BytesIO()
    Image.new("RGB", (10,10)).save(buffer,"PNG")
    path = client.post(f"/api/projects/{project}/inputs/reference?filename=pasted.png",content=buffer.getvalue()).json()["path"]
    from app.models import AgentSession
    session = app.state.store.load_state(project,"agent_session.json",AgentSession)
    session.thread_id = "old-visual-thread"
    session.reconstruction_state = "planned"
    app.state.store.save_state(project,session,"agent_session.json")
    response = client.delete(f"/api/projects/{project}/reference-image",params={"path":path})
    assert response.status_code == 200
    assert not (app.state.store.project_dir(project)/path).exists()
    current = client.get(f"/api/projects/{project}").json()
    assert current["agent_session"]["reconstruction_state"] == "clarifying"
    assert current["agent_session"]["thread_id"] == ""
    assert client.post(f"/api/trash/{response.json()['deleted_id']}/restore").status_code == 200
    assert (app.state.store.project_dir(project)/path).is_file()
    assert not su.calls
    assert client.delete(f"/api/projects/{project}/reference-image",params={"path":"../../outside.png"}).status_code == 404


def test_project_delete_restore_and_busy_guard(tmp_path):
    app, client, project, _, su = workspace(tmp_path)
    root = app.state.store.project_dir(project)
    model = root / "outputs/model/retained.skp"
    model.write_bytes(b"test-only retained fixture")
    app.state.agent_lock.acquire()
    try:
        assert client.delete(f"/api/projects/{project}").status_code == 409
    finally:
        app.state.agent_lock.release()
    result = client.delete(f"/api/projects/{project}")
    assert result.status_code == 200 and not root.exists()
    assert client.get("/api/projects").json() == []
    assert len(client.get("/api/trash").json()) == 1
    assert client.post(f"/api/trash/{result.json()['deleted_id']}/restore").status_code == 200
    assert model.read_bytes() == b"test-only retained fixture"
    assert not client.get("/api/trash").json() and not su.calls
    assert client.post("/api/trash/../../outside/restore").status_code == 404

def test_legacy_attachment_migration_is_idempotent_and_busy_safe(tmp_path):
    import os
    from app.main import _append_conversation
    app, client, project, _, _ = workspace(tmp_path)
    data = io.BytesIO()
    Image.new('RGB', (12, 12)).save(data, 'PNG')
    path = client.post(f'/api/projects/{project}/inputs/reference?filename=legacy.png', content=data.getvalue()).json()['path']
    root = app.state.store.project_dir(project)
    os.utime(root / path, (1, 1))
    context = app.state.store.load_context(project)
    _append_conversation(context, 'user', 'agent', '还原这张图片')
    app.state.store.save(context, root / 'state/project_context.json')
    app.state.agent_lock.acquire()
    try:
        busy = client.get(f'/api/projects/{project}').json()
        assert not busy['context']['references'][0]['submitted_at']
    finally:
        app.state.agent_lock.release()
    migrated = client.get(f'/api/projects/{project}').json()['context']
    assert migrated['conversation'][0]['metadata']['legacy_attachments'] == [path]
    again = client.get(f'/api/projects/{project}').json()['context']
    assert again['conversation'][0]['metadata']['legacy_attachments'] == [path]
    assert (root / path).is_file()
