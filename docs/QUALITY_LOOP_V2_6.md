# Quality Loop v2.6 — Do-no-harm KEEP preservation

## Why this iteration

The current v2.1-v2.5 loop now has a dedicated read-only Critic, structured source evidence, compact active context, single verified writer, current-revision review receipts and host-certified six canonical cameras.

One important upstream behavior was still missing:

- 3DCodeBench keeps the last known-good result and does not silently accept a fix that damages it.
- SketchUp Agent Harness requires visual feedback to be converted into structured actions before geometry mutation.

K Studio previously carried the reviewer's KEEP list as prose only. A Builder could be told to fix the roof while accidentally moving/rebuilding balcony, louvers or already-correct facade groups, and the host would notice only on the next visual review.

v2.6 turns KEEP into an explicit write boundary.

## GitHub implementation

- sketchup_run_workspace_ruby now accepts preserve_paths: exact named owned-group paths under the writer's existing script_id.
- After a visual review, any further writer call in the same turn is host-forced to update_mode=edit; replace / allow_full_rebuild is rejected.
- If the current review contains KEEP items, the correction must map at least one KEEP item to exact preserve_paths using sketchup_inspect_owned first.
- Before the write, the host fingerprints every protected path: persistent ID, owned object count and XYZ millimeter bounds.
- After the committed write, the host re-reads the same paths and creates an expected-vs-actual preservation receipt.
- Any protected ID/count/bounds change is surfaced as a regression. The revision remains a real committed revision and must be repaired/reviewed; the host must not call it a successful targeted correction.
- Successful receipts are persisted under runtime/agent_workspace/qa/keep-preservation-write-N.json and returned to the model.

This deliberately does not implement automatic SketchUp undo yet. Automatic rollback would have to reconcile ProjectRuby source/revision state, active document GUID/path and checkpoints. v2.6 first makes regression detection deterministic and testable.

## Windows Codex validation

1. Pull latest main and read AGENTS.md, docs/CURRENT_TASK.md, this file, docs/QUALITY_LOOP_V2_5.md and docs/EXECUTION_GUARDRAILS.md.
2. Run python -m pytest tests/test_modeling_quality.py tests/test_reconstruction_agent_architecture.py, then python -m pytest, then powershell -ExecutionPolicy Bypass -File scripts/check.ps1.
3. In a disposable SketchUp 2024 reconstruction, complete primary build -> host-certified six-view review.
4. When the dedicated Critic returns NEEDS_FIX: YES with KEEP items, use sketchup_inspect_owned to map already-correct semantic groups to exact owned paths; run the correction with the same script_id, update_mode=edit, and those exact preserve_paths; confirm preservation_verification.verified == true and the persisted QA receipt shows identical protected IDs/counts/mm bounds.
5. Negative smoke on a throwaway test model: include one group in preserve_paths and deliberately modify/rebuild it in the same correction. The host must report a KEEP regression and must not describe the correction as clean/successful. Then recover/repair using the normal checkpoint path.
6. Re-run current six canonical captures and dedicated Critic. Check that the targeted defect improves while protected groups stay geometrically stable.
7. Continue current v2.5 acceptance: source-matched evidence pairs where needed, blank replay, web download/native reopen/edit/save/readback.
8. Record evidence in a sanitized docs/test-results/windows/... folder, update HANDOFF.md / CURRENT_TASK.md, commit and push origin/main.

## Acceptance

PASS for this sub-gate requires a real SketchUp correction where the post-review write used edit, nonempty KEEP was mapped to exact preserve_paths, the host preservation receipt passed, unrelated protected persistent IDs/counts/bounds did not change, and fresh post-correction review evidence exists.

This is a do-no-harm engineering gate, not visual fidelity by itself.
