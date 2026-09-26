# CURRENT TASK — Thesis Modeling Showcase v0.1

## Status: Complete

The requested case-study page, GitHub-readable documentation, user-approved image exports, local checks, and handoff record are complete. No later milestone has been started.

## Objective

Create a detailed Chinese case-study page in AI Architecture Studio that explains how the user's graduation-design concept was developed with Codex GPT-6 Astra, SketchUp, and CAD, and shows selected results in a form suitable for web review.

## Scope

- Use the referenced Codex task and the local project QA record as the evidence source; distinguish verified results from open design checks.
- Add a responsive `/showcase` route and an entry point from the studio workspace.
- Add a GitHub-readable case-study document with the same story, metrics, image captions, and limitations.
- Include only user-requested, web-optimized images derived from the user's own SketchUp/CAD previews. Do not add SKP/DWG source files, taskbook uploads, reference packages, raw design graphs, or local machine paths. Link to the official Jinshan Neighbourhood Center page for attribution; do not copy its images.
- Preserve accurate status: scheme-level output is not a reviewed construction set; code compliance, structure, accessibility, fire egress, and conflicting area figures need professional review.
- Keep the existing Alpha workflow intact. Do not add a deployment platform, cloud service, or another product milestone.

## Verification and handoff

- Test the `/showcase` route and its curated assets, run `scripts/check.ps1`, and verify the page over the local app.
- Update `README.md` and `docs/HANDOFF.md` with evidence and public-asset boundaries.
- Commit and push the completed task to `origin/main`, confirm the remote SHA, then stop.

---

## Previous completed task — Product Alpha v0.2

## Objective

Turn the working Demo v0.1 into a **Chinese, real-input, conversational Alpha**.

The important user loop is now:

**任务书 + 场地 + 参考案例 + 设计想法 → 与 AI 讨论/调整 → 生成方案 → SketchUp 建模 → 继续用自然语言修改同一个模型**

Do not rebuild the connector or restart architecture research.

## Before starting

1. Run `git pull --ff-only`.
2. Read `AGENTS.md` and `docs/COLLABORATION.md`.
3. Run the existing checks before changing code.
4. Open the local app and confirm the Simplified-Chinese UI changes currently on `origin/main`.

## Priority 1 — verify the Chinese product UI

The user-facing website must be Simplified Chinese.

Check all visible states, buttons, toast/status messages, modal copy, preview labels, and artifact labels.

Internal schema/tool names such as `DesignIR`, `BuildPlan`, `DXF`, stable IDs, and MCP tool names may remain English.

Do not spend time redesigning the visual style unless Chinese text causes layout problems.

## Priority 2 — make reference URLs real inputs

The current app stores a reference URL but does not actually ingest its content.

Add a small `ReferenceIngestor` boundary that, for ordinary public HTTP/HTTPS pages:

- validates the URL
- blocks localhost/private-network targets
- uses a timeout and response-size limit
- extracts page title and useful visible text
- stores a concise reference excerpt/metadata in project context or a dedicated reference artifact
- passes that material to the Codex brain during design preparation

Do not build a crawler platform.

If a page is JS-heavy or cannot be read safely, keep the URL and tell the user to upload screenshots/images instead of pretending the page was analyzed.

Uploaded reference images should continue to be passed to the Codex brain.

## Priority 3 — add one real Chinese AI conversation box

Replace the demo feeling of fixed buttons with one simple conversation area.

The user should be able to type Chinese natural-language instructions.

### Before SketchUp build

A message should be able to refine the design intent and regenerate/update the structured design state before the user builds.

Examples:
- “公共街道再宽一点，两个主要体块之间更开放。”
- “参考案例的屋顶关系可以借鉴，但不要直接复制造型。”

### After SketchUp build

The same conversation area should send targeted edits to the existing live model through the current BrainAdapter + SketchUpAdapter path.

Do not rebuild the whole model to satisfy an edit.

Keep the two existing demo edit buttons only as optional examples/shortcuts, not as the main interaction.

## Priority 4 — expand safe model edits slightly

Current edit support is mostly floor/height/origin.

Add only the minimum safe extra operations needed for useful alpha conversations, preferably:

- width/depth change of an existing rectangular mass
- circulation/public-route width change

Use stable IDs and deterministic validation.

Do not add a large generic SketchUp tool surface in this milestone.

## Priority 5 — keep the working v0.1 pipeline intact

The following must continue to work:

- project persistence
- Codex as temporary brain
- existing Kongxing SketchUp MCP reuse
- editable SketchUp geometry
- model readback/state
- DXF generation
- viewport capture
- A3 presentation preview

AI photorealistic rendering is **not required in v0.2**. Keep the RenderAdapter boundary and current viewport fallback.

## Tests

Add/adjust tests for:

- reference URL safety and extraction
- conversation before build
- conversation after build
- new width/depth/route-width edit validation
- existing v0.1 regression coverage

Run `scripts/check.ps1`.

If SketchUp is available, run a real smoke test with at least:

1. one Chinese pre-build design refinement
2. build into a disposable model
3. one Chinese post-build natural-language edit against the same model

## Acceptance criteria

1. All normal user-facing website copy is Simplified Chinese.
2. Public reference URL content is actually ingested when safe/readable.
3. Unreadable URLs fail honestly and offer image upload as fallback.
4. A Chinese conversation box exists.
5. A pre-build Chinese instruction can update/regenerate the design state.
6. A post-build Chinese instruction modifies the existing SketchUp model without full regeneration.
7. At least one additional safe dimension edit beyond height/origin works.
8. Existing v0.1 DXF, viewport, presentation, project persistence, and MCP integration still pass.
9. `docs/HANDOFF.md` is updated with exact local evidence.
10. Completed work is committed **and pushed to `origin/main`**.

## Final step

Stop after Product Alpha v0.2 is implemented, tested, handed off, and pushed.

Do not add production model APIs, payments, auth, Rhino/Blender/Revit, or full photorealistic rendering yet.
