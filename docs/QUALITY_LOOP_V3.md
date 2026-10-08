# Quality Loop v3 — independent critic + structured facade schedule

## Why

Quality Loop v2 closes two major gaps: one verified writer and a host-enforced current six-view review gate. It still lets the Builder author its own critique. The Windows v1 evidence already showed that Builder self-evaluation can be optimistic even when wall seams, roof/parapet or opening proportions are visibly wrong.

This iteration applies two more upstream patterns:

- **3DCodeBench**: visual critique is a separate fresh model call over source + current renders, not part of the writer conversation.
- **ArchFlow / SketchUp Agent Harness**: high-value source facts should live in compact structured project state with provenance, while screenshots stay advisory evidence.

## GitHub implementation

1. `notes/facade_schedule.json`
   - seeded in every reconstruction workspace;
   - writable through the same confined workspace tool, but JSON is parsed and must have an object root;
   - planner is instructed to record compact front/rear/left/right opening/features plus roof/parapet/division facts;
   - facts must remain distinguished as observed / user_confirmed / inferred.

2. Fresh independent visual critic for LiteLLM/DeepSeek
   - when Builder calls `sketchup_submit_visual_review`, the host first validates the six current-revision captures as before;
   - then the host makes a **fresh no-tools provider call** containing only source images, current six views and the compact facade schedule;
   - it uses the bounded NEEDS_FIX / <=3 issues / KEEP contract;
   - the independent result overwrites the provisional Builder self-review used by the quality gate;
   - reviewer provenance (kind/status/provider/model) is persisted.

3. Fail closed
   - malformed/unavailable independent critique becomes a persisted `reviewer.status=failed` review;
   - a failed independent review cannot unlock another geometry write;
   - current verified geometry is retained and the run remains PARTIAL.

4. Usage evidence
   - independent critic tokens are added to the turn's measured provider usage;
   - agent event logs record critic start/result/failure separately.

## Windows/Codex validation

Run only after pulling the latest main.

1. Run:
   - `python -m pytest tests/test_modeling_quality.py tests/test_codex_parity.py tests/test_reconstruction_agent_architecture.py tests/test_quality_lift.py`
   - `python -m pytest`
   - `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`
2. Fix code/test failures; do not weaken the new independent-review or JSON assertions.
3. Start K Studio + SketchUp 2024 + Kongxing with the normal saved DeepSeek route.
4. Run one fresh **whole-six-view** reconstruction from a blank disposable model.
5. In planning, verify `notes/facade_schedule.json` is actually updated from the source/user corrections. Do not hand-author the schedule after the fact.
6. Execute normally. Verify the order:
   `writer -> six current captures -> Builder review submission -> independent host critic -> (if NEEDS_FIX) one targeted writer correction -> new six captures -> independent critic`.
7. Inspect `qa/visual_review.json`:
   - `reviewer.kind == independent_host_critic`
   - `reviewer.status == ok`
   - current model revisions match all six evidence sidecars
   - <=3 issues
   - KEEP is present
   - Builder self-review may be recorded for comparison but must not control the writer gate.
8. Compare Builder vs independent critic. If the Builder says PASS and independent critic catches a visible wall/roof/opening defect, record that as a successful architectural separation.
9. Smoke-test `saie_wall_with_openings` in the same run or a dedicated blank model. If boolean subtract is unstable on SU2024, keep the current model and implement a continuous-face/hole fallback rather than returning to many visible sill/jamb/head groups.
10. Finish with fresh-blank replay, web SKP download, native reopen/edit/save/reopen, and full ID/bounds/readback as in v1.
11. Record provider usage separately enough to see the added critic cost. Compare total input tokens/tool calls/latency to the v1 six-view baseline. Do not infer supplier billing from runtime tokens.
12. Update `docs/HANDOFF.md`, `docs/CURRENT_TASK.md`, sanitized test evidence, commit and push `origin/main`.

## Acceptance

Technical PASS requires all tests, verified writes, six current captures, an `independent_host_critic` receipt, replay and native reopen/edit.

Visual PASS still requires the actual current views to satisfy source-defining massing, floor/bay/opening schedule, roof/parapet and major facade depth. The independent critic is stronger evidence than Builder self-review but is still advisory; obvious human-visible contradictions remain failures.

If the critic is still systematically optimistic, the next step is **not** more Builder prompt text. Use a different read-only critic model/tier or add deterministic facade-schedule checks before accepting NEEDS_FIX:NO.

Context/token compaction remains the next engineering item after this independent-review loop is proven in a real paid Windows run.
