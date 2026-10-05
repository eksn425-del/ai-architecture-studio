import os
import pytest
from app.local_credentials import LocalCredentialStore
from app.litellm_runtime import LiteLLMRuntime
from tests.test_novice_flow import workspace


@pytest.mark.skipif(os.name != "nt", reason="real Windows DPAPI required")
def test_windows_encrypted_provider_survives_app_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, *_ = workspace(tmp_path)
    secret = "fake-test-key-never-real-credential"
    response = client.post("/api/model-settings", json={"mode":"deepseek", "api_key":secret,
                                                       "reasoning_effort":"provider-default"})
    assert response.status_code == 200
    assert response.json()["credential_storage"] == "windows-dpapi"
    assert secret not in response.text
    store = app.state.credentials
    assert secret.encode() not in store.path.read_bytes()
    other, other_client, *_ = workspace(tmp_path)
    assert other.state.model_router.china_runtime.session_api_key == secret
    status = other_client.get("/api/status")
    assert secret not in status.text
    assert status.json()["model_router"]["economy"]["reasoning_effort"] == "provider-default"
    assert other_client.delete("/api/model-settings/credential").status_code == 200
    assert not store.path.exists()
    fresh, *_ = workspace(tmp_path)
    assert fresh.state.model_router.china_runtime.session_api_key == ""


def test_unsupported_platform_never_writes_plaintext(tmp_path):
    store = LocalCredentialStore(tmp_path)
    store.supported = False
    assert store.save({"api_key":"fake-test"}) is False
    assert store.load() is None
    assert not store.path.exists()


def test_failed_save_keeps_previous_route_and_hides_credential(tmp_path, monkeypatch):
    monkeypatch.setattr(LiteLLMRuntime, "dependency_installed", property(lambda self: True))
    app, client, *_ = workspace(tmp_path)
    previous = app.state.model_router.economy_route
    def fail_save(settings):
        raise OSError("storage unavailable")
    monkeypatch.setattr(app.state.credentials, "save", fail_save)
    response = client.post("/api/model-settings", json={"mode":"deepseek", "api_key":"fake-only-key"})
    assert response.status_code == 500
    assert "fake-only-key" not in response.text
    assert app.state.model_router.economy_route == previous
    assert app.state.model_router.china_runtime.session_api_key == ""


@pytest.mark.skipif(os.name != "nt", reason="real Windows DPAPI required")
def test_corrupt_credential_is_unconfigured_and_not_disclosed(tmp_path):
    app, *_ = workspace(tmp_path)
    path = app.state.credentials.path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not-valid-dpapi")
    fresh, client, *_ = workspace(tmp_path)
    assert fresh.state.credential_restore_error
    assert fresh.state.model_router.china_runtime.session_api_key == ""
    assert "not-valid-dpapi" not in client.get("/api/status").text
