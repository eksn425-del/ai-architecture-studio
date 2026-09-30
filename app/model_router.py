from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .litellm_runtime import LiteLLMRuntime
from .native_agent import NativeAgentUnavailable


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
        if self.economy_provider not in {"codex", "litellm"}:
            raise ValueError("ARCH_STUDIO_ECONOMY_PROVIDER must be 'codex' or 'litellm'.")
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
        else:
            self.economy_route = ModelRoute(
                "economy", "litellm", self.china_runtime.model, "provider-default", self.china_runtime.region,
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
        }

    @property
    def available(self) -> bool:
        return any(bool(getattr(provider, "available", False)) for provider in self.providers.values())

    def route(self, tier: RoutingTier) -> ModelRoute:
        if tier == "economy":
            return self.economy_route
        if tier == "premium":
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
            raise NativeAgentUnavailable("The local Codex App Server is unavailable.")
        return provider.respond(
            **kwargs,
            model=selection.model,
            reasoning_effort=selection.reasoning_effort,
        )

    def status(self) -> dict[str, Any]:
        return {
            "default_tier": "economy",
            "economy": self.economy_route.as_dict(),
            "premium": self.premium_route.as_dict(),
            "providers": {
                "codex-app-server": {"available": bool(getattr(self.codex_runtime, "available", False))},
                "litellm": {
                    "available": self.china_runtime.available,
                    "credential_configured": self.china_runtime.credential_configured,
                    "dependency_installed": self.china_runtime.dependency_installed,
                    "region": self.china_runtime.region,
                    "model": self.china_runtime.model,
                },
            },
            "premium_rescue_policy": "after repeated Economy failures, suggest Premium; only an explicit Premium request uses Astra",
        }
