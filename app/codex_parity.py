from __future__ import annotations

import json
from pathlib import Path


WORKSPACE_VERSION = 1

_WORKSPACE_README = """# Architecture Agent Workspace

This directory is the agent's persistent project-coding workspace. Treat it like a small software project, not a scratchpad.

## Required working loop

1. Read the current brief/site/reference context from the conversation before editing geometry.
2. Record durable design decisions in `notes/design_notes.md`.
3. For non-trivial project-specific SketchUp geometry, author or revise a `.rb` file under `scripts/` instead of emitting a large one-off inline snippet.
4. Execute that file with the `sketchup_run_workspace_ruby` tool.
5. Inspect model state and capture multiple useful views with the available SketchUp/SAIE tools.
6. Compare the result against the brief, site constraints and requested precedent fidelity.
7. Revise the same script/file and re-run it instead of abandoning project history.
8. Store concise QA findings under `qa/` when a material correction is needed.

## Tool split

- Mature semantic operations such as ordinary walls/openings/slabs/roofs/query should prefer namespaced OSS tools such as `saie__...` when they are available and proven.
- Existing Kongxing tools remain the verified document identity/lifecycle boundary.
- Project-specific geometry that is awkward for semantic tools should use persistent Ruby files under `scripts/` and `sketchup_run_workspace_ruby`.
- ArchFlow owns semantic validation/DXF/Ruby/review artifacts where its adopted backend applies.

## Modeling quality rule

A successful tool call is not a successful design. Do not stop after the first rough massing pass. For a design/modeling request, work through form/section/circulation/openings/site relationships, then visually inspect from multiple useful angles and revise material defects before reporting completion.

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


def prepare_codex_parity_workspace(workspace: Path) -> Path:
    """Seed a persistent project-coding workspace without overwriting agent work."""
    root = workspace.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("Agent workspace may not be a symbolic link.")

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

    manifest = root / ".architecture-studio.json"
    if not manifest.exists():
        manifest.write_text(
            json.dumps(
                {
                    "workspace_version": WORKSPACE_VERSION,
                    "purpose": "persistent-agentic-sketchup-coding",
                    "scripts_dir": "scripts",
                    "notes_dir": "notes",
                    "qa_dir": "qa",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return root


def codex_parity_instructions() -> str:
    return (
        "Codex parity workflow: the current working directory is a persistent architecture-agent workspace. "
        "Read README.md before non-trivial modeling. Keep durable project-specific Ruby under scripts/; prefer "
        "sketchup_run_workspace_ruby for complex forms so the same file can be revised and re-run across turns. "
        "Use mature semantic OSS tools for ordinary building elements, then use model queries and multiple screenshots "
        "to inspect the result. Do not stop at first-pass rough massing when the user requested a developed building: "
        "iterate the same model and scripts until the major form, section, circulation, openings and site relationships "
        "are coherent with the brief and requested precedent fidelity."
    )
