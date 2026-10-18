import hashlib
import json
import threading
import zipfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import connector_setup as subject


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    package = tmp_path / "package"
    package.mkdir()
    for name in subject.PAYLOADS:
        (package / name).write_bytes(("test fixture " + name).encode())
    with zipfile.ZipFile(package / subject.PLUGIN_FILE, "w") as archive:
        archive.writestr("kongxing_ai_sketchup.rb", "# test fixture, never executed")
    manifest = {"schema": 1, "version": "0.1.0-test", "publication": "private_local_trial", "files": {
        name: {"bytes": (package / name).stat().st_size, "sha256": hashlib.sha256((package / name).read_bytes()).hexdigest()}
        for name in subject.PAYLOADS}}
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("ARCH_STUDIO_CONNECTOR_PACKAGE", str(package))
    monkeypatch.delenv("ARCH_STUDIO_MCP_CONFIG", raising=False)
    monkeypatch.setattr(subject, "detect_installations", lambda: [{"year": 2022, "name": "SketchUp 2022", "plugin_present": False}])
    monkeypatch.setattr(subject, "platform_supported", lambda: True)
    monkeypatch.setattr(subject, "_configured", lambda: False)
    calls = []
    monkeypatch.setattr(subject, "verify_runtime", lambda *args: calls.append(args))
    app = FastAPI()
    lock = threading.Lock()
    subject.register_routes(app, lock)
    return TestClient(app), package, calls, lock


def test_download_is_real_rbz_and_install_activates_only_local_runtime(fixture):
    client, package, calls, _ = fixture
    response = client.get("/api/connectors/sketchup/plugin")
    assert response.content == (package / subject.PLUGIN_FILE).read_bytes()
    response = client.post("/api/connectors/sketchup/install", json={"confirm_install": True, "year": 2022})
    assert response.status_code == 200
    assert response.json()["native_reachability"] == "not_checked"
    assert response.json()["plugin_installed_by_setup"] is False
    assert len(calls) == 1
    config = json.loads(subject.target_config().read_text(encoding="utf-8"))
    assert config["command"].endswith("node.exe")
    assert "KONGXING_CONNECTION_FILE" in config["env"]
    assert not (subject.managed_root() / "connection.json").exists()
    # There was no SketchUp extension directory creation or credential copying.
    assert not (subject.managed_root() / "Plugins").exists()


def test_existing_configuration_is_never_overwritten(fixture, monkeypatch):
    client, _, calls, _ = fixture
    path = subject.target_config()
    path.parent.mkdir(parents=True)
    path.write_bytes(b"original settings")
    monkeypatch.setattr(subject, "_configured", lambda: True)
    response = client.post("/api/connectors/sketchup/install", json={"confirm_install": True, "year": 2022})
    assert response.json()["status"] == "existing_configuration_preserved"
    assert path.read_bytes() == b"original settings"
    assert not calls


@pytest.mark.parametrize("payload", [{"year": 2022}, {"confirm_install": False, "year": 2022}, {"confirm_install": True, "year": 2024}, {"confirm_install": True, "year": True}, {"confirm_install": True, "year": "2022"}])
def test_unconfirmed_or_undetected_version_cannot_install(fixture, payload):
    client, _, calls, _ = fixture
    assert client.post("/api/connectors/sketchup/install", json=payload).status_code == 400
    assert not calls
    assert not subject.target_config().exists()


def test_tampered_package_does_not_execute_or_enable_config(fixture):
    client, package, calls, _ = fixture
    path = package / "node.exe"
    data = path.read_bytes()
    path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
    assert client.post("/api/connectors/sketchup/install", json={"confirm_install": True, "year": 2022}).status_code == 400
    assert client.get("/api/connectors/sketchup/plugin").status_code == 503
    assert not calls and not subject.target_config().exists()


def test_missing_bundle_has_no_fake_download(fixture):
    client, package, calls, _ = fixture
    (package / "node.exe").unlink()
    assert client.get("/api/connectors/sketchup/setup").json()["package_available"] is False
    assert client.get("/api/connectors/sketchup/plugin").status_code == 503
    assert not calls


def test_runtime_check_failure_never_activates_partial_config(fixture, monkeypatch):
    client, _, _, _ = fixture
    def fail(*args):
        raise ValueError("runtime self-test failed")
    monkeypatch.setattr(subject, "verify_runtime", fail)
    assert client.post("/api/connectors/sketchup/install", json={"confirm_install": True, "year": 2022}).status_code == 400
    assert not subject.target_config().exists()


def test_installer_cannot_run_during_model_write(fixture):
    client, _, calls, lock = fixture
    lock.acquire()
    try:
        assert client.post("/api/connectors/sketchup/install", json={"confirm_install": True, "year": 2022}).status_code == 409
    finally:
        lock.release()
    assert not calls


def test_invalid_existing_config_is_preserved(fixture):
    client, _, calls, _ = fixture
    path = subject.target_config()
    path.parent.mkdir(parents=True)
    path.write_bytes(b"invalid original config")
    assert client.post("/api/connectors/sketchup/install", json={"confirm_install": True, "year": 2022}).status_code == 400
    assert path.read_bytes() == b"invalid original config" and not calls


def test_repeat_install_does_not_replace_version_files(fixture):
    client, _, calls, _ = fixture
    request = {"confirm_install": True, "year": 2022}
    assert client.post("/api/connectors/sketchup/install", json=request).status_code == 200
    config = subject.target_config().read_bytes()
    assert client.post("/api/connectors/sketchup/install", json=request).status_code == 400
    assert subject.target_config().read_bytes() == config and len(calls) == 1


def test_installed_config_is_discovered_without_codex_and_uses_matching_script_root(fixture, tmp_path, monkeypatch):
    from app.sketchup_mcp import _resolve_server, _generated_script_dir
    client, _, _, _ = fixture
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "no-codex"))
    assert client.post("/api/connectors/sketchup/install", json={"confirm_install":True,"year":2022}).status_code == 200
    command, environment, _ = _resolve_server()
    assert command[0].endswith("node.exe")
    assert _generated_script_dir() == subject.managed_root() / "generated_scripts"
    assert environment["KONGXING_CONNECTION_FILE"].endswith("connection.json")


def test_explicit_missing_profile_never_borrows_managed_or_codex(fixture, tmp_path, monkeypatch):
    from app.sketchup_mcp import _resolve_server, ConnectorUnavailable
    client, _, _, _ = fixture
    assert client.post("/api/connectors/sketchup/install", json={"confirm_install":True,"year":2022}).status_code == 200
    monkeypatch.setenv("ARCH_STUDIO_MCP_CONFIG", str(tmp_path / "missing.json"))
    with pytest.raises(ConnectorUnavailable):
        _resolve_server()
