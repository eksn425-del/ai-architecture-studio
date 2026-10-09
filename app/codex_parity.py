from __future__ import annotations

import json
from pathlib import Path

from .construction_strategy import default_construction_strategy, construction_strategy_schema_note
from .reconstruction_evidence import default_reconstruction_evidence
from .adai_components import geometry_helper


WORKSPACE_VERSION = 12

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
3. Update `notes/reconstruction_card.md`, classify source coverage in `notes/reconstruction_evidence.json`, keep `notes/facade_schedule.json` as the compact machine-readable facade/roof schedule, and write `notes/construction_strategy.json` with shared parameters, method ownership and verification views.
4. Show the compact parameter/construction plan and wait for approval.
5. After approval, follow the internal construction stages in order: primary form → representative module → replication → variants → finish. These are not extra user approval gates.
6. Author or revise durable `.rb` files under `scripts/`; verify one representative repeated module before copying it.
7. Execute the same files with `sketchup_run_workspace_ruby`, inspect returned screenshots/model state, and correct the same scripts/model rather than restarting.
8. Maintain `qa/visual_qa.md`: compare source first, then current front/rear/left/right/roof/oblique evidence; keep at most three highest-impact mismatches plus a KEEP list.
9. `qa/repair_history.json` is host-owned read-only memory of prior correction attempts. Before repeating a fix after context compaction, read it and avoid methods whose next trusted review still said `still_needs_fix`.

## Architecture-design loop

For later design workflows, record durable design decisions in `notes/design_notes.md`, keep project-specific code under `scripts/`, execute, inspect and revise the same model.

## Tool split

- **Primary for reconstruction:** persistent workspace Ruby for project-specific and repeated geometry.
- **Geometry helpers inside the single writer:** use injected SAIE wall/opening helpers from persistent ProjectRuby when suitable; reconstruction-profile SAIE/Kongxing backend tools remain read-only evidence helpers.
- **Optional ADAI:** read `notes/adai_geometry_contract.md` for this process's verified enabled/disabled state and exact supported profile signatures before writing geometry.
- **Bridge/lifecycle:** Kongxing for verified model identity, viewport/camera/readback and transport.
- **Later engineering outputs:** ArchFlow for validation/DXF/Ruby/review where relevant.

Do not choose a large set of tiny one-off tool calls when a parameterized Ruby/component system better expresses the source. A successful tool call is not a successful model.

## Modeling quality rule

Read `notes/volume_inventory.md` before geometry. Fill its source-to-model table for EVERY visible primary/attached volume, roof and canopy across ALL sources. Record attachment/height relationships, silhouette landmarks, estimated ratios and exact target named paths. Do not infer that a material boundary is a separate storey, or collapse a visible lower annex into the taller main box. Estimates need a visible anchor and cross-view check, not merely "estimated from images".

At the primary-form stage, compare both source-angle silhouettes BEFORE spending effort on plants/furniture. This is an internal continuous-agent check, not another user confirmation gate. After each commit update the same inventory with actual built paths and missing/mismatched regions. The Native host runs a fresh independent read-only Critic on trusted source/current images; its verdict replaces Builder self-review. Prioritize its massing/roof issues and preserve only genuinely correct geometry.

For image reconstruction, a few boxes are not completion when the source contains developed facade/roof geometry. Match silhouette, storeys/bays, major voids, facade depth, repeated modules, roof/canopy and material zones, then compare source-matched screenshots and revise.

At each visual review, inventory every visible primary and attached volume in both source and model before judging details. Missing annexes/lower roofs and wrong silhouettes outrank decoration or template clutter. Do not call these matched merely because the main facade is recognizable. Do not invent extra plants or geometry to hide a template figure: record the lifecycle artifact and preserve the source layout. A correction should address the largest remaining source mismatch, not conceal evidence.

KEEP fingerprints protect unchanged geometry, not every object sharing a correct material or style. If a roof needs a slope change, do not freeze that roof's dimensions or add a duplicate roof merely to satisfy KEEP. Map the review to unaffected named subgroups and correct the target in place; record ambiguous KEEP interpretations before a write.

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

## 4. Evidence fidelity / Unseen geometry policy

- Fidelity mode: pending (single_view_inference / multi_view_reconstruction / full_evidence_reconstruction)
- Primary visible source: pending
- May infer genuinely unseen depth/backside: yes unless user forbids
- May infer unseen interior: yes unless user forbids
- Inference rule: coherent with observed structure, circulation and facade vocabulary; never overwrite evidenced regions
- Full-evidence mode: CAD/floorplan dimensions are geometry constraints; exterior/interior images are visible-appearance constraints

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



