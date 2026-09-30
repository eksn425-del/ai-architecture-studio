# Image → SketchUp v1

## Product decision

The next product milestone is **not** full architecture design from taskbook + site + precedent. First prove a narrower, commercially useful capability:

> **Upload one architectural reference image → a cost-efficient multimodal model + strong Skill/Agent/MCP reconstructs it as an editable SketchUp model.**

Only after this is reliable should the product combine taskbook, site and precedent images to create a new design.

## Why this milestone exists

Recent local work proved that the execution foundation is no longer the main unknown:

- SketchUp 2024.0.484 is connected;
- patched SAIE can create/query/edit walls, real openings, slabs and roofs;
- persistent project Ruby can be authored, executed, revised and re-run on the same owned model;
- multi-view screenshots/readback are available.

But deterministic white-box fixtures are **not** product quality. The product must now prove source-driven reconstruction quality.

The user-provided PylonLab screenshots demonstrate a dedicated image-to-SketchUp Skill plus a connector producing developed facade geometry. Building-Xuezhang teaching material demonstrates another important product behavior: **do not start modeling immediately when the image leaves important uncertainties**. Ask concise high-impact questions, convert the answers into explicit modeling parameters/assumptions, let the user confirm them, then execute and continue editing the same model.

No proprietary competitor code is copied. These are observed product/workflow references only.

## Reuse sources and license boundary

- **SAIE** — MIT. Reuse semantic wall/opening/slab/roof/query/edit capability already integrated.
- **Supex** — MIT. Reuse persistent code → execute → inspect → revise patterns and portable introspection ideas.
- **Stultus** — Apache-2.0. Study/reuse portable patterns for Ruby execution, scene readback, screenshots, Undo-scoped operations and continued sessions.
- **ADAI SketchUp Skill + Managed MCP** — CPAL-1.0. Study workflow ideas, but do not copy covered source into this commercial repository without a separate compliance decision.
- **Pylon / Building-Xuezhang** — observed workflow/quality references only when implementation is not publicly reusable.

## Scope

### In scope

- one or more user-uploaded facade/exterior reference images;
- editable SketchUp geometry;
- clarification of reconstruction scope/scale/inference/detail;
- proportional reconstruction when exact dimensions are unknown;
- explicit estimated modeling dimensions;
- visible facade depth and defining details;
- repeated components/instances;
- simple material/color zoning;
- source-matched screenshot QA and correction;
- cost-efficient model first.

### Explicitly out of scope for v1

- taskbook compliance;
- site adaptation;
- generating a new design from a precedent;
- planning/program optimization;
- code/regulation checks;
- final rendering;
- CAD drawing production;
- Astra benchmark unless later authorized.

## Required workflow

### 1. Inspect and clarify

The model must actually receive the uploaded image as multimodal input.

Before substantial modeling, ask only questions whose answers materially change the model. Normally no more than four:

1. **Intended use / views** — only match the supplied view, or support multi-angle inspection and later editing?
2. **Scope** — which visible building/site elements are included or simplified?
3. **Known scale** — is any reliable dimension known? One anchor is enough.
4. **Inference/detail** — may unseen geometry be reasonably inferred, and what visible detail level matters?

Do not ask low-value micro-detail questions. Do not repeat questions already answered. If no exact dimension is known, continue with a coherent estimated baseline.

### 2. Parameterize before execution

Create/update:

`runtime/projects/<project>/runtime/agent_workspace/notes/reconstruction_card.md`

The card records:

- intended use / required views;
- included/excluded scope;
- known dimension anchor(s);
- unseen-geometry policy;
- visible detail target;
- source view/confidence;
- overall proportions;
- floor lines and bays;
- major solids/voids;
- facade depth stack;
- repeated window/door/rail/louver systems;
- roof/canopy logic;
- material zones;
- persistent script/component strategy.

Every critical value should be tagged conceptually as:

