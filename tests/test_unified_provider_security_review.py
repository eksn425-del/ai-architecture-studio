"""Independent adversarial checks for the opt-in unified Codex/API route.

All credentials, hosts and processes are fabricated fixtures. These tests do not
read an existing credential store, launch Codex, or make provider HTTP requests.
"""
from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest

from app.local_credentials import LocalCredentialStore
from app.native_agent import NativeAgentUnavailable
from tests.test_novice_flow import workspace


KEY = "fixture-security-review-not-a-real-key"


def settings(**changes):
    return {
        "mode": "codex-responses",
        "model": "fixture-wire-model",
        "api_base": "https://api.example.test/v1",
        "api_key": KEY,
        "protocol": "responses",
        "compatibility_acknowledged": True,
        "reasoning_effort": "low",
        **changes,
    }


@pytest.fixture(autouse=True)
def fabricated_environment_only(tmp_path):
    with patch.dict(os.environ, {
        "HOME": str(tmp_path / "home"),
        "CODEX_HOME": str(tmp_path / "unused-source-home"),
        "ARCH_STUDIO_CODEX_HOME": str(tmp_path / "unused-target-home"),
        "ARCH_STUDIO_USE_LAUNCHER_MODEL": "1",
        "PATH": "/usr/bin:/bin",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
    }, clear=True):
        yield


@pytest.fixture
def isolated_workspace(tmp_path, monkeypatch):
    # No inherited provider configuration, saved key, desktop auth or process.
    with patch.dict(os.environ, {
        "HOME": str(tmp_path / "home"),
        "CODEX_HOME": str(tmp_path / "unused-source-home"),
        "ARCH_STUDIO_CODEX_HOME": str(tmp_path / "unused-target-home"),
        "ARCH_STUDIO_USE_LAUNCHER_MODEL": "1",
        "PATH": "/usr/bin:/bin",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
    }, clear=True):
        monkeypatch.setattr(LocalCredentialStore, "load", lambda *_: pytest.fail("Must not read existing credentials"))
        monkeypatch.setattr("app.native_agent.subprocess.Popen", lambda *a, **k: pytest.fail("Must not launch a process"))
        monkeypatch.setattr("app.native_agent.shutil.which", lambda _: "/fixture/not-executed")
        yield workspace(tmp_path)


def test_review_default_route_and_legacy_credentials_are_not_mutated(isolated_workspace, monkeypatch):
    app, client, *_ = isolated_workspace
    router = app.state.model_router
    original = router.economy_route
    router.china_runtime.session_api_key = "fixture-legacy-key"
    monkeypatch.setattr(app.state.credentials, "save", lambda *_: pytest.fail("Codex API must be memory only"))
    response = client.post("/api/model-settings", json=settings())
    assert response.status_code == 200, response.text
    assert response.json()["economy"]["provider"] == "codex-responses"
    assert router.china_runtime.session_api_key == "fixture-legacy-key"
    assert KEY not in response.text
    assert app.state.preset_route == original
    assert client.post("/api/model-settings", json={"mode": "preset"}).status_code == 200
    assert router.economy_route == original


@pytest.mark.parametrize("change", [
    {"protocol": "chat_completions"},
    {"protocol": "messages"},
    {"compatibility_acknowledged": False},
    {"compatibility_acknowledged": "false"},
    {"compatibility_acknowledged": 1},
    {"reasoning_effort": "provider-default"},
])
def test_review_unsupported_contract_rejects_without_route_mutation(isolated_workspace, change):
    app, client, *_ = isolated_workspace
    previous = app.state.model_router.economy_route
    response = client.post("/api/model-settings", json=settings(**change))
    assert response.status_code in {400, 409}, response.text
    assert app.state.model_router.economy_route == previous
    assert KEY not in response.text


@pytest.mark.parametrize("url", [
    "http://api.example.test/v1", "http://127.0.0.1:12345/v1",
    "https://user:fixture-secret@api.example.test/v1",
    "https://api.example.test/v1?api_key=fixture-secret",
    "https://api.example.test/v1#fixture-secret",
    "https://api.example.test/v1/responses/",
    "https://api.example.test/v1/chat/completions", "file:///tmp/provider",
])
def test_review_settings_reject_unsafe_or_nonbase_url(isolated_workspace, url):
    app, client, *_ = isolated_workspace
    previous = app.state.model_router.economy_route
    response = client.post("/api/model-settings", json=settings(api_base=url))
    assert response.status_code in {400, 409}, response.text
    assert app.state.model_router.economy_route == previous
    assert "fixture-secret" not in response.text


