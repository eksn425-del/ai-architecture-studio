# CURRENT TASK — Thesis Parity v1: Reference-Rich Multimodal Benchmark

## Status: Ready for Codex/local execution

## Objective

Reproduce the information conditions that produced the user's successful direct graduation-design Codex workflow, then compare the **website** under two controlled model settings:

- Premium parity candidate: current Astra-class local Codex route at **low** reasoning.
- Economy stress candidate: `gpt-6-luna` at **max** reasoning for this benchmark only.

Both variants must receive the same real taskbook/site/Jinshan precedent image package, the same Architecture Skill, the same guarded Ruby, the same Kongxing SketchUp tools, and the same user-message sequence.

Read `docs/THESIS_PARITY_V1.md` first.

## Important correction from previous benchmarks

The previous model-router benchmark was text-heavy and did **not** reproduce the multimodal precedent evidence that the successful thesis workflow used. Therefore it is not sufficient evidence about reference-rich modeling quality.

Do not judge this milestone until real precedent images are confirmed to reach the model.

## Before starting

1. `git pull --ff-only`
2. Confirm the worktree is clean.
3. Read:
   - `AGENTS.md`
   - `docs/THESIS_PARITY_V1.md`
   - `docs/HANDOFF.md`
   - `docs/DECISIONS.md`
   - `docs/THESIS_MODELING_CASE_STUDY.md`
   - `docs/OPEN_SOURCE_COMPONENT_MAP.md`
4. Run the current automated tests once.
5. Validate the new multimodal code path locally before spending quota on the full benchmark.

## Priority 1 — validate the multimodal migration already pushed

The repository now includes project-reference image discovery and provider-side image attachment.

Validate on Windows/local Codex:

- `inputs/reference/` images are discovered before site/brief images,
- generated `outputs/` images are never fed back as precedent,
- unsupported/oversized images are skipped,
- Codex App Server accepts the emitted `local_image` turn inputs,
- uploaded reference images are actually visible to both tested Codex models,
- no private path is exposed in user-facing transcript/output.

Add/fix focused tests as needed. Do not begin the expensive real benchmark if image delivery is not proven.

## Priority 2 — reconstruct the successful historical workflow locally

The user will make the successful graduation-design Codex conversation/history available locally.

Use it to reconstruct:

- which taskbook/site/reference materials were present,
- the actual order of user requests,
- which Jinshan images/drawings mattered,
- which SketchUp/CAD actions the successful direct workflow used,
- which iterations materially improved the result.

Do not publish private transcript content or hidden reasoning. Record only a sanitized execution trace / benchmark manifest. Keep private transcripts and source assets under ignored local runtime.

## Priority 3 — build one identical private benchmark package

Use local/private files only; do not commit them.

Required:

- current graduation-design taskbook,
- actual site CAD/DXF/coordinate material used in the successful workflow,
- ECADI Jinshan Neighbourhood Center URL:
  `https://www.ecadi.com/index.php?m=index&a=news&id=175`
- selected Jinshan effect images and technical drawings,
- the user's own design intent,
- sanitized/reconstructed prompt sequence from the successful historical run.

Stage reference images under the benchmark project's `inputs/reference/` so the website sends them as first-class multimodal inputs.

The historical successful final model screenshots/CAD are **evaluation references only**, not model input, unless the historical transcript proves they were also original inputs.

## Priority 4 — use real taskbook constraints

At minimum, track/check the taskbook values documented in `THESIS_PARITY_V1.md`:

- site area 11,490.510 m² in taskbook,
- FAR < 1.82 / table 1.82,
- height <= 24 m,
- total area 28,400 m²,
- above-grade counted area about 20,900 m²,
- footprint < 5,520 m²,
- density < 48.05%,
- green ratio 20%,
- culture 8,000 m²,
- library 4,000 m²,
- sports 8,000 m²,
- reception 900 m²,
- underground parking / partial civil defense 7,500 m².

If the local site CAD conflicts with the taskbook, record the conflict and model behavior. Do not silently choose a number.

## Priority 5 — controlled model comparison

### Variant A — Premium parity

