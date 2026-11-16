# Bounded stage-quality workflow

This is a scoped follow-on patch against the frozen 572-test Blender/role snapshot, commit `3f82aa1ca6f8114bbb2f0a190e31fba89c36f253`. Publication is limited to four code/test files and this sanitized note on the independent `trial/readiness-20261016` branch. No main, deployment, existing user SU session or paid provider invocation is changed.

## Behavior
- Host configuration `KSTUDIO_INITIAL_GEOMETRY_LIMIT` defaults to 3; `KSTUDIO_REPAIR_GEOMETRY_LIMIT` defaults to 2. Each accepts integers 1–12; zero/unlimited/invalid values fail closed. These are operator environment settings, not model-controlled arguments. Existing plan/approval and KEEP transaction guards remain.
- Approved Blender tool contexts now apply the same bounded per-turn stage budget. A committed revision consumes budget even if a later step throws. Read-only inspection remains possible after exhaustion.
- SketchUp reconstruction review detects the exact same nonempty `(view, problem)` set persisting through two successive revision changes and stops further writes in that turn. Re-reading one revision does not count as failed progress. Inherited current review seeds the comparison. No semantic score or paraphrase detection is claimed.
- Exhaustion/no-progress errors state actual stage and count, preserve candidate status, explicitly say quality is not accepted, and request remaining-issue inspection plus a scoped confirmed continuation plan. There is no automatic budget reset or automatic continuation.
- Blender rejects a mutation that leaves the entire named object specification unchanged, before invoking native execution or changing saved revision.
- Blender saved receipts now distinguish `candidate_status=saved_candidate` and `quality_status=unverified`. A diagnostic-only `geometry_qa` lists exact duplicate box volumes and full coincident polygon faces. It operates on bounded world-coordinate inputs supported by this backend. It never auto-repairs.

## Diagnostic limits
Shared boundary faces can represent intentional joins. Findings require review, not automatic deletion. Partial coplanar intersections, near gaps, intended connection topology, structural safety, arbitrary meshes/transforms, image fidelity and architectural quality are not certified. Without declared connection intent, the tool does not invent missing structure. Face scanning is capped at 50,000 and reports truncation.

The review convergence guard is per execution context. It does not claim cross-turn semantic convergence, and new user-approved turns still undergo existing current-review/KEEP controls. Blender does not yet have an independent visual critic; its guard detects identical state and bounded writes, not visual improvement. No real red-house geometry was edited.

## Regression coverage
The tests include configurable limits/invalid values, same-revision vs new-revision review repetition, conservative duplicate/coincident-face diagnostics, real Blender save/reopen with candidate preservation after budget exhaustion and identical-state rejection, and simulated SU stop before a higher configured limit. Existing full regression preserves transaction/rollback/KEEP tests. Native Blender and deterministic provider/executor tests are not independent reasoning/vision evidence.

## Publication verification

The four code/test files matched the author snapshot SHA-256 manifest. The patch applied without conflicts to the published Blender/role checkpoint. A fresh isolated publication-check rerun completed **577 passed, 15 skipped, 1 dependency deprecation warning in 38.53 seconds** on 2026-10-17. The author's preceding run was 577 passed / 15 skipped in 37.95 seconds; these are distinct runs. Skips are not passes. This does not establish GitHub CI success or autonomous visual-quality improvement. No private pictures, models, raw execution logs or interactive simulated-provider harness are published.