_FACADE_SCHEDULE = {
    "schema_version": 1,
    "source_mode": "pending",
    "dimensions_mm": {
        "overall_width": None,
        "overall_depth": None,
        "level_height": None,
        "floor_count": None,
    },
    "views": {
        name: {
            "provenance": "pending",
            "opening_count": None,
            "door_count": None,
            "features": [],
            "notes": [],
        }
        for name in ("front", "rear", "left", "right")
    },
    "roof": {
        "provenance": "pending",
        "type": "pending",
        "parapet": "pending",
        "divisions": [],
        "notes": [],
    },
    "global_features": [],
    "user_confirmed": [],
    "inferred": [],
}


_VISUAL_QA = """# Visual QA

This is the durable read-only review record for the current reconstruction.

## Review contract

- Reference evidence reviewed first: pending
- Current model revision: pending
- Required current views: front / rear / left / right / roof / oblique
- Do not reuse an old screenshot after a geometry revision.
- Tool success, file save and nonempty geometry are not visual acceptance.

## Critic result

NEEDS_FIX: pending

### Highest-impact mismatches

1. pending
2. pending
3. pending

### KEEP — already correct, do not disturb

- pending

## Deterministic readback

- post-write verification receipt: pending
- expected vs actual bounds / counts: pending

## Correction rounds

- Round 1: pending
- Round 2: pending

Stop after at most two targeted correction rounds in one turn. If blocking mismatches remain, report them instead of claiming completion.
"""

