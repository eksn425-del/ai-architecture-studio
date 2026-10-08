# Quality Loop v2.2 — structured facade/roof schedule

## Why this follows v2.1

v2.1 already separates the DeepSeek/LiteLLM visual Critic from the Builder. The clean Critic sees source reference images and six validated current SketchUp views with no geometry tools or Builder history.

The next remaining gap from the OSS comparison is source fact stability. In the Windows v1 run, opening counts and roof facts were partly corrected by the user in prose. ArchFlow and SketchUp Agent Harness both show a useful pattern: keep source-facing constraints in compact structured project state with provenance instead of forcing later turns to recover them from a long chat.

This change does **not** make a rigid DesignIR the geometry source of truth. Persistent Ruby and the real SketchUp model remain the modeling truth. The schedule is a compact source/acceptance ledger.

## GitHub changes

- every reconstruction workspace now seeds `notes/facade_schedule.json`;
- the planner must update it together with `reconstruction_card.md`;
- it records front/rear/left/right opening/features and roof/parapet/division facts, with observed / user_confirmed / inferred provenance;
- workspace file tools allow validated `notes/*.json` only inside the project workspace;
- the dedicated read-only Critic receives this compact schedule in its clean source+six-view call;
- full provider/tool history is still kept locally; this milestone does not yet rewrite active-context compaction.

## Local Codex / Windows validation

1. `git pull --ff-only`; read this file, the top of `docs/CURRENT_TASK.md`, `docs/OSS_GAP_REVIEW_2026-10-08.md`, and the v1 Windows report.
2. Run:
   - `python -m pytest tests/test_codex_parity.py tests/test_modeling_quality.py tests/test_reconstruction_agent_architecture.py tests/test_quality_lift.py`
   - `python -m pytest`
   - `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`
3. Fix integration failures without weakening assertions.
4. On a fresh whole-six-view project, verify the plan turn itself writes `runtime/agent_workspace/notes/facade_schedule.json`. Do not hand-edit it after planning.
5. Check the schedule against source/user input. In particular record the known six-view constraints (for the current villa benchmark, user-confirmed opening counts must remain user_confirmed rather than being relabeled observed).
6. Run the normal approved build on real SketchUp 2024. Confirm event logs show the dedicated Critic and that its clean request includes the schedule.
7. Keep the v2.1 loop: writer → six current captures → dedicated Critic → targeted correction only if NEEDS_FIX → fresh six captures → dedicated Critic. Writer commits remain bounded.
8. Smoke `saie_wall_with_openings` in real SU2024. Confirm one continuous wall with real openings, including reversed centerline/side wall. If boolean subtract is unreliable, implement a continuous-face/hole fallback; do not return to visible sill/jamb/head wall-group stacks.
9. Judge actual source fidelity: wall seams/opening topology, roof divisions/parapet/capping, opening proportions/positions, then materials/details. A critic NO does not override an obvious human-visible contradiction.
10. Replay the integrated baseline in a new blank model; web download; native reopen; edit one guarded object; save/reopen; compare IDs/bounds.
11. Record Builder tokens, dedicated-Critic tokens, tool calls and latency separately. Compare with the v1 six-view ~4.92M reported input-token baseline, but do not infer supplier billing.
12. Update HANDOFF/CURRENT_TASK/test-results, commit and push main.

## Next decision

- If source fidelity improves and the independent Critic tracks human inspection, next engineering priority is active-context compaction.
- If the independent Critic still false-passes obvious opening/roof discrepancies, add deterministic checks against the schedule before accepting NEEDS_FIX:NO.
- Do not broaden to Rhino/CAD/render/payment until one representative SketchUp reconstruction is stable.
