# Quality Loop v2.8 — Pre-commit KEEP rollback

## Why this iteration exists

The Windows v1/v2 work proved that a targeted correction can still damage geometry that the visual reviewer marked as already correct. v2.6 added a post-write KEEP comparison, but that check happened **after** the SketchUp revision had already committed. It could detect damage, not prevent it.

This iteration adopts two proven open-source ideas more literally:

- **3DCodeBench** keeps a last-known-good state and reverts a failed visual-fix attempt instead of allowing the broken candidate to become the new baseline.
- **dcc-mcp-sketchup** treats mutation verification as part of the write contract, not as an optimistic follow-up.
- **SketchUp Agent Harness** keeps visual feedback advisory until it is converted into an explicit scoped action.

K Studio keeps its existing single writer, ProjectRuby/Kongxing transport, dedicated visual Critic, construction strategy and post-write receipts. No second geometry writer is added.

## GitHub implementation

For a post-review correction with `preserve_paths`:

1. The host reads each protected named owned path and fingerprints:
   - persistent ID
   - direct owned child count
   - parent-local millimeter bounds
2. Those fingerprints are injected as a **host-only** field. The model-visible tool schema cannot invent the expected state.
3. ProjectRuby embeds those fingerprints in the same SketchUp transaction that runs the correction.
4. After the candidate Ruby executes but **before commit**, SketchUp re-reads the protected paths.
5. If any protected ID/count/bounds changes, the helper raises inside the open SketchUp operation. `model_session.rb` aborts the operation, so the bad revision never becomes the committed model.
6. The failed candidate Ruby is archived under the project's reports directory and the prior persistent Ruby file is restored as the active baseline.
7. If the transaction commits, the existing post-commit Python readback still rechecks KEEP paths as defense in depth.

This is intentionally narrow: the guard protects named KEEP paths selected from the current visual review. It is not a general semantic proof that the whole building matches the source.

## Local Codex validation

Run on Windows + real SketchUp 2024 after pulling latest main.

1. Repository checks:
   - `git pull --ff-only`
   - `git status --short`
   - read `AGENTS.md`, `docs/CURRENT_TASK.md`, this file and `docs/QUALITY_LOOP_V2_7.md`
   - `python -m pytest tests/test_adopted_helpers.py tests/test_quality_lift.py tests/test_modeling_quality.py tests/test_construction_strategy.py tests/test_context_compaction.py`
   - `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`

2. Real **negative KEEP smoke**:
   - use a fresh disposable SketchUp project with at least two named top-level systems, for example `BALCONY` and `ROOF`;
   - obtain a current dedicated visual review that contains a KEEP item and map it to an exact `preserve_paths` path;
   - intentionally make one throwaway correction candidate that changes the protected path while using `update_mode=edit`;
   - expected result: the writer call fails before commit, the project revision does not advance, protected persistent ID/count/mm bounds remain identical, the previous model stays visible, the failed candidate Ruby is archived and the last-good persistent script is restored;
   - do not count a manually repaired committed revision as PASS. The point of this smoke is transaction abort.

3. Real **positive targeted correction**:
   - use a real critic issue on roof/wall/opening quality;
   - protect unrelated balcony/louver/already-correct opening groups;
   - change only the affected named group;
   - expected result: transaction commits, `precommit_keep_guard.armed=true`, post-write KEEP receipt passes, and protected IDs/count/bounds remain unchanged.

4. Continue the v2.7 six-view benchmark:
   - primary form → representative module → replication → variants → finish;
   - use `saie_wall_with_openings` when a rectangular facade wall suits it;
   - verify one repeated module before copying;
   - use host-certified front/rear/left/right/roof/oblique views and the dedicated read-only Critic;
   - total writer commits remain bounded and all corrections after review use targeted edit.

5. Record:
   - writer/critic token and tool counts;
   - number of full-root rebuilds;
   - whether representative-module-first reduced later repair;
   - whether the negative KEEP candidate truly aborted before commit;
   - final visual defects and whether the result is PASS or PARTIAL.

6. Update `docs/HANDOFF.md`, `docs/CURRENT_TASK.md` and sanitized test-results, commit and push `origin/main`.

## Acceptance

**Technical PASS** requires a real SU2024 negative smoke proving that a protected-path regression is aborted before commit and the last-good model/script remain active. Unit tests alone are not enough.

**Modeling-quality PASS** still requires source-matched current evidence. A safe rollback mechanism only prevents regressions; it does not make an inaccurate first model accurate.
