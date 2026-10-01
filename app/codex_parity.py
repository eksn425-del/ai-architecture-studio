from __future__ import annotations

import json
from pathlib import Path


WORKSPACE_VERSION = 5

_WORKSPACE_AGENTS = """# Modeling runtime scope

This generated workspace is a modeling job, not a repository maintenance job.
The outer integration agent owns git pull, repository tests, HANDOFF, commit and push.
Do not perform those chores here. Spend this turn on the requested reconstruction.
Write only project scripts, notes and QA inside this workspace. Reference inputs are read-only.
Use only the verified disposable SketchUp model through the supplied tools.
Follow the current host stage: clarify/plan cannot edit geometry; approved execute may
revise persistent Ruby, inspect screenshots and improve the same owned model root.
Never edit original/private SKP/DWG or repository source. Keep modeling network disabled.
"""

_WORKSPACE_README = """# Architecture Agent Workspace

This directory is the agent's persistent project-coding workspace. Treat it like a small software project, not a scratchpad.

## Image reconstruction loop

1. Inspect the actual source image(s).
2. Clarify only high-impact unknowns that materially change the model.
3. Update `notes/reconstruction_card.md` with confirmed scope plus KNOWN / ESTIMATED / ASSUMED parameters.
4. Show the compact parameter/construction plan and wait for approval.
5. After approval, author or revise durable `.rb` files under `scripts/`.
6. Execute the same files with `sketchup_run_workspace_ruby`.
7. Inspect returned screenshots/model state.
8. Correct the same scripts/model rather than restarting.
9. Save concise visual QA notes under `qa/` when useful.

## Architecture-design loop

For later design workflows, record durable design decisions in `notes/design_notes.md`, keep project-specific code under `scripts/`, execute, inspect and revise the same model.

## Tool split

- **Primary for reconstruction:** persistent workspace Ruby for project-specific and repeated geometry.
- **Helper library:** SAIE semantic tools for ordinary walls/openings/slabs/roofs/query/edit when simpler than custom code.
- **Bridge/lifecycle:** Kongxing for verified model identity, viewport/camera/readback and transport.
- **Later engineering outputs:** ArchFlow for validation/DXF/Ruby/review where relevant.

Do not choose a large set of tiny one-off tool calls when a parameterized Ruby/component system better expresses the source. A successful tool call is not a successful model.

## Modeling quality rule

For image reconstruction, a few boxes are not completion when the source contains developed facade/roof geometry. Match silhouette, storeys/bays, major voids, facade depth, repeated modules, roof/canopy and material zones, then compare source-matched screenshots and revise.

Never write private source inputs into this workspace. Never modify the user's original SKP/DWG; work only on the verified disposable project model.
"""

_DESIGN_NOTES = """# Design notes

Keep this file short and durable. Update it when the user confirms or materially changes a design decision.

## Brief / constraints

- Pending extraction from current project context.

## Precedent grammar

- Pending visual/text synthesis from current references.

## Current design decisions

- Pending.

## Open quality issues

- Pending first model/review pass.
"""

