# Evidence Fidelity v2.4 — local acceptance

This milestone turns source completeness into explicit reconstruction behavior.

## Product contract

### Single image

Goal: source-facing visual reconstruction, not generic massing.

- The visible source view is a hard target for silhouette, floor/bay proportions, opening count/position, facade depth, colors/material zones, glass, railings and visible interior/furniture/detail.
- Unseen exterior, roof and interior may be inferred when the source does not show them.
- Inference must be coherent with visible structure/circulation and remain marked as inferred.
- A single-image PASS is judged mainly by the source-visible view. Hidden invented regions must not contradict that view.

### Multiple exterior views

Every supplied observed facade becomes a hard constraint on one building. Geometry seen in one view must remain consistent in the others. Only unseen regions may be inferred.

### Full evidence package

When the user supplies front/rear/left/right/roof views, floor plans, CAD/dimensions and interior reference images, use full_evidence_reconstruction.

- CAD/floor-plan dimensions control geometry when perspective images are ambiguous.
- Exterior/interior images control visible appearance, materials, openings, railings, glazing, built-ins, furniture and source-visible details.
- Do not redesign evidenced regions.
- Contradictions must be resolved explicitly; do not average them silently.
- PASS means all evidenced exterior/interior regions are mutually consistent. This is the project's "1:1 to supplied evidence" target, not a promise that missing or contradictory source data can produce mathematically exact ground truth.

## Local Codex execution

1. git pull --ff-only
2. Read AGENTS.md, docs/CURRENT_TASK.md, this file, docs/QUALITY_LOOP_V2_3.md and the latest HANDOFF.
3. Run:
   python -m pytest tests/test_reconstruction_evidence.py tests/test_codex_parity.py tests/test_context_compaction.py tests/test_modeling_quality.py tests/test_image_to_sketchup.py
   python -m pytest
   powershell -ExecutionPolicy Bypass -File scripts/check.ps1
4. Fix integration failures without weakening assertions.
5. Confirm planning writes a valid notes/reconstruction_evidence.json in the same turn as reconstruction_card/facade_schedule.
6. Single-image real SU2024 test:
   - upload one architectural image;
   - do not manually provide hidden-side geometry;
   - planner selects single_view_inference;
   - Builder matches the source-facing silhouette/openings/colors/glass/railings/visible details;
   - unseen sides/interior are plausible inferred geometry rather than blank/mirrored shells;
   - capture a source-matched current camera when canonical oblique does not match the source perspective; submit it as an evidence_pair;
   - independent critic prioritizes the source-visible view and must not PASS obvious source-facing mismatches.
7. Whole-six-view test:
   - planner selects multi_view_reconstruction unless CAD+floorplan+interior evidence also exists;
   - all observed facades remain hard constraints;
   - run the existing dedicated critic/write-budget/replay/native-edit gates from v2.3.
8. Full-evidence test when a local package is available:
   - exterior views + CAD/DXF + floorplan + interior images;
   - planner must select full_evidence_reconstruction only when the machine-validated ledger has all required coverage;
   - compare footprint/levels/openings against CAD/floorplan and visible materials/details against images;
   - for interior/detail reference images capture corresponding current SketchUp cameras and submit evidence_pairs; exterior-only six-view QA cannot certify full-evidence interior fidelity;
   - no evidenced region may be replaced by free invention;
   - record unresolved contradictions as PARTIAL rather than claiming 1:1 PASS.
   If no non-private complete package is available, run schema/unit tests and leave the real full-evidence visual gate pending_external; do not fabricate a PASS.
9. Record screenshots, ledger, facade schedule, critic receipt, writer receipts, token/tool/latency and manual interventions in a sanitized test-results folder.
10. Update HANDOFF/CURRENT_TASK, commit and push origin/main. ChatGPT reviews the result afterward.
