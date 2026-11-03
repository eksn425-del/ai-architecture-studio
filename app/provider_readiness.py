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
        "verified_offline_only_live_not_run",
        "Responses adapter shares project Skills, guarded tools and dedicated Critic; only simulated protocol tested.",
        "Owner-approved independent API budget/key required for actual native quality validation; no hidden Codex fallback.",
    ),
    ProviderReadiness(
        "openai-official", "OpenAI direct API", "independent_api",
        "gpt-6-astra", "officially_documented_not_product_verified", "Responses",
        "adapter_available_live_not_run",
        "Shared Responses transport exists; Astra capability, budget and native quality have not been tested.",
        "Optional premium route only after independent verification, explicit cost consent.",
    ),
    ProviderReadiness(
        "b-ai", "B.AI gateway", "third_party_gateway",
        "gpt-6.1-sol", "provider_documented_not_product_verified", "Responses-compatible advertised",
        "candidate_not_verified",
        "Operator Responses adapter is offline-tested; K Studio has not live-tested B.AI protocol fidelity or quality.",
        "Small pre-paid test with real model identity, function/tool/image/thinking/caching/usage checks and no hidden substitution.",
    ),
    ProviderReadiness(
        "b-ai", "B.AI DeepSeek real product test", "third_party_gateway",
        "deepseek-v4.1-flash", "live_image_recognition_with_errors", "Chat Completions SSE / functions",
        "live_planning_failed_native_not_run",
        "2026-10-21: 18 product responses, workspace tool cycles, five timeouts; repeated strategy validation failed before native modeling. API-only intent and typed plan updates are offline fixes awaiting a live rerun.",
        "Preserve the USD2 liability ledger; require a live same-project build/edit/native-delivery test before promoting this route. Never substitute Codex inference.",
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
        "deepseek/deepseek-flash", "historical_basic_chat_tools_current_version_unverified", "LiteLLM Chat Completions",
        "adapter_available_quality_unverified",
        "Historical basic chat/tool checks do not qualify the current rolling Flash version, vision or native source fidelity.",
        "Do not label it high-fidelity without native new-user evidence.",
    ),
    ProviderReadiness(
        "aliyun-bailian", "Aliyun Bailian official API", "independent_api",
        "dashscope/qwen3.8-flash", "official_documentation_only", "LiteLLM Chat Completions candidate",
        "candidate_not_verified",
        "Official vision/tools documentation and Beijing pricing checked on 2026-10-20; current K Studio native quality not tested.",
        "Benchmark images, reasoning/tool continuation, exact model, usage and native delivery before selecting this route. No automatic switch.",
    ),
)


def readiness_matrix() -> list[dict[str, str]]:
    return [entry.as_dict() for entry in CAPABILITY_MATRIX]


def standalone_premium_ready() -> bool:
    """Fail closed until a measured independent API builder acceptance exists."""
    return False
