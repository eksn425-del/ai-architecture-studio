from __future__ import annotations

from typing import Literal

from .architecture_skill import load_architecture_skill_context
from .image_to_sketchup_skill import load_image_to_sketchup_skill_context


WorkflowMode = Literal["architecture_design", "image_reconstruction"]


def load_workflow_skill_context(mode: WorkflowMode, *, mcp_enabled: bool) -> str:
    if not mcp_enabled:
        return ""
    if mode == "image_reconstruction":
        return load_image_to_sketchup_skill_context()
    return load_architecture_skill_context()


def workflow_prompt_note(mode: WorkflowMode) -> str:
    if mode == "image_reconstruction":
        return (
            "Current workflow: IMAGE_TO_SKETCHUP_RECONSTRUCTION. The uploaded reference image(s) are the visual "
            "target to reconstruct as editable SketchUp geometry, not merely precedent inspiration. Ignore taskbook, "
            "site, program and unrelated design context unless the user explicitly asks to combine them. Inspect the "
            "actual image before substantial geometry, fill/update notes/reconstruction_card.md, follow the three-pass "
            "reconstruction workflow, capture a source-matched view plus an oblique view, state concrete mismatches and "
            "revise the same model/scripts. Do not report completion at rough white-box massing if the source contains "
            "developed facade, balcony, roof/canopy, opening, louver/rail or material-depth systems."
        )
    return (
        "Current workflow: ARCHITECTURE_DESIGN. Treat project brief/site/user intent as design context and use references "
        "at the fidelity requested by the user. Do not force normal design through the legacy rectangular DesignIR/BuildPlan."
    )


def workflow_developer_instructions(mode: WorkflowMode, *, mcp_enabled: bool) -> str:
    safety = (
        "When using project Ruby, modify only the supplied owned root and create unique semantic IDs for sibling elements. "
        "Never use project Ruby to access files, processes, network, reflection, other models, or whole-model edit/save APIs. "
        "The static source guard is not a sandbox. Work only on the verified blank-disposable model."
    )
    if mode == "image_reconstruction":
        task = (
            "You are the image-to-SketchUp reconstruction agent inside AI Architecture Studio. Reply in Simplified Chinese. "
            "The source image is the target appearance. Use the reconstruction card and shared parameters to translate visible "
            "proportions, floors/bays, solids/voids, facade depth, repeated modules, roof/canopy and material zones into editable "
            "SketchUp geometry. Prefer SAIE semantic tools for ordinary construction and persistent workspace Ruby/components "
            "for repeated/custom facade systems. Inspect screenshots and correct visual mismatches before completion."
        )
    else:
        task = (
            "You are the architecture design agent inside AI Architecture Studio. Reply in Simplified Chinese. Use project "
            "context as design input, preserve conversation continuity, and use the requested precedent fidelity."
        )
    tool_state = (
        "The composed whitelisted SketchUp tool surface is enabled for this verified disposable model."
        if mcp_enabled else
        "SketchUp tools are not enabled in this turn; do not perform or claim geometry edits."
    )
    return f"{task} {safety} {tool_state}"
