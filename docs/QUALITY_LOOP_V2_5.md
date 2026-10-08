# Quality Loop v2.5 — host-certified canonical review cameras

## Why this follows v2.4

v2.1-v2.4 fixed the major control-flow gaps: single writer, current-revision evidence, dedicated read-only Critic, structured facade/evidence memory and active-context compaction.

One trust gap still remained in the six-view gate: a path could be current and distinct while the Agent had chosen the wrong camera and merely labelled it "front", "rear" or "roof". Scenario-style DCC review sheets avoid this by generating review cameras deterministically instead of trusting free-form camera labels.

v2.5 closes that gap without changing the geometry writer.

## GitHub changes

- added `sketchup_capture_canonical_view` to the reconstruction tool profile;
- the tool reads the selected persistent ProjectRuby root bounds, then uses the project coordinate convention X=east, Y=north, Z=up to generate deterministic front/rear/left/right/roof/oblique cameras;
- each capture stores immutable camera provenance, canonical view name, persistent script ID and current writer revisions in the existing `.evidence.json` sidecar;
- the six-view quality gate now rejects arbitrary/stale/mislabeled screenshots even when the files are current;
- arbitrary camera/export remains available only for source-perspective/interior/detail `evidence_pairs`;
- developer instructions and the reconstruction Skill now explicitly require the canonical capture tool for the six review views.

No new geometry engine or Agent is added. Builder remains the only writer; Critic remains read-only.

## Local Codex validation

1. `git pull --ff-only`.
2. Read this file, `docs/EVIDENCE_FIDELITY_V2_4.md`, `docs/CURRENT_TASK.md`, the latest HANDOFF and execution guardrails.
3. Run:
   - `python -m pytest tests/test_modeling_quality.py tests/test_reconstruction_agent_architecture.py tests/test_context_compaction.py tests/test_reconstruction_evidence.py`
   - `python -m pytest`
   - `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`
4. Fix any integration failure without weakening the new camera provenance assertions.
5. In a disposable SU2024 model, call `sketchup_capture_canonical_view` for all six names against the actual persistent building script ID.
6. Confirm:
   - each returned PNG is visibly the intended front/rear/left/right/roof/oblique direction;
   - the building is framed usefully and is not clipped;
   - `.evidence.json` contains `camera_contract_version=1`, the matching `canonical_view`, script ID, camera vectors and current revisions;
   - swapping/mislabelling two paths makes `sketchup_submit_visual_review` reject the review.
7. Then execute the v2.4 single-image and multi-view real reconstruction acceptance. Canonical six views are broad coverage; source camera/interior/detail images still require `evidence_pairs`.
8. If a canonical view is poorly framed because the persistent root contains an oversized site/context object, do not relax provenance. Record the failure and add a verified building-focus bounds mechanism in the next patch.
9. Record Builder/Critic tokens, tool calls, camera receipts, source-matched pairs, wall-opening smoke, blank replay and native SKP edit/reopen results.
10. Update HANDOFF/CURRENT_TASK/test-results, commit and push main, then return to ChatGPT for review.

## Acceptance

Technical PASS requires the host to prove the six canonical labels from camera provenance, not filenames or Agent prose.

Visual PASS still requires the dedicated Critic plus source-matched evidence to agree with visible source fidelity. A valid camera receipt is evidence that the review image is the intended view, not evidence that the model itself is correct.
