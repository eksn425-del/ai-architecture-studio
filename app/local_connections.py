"""Personal, DPAPI-encrypted named API connections. Configuration never calls a provider."""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException, Request

from .local_credentials import LocalCredentialStore
from .model_router import DeterministicModelRouter, ModelRoute
from .native_agent import NativeAgentUnavailable


class ConnectionVault:
    def __init__(self, root: Path):
        self.storage = LocalCredentialStore(root)
        self.storage.path = root / "connections.dpapi"

    def load(self) -> dict:
        saved = self.storage.load()
        if saved is None:
            return {"schema_version": 1, "active_id": None, "connections": []}
        data = json.loads(saved["payload"])
        if (not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("connections"), list)
                or len(data["connections"]) > 100):
            raise ValueError("Invalid local connection store")
        ids = []
        for item in data["connections"]:
            if (not isinstance(item, dict) or not all(isinstance(v, (str, bool)) for v in item.values())
                    or not all(isinstance(item.get(key), str) for key in
                        ("id", "name", "mode", "model", "api_base", "api_key", "reasoning_effort"))
                    or not re.fullmatch(r"[a-f0-9]{32}", item.get("id", ""))):
                raise ValueError("Invalid local connection entry")
            ids.append(item["id"])
        if len(set(ids)) != len(ids) or data.get("active_id") not in [None, *ids]:
            raise ValueError("Invalid active local connection")
        return data

    def save(self, data: dict) -> None:
        if not self.storage.save({"payload": json.dumps(data, ensure_ascii=False)}):
            raise OSError("Encrypted connection persistence is unavailable")

    @staticmethod
    def public(data: dict) -> dict:
        fields = ("id", "name", "mode", "model", "api_base", "reasoning_effort")
        return {"active_id": data["active_id"], "connections": [
            {**{key: item[key] for key in fields}, "credential_configured": True}
            for item in data["connections"]], "credential_storage": "windows-dpapi",
            "account_scope": "current_windows_user", "cloud_sync": False}


def normalized_connection(data: dict, old: dict | None = None) -> dict:
    """A changed transport destination always requires a freshly supplied key."""
    mode = str(data.get("mode", "compatible"))
    if mode not in {"deepseek", "bai", "compatible", "codex-responses"}:
        raise ValueError("请选择受支持的 API 协议。")
    name = str(data.get("name", "")).strip()
    model = str(data.get("model", "")).strip()
    base = str(data.get("api_base", "")).strip().rstrip("/")
    effort = str(data.get("reasoning_effort", "provider-default"))
    if mode == "deepseek":
        model, base = "deepseek/deepseek-flash", "https://api.deepseek.com"
    elif mode == "bai":
        model, base = "openai/" + model.removeprefix("openai/"), "https://api.b.ai/v1"
    elif mode == "compatible":
        model = "openai/" + model.removeprefix("openai/")
    parsed = urlsplit(base)
    if (not name or len(name) > 80 or any(ord(c) < 32 for c in name)
            or not model or model == "openai/" or len(model) > 160
            or any(c.isspace() or ord(c) < 32 for c in model)):
        raise ValueError("请填写连接名称和服务商提供的准确模型标识。")
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or any(ord(c) < 32 for c in base)
            or base.endswith(("/chat/completions", "/responses", "/messages"))):
        raise ValueError("请填写不含凭据的 HTTPS API Base，通常以 /v1 结尾。")
    if mode == "codex-responses":
        if data.get("compatibility_acknowledged") is not True or effort not in {"low", "medium", "high", "xhigh", "max"}:
            raise ValueError("Responses 连接需确认协议能力并选择推理档位。")
    else:
        from .litellm_runtime import requires_responses_tools
        if requires_responses_tools(model):
            raise ValueError("此模型需要显式选择 Responses API，不能使用 Chat Completions。")
        if effort not in {"low", "high", "max", "provider-default"}:
            raise ValueError("此 API 请选择供应商默认、Low、High 或 Max。")
    key = str(data.get("api_key", "")).strip()
    if not key and old and (mode, model, base) == (old["mode"], old["model"], old["api_base"]):
        key = old["api_key"]
    if not key or len(key) > 4096 or any(ord(c) < 32 for c in key):
        raise ValueError("请填写此连接的 API Key；更换地址或模型后需重新填写。")
    return {"id": old["id"] if old else uuid.uuid4().hex, "name": name, "mode": mode,
            "model": model, "api_base": base, "api_key": key, "reasoning_effort": effort,
            "compatibility_acknowledged": mode == "codex-responses"}