_VOLUME_INVENTORY = """# Source-to-model volume inventory

This is a visual reasoning record, not a finite geometry action vocabulary.
Fill before building; update from actual source-matched views after every commit.

| Stable feature ID | Source files / visible landmarks | Main or attached volume / roof / canopy | Attachment and height relation | Estimated ratio + visible anchor + uncertainty | Exact owned paths | Current source-match / missing / wrong |
|---|---|---|---|---|---|---|
| pending | pending | pending | pending | pending | pending | not built |

Compare ALL supplied whole images. Account for lower white annexes and their separate roofs, setbacks and openings, not just the dominant facade. Mark unseen portions as inferred. A legal JSON plan or successful writer is not evidence of silhouette agreement.

## Primary-form silhouette check

- Source-angle high/low landmarks, roof-edge endpoints and step in height: pending
- Largest unresolved massing mismatch (before details): pending
- Alternate spatial interpretation / confidence: pending
- Actual helper choice and reason (SAIE / verified ADAI profile / project Ruby): pending

Do not invent landscaping to cover template people. Fix lifecycle separately. Never claim installed ADAI was used without actual script calls.
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

    inventory = root / "notes" / "volume_inventory.md"
    if not inventory.exists():
        inventory.write_text(_VOLUME_INVENTORY, encoding="utf-8", newline="\n")

    # Give the coding agent the verified optional API contract without copying
    # upstream CPAL source into generated workspaces or the public repository.
    adai_enabled = geometry_helper(Path(__file__).resolve().parents[1]) is not None
    (root / "notes" / "adai_geometry_contract.md").write_text(
        "# Optional ADAI geometry contract\n\n"
        + ("ADAI 0.5.39 verified helper is enabled for this process. Upstream: "
           "laowang-wy/adai-sketchup-skill-mcp; CPAL-1.0; original LICENSE/NOTICE retained in the isolated installation.\n"
           "The host injects `adai_geometry` inside the single guarded ProjectRuby transaction. "
           "Write only into root.entities; no separate ADAI MCP writer.\n\n"
           "- profile(entities, name, outline_mm, depth_mm, plane='xz', offset_mm=0, material=nil)\n"
           "- profile_with_holes(entities, name, outer_mm, holes_mm, depth_mm, plane='xy', offset_mm=0, material=nil)\n"
           "Coordinates are 2D numeric mm rings; depth must be positive. xy extrudes +Z, xz +Y, yz +X. "
           "Holes must be fully inside the outer contour without crossing/touching it. "
           "Wall-bottom doors require a notched/segmented outer profile or the existing SAIE wall/opening helper, "
           "not a boundary-touching hole. Use returned named groups for later targeted editing. "
           "Non-rectangular roof sections may use profile; do not invent a complex roof absent from the source.\n"
           if adai_enabled else "ADAI is disabled. Do not call adai_geometry; use existing verified helpers.\n"),
        encoding="utf-8", newline="\n",
    )

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

    facade_schedule = root / "notes" / "facade_schedule.json"
    if not facade_schedule.exists():
        facade_schedule.write_text(
            json.dumps(_FACADE_SCHEDULE, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    reconstruction_evidence = root / "notes" / "reconstruction_evidence.json"
    # Native coding models cannot inspect host validators outside their workspace.
    (root / "notes" / "reconstruction_contracts.md").write_text(
        "# Reconstruction planning JSON contracts\n\n"
        "Paths are relative to the PROJECT root: inputs/reference/file.png, never ../../inputs/... . "
        "Keep whole view sheets intact. Evidence sources.kind is exterior_image/interior_image/floorplan_image/"
        "cad/document/dimension_note; provenance is pending/observed/user_confirmed/inferred. "
        "A six-panel sheet is kind=exterior_image; describe its panels in notes/role. "
        "Observed exterior_views.source_refs and scale_anchors.source_ref must be actual PROJECT-relative input FILE PATHS "
        "(inputs/reference/file.png), never source IDs such as source_sheet_01. "
        "Estimated scale anchors are objects with name, positive value_mm, provenance=inferred. "
        "hard_constraints and assumptions are string lists. "
        "unseen_exterior is infer_coherent/do_not_infer; unseen_interior is infer_plausible/do_not_infer. "
        "Mark absent CAD/floorplan/interior provided=false and provenance=pending.\n\n"
        "Facade provenance additionally allows mixed. opening_count and door_count must be nonnegative integers or null; "
        "dimensions_mm values are nonnegative numbers or null. features/notes/divisions/global_features/"
        "user_confirmed/inferred are string lists. JSON syntax alone does not prove schema validity.\n\n"
        "## Evidence template\n```json\n" + json.dumps(default_reconstruction_evidence(), ensure_ascii=False, indent=2) +
        "\n```\n\n## Facade schedule template\n```json\n" + json.dumps(_FACADE_SCHEDULE, ensure_ascii=False, indent=2) +
        "\n```\n", encoding="utf-8"
    )
    if not reconstruction_evidence.exists():
        reconstruction_evidence.write_text(
            json.dumps(default_reconstruction_evidence(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    construction_strategy = root / "notes" / "construction_strategy.json"
    (root / "notes" / "construction_strategy_schema.md").write_text(
        construction_strategy_schema_note(), encoding="utf-8"
    )
    if not construction_strategy.exists():
        construction_strategy.write_text(
            json.dumps(default_construction_strategy(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    visual_qa = root / "qa" / "visual_qa.md"
    if not visual_qa.exists():
        visual_qa.write_text(_VISUAL_QA, encoding="utf-8", newline="\n")

    manifest = root / ".architecture-studio.json"
    manifest_data = {
        "workspace_version": WORKSPACE_VERSION,
        "purpose": "persistent-agentic-sketchup-coding",
        "scripts_dir": "scripts",
        "notes_dir": "notes",
        "qa_dir": "qa",
        "reconstruction_card": "notes/reconstruction_card.md",
        "facade_schedule": "notes/facade_schedule.json",
        "reconstruction_evidence": "notes/reconstruction_evidence.json",
        "construction_strategy": "notes/construction_strategy.json",
        "visual_qa": "qa/visual_qa.md",
        "repair_history": "qa/repair_history.json",
        "repair_history_policy": "host-owned-read-only",
        "reconstruction_flow": ["clarify", "parameterize", "approve", "execute", "verify", "inspect", "critic", "revise"],
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
        "Before geometry read and fill notes/volume_inventory.md for all visible primary/attached volumes, roofs and canopies across every source. "
        "Check their attachment, height steps and silhouette in source-matched views before details; give visual anchors for estimated ratios. "
        "Missing low annexes/roofs and wrong silhouettes outrank plants/furniture. Native visual-review submission invokes a fresh independent read-only Critic; follow its returned issues, not your proposed verdict. "
        "KEEP applies only to unchanged geometry: preserving roof material/character does not freeze a roof that needs a slope change. Do not add duplicate roof geometry to bypass KEEP. "
        "Direct-Codex parity workflow: use the persistent agent workspace as the source of truth for project code. "
        "For image reconstruction, inspect the source, clarify only high-impact unknowns, then update "
        "notes/reconstruction_card.md with confirmed scope and explicit KNOWN/ESTIMATED/ASSUMED parameters, and update "
        "notes/reconstruction_evidence.json with the fidelity mode/source coverage/inference boundary, notes/facade_schedule.json with compact per-view opening/roof facts and observed/user_confirmed/inferred provenance, and notes/construction_strategy.json with shared parameters, construction methods, stage ownership and verification views. "
        "In single-view mode, the visible source view is a hard appearance target while hidden regions may be inferred coherently. In full-evidence mode, supplied exterior views, CAD/floor plans and interior images are hard constraints and only genuinely unseen gaps may be inferred. Do not edit SketchUp before the parameter/construction plan is approved. After approval, author/revise durable Ruby "
        "under scripts/. Follow primary form → representative module → replication → variants → finish internally, without new user approvals. Prefer sketchup_run_workspace_ruby for project-specific or repeated geometry; use only the injected SAIE "
        "geometry helpers inside guarded ProjectRuby when they fit, while reconstruction backend tools stay read-only. After every mutation, require the "
        "post-write verification receipt before trusting success. Maintain qa/visual_qa.md from fresh front/rear/left/right/roof/oblique "
        "evidence: record at most three highest-impact mismatches plus a KEEP list, then make at most two targeted correction rounds. "
        "Inspect actual screenshots/model state after substantial edits and revise the same files/model until the source-defining "
        "silhouette, floors/bays, voids, facade depth, repeated systems and roof/canopy are recognizably aligned."
    )
