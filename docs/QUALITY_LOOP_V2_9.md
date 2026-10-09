# Quality Loop v2.9 — Host repair memory

## Goal

Keep the reconstruction loop from repeating the same failed correction after long provider history is compacted.

This iteration adapts two public patterns without changing the single-writer architecture:

- **3DCodeBench** keeps critique history and last-known-good attempts so later iterations can distinguish a failed fix from a useful one.
- **SketchUp Agent Harness** keeps project-local runtime memory separate from canonical model truth and source evidence.

K Studio now records compact host-generated correction memory under `qa/repair_history.json`. The modeling agent may read it, but cannot write or rewrite it.

## Runtime behavior

After a trusted visual review says `NEEDS_FIX: YES`:

1. Builder performs one guarded targeted correction.
2. If a real writer revision commits, the host records:
   - the review issues that motivated the correction;
   - writer script/revision/path/update mode/source hash;
   - pre-commit KEEP guard state;
   - post-commit KEEP preservation status.
3. Status starts as `awaiting_review`.
4. The **next trusted visual review** finalizes that attempt:
   - `accepted`: the next review cleared blocking issues;
   - `still_needs_fix`: the next review still contains blocking issues.
5. Active-context compaction injects only recent trusted repair memory into the next provider request.
6. The runtime Skill tells Builder not to blindly repeat a method whose prior attempt is marked `still_needs_fix`.

This memory is advisory. It never overrides source pixels, reconstruction evidence, facade schedule, actual SketchUp geometry or current visual review.

## Local Codex validation

After pulling latest main:

1. Read `AGENTS.md`, `docs/CURRENT_TASK.md`, this file, `docs/QUALITY_LOOP_V2_8.md` and `docs/QUALITY_LOOP_V2_7.md`.
2. Run:
   - `python -m pytest tests/test_repair_memory.py tests/test_context_compaction.py tests/test_modeling_quality.py tests/test_quality_lift.py tests/test_codex_parity.py`
   - `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`
3. Perform the v2.8 real SU2024 negative KEEP smoke first. Do not proceed on a broken transaction guard.
4. On a fresh six-view reconstruction, let the dedicated Critic identify a real high-impact issue, apply one targeted correction, then recapture/re-review.
5. Verify `runtime/agent_workspace/qa/repair_history.json` is created by the host, not the model:
   - before the correction: no fabricated entry;
   - after committed correction: newest entry is `awaiting_review`;
   - after the next trusted review: it becomes `accepted` or `still_needs_fix`.
6. If the first correction remains `still_needs_fix`, use the next correction round to change the construction approach or parameterization rather than blindly replaying the same patch. Record the evidence.
7. Confirm the Agent can `workspace_read qa/repair_history.json` but `workspace_write` to that JSON is rejected.
8. Trigger/inspect active-context compaction using the normal long-session path or a controlled test session; the provider event/checkpoint must contain `HOST_REPAIR_MEMORY` while full audit history remains on disk.
9. Continue v2.7 staged-construction checks: primary form → representative module → replication → variants → finish; one real repeated module must be visually checked before copying.
10. Record tool count, writer count, Builder/Critic tokens, full-root rebuild count, correction methods and whether repair memory prevented a repeated failed method.
11. Update `docs/HANDOFF.md`, `docs/CURRENT_TASK.md` and sanitized test results, commit and push `origin/main`.

## Acceptance

Technical PASS requires host-owned repair memory to survive restart/context compaction, remain read-only to the model, and finalize only from the next trusted review.

Modeling-quality PASS still depends on current source-matched evidence. Repair memory is useful only if it measurably reduces repeated bad corrections or wasted writer/token budget; otherwise simplify or remove it.
