# CURRENT TASK — Build Demo v0.1

## Objective

Build a working **AI Architecture Studio Demo v0.1** now.

Do not stop after research.

The demo should prove this product path:

**Brief + Site + Reference + User Intent → Codex brain → DesignIR → BuildPlan → SketchUp editable model → basic DXF → output/presentation preview**

For this milestone, **Codex itself is the temporary AI brain**. A real model API will replace it later.

## Required reading

1. `AGENTS.md`
2. `docs/DEMO_V0_1_SPEC.md`
3. `docs/DEMO_ARCHITECTURE.md`
4. `docs/SCHEMAS_V0_1.md`
5. `docs/OPEN_SOURCE_COMPONENT_MAP.md`
6. `docs/CODEX_DEMO_RUNBOOK.md`

## Priority 1 — inspect and reuse the existing SketchUp connection

The user already has Codex controlling SketchUp through MCP.

Inspect the actual local Codex/MCP configuration and determine whether it already provides the demo's minimum operations.

If yes:
- use it,
- wrap only the minimum needed adapter around it,
- do not replace it.

If no:
- inspect SAIE first,
- then VBO SkAgent,
- then other compatible OSS,
- choose the fastest safe option.

Do not build a generic MCP bridge from scratch unless all reuse paths fail.

## Priority 2 — build the local product demo

Create a small local web app.

Preferred implementation when no better repo-compatible choice exists:
- Python/FastAPI backend
- React/Vite frontend

But speed and reliability are more important than framework preference.

The UI must include one project workspace with:

- Design
- Model
- Drawing
- Render
- Present

Support:
- brief text/file
- site file/image
- reference URL/image
- user intent
- project status
- artifact previews

Create a synthetic example under `examples/demo_project/`.

Never commit the user's private project assets.

## Priority 3 — implement shared project state

Implement the small schemas in `docs/SCHEMAS_V0_1.md`:

- ProjectContext
- DesignIR
- BuildPlan
- ModelState
- OutputManifest

Store real runtime projects under ignored `runtime/projects/`.

Do not create an oversized BIM ontology.

## Priority 4 — Codex brain mode

Implement a small BrainAdapter boundary.

For this demo:
- Codex is the real reasoning engine.
- If a safe non-interactive Codex invocation is available locally, integrate it behind the adapter.
- Otherwise implement Codex Job Mode and use the current Codex session to process the seeded demo job.

The seeded demo must produce a real `design_ir.json` and `build_plan.json`.

A mock brain may exist only for automated tests/UI fallback and must be clearly marked.

## Priority 5 — real SketchUp execution

Use a blank/disposable SketchUp model.

From the seeded DesignIR, create at minimum:
- site/base
- 3 editable building masses
- 1 circulation/public-space object

Every important object must have a stable ID/name.

Then perform **two sequential edits against the same model**:
1. change the height/floor count of one mass
2. move or resize another mass/circulation object

Do not regenerate the entire model to fake continuity.

After build and each edit:
- read back state
- capture viewport evidence where possible

## Priority 6 — basic drawing

Generate a real DXF from the same DesignIR/shared state.

Minimum:
- site boundary
- mass footprints
- circulation/public-space geometry

Reuse ArchFlow DXF logic if doing so is faster and license-compatible; otherwise use a small deterministic generator.

## Priority 7 — render/output preview

Implement a RenderAdapter.

Guaranteed demo fallback:
- SketchUp viewport capture

Optional:
- if a compatible image-generation provider is already configured locally, generate an AI render

No API key may be committed and lack of an image API must not block the demo.

## Priority 8 — presentation

Generate one simple A3 landscape presentation preview from:
- project title/concept
- drawing
- model screenshot
- render/viewport image

HTML/CSS is acceptable.
Export PDF/PNG if local tooling allows.

## Required developer UX

Provide Windows-friendly scripts, for example:

- `scripts/setup.ps1`
- `scripts/dev.ps1`
- `scripts/demo.ps1`
- `scripts/check.ps1`

Exact names may differ if a better structure is justified.

A new developer should have a short documented path to launch the demo.

## Tests

At minimum:
- schema validation
- project create/load
- job lifecycle
- DXF generation
- presentation generation
- adapter unit tests with fakes
- any connector tests that can run safely

If live SketchUp is available, also run a real smoke test.

## Acceptance criteria

Mark each as PASS / PARTIAL / FAIL in `docs/HANDOFF.md`.

1. Local web app launches.
2. Synthetic project can be created/loaded.
3. Inputs are stored into ProjectContext.
4. Codex produces a structured DesignIR and BuildPlan for the seeded demo.
5. SketchUp connection is reused/adopted rather than unnecessarily rebuilt.
6. Live SketchUp creates at least 3 editable named masses + 1 circulation object when the local environment permits.
7. Two sequential model edits operate on the existing model.
8. Model state/readback is persisted.
9. A real basic DXF is generated.
10. A render/viewport artifact is produced.
11. An A3 presentation preview is generated.
12. Private assets/secrets are not committed.
13. Open-source licenses/notices are respected.
14. `docs/HANDOFF.md` contains exact run instructions and honest evidence.

## Failure handling

If live SketchUp cannot be reached:
- continue building the rest of the demo,
- use an adapter fake only for UI/tests,
- mark live-model criteria PARTIAL/FAIL,
- document the exact blocker and shortest manual step needed.

Do not claim live integration succeeded when it did not.

## Final step

Commit the finished milestone and stop.

Do not start production cloud/API migration, auth, payments, Rhino, Blender, or full CAD.