Use the actual current local Codex model ID that corresponds to the successful Astra/Extra-class route and record it exactly.

Expected current repo route: `gpt-6-astra`.

Reasoning effort: **low**.

### Variant B — Luna stress

Model: `gpt-6-luna`.

Reasoning effort: **max** for this benchmark only.

Use the newly supported environment override rather than changing the product's normal defaults permanently.

### Common environment

Both variants must use:

- identical taskbook/site/reference files,
- identical image filenames/order,
- identical user-message sequence,
- identical Architecture Skill revision,
- identical Kongxing MCP tools,
- identical guarded project Ruby path,
- separate blank disposable SketchUp copies,
- matched review cameras/views.

Do not let one route receive better references, more tools, a different prompt sequence, or hidden manual fixes.

## Priority 6 — compare to the historical direct-Codex result

The real quality bar is no longer “better than three boxes”.

Compare the website outputs against the successful historical thesis result on:

1. taskbook compliance,
2. Jinshan precedent understanding/adaptation,
3. site/entry/road relationships,
4. clustered massing and silhouette,
5. plan/section/level logic,
6. openings/envelope/platform/bridge/stair detail,
7. semantic/editable model structure,
8. screenshot self-check and correction,
9. targeted same-model revisions,
10. CAD/drawing continuity where available.

Record strengths and failures honestly; do not invent a numeric architecture score unless the rubric is explicitly defined in the benchmark notes.

## Priority 7 — CAD secondary parity check

The historical direct workflow also produced strong CAD output.

After the model comparison, test whether the current website can derive useful CAD/drawing output from the rich model without routing back through the legacy rectangle-only DesignIR.

If current CAD export cannot represent the agentic model, record that as a separate capability gap. Do not downgrade the 3D model to fit the old schema.

## Tests / local verification

At minimum:

- run `scripts/check.ps1`,
- test `app/reference_assets.py`,
- prove Codex App Server accepts `local_image`,
- verify the same image set reaches Astra Low and Luna Max,
- run one cheap smoke turn before the full modeling run,
- run the real SketchUp benchmark,
- inspect matched screenshots manually,
- preserve benchmark metadata under ignored runtime and safe summary/evidence in `docs/HANDOFF.md`.

## Acceptance criteria

1. Real uploaded reference images reach the local Codex model — PASS/FAIL.
2. Generated output screenshots are not reused as precedent input — PASS/FAIL.
3. Historical successful prompt/input sequence is reconstructed sufficiently for a fair product test — PASS/PARTIAL/FAIL.
4. Astra-class Low website run completes with the full reference-rich package — PASS/FAIL.
5. Luna Max website run completes with the exact same package — PASS/FAIL.
6. Matched screenshots compare both against the historical direct-Codex result — PASS/FAIL.
7. Premium quality is judged against the thesis result, not the old coarse benchmark — PASS/FAIL.
8. Luna result is assessed for commercial usability, not merely tool-call completion — PASS/FAIL.
9. Same-model natural-language revision is tested for both variants — PASS/FAIL.
10. Taskbook/site conflicts are disclosed rather than silently reconciled — PASS/FAIL.
11. Private taskbook/site/reference packages/transcripts/source SKP/DWG stay out of Git — PASS/FAIL.
12. Tests pass and completed work is committed/pushed to `origin/main` — PASS/FAIL.

## What NOT to do

- Do not run another synthetic text-only benchmark and call it thesis parity.
- Do not feed the successful final thesis model screenshots into the model unless they were historical original inputs.
- Do not change both model and reference package at the same time.
- Do not improve Luna by silently invoking Astra.
- Do not replace the current Architecture Skill/Ruby/MCP stack during the comparison.
- Do not force complex agentic geometry back into legacy DesignIR rectangles.
- Do not publish private thesis assets, transcripts, credentials, or machine paths.

## Final step

Update `docs/HANDOFF.md` with the real multimodal delivery evidence, exact model IDs/efforts, reference-image count/hash/filenames (safe names only), matched screenshots, taskbook compliance findings, CAD findings, and remaining gaps. Commit, push to `origin/main`, verify remote SHA, then stop for ChatGPT review.
