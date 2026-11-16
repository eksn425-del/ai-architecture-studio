# Blender and shared reference-role integration checkpoint

Scope: independent `trial/readiness-20261016` product test branch, based on `a6347ca3f549e9bb52bd01f43a3d5848a4f0b7f5`. The closed SketchUp r20 case is unchanged. This record accompanies production code, regression tests and this sanitized engineering note only; private reference pictures, models, raw logs and the interactive simulation harness are excluded.

## Changes

- Explicit project-level Blender opt-in, with existing SketchUp sessions protected from rebinding. The existing conversation/router/tool pipeline receives bounded named boxes or indexed meshes and simple materials; it never executes model-supplied Python.
- Native Blender saves are reopened in a separate process with auto-execution disabled. Selected mesh geometry and material receipt equality is checked before advancing the current revision; untouched named objects are retained in the declarative scene. This is not a complete Blender-data or visual-fidelity audit.
- Image roles distinguish target building references, historical defect-location screenshots, supporting material and unresolved legacy images. Roles are chosen explicitly, never inferred from filenames. First-submission message IDs and model revisions preserve provenance.
- Changing a reference role invalidates the plan. Unknown Blender image roles gate planning/execution. Shared native visual-review checks reject stale evidence and exact conflicting feature requirements; this is not a general semantic contradiction detector.
- The UI exposes separate target/problem uploads, legacy-role confirmation, backend-aware progress and Blender artifacts. Model saves and previews do not claim architectural quality acceptance.

## Verified checkpoint

The frozen integrated patch SHA-256 is `30c9a36bfc7e614c6f9c484dca49e3f914ba6b167e879f2f32fb88e3152e2ded`. It applied without conflicts to the prior approved code snapshot. A fresh isolated publication-check rerun on 2026-10-17 completed **572 passed, 15 skipped, 1 dependency deprecation warning in 37.87 seconds**. JavaScript syntax checking passed. Tests include real Blender save/reopen operations; deterministic test providers are clearly labeled and do not call an external model.

The preceding integration run recorded 572 passed / 15 skipped in 44.82 seconds. Three separate real-Blender role/provenance scenarios passed with four native saves/reopens: target creation, a historical defect-linked revision change with an unrelated pillar preserved, and an unknown-role gate followed by explicit classification and execution. These scenarios used deterministic simulated model responses, not autonomous image understanding.

The UI worker verified actual cloud-browser interaction for legacy-image classification persistence and plan invalidation, target/problem file selection through the visible Open button, historical problem-image revision binding, preserved first-message binding and a plan awaiting approval. Filename/role wrapping was fixed and visually retested. Earlier Return-key file-chooser attempts did not submit; the visible Open button succeeded, so these attempts do not establish a product upload defect. Browser developer tools were blocked by organization policy and were not bypassed.

## Limits and next acceptance checks

- No live external-model/paid-provider invocation or autonomous visual-critic acceptance is established by these tests.
- Live SketchUp regression, cross-software source fidelity, full Blender UI modeling/edit/download/reopen acceptance and end-user acceptance remain separate checks. Existing historical SU evidence is not this run's result.
- The Blender backend currently reconstructs its bounded project-owned declarative mesh scene when saving. It does not preserve arbitrary hand-edited Blender objects, animations, modifiers, rigging or imported scenes; use disposable test projects.
- Rendering uses fixed front/rear CPU review cameras. It is not an unrestricted scene/game/animation system.
- The 15 skipped tests are not passes. Local suite results do not establish GitHub CI status or commercial readiness.
- Publication of this checkpoint does not merge into main, deploy a service, resume the closed building, or authorize new API spending.