def connection_router(app, item: dict | None):
    router = DeterministicModelRouter(app.state.native_agent, runtime_root=app.state.store.root)
    # An empty or removed selection cannot restore a developer account or env key.
    router.china_runtime.session_api_key = ""
    router.china_runtime.key_env = "KSTUDIO_NO_INHERITED_API_KEY"
    if item is None:
        router.economy_route = ModelRoute("economy", "litellm", "", "provider-default", "local-personal")
        return router
    if os.environ.get('KSTUDIO_AGENT_ENGINE') == 'deepseek-harness':
        from .deepseek_studio import DeepSeekStudioRuntime
        provider = DeepSeekStudioRuntime(app.state.store.root, connection=item,
            mcp=getattr(app.state.native_agent, 'sketchup_mcp', None))
        router.providers['deepseek-harness'] = provider
        router.economy_route = ModelRoute('economy','deepseek-harness',provider.model,'high','user-configured (not verified)')
    elif item["mode"] == "codex-responses":
        router.configure_codex_responses(model=item["model"], api_base=item["api_base"],
            api_key=item["api_key"], reasoning_effort=item["reasoning_effort"],
            protocol="responses", compatibility_acknowledged=item["compatibility_acknowledged"])
    else:
        if not router.china_runtime.dependency_installed:
            raise ValueError("本机缺少 API 运行依赖，请修复安装。")
        provider = router.china_runtime
        provider.model, provider.custom_api_base, provider.session_api_key = item["model"], item["api_base"], item["api_key"]
        provider.region = "user-configured (not verified)"
        router.economy_route = ModelRoute("economy", "litellm", item["model"], item["reasoning_effort"], provider.region)
    return router


def register_local_connections(app, root: Path) -> None:
    vault = ConnectionVault(root)
    app.state.connection_vault = vault
    app.state.model_router = connection_router(app, None)
    try:
        saved = vault.load()
        active = next((x for x in saved["connections"] if x["id"] == saved["active_id"]), None)
        if active:
            # Validate encrypted data again; no inference and no login fallback.
            active = normalized_connection(active, active)
            app.state.model_router = connection_router(app, active)
    except (OSError, ValueError, KeyError, TypeError, NativeAgentUnavailable):
        app.state.credential_restore_error = True

    def read():
        try:
            return vault.load()
        except (OSError, ValueError, KeyError, TypeError):
            raise HTTPException(503, "本机加密连接无法读取；原文件已保留，请检查 Windows 用户和备份。") from None

    def result(data):
        return {**vault.public(data), "model_router": app.state.model_router.status()}

    def lock():
        if not app.state.agent_lock.acquire(blocking=False):
            raise HTTPException(409, "请等当前回合结束后再更换 API。")

    @app.get("/api/model-connections")
    def list_connections():
        return result(read())

    @app.post("/api/model-connections")
    async def save_connection(request: Request):
        lock()
        try:
            data = await request.json()
            if not isinstance(data, dict):
                raise ValueError("连接格式不正确。")
            saved = read()
            connection_id = data.get("id")
            old = next((x for x in saved["connections"] if x["id"] == connection_id), None)
            if connection_id and old is None:
                raise HTTPException(404, "连接不存在。")
            if old is None and len(saved["connections"]) >= 100:
                raise ValueError("本机最多保存 100 个连接。")
            item = normalized_connection(data, old)
            router = connection_router(app, item)
            saved["connections"] = [x for x in saved["connections"] if x["id"] != item["id"]] + [item]
            saved["active_id"] = item["id"]
            vault.save(saved)
            app.state.model_router = router
            app.state.credential_restore_error = False
            return result(saved)
        except NativeAgentUnavailable:
            raise HTTPException(409, "此 Responses 连接的本机运行时或金额预算条件不满足；没有改用其他模型。") from None
        except ValueError as error:
            # Validation messages are fixed by this module; JSON decode errors
            # must not echo the incoming credential-bearing body.
            detail = "连接格式不正确。" if isinstance(error, json.JSONDecodeError) else str(error)
            raise HTTPException(400, detail) from None
        except OSError:
            raise HTTPException(500, "Windows 加密保存失败，原配置未改变。") from None
        finally:
            app.state.agent_lock.release()

    @app.post("/api/model-connections/active")
    async def activate_connection(request: Request):
        lock()
        try:
            data = await request.json()
            if not isinstance(data, dict) or "id" not in data:
                raise ValueError("Invalid selection")
            saved = read()
            connection_id = data.get("id")
            item = next((x for x in saved["connections"] if x["id"] == connection_id), None)
            if connection_id is not None and item is None:
                raise HTTPException(404, "连接不存在。")
            router = connection_router(app, item)
            saved["active_id"] = connection_id
            vault.save(saved)
            app.state.model_router = router
            return result(saved)
        except (ValueError, NativeAgentUnavailable):
            raise HTTPException(409, "此连接无法启用；原连接保持不变，未调用 API。") from None
        except OSError:
            raise HTTPException(500, "Windows 加密保存失败，原配置未改变。") from None
        finally:
            app.state.agent_lock.release()

    @app.delete("/api/model-connections/{connection_id}")
    def remove_connection(connection_id: str):
        lock()
        try:
            saved = read()
            if not any(x["id"] == connection_id for x in saved["connections"]):
                raise HTTPException(404, "连接不存在。")
            saved["connections"] = [x for x in saved["connections"] if x["id"] != connection_id]
            router = app.state.model_router
            if saved["active_id"] == connection_id:
                saved["active_id"] = None
                router = connection_router(app, None)
            vault.save(saved)
            app.state.model_router = router
            return result(saved)
        except OSError:
            raise HTTPException(500, "Windows 加密保存失败，原配置未改变。") from None
        finally:
            app.state.agent_lock.release()
