from __future__ import annotations


MAX_CONTEXT_CHARS = 8_000


_IMAGE_TO_SKETCHUP_CONTEXT = r"""
# Image → SketchUp reconstruction skill

This Skill reconstructs visible architecture from user-supplied reference image(s) into an editable SketchUp model. The image is the target appearance, not generic inspiration. Do not redesign unless the user explicitly asks.

## Success condition

The final model should be recognizable from the source viewpoint and editable as organized SketchUp groups/components. A few white boxes are an automatic failure when the source visibly contains developed roofs, balconies, openings, frames, louvers, rails, facade depth or material zoning.

## Working method

Use a Direct-Codex-like coding loop:

**inspect source → write/update reconstruction card → propose geometry plan → approval → author/revise persistent Ruby → execute → inspect screenshot/model → revise the same scripts/model**.

For image reconstruction, persistent workspace Ruby is the primary authoring mechanism for repeated or custom geometry. Use SAIE only as a mature helper for ordinary semantic construction/query/edit where it is simpler. Kongxing remains the verified SketchUp bridge, lifecycle and viewport/readback boundary. Do not create dozens of unrelated one-off tool calls when one parameterized script/component system can express the visible pattern.

## Method card A — source decomposition

Before geometry, inspect every source image and update `notes/reconstruction_card.md` with:

- source view type and confidence;
- one coherent inferred scale anchor if no measurement exists;
- overall width / height / likely depth;
- floor count and floor-line heights;
- bay count / main axes;
- major solids and negative spaces;
- facade depth stack, back-to-front;
- window/door module rhythm;
- balcony / railing / canopy / louver logic;
- roof/parapet/overhang profile;
- major material/color zones;
- repeated elements that should be components/instances;
- conservative assumptions for unseen geometry.

Do not block on exact dimensions. Preserve proportions first and make shared dimensions easy to revise later.

## Method card B — geometry plan before execution

Before the first substantial build, summarize a compact construction plan for user approval. It should describe:

1. primary envelope and levels;
2. bay/module grid;
3. main voids/recesses/projections;
4. facade depth layers;
5. repeated component families;
6. roof/canopy/pergola strategy;
7. major material zones;
8. the persistent Ruby files/components you intend to use.

Planning is not completion. In plan mode do not edit SketchUp geometry.

## Method card C — Pass 1: recognizable primary form

After approval, build the primary form in the verified disposable model:

- overall envelope and levels;
- bay grid;
- major recesses/projections;
- principal balconies/terraces;
- main roof/canopy;
- largest openings/negative spaces.

From the source viewpoint it should already be recognizable before detail work.

## Method card D — Pass 2: repeated facade systems

Add the source-defining systems:

- glazing/door modules and mullions;
- balcony slabs and rails;
- fins/louvers/pergola members;
- soffits, piers, parapets and trims;
- ground-floor special treatment;
- major material/color zones.

Build one representative repeated module correctly, inspect it, then instance/array it from shared parameters. Prefer components/instances and clear semantic names over loose faces. Real visible openings/depth should be geometric, not faked only with color.

## Method card E — Pass 3: visual QA and correction

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

State concrete mismatches, revise the same persistent script(s)/model, execute again, and capture the corrected views. Do not report completion merely because tools succeeded.

## Cheap-model discipline

For cost-efficient models, reduce open-ended invention:

- follow the reconstruction card and method cards in order;
- prefer explicit shared parameters;
- use persistent files rather than huge transient snippets;
- batch repeated work;
- inspect screenshots after each major pass;
- revise instead of restarting;
- keep the tool surface small and use coding for project-specific geometry.

## Scope

Ignore taskbook/site/program fields in this workflow unless the user explicitly asks to combine them. Never modify an original user SKP/DWG. Work only in the verified disposable/generated model and agent workspace.
""".strip()


def load_image_to_sketchup_skill_context(*, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if max_chars < 512:
        raise ValueError("Image-to-SketchUp skill context limit must be at least 512 characters.")
    if len(_IMAGE_TO_SKETCHUP_CONTEXT) <= max_chars:
        return _IMAGE_TO_SKETCHUP_CONTEXT
    return _IMAGE_TO_SKETCHUP_CONTEXT[:max_chars].rsplit("\n", 1)[0].rstrip()
