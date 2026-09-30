from __future__ import annotations


MAX_CONTEXT_CHARS = 8_000


_IMAGE_TO_SKETCHUP_CONTEXT = r"""
# Image → SketchUp reconstruction skill

This Skill reconstructs visible architecture from user-supplied reference image(s) into an editable SketchUp model. The image is the target appearance, not generic inspiration. Do not redesign unless the user explicitly asks.

## Success condition

The final model should be recognizable from the source viewpoint and editable as organized SketchUp groups/components. A few white boxes are an automatic failure when the source visibly contains developed roofs, balconies, openings, frames, louvers, rails, facade depth or material zoning.

## Core workflow

Use a professional reconstruction loop:

**inspect source → clarify high-impact unknowns → parameterize assumptions → user approval → author/revise persistent Ruby → execute → inspect screenshots/model → revise the same scripts/model**.

Do not start substantial geometry while scope, scale/inference policy or requested detail is still unclear.

## Method card A — clarify only what changes the model

Before planning, inspect the image and ask only the questions that materially affect reconstruction. Maximum four concise questions per clarification turn.

Priority questions:

1. **Use / viewing requirement** — only match the source view, or must the model support multi-angle viewing and later editing?
2. **Scope** — which visible parts must be modeled: main building, bridge, chimney, landscape/hardscape, simple vegetation, interior glimpses?
3. **Known scale** — is any reliable dimension known (overall width/depth, floor height, opening width, chimney height, etc.)? One anchor is enough.
4. **Inference / detail** — may unseen backsides/depths be reasonably inferred, and what visible detail level matters?

Do not ask questions already answered by the user. Do not ask about low-impact micro-details. If there is no known size, propose a coherent visual estimate later instead of blocking.

## Method card B — parameter card, not vague prose

After the user's clarification response, update `notes/reconstruction_card.md` with a compact parameter card. Clearly label values as KNOWN / ESTIMATED / ASSUMED.

Record:

- intended use / required views;
- included and excluded scope;
- known dimension anchor, if any;
- unseen-geometry policy;
- requested detail level;
- overall width / height / inferred depth;
- floor count and floor-line heights;
- bay count / main axes;
- major solids and negative spaces;
- facade depth stack, back-to-front;
- window/door module rhythm;
- balcony / railing / canopy / louver logic;
- roof/parapet/overhang profile;
- major material/color zones;
- repeated elements that should be components/instances;
- persistent script/component plan.

Estimated dimensions are a modeling baseline, not a claim of real-world measurement. Preserve source proportions first and make shared dimensions easy to revise later.

## Method card C — explicit approval gate

Before the first substantial build, summarize the parameter/construction plan for approval. The user must be able to see the important assumptions and change them before SketchUp is edited.

Planning is not completion. In clarify/plan mode do not edit SketchUp geometry.

## Method card D — Pass 1: recognizable primary form

After approval, use persistent workspace Ruby as the primary project-specific authoring mechanism. Use SAIE only as a helper for ordinary semantic elements when it is genuinely simpler.

Build:

- overall envelope and levels;
- bay/module grid;
- major recesses/projections;
- principal balconies/terraces;
- main roof/canopy;
- largest openings/negative spaces.

From the source viewpoint the building should already be recognizable before detail work.

## Method card E — Pass 2: repeated facade systems

Add the source-defining systems:

- glazing/door modules and mullions;
- balcony slabs and rails;
- fins/louvers/pergola members;
- soffits, piers, parapets and trims;
- ground-floor special treatment;
- major material/color zones.

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

## Cheap-model discipline

For cost-efficient models:

- reduce open-ended invention before execution by clarifying scope/scale/inference once;
- use an explicit parameter card instead of long free-form context;
- prefer shared parameters and persistent files;
- batch repeated work;
- keep the tool surface small;
- inspect screenshots after each major pass;
- revise instead of restarting;
- never switch to a stronger model merely to hide missing workflow/tool capability.

## Scope

Ignore taskbook/site/program fields in this workflow unless the user explicitly asks to combine them. Never modify an original user SKP/DWG. Work only in the verified disposable/generated model and agent workspace.
""".strip()


def load_image_to_sketchup_skill_context(*, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if max_chars < 512:
        raise ValueError("Image-to-SketchUp skill context limit must be at least 512 characters.")
    if len(_IMAGE_TO_SKETCHUP_CONTEXT) <= max_chars:
        return _IMAGE_TO_SKETCHUP_CONTEXT
    return _IMAGE_TO_SKETCHUP_CONTEXT[:max_chars].rsplit("\n", 1)[0].rstrip()
