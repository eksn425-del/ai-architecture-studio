"""Offline campaign calculator. Quotes/assumptions only; never a credit ledger.

Rates captured 2026-10-20 from primary provider pages. Recheck before spending.
USD conversion is a configurable planning reserve, not a current FX quote.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_FLOOR
import json


RATES = {
    "qwen3.8-flash-beijing": {"currency": "CNY", "input": "0.8", "output": "2.7",
        "source": "https://help.aliyun.com/zh/model-studio/model-pricing"},
    "deepseek-flash-peak": {"currency": "USD", "input": "0.30", "output": "1.20",
        "source": "https://api-docs.deepseek.com/quick_start/pricing/"},
    "deepseek-flash-offpeak": {"currency": "USD", "input": "0.15", "output": "0.60",
        "source": "https://api-docs.deepseek.com/quick_start/pricing/"},
    "bai-gpt-6.1-sol-standard": {"currency": "USD", "input": "2", "output": "10",
        "source": "https://docs.b.ai/llmservice/pricing-and-usage/"},
}

WORKLOADS = {
    "small_edit_assumption": (200_000, 12_000),
    "building_assumption": (2_000_000, 60_000),
    # Actual historic Sol Builder telemetry, NOT DeepSeek/Qwen measurements.
    # Nine additional Critic calls are excluded: this is not a total invoice.
    "historic_red_house_builder_only": (10_299_507, 73_288),
}


def money(value: str | Decimal) -> Decimal:
    result = Decimal(value)
    if not result.is_finite() or result < 0:
        raise ValueError("Amounts must be finite and non-negative.")
    return result


def estimate_cny(rate: dict, input_tokens: int, output_tokens: int, usd_cny: Decimal) -> Decimal:
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
        raise ValueError("Token counts must be non-negative integers.")
    if rate["currency"] not in {"CNY", "USD"} or money(usd_cny) <= 0:
        raise ValueError("Only CNY/USD prices with a positive planning conversion are supported.")
    amount = (money(rate["input"]) * input_tokens + money(rate["output"]) * output_tokens) / 1_000_000
    return amount * (usd_cny if rate["currency"] == "USD" else 1)


def campaign_plan(budget="300", gift="5", qualification="50", reserve="50", usd_cny="7.5") -> dict:
    budget, gift, qualification, reserve, usd_cny = map(money, (budget, gift, qualification, reserve, usd_cny))
    if budget <= 0 or gift <= 0 or usd_cny <= 0 or qualification + reserve > budget:
        raise ValueError("Positive budget/gift/conversion and funded reserves are required.")
    remaining = budget - qualification - reserve
    invite_count = int((remaining / gift).to_integral_value(rounding=ROUND_FLOOR))
    return {
        "snapshot_date": "2026-10-20", "mode": "OFFLINE_ESTIMATE_NOT_BILLING_OR_QUALITY_PROOF",
        "campaign_budget_cny": str(budget), "qualification_allowance_cny": str(qualification),
        "contingency_cny": str(reserve), "gift_cost_ceiling_per_user_cny": str(gift),
        "maximum_invites_financial_only": invite_count,
        "unused_cny": str(remaining - gift * invite_count),
        "planning_usd_cny_not_live_exchange_rate": str(usd_cny),
        "excludes": ["monthly hosting/storage/SMS/payment/tax", "render/GPU", "unknown usage and price changes"],
        "assumptions": ["Input charged entirely as cache misses; no promotional credits assumed.",
            "Workloads are aggregate tokens across requests, not a single context window.",
            "New providers tokenize/reason/retry differently; equal token assumptions do not imply equal quality.",
            "Historical workload excludes additional Critic usage; failed calls/QA must count in actual settlement.",
            "Invite count is a funded quota calculation, not a capacity or completed-model promise.",
            "Hard quota reservation/settlement and signup/tenant isolation are not implemented by this calculator."],
        "rates_per_million": RATES,
        "workloads": {name: {"input_tokens": usage[0], "output_tokens": usage[1],
            "estimated_cny": {model: str(estimate_cny(rate, *usage, usd_cny).quantize(Decimal("0.0001")))
                              for model, rate in RATES.items()}}
                      for name, usage in WORKLOADS.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget-cny", default="300")
    parser.add_argument("--gift-cny", default="5")
    parser.add_argument("--qualification-cny", default="50")
    parser.add_argument("--reserve-cny", default="50")
    parser.add_argument("--planning-usd-cny", default="7.5")
    args = parser.parse_args()
    print(json.dumps(campaign_plan(args.budget_cny, args.gift_cny, args.qualification_cny,
                                  args.reserve_cny, args.planning_usd_cny), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
