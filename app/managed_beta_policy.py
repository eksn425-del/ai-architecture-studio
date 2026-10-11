"""Fail-closed commercial-model pilot policy, not a deployed billing system.

K Studio may buy provider inference and sell a COMPLETE Agent service. Before
trusted multi-user auth, atomic reservations, reconciled usage, licensing and
tenant isolation exist, no browser/user should obtain this operator key.
This module contains NO credentials and sends NO network request.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_UP
from typing import Literal


Protocol = Literal["responses", "chat_completions", "anthropic_messages"]
Channel = Literal["official", "bai", "openrouter", "other_approved"]


@dataclass(frozen=True)
class ManagedProviderCandidate:
    channel: Channel
    base_url: str
    protocol: Protocol
    model_id: str
    advertised: bool
    tool_image_roundtrip_verified: bool
    model_identity_verified: bool
    privacy_and_commercial_terms_approved: bool
    enabled_for_paid_users: bool = False

    def release_reasons(self) -> tuple[str, ...]:
        reasons = []
        if not self.advertised:
            reasons.append("model_or_endpoint_not_advertised")
        if not self.tool_image_roundtrip_verified:
            reasons.append("real_multimodal_tool_roundtrip_not_verified")
        if not self.model_identity_verified:
            reasons.append("served_model_identity_not_verified")
        if not self.privacy_and_commercial_terms_approved:
            reasons.append("upstream_privacy_and_commercial_terms_not_approved")
        if not self.enabled_for_paid_users:
            reasons.append("operator_has_not_approved_paid_launch")
        return tuple(reasons)

    def ready(self) -> bool:
        return not self.release_reasons()


@dataclass(frozen=True)
class TokenPricing:
    """Operator-entered USD per MILLION tokens; not a public price promise."""
    input_per_million: Decimal
    output_per_million: Decimal
    cache_read_per_million: Decimal
    cache_write_per_million: Decimal

    def __post_init__(self) -> None:
        for name in ("input_per_million", "output_per_million",
                     "cache_read_per_million", "cache_write_per_million"):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError(f"{name} requires a finite nonnegative Decimal")


@dataclass(frozen=True)
class TokenUsage:
    input_uncached: int
    output: int
    cache_read: int = 0
    cache_write: int = 0

    def __post_init__(self) -> None:
        for name in ("input_uncached", "output", "cache_read", "cache_write"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative exact integer")


def estimate_upstream_usd(pricing: TokenPricing, usage: TokenUsage) -> Decimal:
    """Transparent token-only estimate; exclude tools, tax, fees and failed retries."""
    raw = (
        Decimal(usage.input_uncached) * pricing.input_per_million
        + Decimal(usage.output) * pricing.output_per_million
        + Decimal(usage.cache_read) * pricing.cache_read_per_million
        + Decimal(usage.cache_write) * pricing.cache_write_per_million
    ) / Decimal(1_000_000)
    return raw.quantize(Decimal("0.000001"), rounding=ROUND_UP)


def require_owner_approved_spend(
    candidate: ManagedProviderCandidate,
    *,
    authenticated_operator: bool,
    explicit_spend_consent: bool,
    requested_max_usd: Decimal,
    remaining_test_budget_usd: Decimal,
) -> None:
    """Only preflight, not an atomic reservation or release-ready billing claim."""
    if not authenticated_operator or not explicit_spend_consent:
        raise PermissionError("Only an explicitly consenting authenticated operator can start a paid pilot.")
    if not candidate.ready():
        raise PermissionError("Managed provider is not launch-approved: " + ", ".join(candidate.release_reasons()))
    if (not all(isinstance(x, Decimal) and x.is_finite() for x in
                (requested_max_usd, remaining_test_budget_usd))
            or requested_max_usd <= 0 or remaining_test_budget_usd < requested_max_usd):
        raise ValueError("Explicit finite positive spend cap must fit remaining test budget.")
    # No actual API call happens here. Production needs database-backed atomic
    # reservation, per-tenant authentication/authorization, reconciliation,
    # rate/concurrency controls, idempotency and failure/refund semantics.


def managed_public_status(candidate: ManagedProviderCandidate) -> dict[str, object]:
    """A safe overview; never serialize a credential or private full URL."""
    return {
        "channel": candidate.channel,
        "model_id": candidate.model_id,
        "protocol": candidate.protocol,
        "pilot_eligible": candidate.ready(),
        "blockers": list(candidate.release_reasons()),
        "not_a_live_availability_check": True,
    }
