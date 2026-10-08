from __future__ import annotations

from pathlib import Path


MAX_CONTEXT_CHARS = 10_000


_IMAGE_TO_SKETCHUP_CONTEXT = r"""
# Image → SketchUp reconstruction skill

Reconstruct reference architecture as editable SketchUp geometry. Images are the target appearance; redesign only when asked.

## Success condition

Deliver developed source-matched editable geometry; a few white boxes are an automatic failure.

## Core workflow

**inspect source → clarify high-impact unknowns → parameterize assumptions → user approval → author/revise persistent Ruby → execute → inspect screenshots/model → revise the same scripts/model**.

## Method card A — clarify only what changes the model

Ask only unanswered use/views, scope, scale or inference/detail questions. Propose missing scale; otherwise plan directly.

Never repeat questions or ask micro-details. Accepted estimates/defaults belong in the card; planning revisions do not restart clarification.

## Method card B — parameter card, not vague prose

Update `notes/reconstruction_card.md` before geometry; label KNOWN / ESTIMATED / ASSUMED.

Record scope, dimensions, axes/levels, voids/depth, facade/roof/material systems, instances and scripts.

Approved estimates remain ESTIMATED; exact anchors KNOWN. Distinguish floor/clear height; preserve shared proportions.

## Method card C — explicit approval gate

Before substantial geometry, summarize parameters/assumptions for user approval and revision.

Approval covers all passes/details/QA continuously; never ask for another continue.

No geometry in clarify/plan mode.

## Evidence across views and unseen geometry

Classify evidence: one image, multiple views of ONE building, or text only. Text-only work proposes a design, not an observed reconstruction; do not demand images. Keep the same approval/coding/QA loop.

Record views, floors, openings/materials/landmarks; reconcile ONE building's dimensions and contradictions. Never promise zero errors.

Count openings by facade/floor/panel. OBSERVED source counts differ from approved defaults: obeying a default does not prove fidelity. Check narrow windows, entries, wall returns and roof inner edges. Persist corrected observations in the parameter card and QA notes; old prose must not override pixels.

Record exact filename, landmarks, floor lines/openings. Labels are hints; distinguish street entrance and pool facade. Pair QA by landmarks; correct card/model before acceptance.

With approved inference, rear/sides/roof/interiors stay ASSUMED. Continue levels, thickness, drainage and facade vocabulary; avoid blank/mirrored backs. Stairs, landings and balcony access must connect.

## Facade schedule and numerical checks

In the parameter card, use ONE coordinate convention for the entire building: origin, +X/+Y directions, floor elevations and front/rear mapping. For a whole six-view sheet, identify panels by row/column and visible landmarks; keep the original image intact. Do not treat six panels as six unrelated designs.

Card facade schedule: side/panel, level, opening count/x/z intervals/type, recess depth/confidence. Resolve conflicting panels before approval; unknowns stay ASSUMED. Generate/check from ONE schedule, not independent guesses. Estimate small details.

Before repeating, calculate expected mm bounds for one wall, opening and roof section. Use injected saie_wall.call with string-key mm params for solid wall segments when suitable. This adopted SAIE subset does NOT cut openings: build sill/jamb/head segments around each void or use a verified opening method. A glass face covering a continuous solid wall is not an opening. Roof slab and parapet are separate named children; no full-height cap over a intended recessed roof.

Check transaction owned_after XYZ mm bounds/child IDs against expected positions/sizes, especially opposite walls. Verify each view's openings/roof/glass/frames/soffits/relief/material scale/normals; record defects in qa/visual_qa.md. Size checks cannot prove topology/fidelity. Unchecked views mean partial.

## Method card D — Pass 1: recognizable primary form

After approval, use persistent workspace Ruby as the primary project-specific authoring mechanism. Use SAIE only as a helper for ordinary semantic elements when it is genuinely simpler.

Build envelope/levels, bays, recesses/projections, balconies, roof/canopy and largest openings.

The source-view building must be recognizable before detailing.

Before a full build, verify one representative section: SketchUp numeric lengths are inches. Convert metric parameters once with `.mm` or `.m`; do not mix converted lengths with raw metric coordinates. Read back the section dimensions in the card's units. Check face normals and extrusion direction; a roof must be a shell of the intended thickness, not a filled wedge. Fix scale/direction before repeating geometry.
Convert origins too: `Geom::Point3d.new(10,8,0)` means inches; a 10×8 m corner needs `10.m,8.m,0`. Check all wall corner bounds, not just z. `add_face` does not accept nested arrays as holes; use supported face/opening construction.

Include the source-defining opening in this pass (for example a glazed gable). A solid box hiding it is not an acceptable primary-form checkpoint. Keep durable source files and checkpoints; a timeout requires model readback before retrying, since the operation may have committed.

## Method card E — Pass 2: repeated facade systems

Add glazing/doors/mullions, balcony slabs/rails, louvers, soffits/piers/parapets/trims and material zones.

Build one representative repeated module correctly, inspect it, then instance/array it from shared parameters. Prefer components/instances and clear semantic names over loose faces. Real visible openings/depth should be geometric, not faked only with color.

## Method card F — Pass 3: bounded visual critic and correction

After a geometry pass, run read-only visual QA: compare SOURCE first against CURRENT latest-revision screenshots. Tool/save success is not visual success.

Review front/rear/left/right/roof/oblique with source-matched framing. Write qa/visual_qa.md: current revision, write_verification status, NEEDS_FIX: YES|NO, assessment, at most THREE high-impact mismatches, KEEP list. Prioritize silhouette, storeys/bays, openings, depth, roof/parapet, material zones and intersections.

Only the Builder writes Ruby. For YES, edit named affected groups while preserving KEEP, recapture and review. At most two targeted corrections per turn; remaining blockers mean partial. NO still requires current views and deterministic verification.

Record each QA capture's revision. After any correction, recapture ALL required views; missing/stale rows mean incomplete QA. Correct via edit, integrate baseline separately; replaying replace destroys KEEP IDs.

Report panel/view → observed source fact → actual model → mismatch/action. Integrate successful fixes into the persistent baseline/replay entrypoint so rerunning cannot resurrect defects. Incremental moves are not idempotent builders.

Match source framing; target the building rather than zooming to the entire site. Inspect close oblique roof/wall junctions and openings. A roof cap hiding the parapet and remaining coplanar seams are defects regardless of code intentions. After geometry edits capture new views; older views are historical. Use actual tool-returned image paths and saved SKP artifacts, never invented QA names or an unsaved active blank-model path.

## Replacement versus incremental edits

Default update_mode=replace executes the COMPLETE persistent reconstruction source after clearing the owned root. Never overwrite that baseline with a partial patch or inspection code. Existing-root replace requires allow_full_rebuild=true; disclose that IDs change.

For local fixes, write a separate patch file, reuse the same script_id and update_mode=edit. Use sketchup_inspect_owned for named nested IDs/XYZ mm; it is read-only and paginated, so never create diagnostic geometry to get coordinates. remove_owned_group.call(exact_name) removes one direct child; an array of exact names scopes a nested child, rejecting absent/duplicate/locked/shared ancestors. Rebuild only affected children. Read all pages when proving ID preservation; truncated snapshots cannot prove it. Make repeated instances unique before one-instance edits. General erase/clear and outside-root access remain blocked.

## Finite modeling turns

After one geometry pass and at most two targeted corrections, report actual screenshots and remaining work. Continue large requests on the same scripts/model in later turns. Checkpoints are partial progress, not quality acceptance. Honor readback-only requests without rebuilding.

## Cheap-model discipline

Keep compact shared parameters; inspect each pass and revise persistent files. Never switch models to hide harness failures.

## Scope

Combine taskbook/site/program only when asked. Never modify original SKP/DWG. Work only in the verified disposable/generated model and agent workspace.
""".strip()


_IMAGE_TO_SKETCHUP_CONTEXT += "\n\n" + (Path(__file__).parent / "vendor/sketchup_runtime_skills/reconstruction-excerpts.md").read_text(encoding="utf-8").strip()


def load_image_to_sketchup_skill_context(*, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if max_chars < 512:
        raise ValueError("Image-to-SketchUp skill context limit must be at least 512 characters.")
    if len(_IMAGE_TO_SKETCHUP_CONTEXT) <= max_chars:
        return _IMAGE_TO_SKETCHUP_CONTEXT
    return _IMAGE_TO_SKETCHUP_CONTEXT[:max_chars].rsplit("\n", 1)[0].rstrip()
