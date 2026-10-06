from __future__ import annotations


MAX_CONTEXT_CHARS = 10_000


_IMAGE_TO_SKETCHUP_CONTEXT = r"""
# Image → SketchUp reconstruction skill

Reconstruct reference architecture as editable SketchUp geometry. Images are the target appearance; redesign only when asked.

## Success condition

Deliver recognizable source-matched geometry in editable groups/components. A few white boxes are an automatic failure when the reference has roofs, balconies, openings, frames, louvers, rails, facade depth or materials.

## Core workflow

Use a professional reconstruction loop:

**inspect source → clarify high-impact unknowns → parameterize assumptions → user approval → author/revise persistent Ruby → execute → inspect screenshots/model → revise the same scripts/model**.

Clarify scope/scale/inference before geometry.

## Method card A — clarify only what changes the model

Inspect first; ask at most four high-impact questions.

Cover use/views, scope (building/site/interior), one known scale anchor and unseen-geometry/detail permission. Without a known size, propose coherent estimates.

Do not repeat answered questions or ask micro-details.
Once the user accepts estimates, do not ask about color values, member counts or minor dimensions again. Put defaults in the card. Planning revisions are not a new clarification gate.

## Method card B — parameter card, not vague prose

After the user's clarification response, update `notes/reconstruction_card.md` with a compact parameter card. Clearly label values as KNOWN / ESTIMATED / ASSUMED.

Record scope/views, scale anchors, inference/detail policy, overall dimensions/levels, axes/bays, solids/voids, facade depth, opening rhythm, balconies/rails/louvers, roof profile, materials, repeated components and persistent script plan.

User 'about/estimate' values stay ESTIMATED after approval; exact anchors are KNOWN. Distinguish floor-to-floor/clear height. Bridge landing and served floor must agree before approval. Preserve proportions/shared parameters.

## Method card C — explicit approval gate

Before substantial geometry, summarize parameters/assumptions for user approval and revision.

Approval covers all passes. After confirm/start, execute all requested details and QA continuously; never ask for another continue between passes.

No geometry in clarify/plan mode.

## Evidence across views and unseen geometry

First classify the supplied evidence: one image, multiple views of ONE building, or text only. For text only, plan a proposed design from the user's description; do not claim to have inspected a photo or recovered an existing building. Do not demand an image if the user wants a text-described building. Use the same approval, persistent coding, editable model and QA loop.

Record views, floors, openings, materials and landmarks in the card. Reconcile dimensions; flag contradictions for approval. Views constrain ONE building; never promise zero errors.

Count openings by facade/floor/panel. OBSERVED source counts differ from approved defaults: obeying a default does not prove fidelity. Check narrow windows, entries, wall returns and roof inner edges. Persist corrected observations in the parameter card and QA notes; old prose must not override pixels.

Record each image's exact filename, landmarks, side, floor lines and openings. Labels are hints. Do not swap the street entrance and pool facade. Pair QA views by landmarks; correct changed interpretations in card and geometry before acceptance.

With approved inference, complete rear/sides/roof as ASSUMED. Continue levels, wall thickness, roof/drainage and facade vocabulary; infer rear openings, circulation and service spaces. Avoid blank backs or blindly mirrored fronts. Stairs must reach requested floors; doors need usable landings and balcony access. Interiors without evidence are schematic assumptions.

## Facade schedule and numerical checks

In the parameter card, use ONE coordinate convention for the entire building: origin, +X/+Y directions, floor elevations and front/rear mapping. For a whole six-view sheet, identify panels by row/column and visible landmarks; keep the original image intact. Do not treat six panels as six unrelated designs.

Create a compact facade schedule: side/panel, level, opening count, opening x/z intervals, glazing/door type, recess depth and confidence. Unknowns remain ASSUMED; conflicting panels need explicit resolution before approval. Use this same schedule to generate and check geometry; do not re-infer the facade independently in each script. Small details stay estimates, not more user questions.

Before repeating, calculate expected mm bounds for one wall, opening and roof section. Use injected saie_wall.call with string-key mm params for solid wall segments when suitable. This adopted SAIE subset does NOT cut openings: build sill/jamb/head segments around each void or use a verified opening method. A glass face covering a continuous solid wall is not an opening. Roof slab and parapet are separate named children; no full-height cap over a intended recessed roof.

Read actual transaction owned_after XYZ mm bounds and child persistent IDs. Compare measured position/size to expected intervals, especially opposite walls. Inspect each required view's opening count and roof junction; write actual vs expected and the defect in notes/visual_qa.md. A passing size check cannot prove topology or image fidelity. Check glass, frames, soffits, relief, material scale and face orientation. Inspect front/rear/both sides/roof/oblique for multi-angle delivery. Unchecked views mean partial delivery.

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

## Method card F — Pass 3: visual QA and correction

Capture at least:

- a source-matched view;
- one oblique/isometric view.

Inspect the actual screenshots and compare silhouette/proportions, floor lines, bay count/spacing, solids/voids, facade depth, projections, repeated modules, materials and defining details.

State mismatches, revise persistent scripts/model and recapture; tool success is not completion.

Report panel → observed feature/count → actual model → mismatch/action. Unreviewed details stay pending; code intentions are not visual checks. Integrate successful fixes into the persistent baseline/replay entrypoint so rerunning cannot resurrect defects. Incremental moves are not idempotent builders.

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


def load_image_to_sketchup_skill_context(*, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if max_chars < 512:
        raise ValueError("Image-to-SketchUp skill context limit must be at least 512 characters.")
    if len(_IMAGE_TO_SKETCHUP_CONTEXT) <= max_chars:
        return _IMAGE_TO_SKETCHUP_CONTEXT
    return _IMAGE_TO_SKETCHUP_CONTEXT[:max_chars].rsplit("\n", 1)[0].rstrip()
