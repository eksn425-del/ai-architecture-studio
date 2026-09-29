from __future__ import annotations

import json
from pathlib import Path


WORKSPACE_VERSION = 2

_WORKSPACE_README = """# Architecture Agent Workspace

This directory is the agent's persistent project-coding workspace. Treat it like a small software project, not a scratchpad.

## Required working loop

1. Read the current user request and source/reference images before editing geometry.
2. For image reconstruction, update `notes/reconstruction_card.md` before substantial modeling.
3. For architecture design, record durable decisions in `notes/design_notes.md`.
4. For non-trivial project-specific SketchUp geometry, author or revise a `.rb` file under `scripts/` instead of emitting a large one-off inline snippet.
5. Execute that file with the `sketchup_run_workspace_ruby` tool.
6. Inspect model state and capture multiple useful views with the available SketchUp/SAIE tools.
7. Compare the actual result against the source image or project constraints.
8. Revise the same script/file and re-run it instead of abandoning project history.
9. Store concise QA findings under `qa/` when a material correction is needed.

## Tool split

- Mature semantic operations such as ordinary walls/openings/slabs/roofs/query should prefer namespaced OSS tools such as `saie__...` when they are available and proven.
- Existing Kongxing tools remain the verified document identity/lifecycle boundary.
- Project-specific geometry that is awkward for semantic tools should use persistent Ruby files under `scripts/` and `sketchup_run_workspace_ruby`.
- ArchFlow owns semantic validation/DXF/Ruby/review artifacts where its adopted backend applies.

## Modeling quality rule

A successful tool call is not a successful model. For image reconstruction, do not stop at rough massing when the source visibly contains developed facade/roof geometry: match silhouette, floors/bays, major voids, depth layers, repeated modules, roof/canopy and material zones, then visually inspect and revise. For design work, do not stop after the first rough massing pass when the user requested a developed building.

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

_RECONSTRUCTION_CARD = """# Image reconstruction card

Use this for image-to-SketchUp work. Replace placeholders with observations from the actual source image before substantial geometry.

## Source and confidence

- View type: pending
- Known dimension / scale anchor: pending
- Overall confidence: pending
- Unseen geometry assumptions: pending

## Global proportions

- Overall width / height / inferred depth: pending
- Floor count and floor-line heights: pending
- Primary vertical axes / bay count: pending

## Major form and voids

- Main solids: pending
- Main recesses / negative spaces: pending
- Balconies / terraces / canopies: pending
- Roof / parapet / overhang: pending

## Facade depth stack

1. pending

## Repeated modules

- Windows / doors: pending
- Railings / fins / louvers / frames: pending
- Shared parameters / component candidates: pending

## Materials / colors

- pending

## Build plan

- Pass 1 — silhouette + levels + bay grid: pending
- Pass 2 — facade depth + repeated components + material zones: pending
- Pass 3 — source-matched screenshot QA + corrections: pending

## Current visual mismatches

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
        "Codex parity workflow: the current working directory is a persistent architecture-agent workspace. "
        "Read README.md before non-trivial modeling. For image reconstruction, update notes/reconstruction_card.md "
        "from the actual source image before substantial geometry. Keep durable project-specific Ruby under scripts/; "
        "prefer sketchup_run_workspace_ruby for complex forms so the same file can be revised and re-run across turns. "
        "Use mature semantic OSS tools for ordinary building elements, then use model queries and multiple screenshots "
        "to inspect the result. Do not stop at first-pass rough massing when the source visibly contains developed form: "
        "iterate the same model and scripts until silhouette, floors/bays, major voids, depth layers, repeated facade "
        "modules and roof/canopy are recognizably aligned with the source."
    )
