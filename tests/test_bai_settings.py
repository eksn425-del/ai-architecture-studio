from app.litellm_runtime import LiteLLMRuntime
from tests.test_novice_flow import workspace


def test_bai_uses_gateway_model_and_never_reuses_another_host_key(tmp_path, monkeypatch):
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, *_ = workspace(tmp_path)
    assert client.post("/api/model-settings", json={"mode": "deepseek", "api_key": "fixture-official-only"}).status_code == 200
    request = {"mode": "bai", "model": "deepseek-v4.1-flash", "reasoning_effort": "provider-default"}
    rejected = client.post("/api/model-settings", json=request)
    assert rejected.status_code == 400
    assert app.state.model_router.china_runtime.api_base == "https://api.deepseek.com"
    request["api_key"] = "fixture-bai-only"
    result = client.post("/api/model-settings", json=request)
    assert result.status_code == 200
    assert result.json()["economy"]["model"] == "openai/deepseek-v4.1-flash"
    assert result.json()["providers"]["litellm"]["api_base"] == "https://api.b.ai/v1"
    assert "fixture-bai-only" not in result.text
    assert client.post("/api/model-settings", json={**request, "api_key": ""}).status_code == 200
    assert client.post("/api/model-settings", json={"mode": "deepseek", "api_key": ""}).status_code == 400
    assert app.state.model_router.china_runtime.session_api_key == "fixture-bai-only"
