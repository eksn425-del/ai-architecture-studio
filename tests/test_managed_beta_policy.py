"""K Studio sells a service, not an uncontrolled shared upstream API key."""
from decimal import Decimal as D

import pytest

from app.managed_beta_policy import (
    ManagedProviderCandidate, TokenPricing, TokenUsage, estimate_upstream_usd,
    require_owner_approved_spend, managed_public_status,
)


def candidate(**changes):
    data = {
        "channel": "bai", "base_url": "https://api.b.ai/v1",
        "protocol": "responses", "model_id": "gpt-6.1-sol",
        "advertised": True, "tool_image_roundtrip_verified": False,
        "model_identity_verified": False,
        "privacy_and_commercial_terms_approved": False,
        "enabled_for_paid_users": False,
    }
    data.update(changes)
    return ManagedProviderCandidate(**data)


def test_advertised_catalog_entry_is_not_usable_for_real_paying_users():
    x = candidate()
    assert not x.ready()
    assert "real_multimodal_tool_roundtrip_not_verified" in x.release_reasons()
    output = managed_public_status(x)
    assert output["pilot_eligible"] is False
    assert "base_url" not in output


def test_every_release_gate_and_spend_authorization_is_required():
    c = candidate(tool_image_roundtrip_verified=True, model_identity_verified=True,
                  privacy_and_commercial_terms_approved=True, enabled_for_paid_users=True)
    assert c.ready()
    with pytest.raises(PermissionError):
        require_owner_approved_spend(c, authenticated_operator=True, explicit_spend_consent=False,
                                     requested_max_usd=D("3"), remaining_test_budget_usd=D("5"))
    with pytest.raises(ValueError):
        require_owner_approved_spend(c, authenticated_operator=True, explicit_spend_consent=True,
                                     requested_max_usd=D("6"), remaining_test_budget_usd=D("5"))
    require_owner_approved_spend(c, authenticated_operator=True, explicit_spend_consent=True,
                                 requested_max_usd=D("3"), remaining_test_budget_usd=D("5"))


def test_rounding_and_cache_classes_never_assume_free_tokens():
    p = TokenPricing(D("2"), D("10"), D("0.10"), D("2.5"))
    usage = TokenUsage(input_uncached=1_000_000, output=100_000,
                       cache_read=1_000_000, cache_write=10_000)
    assert estimate_upstream_usd(p, usage) == D("3.125000")
    with pytest.raises(ValueError):
        TokenUsage(input_uncached=-1, output=1)
    with pytest.raises(ValueError):
        TokenPricing(D("NaN"), D("10"), D("0.10"), D("2.5"))


def test_disabled_paid_users_cannot_be_laundered_through_operator_consent():
    c = candidate(tool_image_roundtrip_verified=True, model_identity_verified=True,
                  privacy_and_commercial_terms_approved=True)
    with pytest.raises(PermissionError, match="launch-approved"):
        require_owner_approved_spend(c, authenticated_operator=True, explicit_spend_consent=True,
                                     requested_max_usd=D("1"), remaining_test_budget_usd=D("5"))