- **KNOWN** — user/source provided;
- **ESTIMATED** — visual proportional baseline;
- **ASSUMED** — conservative unseen-geometry/detail rule.

Estimated dimensions are not presented as real measurements.

### 3. Approval gate

Show the compact parameter/construction plan to the user before editing SketchUp.

The user can:

- approve and build;
- modify parameters;
- clarify a remaining assumption;
- cancel.

Planning is not completion and must not modify SketchUp geometry.

### 4. Pass 1 — primary recognizable form

After approval, use persistent workspace Ruby as the primary project-specific authoring mechanism. Use SAIE only when it genuinely simplifies ordinary semantic work.

Build:

- envelope;
- storey levels;
- main bay grid;
- major recesses/projections;
- principal balcony/terrace slabs;
- main roof/canopy;
- largest openings and negative spaces.

**Gate:** from a source-matched camera, the building must already be recognizably the same architecture. Generic boxes fail.

### 5. Pass 2 — facade system

Add source-defining systems:

- repeated glazing/door modules;
- frames/mullions;
- balcony rails;
- fins/louvers/pergola;
- columns/piers;
- soffits/parapets;
- ground-floor special zones;
- major material/color groups.

Build one representative repeated module correctly, inspect it, then instance/array it. Avoid hundreds of unrelated one-off geometry calls.

### 6. Pass 3 — evidence and revision

Capture at minimum:

- source-matched front/perspective;
- one oblique/isometric view.

The Agent must visually compare actual screenshots with the source and revise the **same model / same persistent scripts**. Tool success without visual correspondence is a failure.

## Tool policy

The reconstruction profile is coding-first and deliberately small.

Primary:

1. persistent `sketchup_run_workspace_ruby` for custom/repeated project geometry.

Helpers:

2. selected SAIE wall/opening/slab/roof/query/edit operations;
3. existing Kongxing identity/lifecycle/view/readback/transform/undo-style operations that actually exist locally.

Do not add another generic MCP. Do not expose broad ArchFlow/CAD tooling here. Do not implement new wall/opening/slab engines already covered by SAIE.

## Economy-model strategy

The economy model should be **guided**, not asked to solve a whole building in one unconstrained thought.

The workflow gives it:

1. the actual source image;
2. concise clarification answers;
3. explicit reconstruction parameter card;
4. clear pass order;
5. mature tool/code recipes;
6. screenshot/readback gates.

Use Sol Low as the parity baseline because it already works well in direct Codex when the harness is strong. Do not use Astra to hide workflow defects.

## Quality acceptance

Use the same real image for direct-Codex and website comparison.

PASS requires all of the following where present in the source:

- correct approximate floor count;
- correct major bay rhythm;
- recognizable silhouette/proportions;
- major balconies/recesses/projections;
- windows/doors as repeated editable systems rather than a flat texture;
- roof/canopy/pergola logic;
- meaningful facade depth layers;
- basic material/color zoning;
- editable groups/components with semantic names;
- parameter card with explicit estimates/assumptions;
- approval before geometry execution;
- source-matched screenshot comparison;
- at least one subsequent correction on the same model/scripts;
- no modification of original user models.

Immediate FAIL conditions:

- result is primarily a few white boxes;
- source image never reached the model as multimodal input;
- visible defining details are omitted while the Agent claims completion;
- no clarification/parameter baseline exists when the source is ambiguous;
- repeated elements are built as unrelated loose geometry when a shared component/module is obvious;
- no screenshot-based visual revision occurs;
- success is claimed only from tool/test return values;
- model is silently upgraded to Astra.

## Later roadmap

Only after Image → SketchUp v1 is repeatable:

`taskbook + site + precedent images + user intent`

→ extract precedent grammar
→ adapt to constraints
→ create a new architecture design
→ editable SU/CAD/render/presentation.

That later phase must reuse the reconstruction capabilities built here rather than start another modeling stack.
