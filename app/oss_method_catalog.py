"""K AI Studio capability registry: domain-independent adoption states + SketchUp methods.

A method being documented or installed never implies product use or fidelity.
This catalog is intentionally small and backed by concrete existing adapters.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityMethod:
    method_id: str
    provider: str
    source: str
    license: str
    tasks: tuple[str, ...]
    api: str
    conditions: str
    note: str


METHODS = (
    CapabilityMethod(
        "saie.wall", "SAIE", "iamahsanmehmood/saie", "MIT",
        ("wall",), "saie_wall.call(params)",
        "Straight continuous solid wall with mm centerline; installed K Studio adapter.",
        "Prefer a single source-backed wall group over many floating segments.",
    ),
    CapabilityMethod(
        "saie.wall_with_openings", "SAIE", "iamahsanmehmood/saie", "MIT",
        ("wall", "opening"), "saie_wall_with_openings.call(params)",
        "Straight wall with rectangular voids; combined cutter, required mm params.",
        "Correct for standard rectangular doors/windows, not arbitrary polygon holes.",
    ),
    CapabilityMethod(
        "adai.profile", "ADAI", "laowang-wy/adai-sketchup-skill-mcp", "CPAL-1.0",
        ("profile", "roof", "trim"), "adai_geometry.profile(root.entities, ...)",
        "Only when ARCH_STUDIO_ENABLE_ADAI_GEOMETRY=1 and pinned helper verified.",
        "Useful for source-backed constant-section edge/fascia/extrusions.",
    ),
    CapabilityMethod(
        "adai.profile_with_holes", "ADAI", "laowang-wy/adai-sketchup-skill-mcp", "CPAL-1.0",
        ("profile", "opening"), "adai_geometry.profile_with_holes(root.entities, ...)",
        "Only when enabled/verified; confirm actual upstream Ruby parameter contract.",
        "Non-rectangular/perforated profile; do not replace a working SAIE straight wall blindly.",
    ),
    CapabilityMethod(
        "adai.loft_sections", "ADAI", "laowang-wy/adai-sketchup-skill-mcp", "CPAL-1.0",
        ("roof", "loft"), "adai_geometry.loft_sections(root.entities, ...)",
        "Only when enabled/verified and the roof can be expressed by sections.",
        "Try for genuine changing roof sections, not for every simple roof plane.",
    ),
    CapabilityMethod(
        "adai.shell_grid", "ADAI", "laowang-wy/adai-sketchup-skill-mcp", "CPAL-1.0",
        ("shell", "roof"), "adai_geometry.shell_grid(root.entities, ...)",
        "Only when enabled/verified; geometry fidelity and SU compatibility still require real proof.",
        "For an actual grid-based curved shell, not a facade full of unrelated boxes.",
    ),
    CapabilityMethod(
        "adai.closed_band", "ADAI", "laowang-wy/adai-sketchup-skill-mcp", "CPAL-1.0",
        ("roof", "band", "trim"), "adai_geometry.closed_band(root.entities, ...)",
        "Only when enabled/verified and closed-band topology matches the design.",
        "Potential use for coherent roof/fascia perimeter where geometry supports it.",
    ),
    CapabilityMethod(
        "kstudio.custom_owned_ruby", "K AI Studio", "eksn425-del/ai-architecture-studio", "project",
        ("any",), "root.entities (guarded project Ruby)",
        "Fallback only after checking suitable installed, compatible, licensed helpers.",
        "Document the actual mismatch or failure before writing a new geometry primitive.",
    ),
)
BY_ID = {item.method_id: item for item in METHODS}
STAGES = (
    "researched", "installed", "exposed", "smoke_verified", "product_used", "effect_verified",
    "rejected",
)


def candidate_methods(task: str, *, adai_enabled: bool = False) -> tuple[CapabilityMethod, ...]:
    """List plausible implementations, not an automatic fidelity/quality endorsement."""
    return tuple(
        m for m in METHODS
        if ("any" in m.tasks or task in m.tasks)
        and (adai_enabled or m.provider != "ADAI")
    )


def capability_selection_note(*, adai_enabled: bool) -> str:
    """Compact, factual method list for the actual Agent tool context."""
    # The full registry is intentionally small, so enumerate every callable entry.
    chosen = tuple(m for m in METHODS if adai_enabled or m.provider != "ADAI")
    lines = [
        "K AI Studio OSS METHOD ROUTING (real product, not just component installation):",
        "For each roof/wall/opening/profile system, consider a verified suitable OSS method before hand-written Ruby.",
        "Do not force an incompatible OSS method merely to increase call counts.",
        "Write the chosen method_id and source-backed reason in the construction plan; if custom Ruby,",
        "explain why the available SAIE/ADAI implementation does not fit or has failed.",
        "The host reports only actual wrapped method invocations as committed model evidence.",
        "ZERO method calls is zero product use even if the distribution was installed or smoke-tested.",
    ]
    for item in chosen:
        lines.append(f"- {item.method_id}: {item.api}. {item.conditions}")
    if not adai_enabled:
        lines.append("- ADAI: not exposed in this session; install and enable the verified helper explicitly if its geometry is required.")
    lines.append("A successful method call proves execution, NOT source-image match: inspect current SketchUp views.")
    return "\n".join(lines)


def assess_method_adoption(
    construction_strategy: dict | None, committed_ledger: dict | None
) -> dict:
    """Explicitly distinguish *selected* from *executed* and *effect verified*.

    A model-level call does not prove which facade group benefited; that needs
    named geometry readback and independent source-matched review.
    """
    proof = isinstance(committed_ledger, dict) and committed_ledger.get("status") == "committed_readback"
    events = committed_ledger.get("events", []) if proof else []
    if not isinstance(events, list):
        events = []
        proof = False
    used = {}
    if proof:
        for event in events:
            if (isinstance(event, dict) and event.get("status") == "returned"
                    and event.get("method_id") in BY_ID):
                method_id = event["method_id"]
                used[method_id] = used.get(method_id, 0) + 1
    choices = []
    for system in (construction_strategy or {}).get("systems", []):
        if not isinstance(system, dict):
            continue
        selected = system.get("method_id")
        if selected is None:
            disposition = "provider_not_selected"
        elif selected == "kstudio.custom_owned_ruby":
            disposition = "custom_fallback_not_automatically_attributed"
        elif not proof:
            disposition = "execution_receipt_missing"
        elif used.get(selected, 0):
            disposition = "method_seen_in_committed_write"
        else:
            disposition = "selected_but_not_invoked"
        choices.append({
            "system": system.get("id"),
            "method_id": selected,
            "selection_reason": system.get("selection_reason"),
            "disposition": disposition,
        })
    return {
        "schema_version": 1,
        "ledger_status": committed_ledger.get("status") if isinstance(committed_ledger, dict) else "missing",
        "actual_wrapped_calls": used,
        "any_oss_product_use": bool(used),
        "effect_verified": False,
        "effect_verification_required": "Named component readback and independent source-matched visual review.",
        "plan_choices": choices,
    }