_RECONSTRUCTION_CARD = """# Image reconstruction parameter card

Use this for image-to-SketchUp work. Replace placeholders with observations and user-confirmed assumptions before substantial geometry.

## 1. Intended use / required views

- Primary use: pending
- Must support multi-angle viewing / later editing: pending

## 2. Scope

- Include: pending
- Exclude / simplify: pending
- Interior requirement: pending

## 3. Scale anchors

- Known dimension(s): none provided yet
- Visual scale anchor(s): pending
- Dimension confidence: pending

## 4. Unseen geometry policy

- May infer unseen depth/backside: pending
- Inference rule: simplest coherent continuation unless user says otherwise

## 5. Detail target

- Visible detail level: pending
- Micro-detail intentionally omitted: pending

## 6. Source and confidence

- View type: pending
- Overall confidence: pending
- Major ambiguity: pending

## 7. Estimated modeling dimensions

Mark each value as KNOWN / ESTIMATED / ASSUMED.

- Overall width / height / depth: pending
- Floor count and floor-line heights: pending
- Primary bay/module dimensions: pending
- Major opening / balcony / roof projection dimensions: pending

These values are a modeling baseline, not a claim of real-world measurement.

## 8. Major form and voids

- Main solids: pending
- Main recesses / negative spaces: pending
- Balconies / terraces / canopies: pending
- Roof / parapet / overhang: pending

## 9. Facade depth stack

1. pending

## 10. Repeated modules

- Windows / doors: pending
- Railings / fins / louvers / frames: pending
- Shared parameters / component candidates: pending

## 11. Materials / colors

- pending

## 12. Persistent build plan

- Script/component family plan: pending
- SAIE helper operations, if any: pending
- Pass 1 — recognizable primary form: pending
- Pass 2 — facade systems / material zones: pending
- Pass 3 — source-matched screenshot QA + correction: pending

## 13. Approval

- Parameter card approved by user: no
- User-requested changes before build: pending

## 14. Current visual mismatches

- Pending first screenshot comparison.
"""


def prepare_codex_parity_workspace(workspace: Path) -> Path:
    """Seed a persistent project-coding workspace without overwriting agent work."""
    requested_root = workspace.expanduser()
    if requested_root.is_symlink():
        raise ValueError("Agent workspace may not be a symbolic link.")
    root = requested_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    for name in ("scripts", "notes", "qa"):
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        if directory.is_symlink() or not directory.resolve().is_relative_to(root):
            raise ValueError("Codex parity workspace subdirectories must remain inside the agent workspace.")

    instructions = root / "AGENTS.md"
    if not instructions.exists():
        instructions.write_text(_WORKSPACE_AGENTS, encoding="utf-8", newline="\n")

    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(_WORKSPACE_README, encoding="utf-8", newline="\n")

    notes = root / "notes" / "design_notes.md"
    if not notes.exists():
        notes.write_text(_DESIGN_NOTES, encoding="utf-8", newline="\n")

    reconstruction = root / "notes" / "reconstruction_card.md"
    if not reconstruction.exists():
        reconstruction.write_text(_RECONSTRUCTION_CARD, encoding="utf-8", newline="\n")

    manifest = root / ".architecture-studio.json"
    manifest_data = {
        "workspace_version": WORKSPACE_VERSION,
        "purpose": "persistent-agentic-sketchup-coding",
        "scripts_dir": "scripts",
        "notes_dir": "notes",
        "qa_dir": "qa",
        "reconstruction_card": "notes/reconstruction_card.md",
        "reconstruction_flow": ["clarify", "parameterize", "approve", "execute", "inspect", "revise"],
    }
    if not manifest.exists():
        manifest.write_text(
            json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    else:
        try:
            current = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            current = {}
        if isinstance(current, dict) and int(current.get("workspace_version", 0) or 0) < WORKSPACE_VERSION:
            merged = dict(current)
            merged.update(manifest_data)
            manifest.write_text(
                json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
    return root


def codex_parity_instructions() -> str:
    return (
        "This is a generated modeling job; the outer integration agent handles repository maintenance. "
        "Do not run git pull, repository tests, commit or push during modeling. "
        "Direct-Codex parity workflow: use the persistent agent workspace as the source of truth for project code. "
        "For image reconstruction, inspect the source, clarify only high-impact unknowns, then update "
        "notes/reconstruction_card.md with confirmed scope and explicit KNOWN/ESTIMATED/ASSUMED parameters. "
        "Do not edit SketchUp before the parameter/construction plan is approved. After approval, author/revise durable Ruby "
        "under scripts/. Prefer sketchup_run_workspace_ruby for project-specific or repeated geometry; use SAIE as a helper "
        "library for ordinary semantic elements, not as the primary orchestration strategy. Inspect actual screenshots/model state "
        "after substantial edits and revise the same files/model until the source-defining silhouette, floors/bays, voids, facade "
        "depth, repeated systems and roof/canopy are recognizably aligned."
    )
