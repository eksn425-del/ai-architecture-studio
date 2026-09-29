# Image → SketchUp v1

## Product decision

The next product milestone is **not** full architecture design from taskbook + site + precedent. First prove a narrower, commercially useful capability:

> **Upload one architectural reference image → a cost-efficient multimodal model + strong Skill/MCP reconstructs it as an editable SketchUp model.**

Only after this is reliable should the product combine taskbook, site and precedent images to create a new design.

## Why this milestone exists

Recent local work proved that the execution foundation is no longer the main unknown:

- SketchUp 2024.0.484 is connected;
- patched SAIE can create/query/edit walls, real openings, slabs and roofs;
- persistent project Ruby can be authored, executed, revised and re-run on the same owned model;
- multi-view screenshots/readback are available.

But deterministic white-box fixtures are **not** product quality. The product must now prove source-driven reconstruction quality.

The user-provided PylonLab video screenshots are the immediate quality reference: a single facade image is translated into a developed SketchUp facade with multiple storeys, repeated glazing modules, balconies, railings, layered frame depth, ground-floor gate/stone zone, roof pergola/louvers and differentiated materials. The screenshots show a dedicated `pylon-sketchup2model` Skill plus a SketchUp connector. No public repository for that private Skill was found, so no Pylon code is copied.

## Reuse sources and license boundary

Use public projects as architecture references for our implementation:

- **SAIE** — MIT. Reuse semantic wall/opening/slab/roof/query/edit capability already integrated.
- **Supex** — MIT. Reuse the persistent code → execute → inspect → revise pattern and exact-entity introspection ideas.
- **Stultus** — Apache-2.0. Study/reuse portable patterns for `execute_ruby`, scene readback, viewport screenshots, Undo-scoped operations, selection context and continued Codex sessions. Do not import its gateway/product assumptions unless needed.
- **ADAI SketchUp Skill + Managed MCP** — CPAL-1.0. Study its public workflow ideas (source-first reconstruction, task/method cards, guided/autonomous modes, visual evidence, experience packs), but **do not copy its covered source into this commercial repository without an explicit license/compliance decision**.
- **Pylon `pylon-sketchup2model`** — observed only from user-provided screenshots; no public source found. Treat it as a product-quality reference, not a code donor.

## Scope

### In scope

- one or more user-uploaded facade/exterior reference images;
- editable SketchUp geometry;
- proportional reconstruction when exact dimensions are unknown;
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

### 1. Source inspection

The model must actually receive the uploaded image as multimodal input. Before modeling it creates/updates:

`runtime/projects/<project>/runtime/agent_workspace/notes/reconstruction_card.md`

The card records:

- source view type and confidence;
- assumed scale anchor;
- overall proportions;
- floor lines;
- bay/grid structure;
- major solids and voids;
- facade depth layers;
- repeated window/door modules;
- balconies/rails/louvers/canopies;
- roof/parapet/overhang;
- material/color zones;
- unseen-depth assumptions.

This is the cheap-model equivalent of a method card. It reduces open-ended reasoning and gives later tool calls explicit shared parameters.

### 2. Pass 1 — primary recognizable form

Build:

- envelope;
- storey levels;
- main bay grid;
- major recesses/projections;
- principal balcony/terrace slabs;
- main roof/canopy;
- largest openings and negative spaces.

**Gate:** from a source-matched camera, the building must already be recognizably the same architecture. Generic boxes fail.

### 3. Pass 2 — facade system

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

### 4. Pass 3 — evidence and revision

Capture at minimum:

- source-matched front/perspective;
- one oblique/isometric view.

The Agent must visually compare the actual screenshots with the source and revise the **same model / same persistent scripts**. Tool success without visual correspondence is a failure.

## Tool policy

Use the smallest mature execution path for each task:

1. SAIE semantic tools for ordinary wall/opening/slab/roof/query/edit operations;
2. persistent `sketchup_run_workspace_ruby` for custom/repeated facade systems and project-specific geometry;
3. existing Kongxing tools for verified document identity/lifecycle and available view/query operations;
4. ArchFlow only where its adopted artifacts are genuinely useful.

Do not add another generic MCP. Do not implement new wall/opening/slab engines already covered by SAIE.

## Economy-model strategy

The economy model should be **guided**, not asked to solve a whole building in one unconstrained thought.

The workflow gives it:

1. the source image;
2. reconstruction card template;
3. explicit pass order;
4. mature tool recipes;
5. repeated-module strategy;
6. screenshot/readback gates.

For the first real benchmark, use the normal Economy route with a cost-efficient Sol-class model. Prefer low reasoning if it is stable; raise only if the local integration evidence shows the workflow itself is correct but the model cannot follow it. Do not use Astra to hide workflow defects.

## Quality acceptance

The first benchmark should use a medium-complexity exterior/facade image similar in difficulty to the user-provided PylonLab example.

PASS requires all of the following visible in the resulting SketchUp model where present in the source:

- correct approximate floor count;
- correct major bay rhythm;
- recognizable silhouette/proportions;
- major balconies/recesses/projections;
- windows/doors as repeated editable systems rather than a flat texture;
- roof/canopy/pergola logic;
- at least two meaningful depth layers on the facade;
- basic material/color zoning;
- editable groups/components with semantic names;
- at least one source-matched screenshot comparison and one subsequent correction;
- no modification of original user models.

Immediate FAIL conditions:

- result is primarily a few white boxes;
- source image never reached the model as multimodal input;
- facade details visible in the source are omitted while the Agent claims completion;
- repeated elements are built as unrelated loose geometry when a shared component/module is obvious;
- no screenshot-based visual revision occurs;
- success is claimed only from tool return values.

## Later roadmap

Only after Image → SketchUp v1 is repeatable:

`taskbook + site + precedent images + user intent`

→ extract precedent grammar
→ adapt to constraints
→ create a new architecture design
→ editable SU/CAD/render/presentation.

That later phase must reuse the reconstruction capabilities built here rather than start another modeling stack.
