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
    updated = client.post("/api/model-settings", json={**request, "api_key": "", "reasoning_effort": "low"})
    assert updated.status_code == 200
    assert updated.json()["economy"]["reasoning_effort"] == "low"
    assert app.state.model_router.china_runtime.session_api_key == "fixture-bai-only"


def test_compatible_api_configuration_is_explicit_and_host_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, *_ = workspace(tmp_path)
    payload = {"mode": "compatible", "model": "vendor/vision-coder", "api_base": "https://api.example.test/v1/",
               "api_key": "fixture-custom-only", "reasoning_effort": "provider-default"}
    result = client.post("/api/model-settings", json=payload)
    assert result.status_code == 200 and "fixture-custom-only" not in result.text
    assert result.json()["economy"]["model"] == "openai/vendor/vision-coder"
    assert app.state.model_router.china_runtime.api_base == "https://api.example.test/v1"
    assert client.post("/api/model-settings", json={**payload, "api_key": ""}).status_code == 200
    assert client.post("/api/model-settings", json={**payload, "api_key": "", "api_base": "https://other.example.test/v1"}).status_code == 400
    assert app.state.model_router.china_runtime.api_base == "https://api.example.test/v1"


def test_compatible_api_rejects_nonbase_or_credential_bearing_urls(tmp_path, monkeypatch):
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, *_ = workspace(tmp_path)
    for url in ("", "http://example.test/v1", "https://key@example.test/v1", "https://example.test/v1?key=fixture",
                "https://example.test/v1/chat/completions/", "https://example.test/v1/responses"):
        assert client.post("/api/model-settings", json={"mode": "compatible", "model": "fixture-model", "api_base": url,
            "api_key": "fixture-custom-only"}).status_code == 400
