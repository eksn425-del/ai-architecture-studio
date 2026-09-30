from __future__ import annotations

from typing import Literal

from .architecture_skill import load_architecture_skill_context
from .image_to_sketchup_skill import load_image_to_sketchup_skill_context


WorkflowMode = Literal["architecture_design", "image_reconstruction"]
AgentAction = Literal["auto", "plan", "execute"]
ToolProfile = Literal["full", "reconstruction_coding"]


def load_workflow_skill_context(mode: WorkflowMode, *, mcp_enabled: bool) -> str:
    # Planning turns still need the reconstruction Skill even when SketchUp tools
    # are withheld. Architecture-design keeps its historical behavior.
    if mode == "image_reconstruction":
        return load_image_to_sketchup_skill_context()
    if not mcp_enabled:
        return ""
    return load_architecture_skill_context()


def workflow_tool_profile(mode: WorkflowMode) -> ToolProfile:
    return "reconstruction_coding" if mode == "image_reconstruction" else "full"


def workflow_reference_categories(mode: WorkflowMode) -> tuple[str, ...]:
    return ("reference",) if mode == "image_reconstruction" else ("reference", "site", "brief")


def workflow_prompt_note(mode: WorkflowMode, action: AgentAction = "auto") -> str:
    if mode == "image_reconstruction":
        stage = (
            "This is a PLANNING turn: inspect the reference image, update notes/reconstruction_card.md, propose a compact geometry plan, and do not edit SketchUp geometry."
            if action == "plan" else
            "This is an EXECUTION turn: use the approved reconstruction card/plan, author or revise persistent Ruby, build in the same disposable SketchUp model, inspect screenshots/readback, and correct visible mismatches before replying."
            if action == "execute" else
            "Follow the reconstruction session state: plan before the first substantial build; after approval, continue execution/revision on the same model and persistent scripts."
        )
        return (
            "Current workflow: IMAGE_TO_SKETCHUP_RECONSTRUCTION. The uploaded files under inputs/reference are the visual "
            "target to reconstruct as editable SketchUp geometry. Ignore taskbook, site, program and unrelated design context. "
            "Do not weaken the source into generic precedent principles. " + stage
        )
    return (
        "Current workflow: ARCHITECTURE_DESIGN. Treat project brief/site/user intent as design context and use references "
        "at the fidelity requested by the user. Do not force normal design through the legacy rectangular DesignIR/BuildPlan."
    )


def workflow_developer_instructions(mode: WorkflowMode, *, mcp_enabled: bool,
                                    action: AgentAction = "auto") -> str:
    safety = (
        "When using project Ruby, modify only the supplied owned root and create unique semantic IDs for sibling elements. "
        "Never use project Ruby to access files, processes, network, reflection, other models, or whole-model edit/save APIs. "
        "The static source guard is not a sandbox. Work only on the verified blank-disposable model."
    )
    if mode == "image_reconstruction":
        if action == "plan":
            task = (
                "You are the image-to-SketchUp reconstruction planner. Inspect the actual source image(s), update "
                "notes/reconstruction_card.md, infer coherent proportions/modules, and return a concise construction plan for "
                "approval. Do not edit SketchUp geometry in this turn."
            )
        else:
            task = (
                "You are the image-to-SketchUp reconstruction coding agent. The source image is the target appearance. "
                "Use the approved reconstruction card. Prefer persistent workspace Ruby/components for project-specific and "
                "repeated geometry; use SAIE as a helper for ordinary semantic elements. Execute, inspect actual screenshots/model "
                "state, state concrete mismatches, revise the same scripts/model, and do not stop at rough white-box massing."
            )
    else:
        task = (
            "You are the architecture design agent inside AI Architecture Studio. Reply in Simplified Chinese. Use project "
            "context as design input, preserve conversation continuity, and use the requested precedent fidelity."
        )
    tool_state = (
        "The composed whitelisted SketchUp tool surface is enabled for this verified disposable model."
        if mcp_enabled else
        "SketchUp geometry tools are withheld in this turn; do not perform or claim geometry edits."
    )
    return f"{task} {safety} {tool_state}"
