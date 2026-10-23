from __future__ import annotations

import os
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit

from .litellm_runtime import LiteLLMRuntime
from .native_agent import CodexAppServerRuntime, NativeAgentUnavailable
from .responses_runtime import ResponsesRuntime, ResponsesProfile, PilotBudget
from .modeling_test_profile import assess_sol_low_surrogate
from decimal import Decimal


RoutingTier = Literal["economy", "premium"]
_ALLOWED_REASONING = {"low", "medium", "high", "xhigh", "max"}


@dataclass(frozen=True)
class ModelRoute:
    tier: RoutingTier
    provider: str
    model: str
    reasoning_effort: str
    region: str

    def as_dict(self) -> dict[str, str]:
        return {**asdict(self), "agent_engine": ("codex-app-server" if self.provider in {"codex-app-server", "codex-responses"} else "kstudio-api-loop")}


def _reasoning_effort(env_name: str, default: str) -> str:
    value = os.environ.get(env_name, default).strip().lower()
    if value not in _ALLOWED_REASONING:
        allowed = ", ".join(sorted(_ALLOWED_REASONING))
        raise ValueError(f"{env_name} must be one of: {allowed}.")
    return value


class DeterministicModelRouter:
    """Explicit replaceable model tiers; the Skill/Agent/bridge stack is shared."""

    def __init__(self, codex_runtime: Any, china_runtime: LiteLLMRuntime | None = None,
                 runtime_root: Path | None = None):
        self.codex_runtime = codex_runtime
        self.codex_responses_runtime = None
        self.runtime_root = getattr(codex_runtime, "runtime_root", None) or runtime_root or Path.cwd() / "runtime"
        self.china_runtime = china_runtime or LiteLLMRuntime(
            getattr(codex_runtime, "runtime_root", None) or runtime_root or Path.cwd() / "runtime",
            sketchup_mcp=getattr(codex_runtime, "sketchup_mcp", None),
        )
        self.economy_provider = os.environ.get("ARCH_STUDIO_ECONOMY_PROVIDER", "codex").strip().lower()
        if self.economy_provider not in {"codex", "litellm", "responses"}:
            raise ValueError("ARCH_STUDIO_ECONOMY_PROVIDER must be 'codex', 'litellm' or 'responses'.")
        budget = None
        if os.environ.get("K_STUDIO_OPERATOR_MAX_USD"):
            budget = PilotBudget(Decimal(os.environ["K_STUDIO_OPERATOR_MAX_USD"]),
                Decimal(os.environ["K_STUDIO_OPERATOR_INPUT_RATE_UPPER"]),
                Decimal(os.environ["K_STUDIO_OPERATOR_OUTPUT_RATE_UPPER"]),
                int(os.environ.get("K_STUDIO_OPERATOR_MAX_INPUT_TOKENS", "200000")),
                int(os.environ.get("K_STUDIO_OPERATOR_MAX_OUTPUT_TOKENS", "12000")),
                int(os.environ.get("K_STUDIO_OPERATOR_MAX_REQUESTS", "12")))
        self.responses_runtime = ResponsesRuntime(
            getattr(codex_runtime, "runtime_root", None) or runtime_root or Path.cwd() / "runtime",
            profile=ResponsesProfile(os.environ.get("K_STUDIO_OPERATOR_PROVIDER", "bai"),
                                     os.environ.get("K_STUDIO_OPERATOR_MODEL", "gpt-6.1-sol")),
            budget=budget, sketchup_mcp=getattr(codex_runtime, "sketchup_mcp", None))
        if self.economy_provider == "codex":
            economy_model = os.environ.get("ARCH_STUDIO_ECONOMY_MODEL", "gpt-6.1-sol")
            if "astra" in economy_model.casefold():
                raise ValueError("Economy cannot use an Astra model; select Premium explicitly for GPT-6 Astra.")
            # Current parity baseline: GPT-6.1 Sol Low in both direct Codex and the website.
            # Improve Skill/Harness/tool parity before raising reasoning effort or using Premium.
            economy_effort = _reasoning_effort("ARCH_STUDIO_ECONOMY_REASONING_EFFORT", "low")
            self.economy_route = ModelRoute(
                "economy", "codex-app-server", economy_model, economy_effort, "codex-managed (not exposed)",
            )
        elif self.economy_provider == "responses":
            self.economy_route = ModelRoute("economy", "managed-responses", self.responses_runtime.model,
                _reasoning_effort("ARCH_STUDIO_ECONOMY_REASONING_EFFORT", "low"), self.responses_runtime.region)
        else:
            api_effort = (_reasoning_effort("ARCH_STUDIO_ECONOMY_REASONING_EFFORT", "low")
                          if os.environ.get("ARCH_STUDIO_ECONOMY_REASONING_EFFORT") else "provider-default")
            self.economy_route = ModelRoute(
                "economy", "litellm", self.china_runtime.model, api_effort, self.china_runtime.region,
            )
        premium_model = os.environ.get("ARCH_STUDIO_PREMIUM_MODEL", "gpt-6-astra")
        if premium_model != "gpt-6-astra":
            raise ValueError("Premium v1 is fixed to GPT-6 Astra; economy configuration remains provider-independent.")
        premium_effort = _reasoning_effort("ARCH_STUDIO_PREMIUM_REASONING_EFFORT", "low")
        self.premium_route = ModelRoute(
            "premium", "codex-app-server", premium_model, premium_effort, "codex-managed (not exposed)",
        )
        self.providers = {
            "codex-app-server": codex_runtime,
            "litellm": self.china_runtime,
            "managed-responses": self.responses_runtime,
            "codex-responses": None,
        }

    def configure_codex_responses(self, *, model: str, api_base: str, api_key: str,
                                  reasoning_effort: str, protocol: str,
                                  compatibility_acknowledged: bool) -> None:
        """Explicit session-only opt-in. Never borrow or migrate saved credentials."""
        self.assert_codex_responses_budget_supported()
        if (not model or len(model) > 160 or any(c.isspace() for c in model)
                or "astra" in model.casefold()):
            raise ValueError("Use the provider's exact Economy model ID; Astra is not supported here.")
        if reasoning_effort not in _ALLOWED_REASONING:
            raise ValueError("Select an explicit Codex reasoning effort.")
        from .codex_provider import CodexResponsesProvider
        config = CodexResponsesProvider(api_base=api_base, api_key=api_key, protocol=protocol,
            compatibility_acknowledged=compatibility_acknowledged)
        runtime = CodexAppServerRuntime(self.runtime_root,
            codex_executable=getattr(self.codex_runtime, "codex_executable", None),
            sketchup_mcp=getattr(self.codex_runtime, "sketchup_mcp", None),
            model=model, reasoning_effort=reasoning_effort, api_provider=config)
        if not runtime.available:
            raise NativeAgentUnavailable("Codex App Server is required for this Responses API route. No LiteLLM or account-login fallback.")
        self.codex_responses_runtime = runtime
        self.providers["codex-responses"] = runtime
        self.economy_route = ModelRoute("economy", "codex-responses", model, reasoning_effort, runtime.region)

    @staticmethod
    def assert_codex_responses_budget_supported() -> None:
        # The Codex subprocess may make multiple autonomous requests. Host-only
        # count/token ceilings do not enforce a monetary reservation ledger.
        if any(os.environ.get(name, "").strip() for name in (
                "K_STUDIO_LOCAL_API_TEST_BUDGET", "K_STUDIO_OPERATOR_MAX_USD")):
            raise NativeAgentUnavailable("Codex Responses cannot enforce the configured API monetary budget; route blocked before dispatch. Preserve the ledger and use the capped route; do not remove the cap to bypass it.")

    def clear_codex_responses(self) -> None:
        self.codex_responses_runtime = None
        self.providers["codex-responses"] = None
        # Keep the selected route unavailable: forgetting a key never switches
        # the next request to an account login or another paid provider.

    def runtime_identity(self, tier: RoutingTier) -> str:
        route = self.route(tier)
        runtime = self.providers.get(route.provider)
        identity = getattr(runtime, "session_identity", "")
        payload = [route.provider, route.model, identity,
                   getattr(runtime, "api_base", ""),
                   hashlib.sha256(getattr(runtime, "session_api_key", "").encode()).hexdigest()]
        return hashlib.sha256(json.dumps(payload, ensure_ascii=True).encode()).hexdigest()

    def resumable_thread(self, session: Any, tier: RoutingTier) -> str | None:
        route = self.route(tier)
        if (session.provider == route.provider and session.model == route.model
                and getattr(session, "runtime_identity", "") == self.runtime_identity(tier)):
            return session.thread_id or None
        return None

    @property
    def available(self) -> bool:
        if os.environ.get("ARCH_STUDIO_STANDALONE") == "1":
            return self.economy_route.provider != "codex-app-server" and bool(getattr(self.providers.get(self.economy_route.provider), "available", False))
        return any(bool(getattr(provider, "available", False)) for provider in self.providers.values())

    def route(self, tier: RoutingTier) -> ModelRoute:
        if tier == "economy":
            if os.environ.get("ARCH_STUDIO_STANDALONE") == "1" and self.economy_route.provider == "codex-app-server":
                raise NativeAgentUnavailable("Standalone mode cannot use Codex as a hidden substitute.")
            return self.economy_route
        if tier == "premium":
            if os.environ.get("ARCH_STUDIO_STANDALONE") == "1":
                raise NativeAgentUnavailable("Standalone API mode cannot invoke Codex or Astra.")
            return self.premium_route
        raise ValueError("Model tier must be 'economy' or 'premium'.")

    def respond(self, *, tier: RoutingTier, **kwargs: Any):
        selection = self.route(tier)
        if selection.provider == "codex-responses":
            self.assert_codex_responses_budget_supported()
        provider = self.providers.get(selection.provider)
        if not bool(getattr(provider, "available", False)):
            if selection.provider == "codex-responses":
                raise NativeAgentUnavailable("The selected Codex Responses API route is unavailable. Reconnect this route; no provider fallback was made.")
            if selection.provider == "litellm":
                raise NativeAgentUnavailable(
                    "The configured Economy provider is unavailable. Check its credential/dependency or switch Economy to the local Codex provider."
                )
            if selection.provider == "managed-responses":
                raise NativeAgentUnavailable("Managed Responses is not ready: operator consent, approved profile, credential and priced finite budget are required. No Codex fallback.")
            raise NativeAgentUnavailable("The local Codex App Server is unavailable.")
        return provider.respond(
            **kwargs,
            model=selection.model,
            reasoning_effort=selection.reasoning_effort,
        )

    def status(self) -> dict[str, Any]:
        base = urlsplit(self.china_runtime.api_base)
        safe_base = urlunsplit((base.scheme, base.netloc, base.path, "", "")) if not base.username and not base.password else ""
        return {
            "default_tier": "economy",
            # Metadata only; this never changes the selected Website or Codex model.
            "sol_low_website_test": assess_sol_low_surrogate(
                route_provider=self.economy_route.provider,
                requested_model=self.economy_route.model,
                requested_effort=self.economy_route.reasoning_effort,
            ),
            "sol_medium_website_test": assess_sol_low_surrogate(
                route_provider=self.economy_route.provider,
                requested_model=self.economy_route.model,
                requested_effort=self.economy_route.reasoning_effort,
                target_effort="medium",
            ),
            "economy": self.economy_route.as_dict(),
            "premium": self.premium_route.as_dict(),
            "providers": {
                "codex-app-server": {"available": os.environ.get("ARCH_STUDIO_STANDALONE") != "1" and bool(getattr(self.codex_runtime, "available", False))},
                "litellm": {
                    "available": self.china_runtime.available,
                    "credential_configured": self.china_runtime.credential_configured,
                    "dependency_installed": self.china_runtime.dependency_installed,
                    "region": self.china_runtime.region,
                    "model": self.china_runtime.model,
                    "api_base": safe_base,
                },
                "codex-responses": {
                    "available": bool(getattr(self.codex_responses_runtime, "available", False)) and not any(
                        os.environ.get(name, "").strip() for name in ("K_STUDIO_LOCAL_API_TEST_BUDGET", "K_STUDIO_OPERATOR_MAX_USD")),
                    "credential_configured": self.codex_responses_runtime is not None,
                    "dependency_installed": bool(getattr(self.codex_runtime, "available", False)),
                    "model": getattr(self.codex_responses_runtime, "model", ""),
                    "api_base": getattr(getattr(self.codex_responses_runtime, "api_provider", None), "api_base", ""),
                    "agent_engine": "codex-app-server",
                    "credential_storage": "memory-only",
                    "protocol": "responses",
                    "required_capabilities": ["responses_sse", "function_tools", "image_inputs", "exact_model_identity", "token_usage"],
                    "capability_status": "user_acknowledged_not_provider_verified",
                    "live_quality_status": "NOT_RUN",
                    "monetary_budget_support": "unsupported_fail_closed",
                    "fallback": "none",
                },
                "managed-responses": {
                    "available": self.responses_runtime.available,
                    "provider_label": self.responses_runtime.profile.provider,
                    "model": self.responses_runtime.model,
                    "protocol_status": "verified_offline_only",
                    "live_quality_status": "NOT_RUN",
                    "paid_multi_user": "NOT_READY",
                },
            },
            "premium_rescue_policy": "after repeated Economy failures, suggest Premium; only an explicit Premium request uses Astra",
        }
