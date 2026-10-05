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

Priority questions:

1. **Use / viewing requirement** — only match the source view, or must the model support multi-angle viewing and later editing?
2. **Scope** — which visible parts must be modeled: main building, bridge, chimney, landscape/hardscape, simple vegetation, interior glimpses?
3. **Known scale** — is any reliable dimension known (overall width/depth, floor height, opening width, chimney height, etc.)? One anchor is enough.
4. **Inference / detail** — may unseen backsides/depths be reasonably inferred, and what visible detail level matters?

Do not repeat answered questions or ask micro-details. Without a known size, propose coherent estimates.
Once the user accepts estimates, do not ask about color values, member counts or minor dimensions again. Put defaults in the card. Planning revisions are not a new clarification gate.

## Method card B — parameter card, not vague prose

After the user's clarification response, update `notes/reconstruction_card.md` with a compact parameter card. Clearly label values as KNOWN / ESTIMATED / ASSUMED.

Record scope/views, scale anchors, inference/detail policy, overall dimensions/levels, axes/bays, solids/voids, facade depth, opening rhythm, balconies/rails/louvers, roof profile, materials, repeated components and persistent script plan.

User 'about/estimate' values stay ESTIMATED after approval; exact anchors are KNOWN. Distinguish floor-to-floor/clear height. Bridge landing and served floor must agree before approval. Preserve proportions/shared parameters.

## Method card C — explicit approval gate

Before the first substantial build, summarize the parameter/construction plan for approval. The user must be able to see the important assumptions and change them before SketchUp is edited.

Approval covers all passes. After confirm/start, execute all requested details and QA continuously; never ask for another continue between passes.

No geometry in clarify/plan mode.

## Evidence across views and unseen geometry

First classify the supplied evidence: one image, multiple views of ONE building, or text only. For text only, plan a proposed design from the user's description; do not claim to have inspected a photo or recovered an existing building. Do not demand an image if the user wants a text-described building. Use the same approval, persistent coding, editable model and QA loop.

Record views, floors, openings, materials and landmarks in the card. Reconcile dimensions; flag contradictions for approval. Views constrain ONE building; never promise zero errors.

For every supplied image, record its exact filename, visible landmarks (street/gate/pool/stair), viewing side, floor lines and major openings before deciding front/rear. Filename labels are hints, not proof. Do not silently swap the street entrance and pool facade. Match each QA screenshot to a named source image using the same landmarks. If a view interpretation changes, correct the card and affected geometry before calling the result acceptable.

With approved inference, complete rear/sides/roof as ASSUMED. Continue levels, wall thickness, roof/drainage and facade vocabulary; infer rear openings, circulation and service spaces. Avoid blank backs or blindly mirrored fronts. Stairs must reach requested floors; doors need usable landings and balcony access. Interiors without evidence are schematic assumptions.

## Materials and full-building QA

Check glass, frames, slab/soffit depth, stone joints, timber and metal profiles. Match color/scale; use local licensed textures or simplified materials plus relief geometry. Flat color is not photographic texture. Inspect face orientation.

Inspect front/rear/both sides/roof/oblique for multi-angle delivery. Match each supplied view; compare silhouette, floors, openings, projections and materials. Check inferred sides for alignment, access and roof continuity. Record defects/corrections/uncertainty in notes/visual_qa.md. Correct largest mismatches first; batch repeated detail, avoid per-member calls/full rebuilds. Unchecked required views mean partial delivery, not completion or construction verification.

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

Inspect the actual screenshots and compare:

1. silhouette / overall proportions;
2. floor-line positions;
3. bay count and spacing;
4. solid/void pattern;
5. facade depth order;
6. balcony/canopy/roof projection;
7. repeated module consistency;
8. material/color zoning;
9. missing defining details.

State concrete mismatches, revise the same persistent script(s)/model, execute again, and capture corrected views. Do not report completion merely because tools succeeded.

Frame the building at a comparable size and angle to the source. If large site extents make it tiny, target the building rather than zooming to the entire site. Inspect roof/wall junctions and openings in a close oblique view; a distant silhouette cannot verify detail. Persist the correction in the source so rerunning does not restore the defect.
Read screenshots as evidence, not as confirmation of your code's intention. A solid roof cap spanning the interior still hides the parapet even if a lower roof slab was added. Remaining coplanar seams are defects even if edges were intended to be hidden. Report them honestly. Use only actual tool-returned screenshot paths and host-verified saved SKP artifacts; never invent QA filenames or claim that the active blank model path was saved when the host saved a separate downloadable checkpoint.

## Replacement versus incremental edits

The workspace Ruby tool defaults to update_mode=replace: it clears the owned root and executes the COMPLETE reconstruction source. Keep that full source as a persistent baseline, never overwrite it with inspection-only code or a partial patch. For a small correction, write a separate patch file and call the same existing script_id with update_mode=edit; this retains its owned root. Use model readback/camera tools to inspect. Do not create a new script_id for edits to an existing building.
Existing-root replace requires allow_full_rebuild=true; local fixes use edit. For an affected direct-child group/component, call injected `remove_owned_group.call(exact_name)` then rebuild that child only. It rejects absent, duplicate or locked targets. Keep unrelated object IDs unchanged and verify them by readback. Do not label a full-root replacement a local edit. General erase/clear and outside-root access remain blocked.

## Finite modeling turns

Keep each execution turn bounded and checkpointable. After one substantive geometry pass and at most two targeted correction passes, return a concise progress report with actual screenshots and remaining work. For large multi-view/interior requests, continue the same script/root in subsequent turns rather than running an unbounded QA loop until the host timeout. A checkpoint is partial progress, never proof that all requested detail is complete. Honor a user request for readback/checkpoint only without rebuilding geometry.

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
