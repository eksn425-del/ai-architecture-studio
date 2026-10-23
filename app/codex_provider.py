"""Explicit Responses transport configuration, not another Agent/tool loop.

Compatibility is an operator declaration, not proof of a live provider's quality,
model identity, billing or complete protocol implementation. Unsupported protocols
fail closed; the runtime never falls back to LiteLLM or a Codex login account.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlsplit

API_KEY_ENV = "KSTUDIO_CODEX_API_KEY"


def validate_base_url(value: str, *, allow_loopback: bool = False) -> str:
    base = value.strip().rstrip("/")
    parsed = urlsplit(base)
    local = allow_loopback and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if (not parsed.hostname or (parsed.scheme != "https" and not (local and parsed.scheme == "http"))
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or any(ord(c) < 32 for c in base)
            or base.endswith(("/responses", "/chat/completions", "/messages"))):
        raise ValueError("Codex Responses requires a credential-free HTTPS API base URL, not a request URL.")
    return base


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class CodexResponsesProvider:
    api_base: str
    api_key: str = field(repr=False)
    provider_id: str = "kstudio_api"
    protocol: str = "responses"
    compatibility_acknowledged: bool = False
    allow_loopback: bool = False

    def __post_init__(self) -> None:
        if self.protocol != "responses" or self.compatibility_acknowledged is not True:
            raise ValueError("Explicit Responses/SSE, function tools and image compatibility acknowledgement is required; Chat Completions is not supported by this runtime.")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", self.provider_id) or self.provider_id == "openai":
            raise ValueError("A separate custom provider identity is required.")
        if (not isinstance(self.api_key, str) or not self.api_key.strip() or len(self.api_key) > 4096
                or any(ord(c) < 32 for c in self.api_key)):
            raise ValueError("A valid nonempty API credential is required.")
        object.__setattr__(self, "api_base", validate_base_url(self.api_base, allow_loopback=self.allow_loopback))

    def identity(self, model: str) -> str:
        return fingerprint({"provider": self.provider_id, "base": self.api_base,
                            "model": model, "wire_api": self.protocol, "auth": "env_bearer",
                            "credential_fingerprint": hashlib.sha256(self.api_key.encode()).hexdigest()})

    def config(self) -> dict[str, Any]:
        return {"name": "K Studio explicit Responses API", "base_url": self.api_base,
                "wire_api": "responses", "env_key": API_KEY_ENV,
                "requires_openai_auth": False, "supports_websockets": False,
                "request_max_retries": 0, "stream_max_retries": 0}


def selected_native_provider(config: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    """Retain only the selected transport, never user MCP/tools/prompts/roots.

    Literal headers/tokens cannot safely be copied into a generated config. Use
    upstream env_key/env_http_headers instead. Unknown providers fail explicitly.
    """
    selected = config.get("model_provider", "openai")
    if not isinstance(selected, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", selected):
        raise ValueError("Invalid selected Codex provider identity.")
    providers = config.get("model_providers") or {}
    raw = providers.get(selected) if isinstance(providers, dict) else None
    if raw is None and selected == "openai":
        return selected, None
    if not isinstance(raw, dict):
        raise ValueError("Selected Codex provider configuration is missing.")
    if raw.get("wire_api", "responses") != "responses":
        raise ValueError("Selected Codex provider must support Responses; no protocol fallback is available.")
    if raw.get("http_headers") or raw.get("experimental_bearer_token"):
        raise ValueError("Inline provider credentials/headers are not copied; configure env_key or env_http_headers instead.")
    allowed = {"name", "base_url", "wire_api", "env_key", "env_key_instructions",
               "requires_openai_auth", "supports_websockets", "request_max_retries",
               "stream_max_retries", "stream_idle_timeout_ms", "env_http_headers"}
    if set(raw) - allowed - {"http_headers", "experimental_bearer_token"}:
        raise ValueError("Selected provider has unsupported transport options; refusing to silently discard them.")
    result = {key: value for key, value in raw.items() if key in allowed}
    result.setdefault("name", selected)
    result["wire_api"] = "responses"
    if "base_url" in result:
        # Native localhost servers remain supported without allowing remote HTTP.
        result["base_url"] = validate_base_url(result["base_url"], allow_loopback=True)
    for name in [result.get("env_key"), *(result.get("env_http_headers") or {}).values()]:
        if name is not None and (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)):
            raise ValueError("Provider environment credential references are invalid.")
    return selected, result


def redact(value: Any, secrets: tuple[str, ...]) -> Any:
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return re.sub(r"(?i)(bearer\s+)[^\s\"'<>]+", r"\1[REDACTED]", value)
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key.lower() in {"authorization", "api_key", "access_token", "refresh_token"}
                      else redact(item, secrets)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    return value


def provider_environment(parent: dict[str, str], credential_names: list[str]) -> dict[str, str]:
    # Do not inherit unrelated credentials, outer Codex auth, custom headers or
    # endpoint overrides. Keep only OS/process essentials and explicit proxy setup.
    allowed = {"PATH", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "SYSTEMROOT", "WINDIR",
               "TEMP", "TMP", "TMPDIR", "XDG_RUNTIME_DIR", "LANG", "LC_ALL", "SSL_CERT_FILE",
               "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"}
    env = {key: value for key, value in parent.items() if key.upper() in allowed}
    env.update({name: parent[name] for name in credential_names if name and name in parent})
    return env


def api_environment(parent: dict[str, str], provider: CodexResponsesProvider) -> dict[str, str]:
    env = provider_environment(parent, [])
    env[API_KEY_ENV] = provider.api_key
    return env
