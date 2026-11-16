# Contextual conversation and scoped repair checkpoint

Baseline: 08a41c3cbfb14b175dc5764156e5a43d4262187b (production code 85777300596e0adc18e6c30b4f773a7002dc27d8). The existing Codex App Server remains the native agent engine. No credentials, paid inference, deployment, main merge or user computer operation was performed.

## Changes and evidence

- Natural user text is sent verbatim. Native contextual interpretation uses a separate read-only turn without dynamic tools. Host-side current-user evidence, conservative nonwriting vetoes and unchanged pending-plan identity/hash/reference/model checks protect authorization. Tests include natural approval, wrong-model execute for refusal/questions/only-plan/quoted/conditional instructions, scoped KEEP and old-plan constraints. This is not a proof of error-free language interpretation.
- Plans carry host-created pending IDs bound to project, model version and source manifest. Execution consumes the pending approval. Completed requests can be replayed repeatedly without duplicate effects; uncertain requests remain blocked instead of silently retried.
- Sent attachments leave the draft and remain in collapsed history with optional correction. Unknown/conflicting evidence retains its safety gate. Drafts are preserved. Plan buttons and text share the displayed plan binding. Stop is shown only when a current native request supports it.
- Native progress uses bounded real protocol event fields. Interrupt requests travel through the live native connection; requested and terminal interrupted are distinct. Cancellation checks prevent later tool dispatch, but do not roll back in-flight writes. Host responses preserve interrupted state with or without a committed checkpoint. These tests use mocked protocol transport, not a live model session.
- Scoped relation repair maps proposed issues to exact component IDs, edit scope, priorities and measured contacts. Tool calls recheck actual native geometry and protect unrelated objects. Two unsuccessful attempts block the same repair scope. A new host-approved plan archives the prior failure and enables recovery; the model cannot reset its own budget.
- Plan-card reads reject links, out-of-workspace paths and files above 256 KiB before interpretation.

## Actual Blender verification

A generic stairs/platform/corridor/rail fixture ran through AgentToolSurface: initial build, repair-plan tool, scoped edit, automatic native check, explicit check, before/after rendering, native save and fresh reopen. Three gaps of approximately 150, 100 and 50 mm closed within 0.01 mm tolerance. Seven protected objects and the original native file remained unchanged. Native files and renders are retained privately.

The repair proposal was a controlled fixture, with zero provider calls. The test establishes geometry/tool mechanics, not autonomous visual diagnosis, whole-building circulation or fidelity to the owner's unavailable SU reference/model.

## Validation and limits

Final integrated suite: 876 passed, 19 skipped, one dependency deprecation warning, 57.25 seconds. Independent focused review: 113 passed. Actual GUI entry returned ERR_CONNECTION_REFUSED, so fresh browser interaction is NOT_RUN; Node/TestClient tests are not GUI evidence. Real SU case and actual Codex model end-to-end are NOT_RUN. Skipped tests retain their original environment requirements; no failing tests were suppressed.

No private images, models, raw event transcripts or fixture runtime are included in this public patch.
