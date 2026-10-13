"""Explicit conditional experiment policy: test K Studio FIRST, original Codex ONLY on failure.

The baseline is diagnostic, not a pretext for more unbounded model usage:
unverified native SKP delivery must first be isolated and fixed. A model
provider capacity outage is BLOCKED, not evidence of inferior agent reasoning.
"""
from __future__ import annotations

from typing import Literal

Result = Literal["PASS", "FAIL", "BLOCKED", "NOT_RUN"]


def decide_codex_baseline(*, delivery: Result, first_pass_source: Result,
                          local_edit: Result, natural_ux: Result,
                          model_capacity_available: bool = True) -> dict[str, str]:
    statuses = (delivery, first_pass_source, local_edit, natural_ux)
    if any(value not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN"} for value in statuses):
        raise ValueError("All acceptance signals require explicit truthful statuses.")
    if delivery != "PASS":
        return {"decision": "P0_DELIVERY_FIRST", "original_codex": "NOT_RUN",
                "reason": "Fix and native-reverify saved/downloaded/reopened geometry first; no new building hides delivery failure."}
    if not model_capacity_available or "BLOCKED" in statuses or "NOT_RUN" in statuses:
        return {"decision": "CONTINUE_SITE_ONCE_AVAILABLE", "original_codex": "NOT_RUN",
                "reason": "Outage or missing evidence cannot rank two agent systems."}
    if all(value == "PASS" for value in statuses):
        return {"decision": "KEEP_K_STUDIO", "original_codex": "NOT_NEEDED",
                "reason": "Website first-version source fidelity, one scoped edit, native delivery and natural UX all passed."}
    return {"decision": "RUN_SAME_SOURCE_NATIVE_CODEX_CONTROL", "original_codex": "CONDITIONAL",
            "reason": "After repaired delivery, same privately held eight original images, actual Sol Medium and comparable MCP/tool permissions: test direct Codex only now. Inspect differences in prompts, image handling, thread history, tool feedback and scope; do not clone unlicensed code."}
