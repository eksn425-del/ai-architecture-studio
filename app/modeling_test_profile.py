"""Honest provenance for a paid-API-free, REAL model-controlled Studio test.

This does not provide an API emulator or switch the user's selected Codex
or website models. A Codex-App-Server-selected Sol Low call is real inference,
but is NOT evidence that B.AI/official Responses executes equivalently.
"""
from __future__ import annotations
from typing import Any


TARGET_MODEL = "gpt-6.1-sol"
TARGET_EFFORT = "low"


def assess_sol_low_surrogate(
    *,
    route_provider: str,
    requested_model: str,
    requested_effort: str,
    actual_model: str | None = None,
    actual_effort: str | None = None,
) -> dict[str, Any]:
    configured = (route_provider == "codex-app-server"
                  and requested_model == TARGET_MODEL
                  and requested_effort == TARGET_EFFORT)
    identity_known = bool(actual_model) and bool(actual_effort)
    executed_match = (configured and identity_known
                      and actual_model == TARGET_MODEL
                      and actual_effort == TARGET_EFFORT)
    return {
        "schema_version": 1,
        "purpose": "K_Studio_website_architectural_modeling_only",
        "underlying_transport": route_provider,
        "requested_model": requested_model,
        "requested_effort": requested_effort,
        "actual_model": actual_model,
        "actual_effort": actual_effort,
        "status": ("REAL_SURROGATE_IDENTITY_VERIFIED" if executed_match
                   else "CONFIGURED_NOT_EXECUTED" if configured and not identity_known
                   else "MODEL_IDENTITY_MISMATCH" if configured
                   else "NOT_THIS_TEST_PROFILE"),
        "real_inference_if_executed": bool(executed_match),
        "paid_gateway_requests_proven": False,
        "official_or_bai_responses_parity_proven": False,
        "future_gateway_protocol_and_quality_test_still_required": True,
        "does_not_override_any_selected_model": True,
    }