def test_review_explicit_api_key_cannot_be_inherited_from_legacy_or_previous_selection(isolated_workspace):
    app, client, *_ = isolated_workspace
    router = app.state.model_router
    router.china_runtime.model = "fixture-wire-model"
    router.china_runtime.custom_api_base = settings()["api_base"]
    router.china_runtime.session_api_key = "fixture-legacy-key"
    previous = router.economy_route
    assert client.post("/api/model-settings", json=settings(api_key="")).status_code == 400
    assert router.economy_route == previous
    assert client.post("/api/model-settings", json=settings()).status_code == 200
    assert client.post("/api/model-settings", json=settings(api_key="")).status_code == 400
    assert router.china_runtime.session_api_key == "fixture-legacy-key"


@pytest.mark.parametrize("variable", ["K_STUDIO_LOCAL_API_TEST_BUDGET", "K_STUDIO_OPERATOR_MAX_USD"])
def test_review_configured_money_budget_cannot_be_bypassed(isolated_workspace, monkeypatch, variable):
    app, client, *_ = isolated_workspace
    previous = app.state.model_router.economy_route
    # A path is not opened: presence alone must block this unsupported budget route.
    monkeypatch.setenv(variable, "/must-not-read-a-ledger" if variable.endswith("BUDGET") else "2")
    response = client.post("/api/model-settings", json=settings())
    assert response.status_code == 409, response.text
    assert app.state.model_router.economy_route == previous


def test_review_api_credential_removal_does_not_delete_legacy_or_fallback(isolated_workspace, monkeypatch):
    app, client, *_ = isolated_workspace
    router = app.state.model_router
    router.china_runtime.session_api_key = "fixture-legacy-key"
    monkeypatch.setattr(app.state.credentials, "clear", lambda: pytest.fail("Scoped forget must preserve legacy store"))
    assert client.post("/api/model-settings", json=settings()).status_code == 200
    response = client.delete("/api/model-settings/credential?mode=codex-responses")
    assert response.status_code == 200, response.text
    assert router.china_runtime.session_api_key == "fixture-legacy-key"
    assert router.economy_route.provider == "codex-responses"
    for provider in (router.codex_runtime, router.china_runtime):
        monkeypatch.setattr(provider, "respond", lambda **kw: pytest.fail("No fallback inference"))
    with pytest.raises(NativeAgentUnavailable):
        router.respond(tier="economy")
    assert KEY not in response.text


def test_review_cancel_uses_selected_codex_api_runtime_and_stale_identity_is_rejected(isolated_workspace, monkeypatch):
    app, client, project, *_ = isolated_workspace
    assert client.post("/api/model-settings", json=settings()).status_code == 200
    router = app.state.model_router
    provider = router.providers["codex-responses"]
    calls = []
    monkeypatch.setattr(provider, "cancel_turn", lambda path: calls.append(path) or {"status": "requested"})
    monkeypatch.setattr(router.codex_runtime, "cancel_turn", lambda path: pytest.fail("Wrong native provider"), raising=False)
    app.state.active_turns[project] = {"provider": "codex-responses", "request_id": "active-request", "started": time.time(), "action": "clarify"}
    assert client.post(f"/api/projects/{project}/agent/cancel", json={"expected_request_id": "stale-request"}).status_code == 409
    assert not calls
    response = client.post(f"/api/projects/{project}/agent/cancel", json={"expected_request_id": "active-request"})
    assert response.status_code == 200, response.text
    assert len(calls) == 1
    assert response.json()["rollback_performed"] is False
    assert response.json()["terminal_confirmed"] is False


def api_runtime(root, *, key=KEY, model="fixture-model", base="https://api.example.test/v1"):
    from app.codex_provider import CodexResponsesProvider
    from app.native_agent import CodexAppServerRuntime
    return CodexAppServerRuntime(
        root / "runtime", codex_executable="MOCK-NOT-EXECUTED", model=model,
        home_root=root / "generated-home",
        api_provider=CodexResponsesProvider(api_base=base, api_key=key, compatibility_acknowledged=True))


def test_review_api_home_never_reads_native_config_or_copies_login(tmp_path, monkeypatch):
    import tomllib
    from app.codex_provider import API_KEY_ENV
    runtime = api_runtime(tmp_path)
    workspace_path = tmp_path / "project/runtime/agent_workspace"
    workspace_path.mkdir(parents=True)
    monkeypatch.setattr("app.native_agent._toml_load", lambda *_: pytest.fail("API route must not read login configuration"))
    monkeypatch.delenv("K_STUDIO_LOCAL_API_TEST_BUDGET", raising=False)
    monkeypatch.delenv("K_STUDIO_OPERATOR_MAX_USD", raising=False)
    runtime._prepare_home(mcp_enabled=True, agent_workspace=workspace_path)
    raw = (runtime.home / "config.toml").read_text()
    config = tomllib.loads(raw)
    assert KEY not in raw
    assert not (runtime.home / "auth.json").exists()
    assert config["model_provider"] == "kstudio_api"
    profile = config["model_providers"]["kstudio_api"]
    assert profile["requires_openai_auth"] is False
    assert profile["env_key"] == API_KEY_ENV
    assert profile["request_max_retries"] == profile["stream_max_retries"] == 0
    assert config["sandbox_mode"] == "workspace-write"
    assert config["sandbox_workspace_write"]["network_access"] is False
    assert config["sandbox_workspace_write"]["writable_roots"] == [str(workspace_path.resolve())]
    assert API_KEY_ENV in config["shell_environment_policy"]["exclude"]
    assert config["shell_environment_policy"]["ignore_default_excludes"] is False


