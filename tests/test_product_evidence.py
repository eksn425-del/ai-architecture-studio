"""Free regression checks; fixtures do not establish real modeling quality."""
from copy import deepcopy

import pytest

from app.image_to_sketchup_skill import load_image_to_sketchup_skill_context
from app.litellm_runtime import _current_visual_context, _image_count
from tests.test_novice_flow import workspace


def test_visual_context_preserves_sources_and_complete_tool_exchanges():
    source = {"role": "user", "content": [{"type": "text", "text": "Source image: street.png"}, {"type": "image_url", "image_url": {"url": "source"}}]}
    messages = [{"role": "system", "content": "skill"}, source]
    for i in range(20):
        messages.extend([
            {"role": "assistant", "reasoning_content": f"reasoning-{i}", "tool_calls": [{"id": str(i)}]},
            {"role": "tool", "tool_call_id": str(i), "content": f"root revision {i}"},
            {"role": "user", "content": [{"type": "text", "text": "Visual readback from SketchUp tool capture."}, {"type": "image_url", "image_url": {"url": f"capture-{i}"}}]},
        ])
    original = deepcopy(messages)
    wire = _current_visual_context(messages)
    assert messages == original
    assert len(wire) == len(messages)
    assert wire[1] == source
    assert _image_count(wire) == 7  # six latest generated views + actual source
    assert [m for m in wire if m["role"] in {"tool", "assistant"}] == [m for m in messages if m["role"] in {"tool", "assistant"}]
    assert "capture-19" in str(wire) and "capture-0'" not in str(wire)


@pytest.mark.parametrize("views", [0, 1, 6])
def test_three_input_modes_reach_approval_without_geometry(tmp_path, views):
    import io
    from PIL import Image
    from tests.test_reconstruction_integration import PlanningAgent
    app, client, project, _, su = workspace(tmp_path)
    agent = PlanningAgent()
    app.state.model_router.codex_runtime = agent
    app.state.model_router.providers["codex-app-server"] = agent
    for i in range(views):
        image = io.BytesIO()
        Image.new("RGB", (12, 12), (i * 20, 10, 50)).save(image, "PNG")
        assert client.post(f"/api/projects/{project}/inputs/reference?filename=view-{i}.png", content=image.getvalue()).status_code == 200
    endpoint = f"/api/projects/{project}/conversation"
    first = client.post(endpoint, json={"message": "建一个三层别墅，含阳台和坡屋顶", "workflow_mode": "image_reconstruction"})
    assert first.status_code == 200 and first.json()["agent"]["agent_action"] == "clarify"
    plan = client.post(endpoint, json={"message": "完整可编辑，尺寸估算，允许推断背面", "workflow_mode": "image_reconstruction"})
    assert plan.status_code == 200 and plan.json()["agent"]["agent_action"] == "plan"
    assert plan.json()["project"]["agent_session"]["reconstruction_state"] == "planned"
    assert all(not call["mcp_enabled"] and call["tool_profile"] == "reconstruction_coding" for call in agent.calls)
    expected_mode = "text_description" if views == 0 else "single_image" if views == 1 else "multi_view"
    assert all(expected_mode in call["prompt"] for call in agent.calls)
    assert not su.calls


def test_skill_keeps_text_inference_view_mapping_and_safety_visible():
    skill = load_image_to_sketchup_skill_context()
    for text in ("text only", "exact filename", "street entrance", "same scripts/model", "verified disposable/generated model"):
        assert text in skill


def test_responses_only_model_rejected_before_credential_or_tool_request(tmp_path):
    from app.litellm_runtime import LiteLLMRuntime
    from app.native_agent import NativeAgentUnavailable
    with pytest.raises(NativeAgentUnavailable, match="Responses API"):
        LiteLLMRuntime(tmp_path, model="openai/gpt-6.1-sol").respond(
            project_dir=tmp_path, thread_id=None, prompt="Build", mcp_enabled=True,
            developer_instructions="fixture")
    _, client, _, _, _ = workspace(tmp_path)
    response = client.post("/api/model-settings", json={"mode":"byok", "model":"openai/gpt-6.1-sol", "api_key":"test-only-key"})
    assert response.status_code == 409 and "Responses" in response.json()["detail"]
    assert "test-only-key" not in response.text


def test_model_connection_is_free_without_provider_and_locked_during_turn(tmp_path):
    from tests.test_reconstruction_integration import setup_project
    client, agent, su, _ = setup_project(tmp_path)
    agent.available = False
    response = client.post("/api/projects/demo-cultural-center/agent/session", json={"confirm_disposable_model":True})
    assert response.status_code == 200 and response.json()["session"]["status"] == "ready"
    assert not agent.calls
    client.app.state.agent_lock.acquire()
    try:
        assert client.post("/api/projects/demo-cultural-center/agent/session", json={"confirm_disposable_model":True}).status_code == 409
    finally:
        client.app.state.agent_lock.release()
