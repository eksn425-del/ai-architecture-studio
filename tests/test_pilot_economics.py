from decimal import Decimal

import pytest

from scripts.pilot_cost_plan import RATES, campaign_plan, estimate_cny


def test_campaign_never_promises_unfunded_gifts():
    plan = campaign_plan()
    assert plan["maximum_invites_financial_only"] == 40
    assert Decimal(plan["gift_cost_ceiling_per_user_cny"]) * 40 + Decimal("50") + Decimal("50") == Decimal("300")
    assert "NOT_BILLING" in plan["mode"]


def test_peak_and_cache_miss_assumptions_and_output_cost_are_counted():
    assert estimate_cny(RATES["deepseek-flash-peak"], 200000, 12000, Decimal("7.5")) == Decimal("0.558")
    assert estimate_cny(RATES["qwen3.8-flash-beijing"], 200000, 12000, Decimal("7.5")) == Decimal("0.1924")
    assert estimate_cny(RATES["bai-gpt-6.1-sol-standard"], 200000, 12000, Decimal("7.5")) == Decimal("3.9")


@pytest.mark.parametrize("args", [{"budget": "NaN"}, {"budget": "-1"}, {"gift": "0"},
    {"reserve": "1000"}, {"usd_cny": "Infinity"}, {"usd_cny": "0"}])
def test_invalid_or_unfunded_plan_rejected(args):
    with pytest.raises(ValueError):
        campaign_plan(**args)
