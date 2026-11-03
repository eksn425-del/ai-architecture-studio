"""Real Windows encryption and app recreation; synthetic keys, zero inference."""
import hashlib
import os

import pytest

from app.brain import BrainUnavailable, CodexBrainAdapter
from app.local_credentials import LocalCredentialStore
from app.native_agent import CodexAppServerRuntime, NativeAgentUnavailable
from tests.test_novice_flow import workspace


@pytest.fixture
def personal(tmp_path, monkeypatch):
    monkeypatch.setenv("KSTUDIO_PERSONAL_DESKTOP", "1")
    monkeypatch.setenv("KSTUDIO_CONNECTIONS_DIR", str(tmp_path / "personal"))
    monkeypatch.setenv("ARCH_STUDIO_CODEX_HOME", str(tmp_path / "agent-home"))
    monkeypatch.setenv("ARCH_STUDIO_STANDALONE", "1")
    monkeypatch.setenv("ARCH_STUDIO_ECONOMY_PROVIDER", "litellm")
    monkeypatch.setenv("ARCH_STUDIO_API_KEY_ENV", "INHERITED_API_KEY")
    monkeypatch.setenv("INHERITED_API_KEY", "synthetic-inherited-must-not-use")
    for name in ("K_STUDIO_LOCAL_API_TEST_BUDGET", "K_STUDIO_OPERATOR_MAX_USD"):
        monkeypatch.delenv(name, raising=False)
    return lambda: workspace(tmp_path)


def connection(**kw):
    return dict({"name": "Design A", "mode": "compatible", "model": "fixture-model",
        "api_base": "https://fixture.invalid/v1", "api_key": "synthetic-secret-A",
        "reasoning_effort": "provider-default"}, **kw)


def test_fresh_desktop_ignores_legacy_and_inherited_keys(personal, tmp_path):
    old = LocalCredentialStore(tmp_path / "runtime")
    if old.supported:
        old.save({"model":"old-model", "api_base":"https://old.invalid", "api_key":"synthetic-old", "reasoning_effort":"low"})
        digest = hashlib.sha256(old.path.read_bytes()).hexdigest()
    app, client, *_ = personal()
    assert not app.state.model_router.available
    assert app.state.model_router.china_runtime.configured_api_key == ""
    response = client.get("/api/model-connections")
    assert response.json()["connections"] == [] and response.json()["active_id"] is None
    assert client.post("/api/model-settings", json=connection()).status_code == 409
    assert client.delete("/api/model-settings/credential").status_code == 409
    if old.supported:
        assert hashlib.sha256(old.path.read_bytes()).hexdigest() == digest


@pytest.mark.skipif(os.name != "nt", reason="actual Windows DPAPI persistence")
def test_multiple_connections_restore_after_app_restart_and_keep_keys_private(personal):
    app, client, *_ = personal()
    one = client.post("/api/model-connections", json=connection())
    assert one.status_code == 200
    first = one.json()["active_id"]
    two = client.post("/api/model-connections", json=connection(name="Design B", model="fixture-B", api_key="synthetic-secret-B"))
    assert two.status_code == 200
    second = two.json()["active_id"]
    assert first != second and len(two.json()["connections"]) == 2
    raw = app.state.connection_vault.storage.path.read_bytes()
    assert b"synthetic-secret" not in raw
    fresh, restored, *_ = personal()
    assert fresh.state.model_router.china_runtime.session_api_key == "synthetic-secret-B"
    assert restored.get("/api/model-connections").json()["active_id"] == second
    activated = restored.post("/api/model-connections/active", json={"id":first})
    assert activated.status_code == 200
    assert fresh.state.model_router.china_runtime.session_api_key == "synthetic-secret-A"
    updated = restored.post("/api/model-connections", json=connection(id=first, name="Renamed", api_key=""))
    assert updated.status_code == 200 and fresh.state.model_router.china_runtime.session_api_key == "synthetic-secret-A"
    for response in [one, two, activated, updated, restored.get("/api/status")]:
        assert "synthetic-secret" not in response.text and "synthetic-inherited" not in response.text