def test_review_home_and_thread_identity_separate_endpoint_model_and_account(tmp_path):
    first = api_runtime(tmp_path)
    profiles = [first, api_runtime(tmp_path, key="fixture-different-account"),
                api_runtime(tmp_path, model="fixture-different-model"),
                api_runtime(tmp_path, base="https://other.example.test/v1")]
    assert len({str(profile.home) for profile in profiles}) == 4
    assert len({profile.session_identity for profile in profiles}) == 4
    assert KEY not in repr(first.api_provider)
    assert KEY not in str(first.home)


def test_review_child_environment_contains_only_selected_transport_credential():
    from app.codex_provider import API_KEY_ENV, api_environment, CodexResponsesProvider
    provider = CodexResponsesProvider(api_base="https://api.example.test/v1", api_key=KEY, compatibility_acknowledged=True)
    parent = {"PATH": "/fixture/bin", "HOME": "/fixture/home", "OPENAI_API_KEY": "fixture-other-key",
              "OPENAI_BASE_URL": "https://wrong.example.test", "CODEX_THREAD_ID": "foreign-thread",
              "ANTHROPIC_API_KEY": "fixture-unrelated-key", "KSTUDIO_CODEX_API_KEY": "fixture-stale-key"}
    child = api_environment(parent, provider)
    assert child[API_KEY_ENV] == KEY
    assert not ({"OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_THREAD_ID", "ANTHROPIC_API_KEY"} & child.keys())
    assert parent["KSTUDIO_CODEX_API_KEY"] == "fixture-stale-key"


def mock_process(*, reported_provider="kstudio_api", start=None):
    from tests.test_native_turn_control import FakeProcess

    class SelectedProviderProcess(FakeProcess):
        def on_write(self, message):
            if message.get("method") in {"thread/start", "thread/resume"}:
                self.feed({"id": message["id"], "result": {
                    "thread": {"id": "actual-thread"}, "model": "fixture-model",
                    **({"modelProvider": reported_provider} if reported_provider is not None else {})}})
            else:
                super().on_write(message)

    return SelectedProviderProcess(start=start)


def run_api(runtime, project, **changes):
    from tests.test_native_turn_control import run
    workspace_path = project / "runtime/agent_workspace"
    workspace_path.mkdir(parents=True, exist_ok=True)
    return run(runtime, project, workspace_path, **changes)


@pytest.mark.parametrize("reported_provider", [None, "openai", "different_custom_api"])
def test_review_wrong_or_missing_provider_confirmation_never_starts_inference(tmp_path, monkeypatch, reported_provider):
    runtime = api_runtime(tmp_path)
    process = mock_process(reported_provider=reported_provider)
    monkeypatch.setattr("app.native_agent.subprocess.Popen", lambda *a, **kw: process)
    with pytest.raises(NativeAgentUnavailable, match="confirm"):
        run_api(runtime, tmp_path / "project")
    assert not any(message.get("method") == "turn/start" for message in process.sent)
    assert process.stopped


def test_review_same_account_resumes_but_new_account_cannot_resume_old_thread(tmp_path, monkeypatch):
    first = api_runtime(tmp_path)
    processes = []

    def spawn(*args, **kwargs):
        process = mock_process()
        processes.append(process)
        return process

    monkeypatch.setattr("app.native_agent.subprocess.Popen", spawn)
    project = tmp_path / "project"
    result = run_api(first, project)
    run_api(first, project, thread_id=result.thread_id)
    second = api_runtime(tmp_path, key="fixture-other-account")
    run_api(second, project, thread_id=result.thread_id)
    assert [next(message["method"] for message in process.sent if message.get("method") in {"thread/start", "thread/resume"})
            for process in processes] == ["thread/start", "thread/resume", "thread/start"]
    for process in processes:
        turn = next(message["params"] for message in process.sent if message.get("method") == "turn/start")
        assert turn["approvalPolicy"] == "never"
        assert turn["sandboxPolicy"]["networkAccess"] is False
        assert turn["sandboxPolicy"]["writableRoots"] == [str((project / "runtime/agent_workspace").resolve())]


