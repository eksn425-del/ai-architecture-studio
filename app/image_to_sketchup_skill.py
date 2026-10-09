from __future__ import annotations

from pathlib import Path


MAX_CONTEXT_CHARS = 10_500


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

## Construction strategy — choose how to build before writing geometry

Maintain `notes/construction_strategy.json` as compact method memory. After approval: **primary form → representative module → replication → variants → finish**, with no extra user gates. Primary form includes defining roof/voids/openings; verify one real repeated module before copying.

Route systems deliberately: `continuous_wall_with_openings` for straight opening hosts; `profile_extrusion` for constant sections; `loft_or_mesh`/`custom_owned_ruby` for changing forms; `prototype_instance` only after its prototype is correct. Store shared dimensions/levels once with provenance and use named owned paths so corrections touch the smallest dependent system and preserve KEEP geometry.

## Evidence fidelity modes

Maintain `notes/reconstruction_evidence.json` beside the parameter card and facade schedule. Evidence completeness controls how much freedom the Builder has.

**single_view_inference** — one exterior image is enough to reconstruct. The visible source view is a HARD visual target: match silhouette, storey/bay proportions, opening count/position, facade depth, colors/material zones, glass, railings, visible furniture/interior and source-defining detail. Do not stop at generic massing. Hidden rear/sides/roof/interior may be plausibly inferred without another questionnaire unless the user forbids inference. Inferred regions must continue the visible structure, circulation and facade vocabulary; never leave them blank or mirror the front blindly.

**multi_view_reconstruction** — two or more observed exterior views constrain ONE coherent building. Every observed facade is a hard target. Reconcile dimensions and landmarks across views; do not improve one observed facade by contradicting another. Infer only regions absent from all sources.

**full_evidence_reconstruction** — use only when the validated evidence ledger actually contains front/rear/left/right/roof views plus floorplan, CAD and interior evidence. Treat supplied CAD/floorplan dimensions and topology as geometry constraints, and supplied exterior/interior images as appearance/detail constraints. Do not redesign any evidenced region. Railings, glazing, mullions, facade layers, stairs, built-ins, visible furniture/materials and interior elements shown by sources belong to the reconstruction target. Only genuinely unobserved gaps may be inferred. If sources conflict, record the contradiction and keep quality PARTIAL until resolved; never average conflicting evidence silently.

Evidence authority when sources disagree: explicit user correction/dimension > CAD/floorplan dimension/topology > orthographic/multi-view observed geometry > perspective image appearance/detail > inference. This hierarchy does not allow CAD to erase visible material/detail evidence.

Record exact source path/kind, exterior-view coverage, floorplan/CAD/interior coverage, scale anchors, hard constraints and assumptions in the evidence ledger. Keep source-backed facts separate from inference. A user correction is not proof that automatic recognition originally succeeded.

Count openings by facade/floor/panel. OBSERVED source counts differ from approved defaults: obeying a default does not prove fidelity. Check narrow windows, entries, wall returns and roof inner edges. Persist corrected observations in the parameter card/schedule/QA; old prose must not override pixels.

## Facade schedule and numerical checks

In the parameter card, use ONE coordinate convention for the entire building: origin, +X/+Y directions, floor elevations and front/rear mapping. For a whole six-view sheet, identify panels by row/column and visible landmarks; keep the original image intact. Do not treat six panels as six unrelated designs.

Card facade schedule: side/panel, level, opening count/x/z intervals/type, recess depth/confidence. Resolve conflicting panels before approval; unknowns stay ASSUMED. Generate/check from ONE schedule, not independent guesses. Estimate small details.

Before repeating, calculate expected mm bounds for one wall, opening and roof section. Use injected saie_wall.call with string-key mm params for a solid wall without openings. For rectangular facade openings, prefer injected saie_wall_with_openings.call with the same wall parameters plus openings:[{offset_mm,width_mm,height_mm,sill_mm},...]. It adapts SAIE's batch-opening pattern: one combined cutter and one subtract, avoiding a facade assembled from many visible wall-segment groups. If the SketchUp boolean fails, do not fake success; keep the last verified model and report/fallback to a verified continuous-face method. A glass face covering a continuous solid wall is not an opening. Roof slab and parapet are separate named children; no full-height cap over an intended recessed roof.

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

Generate the six canonical front/rear/left/right/roof/oblique quality-gate views with `sketchup_capture_canonical_view`; do not hand-label arbitrary camera screenshots as canonical evidence. Keep source-matched framing as separate `evidence_pairs` when the source perspective differs. If the primary source perspective is not represented by those canonical views, capture a current camera that matches it and include it as an evidence_pair. When interior/detail reference images are supplied, capture corresponding current interior/detail cameras and pair each important source with the current model view; full-evidence acceptance requires these source-matched checks rather than exterior-only QA. After all six CURRENT captures exist, call sketchup_submit_visual_review with their exact returned agent-view paths, evidence_pairs when applicable, and the bounded critique. The host rejects stale revisions and persists qa/visual_review.json plus qa/visual_qa.md. Use NEEDS_FIX: YES|NO, assessment, at most THREE high-impact mismatches and a KEEP list. Prioritize silhouette, storeys/bays, openings, depth, roof/parapet, material zones and intersections.

Only the Builder writes Ruby. For YES, first map reviewer KEEP items to exact named owned-group paths with sketchup_inspect_owned. Then use update_mode=edit and pass those exact paths as preserve_paths on the correction writer call; the host must prove their persistent IDs, object counts and mm bounds stayed unchanged. A correction that changes protected KEEP geometry is a regression, not progress. Recapture and review after every correction. At most two targeted corrections per turn; remaining blockers mean partial. NO still requires current views and deterministic verification.

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