@pytest.mark.skipif(os.name != "nt", reason="actual Windows DPAPI persistence")
def test_endpoint_change_requires_new_key_and_atomic_save_failure_keeps_route(personal, monkeypatch):
    app, client, *_ = personal()
    first = client.post("/api/model-connections", json=connection()).json()["active_id"]
    raw = app.state.connection_vault.storage.path.read_bytes()
    denied = client.post("/api/model-connections", json=connection(id=first, api_base="https://other.invalid/v1", api_key=""))
    assert denied.status_code == 400
    assert app.state.connection_vault.storage.path.read_bytes() == raw
    def fail(_): raise OSError("synthetic unavailable")
    monkeypatch.setattr(app.state.connection_vault, "save", fail)
    result = client.post("/api/model-connections", json=connection(api_key="synthetic-new-key"))
    assert result.status_code == 500 and "synthetic-new-key" not in result.text
    assert app.state.model_router.china_runtime.session_api_key == "synthetic-secret-A"
    assert app.state.connection_vault.storage.path.read_bytes() == raw


@pytest.mark.skipif(os.name != "nt", reason="actual Windows DPAPI persistence")
def test_disconnect_and_delete_never_restore_other_key(personal):
    app, client, *_ = personal()
    first = client.post("/api/model-connections", json=connection()).json()["active_id"]
    second = client.post("/api/model-connections", json=connection(name="B", api_key="synthetic-B")).json()["active_id"]
    assert client.delete(f"/api/model-connections/{second}").status_code == 200
    assert not app.state.model_router.available
    fresh, restored, *_ = personal()
    assert not fresh.state.model_router.available
    assert len(restored.get("/api/model-connections").json()["connections"]) == 1
    assert restored.post("/api/model-connections/active", json={"id":first}).status_code == 200
    assert restored.post("/api/model-connections/active", json={"id":None}).status_code == 200
    another, *_ = personal()
    assert not another.state.model_router.available


def test_lock_and_origin_protect_configuration(personal):
    app, client, *_ = personal()
    assert client.post("/api/model-connections", json=connection(), headers={"Origin":"https://outside.invalid"}).status_code == 403
    with app.state.agent_lock:
        assert client.post("/api/model-connections", json=connection()).status_code == 409
        assert client.post("/api/model-connections/active", json={"id":None}).status_code == 409
    assert not app.state.connection_vault.storage.path.exists()


@pytest.mark.skipif(os.name != "nt", reason="actual Windows DPAPI persistence")
def test_responses_connection_persists_explicit_transport_without_login(personal, monkeypatch):
    monkeypatch.setattr(CodexAppServerRuntime, "available", property(lambda self: True))
    app, client, *_ = personal()
    body = connection(mode="codex-responses", model="fixture-responses", reasoning_effort="medium", compatibility_acknowledged=True)
    response = client.post("/api/model-connections", json=body)
    assert response.status_code == 200
    fresh, restored, *_ = personal()
    runtime = fresh.state.model_router.codex_responses_runtime
    assert runtime.api_provider.api_key == "synthetic-secret-A"
    assert not runtime.home.exists()
    assert fresh.state.model_router.economy_route.provider == "codex-responses"
    assert "synthetic-secret" not in restored.get("/api/model-connections").text
    monkeypatch.setenv("K_STUDIO_LOCAL_API_TEST_BUDGET", "synthetic-existing-budget")
    blocked = restored.post("/api/model-connections", json=connection(**{k:v for k,v in body.items() if k not in {"api_key"}}, api_key="synthetic-new"))
    assert blocked.status_code == 409 and runtime.api_provider.api_key == "synthetic-secret-A"


@pytest.mark.skipif(os.name != "nt", reason="actual Windows DPAPI persistence")
def test_corrupt_vault_is_preserved_and_fails_closed(personal):
    app, *_ = personal()
    path = app.state.connection_vault.storage.path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"corrupt-vault-fixture")
    fresh, client, *_ = personal()
    assert fresh.state.credential_restore_error and not fresh.state.model_router.available
    assert client.get("/api/model-connections").status_code == 503
    assert client.post("/api/model-connections", json=connection()).status_code == 503
    assert path.read_bytes() == b"corrupt-vault-fixture"


def test_standalone_has_no_legacy_account_dispatch(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCH_STUDIO_STANDALONE", "1")
    brain = CodexBrainAdapter(codex_executable="fixture")
    assert not brain.available
    with pytest.raises(BrainUnavailable, match="Codex"):
        brain._run("must not dispatch", {})
    native = CodexAppServerRuntime(tmp_path, codex_executable="fixture", home_root=tmp_path / "isolated-home")
    with pytest.raises(NativeAgentUnavailable, match="Codex"):
        native._prepare_home(mcp_enabled=False)
    with pytest.raises(NativeAgentUnavailable, match="Codex"):
        native.respond(project_dir=tmp_path, thread_id=None, prompt="no inference", mcp_enabled=False, developer_instructions="")
    assert not native.home.exists()
