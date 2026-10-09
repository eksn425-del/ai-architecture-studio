# Quality Loop v2.7 — construction-method routing

This task validates the new construction strategy inspired by the public ADAI 0.5.39 architecture while keeping K Studio's existing single-writer and quality gates.

## Local Codex execution

1. Pull latest main and read:
   - AGENTS.md
   - docs/CURRENT_TASK.md
   - docs/ADAI_METHOD_REUSE_2026-10-09.md
   - docs/QUALITY_LOOP_V2_6.md
   - docs/EXECUTION_GUARDRAILS.md

2. Run targeted tests and then the full suite:
   - python -m pytest tests/test_construction_strategy.py tests/test_codex_parity.py tests/test_context_compaction.py tests/test_image_to_sketchup.py
   - powershell -ExecutionPolicy Bypass -File scripts/check.ps1

3. Fix integration failures without weakening the contracts.

4. In a fresh image-reconstruction planning turn, verify the Agent writes all four durable planning files in the same turn:
   - notes/reconstruction_card.md
   - notes/reconstruction_evidence.json
   - notes/facade_schedule.json
   - notes/construction_strategy.json

5. The six-view villa strategy must contain real signal. At minimum:
   - one primary-form wall/opening system using continuous_wall_with_openings;
   - roof method chosen from loft_or_mesh/custom_owned_ruby instead of generic stacked boxes when the source roof varies;
   - one representative repeated facade module before replication;
   - shared parameters for storey height / major bay or opening spacing where applicable;
   - verification views tied to the systems they can actually expose.

6. Run a fresh whole-six-view DeepSeek reconstruction on SketchUp 2024. Do not manually edit geometry. The Agent may use custom owned Ruby, but it should follow the staged strategy internally:
   primary form → representative module → replication → variants → finish.
   These are not extra user approval gates.

7. Measure whether the run improves over the 2026-10-08 quality-loop baseline:
   - writer commits and failed tools;
   - input/output tokens and elapsed time;
   - number of full-root rebuilds;
   - wall seam/opening topology defects;
   - roof/parapet/division fidelity;
   - whether a representative module was verified before copying;
   - KEEP regressions during corrections.

8. Keep v2.6 KEEP protection and host-certified camera tests active. A new strategy file does not override the independent critic, writer receipt or protected-path guard.

9. If the strategy becomes paperwork that the Agent ignores, do not preserve it just because tests pass. Record that failure and either strengthen the host boundary or simplify/remove the artifact.

10. Finish with fresh six-view review, blank replay and native SKP reopen/edit. Update HANDOFF/CURRENT_TASK/test-results, commit, push origin/main, then hand back to ChatGPT for review.

## Acceptance

PASS only if:
- the strategy is valid, current and used by the same run;
- no new approval loops are introduced;
- quality gates still hold;
- the new run has equal or better source fidelity with lower or comparable writer/tool waste;
- no KEEP regression occurs.

Otherwise keep it PARTIAL and use the evidence to decide the next method-level change.
