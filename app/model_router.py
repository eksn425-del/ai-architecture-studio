from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit

from .litellm_runtime import LiteLLMRuntime
from .native_agent import NativeAgentUnavailable
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
        return asdict(self)


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
        }

    @property
    def available(self) -> bool:
        if os.environ.get("ARCH_STUDIO_STANDALONE") == "1":
            return self.economy_route.provider != "codex-app-server" and bool(self.providers[self.economy_route.provider].available)
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
        provider = self.providers[selection.provider]
        if not bool(getattr(provider, "available", False)):
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
