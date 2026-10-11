"""Truthful product readiness, separated from model marketing and API documentation.

A provider advertising Responses does not make K Studio's independent
Responses tool loop functional. All capability flags describe THIS product.
Never probe with private credentials or imply account-specific availability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ProviderReadiness:
    provider: str
    display_name: str
    route: str
    model_id: str
    multimodal_input: str
    tool_protocol: str
    product_status: str
    why: str
    recommendation: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


CAPABILITY_MATRIX = (
    ProviderReadiness(
        "codex-local", "Local Codex (developer baseline)", "codex_app_server",
        "gpt-6.1-sol", "supported_when_available", "Codex native dynamic tools",
        "development_baseline", "Requires a user's legitimately available local Codex session.",
        "Do not require this path for public standalone beta.",
    ),
    ProviderReadiness(
        "openai-official", "OpenAI direct API", "independent_api",
        "gpt-6.1-sol", "officially_documented_not_product_verified", "Responses",
        "blocked_pending_adapter",
        "Current K Studio LiteLLM builder is Chat Completions based and explicitly rejects Sol/Astra tool use.",
        "P0: real Responses image/tools/turn continuation, current-view Critic and native SU output parity.",
    ),
    ProviderReadiness(
        "openai-official", "OpenAI direct API", "independent_api",
        "gpt-6-astra", "officially_documented_not_product_verified", "Responses",
        "blocked_pending_adapter",
        "The OpenAI API documents the model, but K Studio has not completed its independent Responses tool loop.",
        "Optional premium route only after independent verification, explicit cost consent.",
    ),
    ProviderReadiness(
        "b-ai", "B.AI gateway", "third_party_gateway",
        "gpt-6.1-sol", "provider_documented_not_product_verified", "Responses-compatible advertised",
        "candidate_not_verified",
        "Public B.AI docs list Sol, Astra, Opus and compatible APIs; K Studio has not live-tested protocol fidelity or quality.",
        "Small pre-paid test with real model identity, function/tool/image/thinking/caching/usage checks and no hidden substitution.",
    ),
    ProviderReadiness(
        "openrouter", "OpenRouter gateway", "third_party_gateway",
        "openai/gpt-6.1-sol", "provider_documented_not_product_verified", "Responses-compatible advertised",
        "candidate_not_verified",
        "Provider aggregation is documented; K Studio routing/feature preservation and actual serving provider are unverified.",
        "Check model/provider pinning, refusal, tool results, images, costs and retention before any user beta.",
    ),
    ProviderReadiness(
        "anthropic-official", "Anthropic official API", "independent_api",
        "claude-opus-5-5", "officially_documented_not_product_verified", "Anthropic Messages",
        "candidate_not_verified",
        "Official API exists but is not a K Studio verified modeling adapter.",
        "Optional future benchmark; separate protocol adapter and native model proof required.",
    ),
    ProviderReadiness(
        "zai-domestic", "Domestic GLM official API", "independent_api",
        "zai/glm-5.3-flash", "live_tested", "LiteLLM Chat Completions",
        "tested_partial_quality",
        "The independent API really built geometry in historical user tests; source-match quality failed/partial.",
        "Keep as an economical testing baseline, not quality PASS.",
    ),
    ProviderReadiness(
        "deepseek-official", "DeepSeek official API", "independent_api",
        "deepseek/deepseek-flash", "live_tested_for_basic_chat_and_tool_contract", "LiteLLM Chat Completions",
        "adapter_available_quality_unverified",
        "UI default exists, but a working connector is not a proven source-faithful building deliverable.",
        "Do not label it high-fidelity without native new-user evidence.",
    ),
)


def readiness_matrix() -> list[dict[str, str]]:
    return [entry.as_dict() for entry in CAPABILITY_MATRIX]


def standalone_premium_ready() -> bool:
    """Fail closed until a measured independent API builder acceptance exists."""
    return False