def test_review_credentials_redacted_from_reply_progress_and_logs(tmp_path, monkeypatch):
    import io
    import json

    def start(process, message):
        process.feed({"id": message["id"], "result": {"turn": {"id": "actual-turn"}}})
        process.feed({"method": "item/completed", "params": {
            "threadId": "actual-thread", "turnId": "actual-turn",
            "item": {"type": "agentMessage", "text": "upstream echoed " + KEY}}})
        process.complete()

    runtime = api_runtime(tmp_path)
    process = mock_process(start=start)
    process.stderr = io.BytesIO(("upstream stderr echoed " + KEY + "\n").encode())
    monkeypatch.setattr("app.native_agent.subprocess.Popen", lambda *a, **kw: process)
    progress = []
    result = run_api(runtime, tmp_path / "project", progress_callback=progress.append)
    assert KEY not in result.reply and "[REDACTED]" in result.reply
    assert KEY not in json.dumps(progress)
    assert KEY not in json.dumps(process.sent)
    for path in tmp_path.rglob("*.jsonl"):
        assert KEY not in path.read_text()
    assert KEY not in (runtime.runtime_root / "logs/codex-app-server.log").read_text()


def configured_native_api(tmp_path, monkeypatch):
    from app.native_agent import CodexAppServerRuntime
    source = tmp_path / "fabricated-source-home"
    source.mkdir()
    (source / "config.toml").write_text('''model_provider = "fixture_native_api"
[model_providers.fixture_native_api]
name = "Fabricated native API profile"
base_url = "https://api.example.test/v1"
wire_api = "responses"
env_key = "FIXTURE_REVIEW_API_KEY"
requires_openai_auth = false
''')
    monkeypatch.setenv("CODEX_HOME", str(source))
    monkeypatch.setenv("FIXTURE_REVIEW_API_KEY", KEY)
    return CodexAppServerRuntime(tmp_path / "runtime", codex_executable="MOCK-NOT-EXECUTED",
        home_root=tmp_path / "generated-home", model="fixture-model")


def test_review_native_custom_api_cannot_bypass_configured_money_ledger(tmp_path, monkeypatch):
    runtime = configured_native_api(tmp_path, monkeypatch)
    monkeypatch.setenv("K_STUDIO_LOCAL_API_TEST_BUDGET", "/must-not-read-a-ledger")
    monkeypatch.setattr("app.native_agent.subprocess.Popen", lambda *a, **kw: pytest.fail("Budget bypass launched process"))
    with pytest.raises(NativeAgentUnavailable, match="monetary|budget|ledger"):
        runtime._prepare_home(mcp_enabled=False)
        run_api(runtime, tmp_path / "project")


def test_review_native_custom_api_cannot_accept_wrong_reported_provider(tmp_path, monkeypatch):
    runtime = configured_native_api(tmp_path, monkeypatch)
    monkeypatch.delenv("K_STUDIO_LOCAL_API_TEST_BUDGET", raising=False)
    monkeypatch.delenv("K_STUDIO_OPERATOR_MAX_USD", raising=False)
    runtime._prepare_home(mcp_enabled=False)
    process = mock_process(reported_provider="openai")
    monkeypatch.setattr("app.native_agent.subprocess.Popen", lambda *a, **kw: process)
    with pytest.raises(NativeAgentUnavailable, match="confirm|provider"):
        run_api(runtime, tmp_path / "project")
    assert not any(message.get("method") == "turn/start" for message in process.sent)


def test_review_native_source_account_change_blocks_resume_even_with_stale_router_thread(tmp_path, monkeypatch):
    runtime = configured_native_api(tmp_path, monkeypatch)
    runtime._prepare_home(mcp_enabled=False)
    first_home = runtime.home
    processes = []

    def spawn(*args, **kwargs):
        process = mock_process(reported_provider="fixture_native_api")
        processes.append(process)
        return process

    monkeypatch.setattr("app.native_agent.subprocess.Popen", spawn)
    project = tmp_path / "project"
    result = run_api(runtime, project)
    monkeypatch.setenv("FIXTURE_REVIEW_API_KEY", "fixture-replacement-account")
    runtime._prepare_home(mcp_enabled=False)
    assert runtime.home != first_home
    # Model router may have checked the previous identity before prepare_home.
    # Runtime's provider registry must still refuse to resume that account.
    run_api(runtime, project, thread_id=result.thread_id)
    assert all(any(message.get("method") == "thread/start" for message in process.sent) for process in processes)
    assert not any(message.get("method") == "thread/resume" for process in processes for message in process.sent)
