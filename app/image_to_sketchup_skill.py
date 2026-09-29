from __future__ import annotations


MAX_CONTEXT_CHARS = 9_500


_IMAGE_TO_SKETCHUP_CONTEXT = r"""
# Image → SketchUp reconstruction workflow

This workflow is for reconstructing the visible architecture in one or more user-provided reference images into an editable SketchUp model. The source image is the visual target, not merely a precedent. Do not reinterpret it into a new design unless the user explicitly asks for redesign.

## Goal

Produce a recognizable, editable model whose silhouette, floor/bay rhythm, depth layers, openings, repeated façade modules, roof/canopy and major material zones clearly correspond to the source image. A box collection is not an acceptable completion when the image visibly contains developed façade or roof geometry.

## Reconstruction card first

Before substantial geometry, inspect every supplied image and create or update `notes/reconstruction_card.md` in the persistent agent workspace. Keep it compact and operational. Record:

- source view type: front/elevation-like, perspective, oblique, aerial, interior, mixed;
- confidence and ambiguity;
- one consistent inferred scale when no measured dimension is supplied;
- overall width/height/depth estimate;
- floor lines and likely floor count;
- primary vertical axes / structural or façade bays;
- major solids and negative spaces;
- façade depth stack from back to front;
- opening/window/door module sizes and repetition pattern;
- balcony/canopy/railing/louver/parapet logic;
- roof profile and overhangs;
- major material/color zones;
- components that should become reusable definitions/instances;
- unseen geometry that must remain a conservative assumption.

Do not block on missing exact dimensions. If the user gave no scale, infer a coherent proportional model, state the assumption, and keep all repeated dimensions driven by shared parameters so they can be corrected later.

## Construction strategy

Use the mature semantic tool surface for ordinary construction when it helps: SAIE for walls/openings/slabs/ordinary roofs/query, existing Kongxing tools for verified document/model operations, and persistent project Ruby for repeated façade systems, custom profiles, arrays, non-trivial canopies, railings, louvers, shaped roofs, or geometry that would be awkward as dozens of one-off tool calls.

For repeated systems, build one representative module, inspect it, then instance/array it. Prefer SketchUp groups/components with clear semantic names over raw loose faces. Real voids must be real openings when visible in the source; do not fake a door/window only with color if depth is visually important.

## Three-pass build

### Pass 1 — recognizable primary form

Build the overall envelope, floor levels, bay grid, major recesses/projections, principal balconies/terraces, main roof/canopy and the largest openings/negative spaces. The result should already be recognizable from the same viewpoint as the source.

### Pass 2 — façade system and depth

Add the repeated window/door modules, frames, balcony slabs, rails, fins/louvers, soffits, columns/piers, parapets and major material zones. Use shared parameters and component instances wherever repetition exists. Match depth relationships, not just the 2D outline.

### Pass 3 — visual QA and correction

Capture at least a source-matched view plus one oblique/isometric view. Inspect the actual images. Compare:

1. global silhouette and proportions;
2. floor-line positions;
3. bay count and spacing;
4. major solid/void pattern;
5. balcony/canopy/roof projection and depth;
6. repeated module consistency;
7. material/color zoning;
8. obvious missing defining details.

Write concise findings under `qa/` only when needed, revise the same model/scripts, and capture again. Do not report completion merely because tools returned success.

## Cheap-model guidance

When running on a cost-efficient model, reduce open-ended invention. Follow the reconstruction card in order, use explicit shared parameters, batch repeated work, and prefer proven construction recipes. Make one representative element correctly before repetition. Use screenshots/readback as a quality gate after each major pass instead of asking the model to remember the source abstractly across many tool calls.

## Scope discipline

For this workflow, ignore taskbook/site/design-program fields unless the user explicitly asks to combine them. The immediate problem is visual reconstruction from the supplied image(s). Preserve the source's visible architectural language rather than deliberately making it different.

Never modify an original user SKP/DWG. Work only in the verified disposable/generated model and persistent agent workspace supplied by the host.
""".strip()


def load_image_to_sketchup_skill_context(*, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if max_chars < 512:
        raise ValueError("Image-to-SketchUp skill context limit must be at least 512 characters.")
    if len(_IMAGE_TO_SKETCHUP_CONTEXT) <= max_chars:
        return _IMAGE_TO_SKETCHUP_CONTEXT
    return _IMAGE_TO_SKETCHUP_CONTEXT[:max_chars].rsplit("\n", 1)[0].rstrip()
