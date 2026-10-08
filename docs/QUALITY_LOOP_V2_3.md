# Quality Loop v2.3 — active-context compaction + validated source schedule

## Why this follows v2.2

The v1 Windows evidence showed a real six-view run reporting about 4.92M input tokens and 40 tool calls. v2.1 separated the visual Critic from Builder history, and v2.2 externalized facade/roof facts into a structured schedule. The remaining cost problem is that the Builder still sends almost the entire historical tool/chat transcript on later provider calls.

The useful pattern from 3DCodeBench is not to replay every failed attempt: keep the current known-good state and feed only the evidence needed for the next correction. SketchUp Agent Harness makes the same separation between durable project memory and transient execution history.

v2.3 applies that pattern without deleting audit history.

## GitHub changes

- `app/context_compaction.py` builds a bounded active checkpoint from:
  - `notes/reconstruction_card.md`
  - `notes/facade_schedule.json`
  - current ProjectRuby script IDs / revisions / root IDs / verification state
  - latest `qa/visual_review.json`
- compaction is disabled until the structured schedule contains real project signal, so early clarification is not discarded before the planner externalizes facts;
- on a large later turn, the provider request keeps:
  - system/Skill instructions
  - the compact active checkpoint
  - the current real user turn
  - every tool call/result and quality-gate message generated in that current turn;
- completed older Builder/tool history is omitted from the active request only. Full provider-session history remains on disk for audit/recovery;
- current source images are now preferred over duplicate historical image blocks, so compaction cannot accidentally drop all source pixels;
- `provider_started` events record whether compaction happened, dropped-message count and before/after active-context character estimates;
- `notes/facade_schedule.json` now has a host-side schema/type/provenance validator instead of being merely syntactically valid JSON.

## What this intentionally does not do

- It does not summarize geometry from prose or replace SketchUp readback.
- It does not delete provider history.
- It does not compact the current in-flight tool exchange.
- It does not turn the facade schedule into geometry source-of-truth.
- It does not claim supplier billing savings until a real provider run is measured.

## Windows Codex validation

1. Pull latest main and read this file plus the top of `docs/CURRENT_TASK.md`.
2. Run:
   - `python -m pytest tests/test_context_compaction.py tests/test_modeling_quality.py tests/test_codex_parity.py tests/test_reconstruction_agent_architecture.py tests/test_quality_lift.py`
   - `python -m pytest`
   - `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`
3. Verify planner output writes a schema-valid `notes/facade_schedule.json`. Invalid provenance/count types must fail at the workspace boundary rather than silently reaching Builder/Critic.
4. Run a fresh whole-six-view DeepSeek reconstruction on real SketchUp 2024 through the current v2.2 quality loop.
5. Inspect runtime `provider_started` events:
   - early clarification may remain uncompacted;
   - after the schedule contains real facts and history is large, at least one later Builder request should report `context_compacted=true`;
   - `context_messages_dropped > 0`;
   - `context_chars_after < context_chars_before`.
6. Confirm the current request still contains the real source image(s), current user instruction, current-turn tool exchanges and host quality-gate nudges. No source image may disappear because it existed in historical provider messages.
7. Confirm dedicated Critic remains a separate clean no-tool source+six-view call and still receives the validated facade schedule.
8. Continue v2.2 real geometry acceptance: smoke `saie_wall_with_openings`, run Builder → current six views → dedicated Critic → at most two targeted fixes, replay in a new blank model, download/native reopen/edit/save/reopen.
9. Record Builder input/output tokens separately from dedicated-Critic tokens and compare to the v1 ~4.92M input-token reference. Report measured runtime numbers only; do not invent billing.
10. If compaction causes loss of a confirmed requirement, disable/repair the compactor rather than adding more prompt prose. Durable facts belong in card/schedule/project state.
11. Update HANDOFF/CURRENT_TASK/test-results, commit and push main.

## Acceptance

PASS for this sub-milestone requires:
- automated tests green;
- no loss of user-confirmed facade facts;
- current source images still reach the Builder;
- at least one large later request compacts old completed history;
- current-turn function-call protocol remains intact;
- real SketchUp quality/replay gates from v2.2 still behave correctly.

Visual source fidelity remains a separate acceptance gate. Lower token use does not upgrade a visually wrong building to PASS.
