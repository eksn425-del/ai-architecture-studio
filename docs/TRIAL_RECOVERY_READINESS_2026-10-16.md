# Product recovery patch, 2026-10-16 UTC

This is a new product-only task on top of r20 (`564d75c2361f8ac73b3024abffba5035581aa661`). The closed eight-source building, its geometry, accepted scope and original evidence are unchanged. This patch does not certify a commercial release or source fidelity.

## User-visible corrections

- A failed project switch keeps the original project identity, displayed conversation and draft together. Late responses cannot overwrite a newer selection. Optional browser-storage failure no longer interrupts a loaded project.
- Switching to a project checks for an active turn. Sending remains locked during the check. A status outage is treated as unknown and retried with read-only polling instead of immediately enabling a duplicate submission.
- Completion polling does not overlap. It keeps the lock until the completed project actually loads, retries failed reads, and preserves an unsent draft when no running turn was observed.
- The SKP download follows `model_state.model_path`, including recovery to an older checkpoint. It does not silently select a newer historical file. A missing matching artifact fails closed.
- Saved SKP files keep an explicit candidate/native-reopen verification notice. Missing delivery metadata does not imply native acceptance. The app currently writes only UNVERIFIED_NATIVE_REOPEN; separate audit PASS results are not linked to a current-file verification status in the UI. Unknown statuses therefore ask the user to consult the matching native verification record, without asserting that no record exists elsewhere.
- Optional camera capture metadata no longer crashes an adapter-less fixture. Missing camera evidence remains unverified.

## Verification and limits

Thirteen new tests execute the actual frontend JavaScript under Node with controlled I/O. They are function-level regressions, not browser UI tests. Independent code review found two additional races during development; both were fixed and covered.

Final core environment: **537 passed, 15 skipped**. `node --check`, Python compileall and `git diff --check` passed. The skips are Windows PowerShell (1), system Ruby (1), optional LiteLLM (11), and real Windows DPAPI (2). The 11 optional LiteLLM 1.105.1 wire tests also passed separately with locally intercepted HTTP and no live inference. Initial SOCKS transport dependency failures were resolved by installing socksio in an isolated test-only dependency directory; production requirements are unchanged.

The initial unchanged-r20 baseline had 10 failures: eight tried writing the default ArchFlow script cache outside the writable workspace, one test still rejected the explicitly supported timeout=0 policy, and one screenshot fixture lacked an optional adapter. The existing `ARCHFLOW_GENERATED_SCRIPT_DIR` setting resolved the eight environment failures without changing production cache behavior. The timeout regression now tests zero and finite invalid bounds; it does not change runtime timeout policy. Camera evidence remains unverified when unavailable.

**Actual browser interaction: NOT_RUN.** The cloud browser was available, but the localhost server ran inside a separate shell network namespace. The supported external-server launch failed at sandbox initialization. No alternate UI-control route, hidden API login or quota was used. The actual backend received an independently supplied short Chinese reading-room request; a current-assistant simulation replied only after receiving it. The backend correctly left modeling tools disabled for clarification. It did not generate a website model, and the dependent edit/save dialogue was not fabricated.

**SketchUp native: NOT_RUN.** The website currently has no Blender bridge. A separate deterministic Blender 4.3.2 disposable-room fixture built native geometry, moved only the five table meshes, preserved all other mesh fingerprints, saved and reopened an equal native snapshot. This is native Blender smoke evidence, not a website/Agent generalization result or a SketchUp fallback integration. Initial render failure and visual-fixture correction are retained in the local evidence package.

## Review/start instructions

1. Keep the existing model and working checkout unchanged. Review this patch on a separate branch from the exact r20 baseline; do not overwrite an uncommitted local session.
2. Use the project's existing virtual environment and dependencies. For offline checks, set `ARCHFLOW_GENERATED_SCRIPT_DIR` to a writable test-only directory, then run `python -m pytest -q tests`, `python -m compileall -q app`, and `node --check app/static/studio.js`.
3. Start the reviewed checkout with the existing, explicitly selected local model configuration using `python scripts/dev.py --port 8787`, then open `http://127.0.0.1:8787`. This command does not supply a model provider or authorize inference. No credentials or new API keys are included in this patch.
4. In a disposable test project, verify ordinary interaction: create/cancel a session; type and retain a draft; switch sessions and back; temporarily interrupt loading and verify the original title/draft remain; refresh during a running approved turn; verify sending stays locked until synchronization completes; then save/download and confirm the file corresponds to the displayed checkpoint.
5. Perform real native save/download/reopen and protected-edit checks on a safe copy before accepting a modeling trial. A download warning is deliberate until corresponding native evidence exists.

## Remaining risks

- Browser DOM/layout/keyboard and real native SU behavior remain untested in this environment.
- Client-side race prevention is not cross-client idempotency. Existing server writer locking remains the concurrency boundary.
- A failed initial status check deliberately keeps Send locked until a read-only retry succeeds. An offline workspace cannot safely confirm completion.
- A matching historical draft is cleared only after a running turn was actually observed; turn-ID-based draft correlation is not added here.
- Native Blender smoke validates selected mesh geometry/transforms/material assignments at declared numeric precision, not lighting, all Blender data blocks, accessibility, construction compliance, or reference-image fidelity.

Publication is not part of this local result. No GitHub write or remote push was attempted.
