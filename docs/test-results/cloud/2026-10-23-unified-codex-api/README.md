# Unified Codex API route: private cloud candidate, 2026-10-23

## Outcome and boundaries

This change implements an explicit `codex-responses` selection which uses the SAME `CodexAppServerRuntime` as the existing native route. It is not another Agent/tool loop. It is an opt-in Responses-compatible provider path, not a universal converter for Chat Completions providers. Existing LiteLLM and managed Responses routes remain visibly separate and are not silently migrated or used as fallback.

The owner requested implementation after the architectural diagnosis, on the assistant's cloud computer. No owner-PC operations, live paid inference, secret migration, GitHub publication, main merge or deployment occurred. Credentials used in tests are invented fixtures. No real provider was connected.

## Implementation

- `app/codex_provider.py`: explicit Responses/SSE/tools/images compatibility declaration, HTTPS API-base validation, provider/account/model identity, selected-native-config allowlist, process credential filtering and redaction.
- `app/native_agent.py`: the shared runtime accepts explicit provider configuration without borrowing Codex login credentials, retains supported selected native custom-provider settings, isolates homes and provider-bound sessions, checks returned provider/model before inference, and guards both custom-provider entry paths against monetary-budget bypass.
- `app/model_router.py`, `app/main.py`, session model and workflow routing: public settings select the explicit route, use the selected runtime for intent/cancellation/Blender execution, bind thread reuse to engine/provider/account/model, and reject unavailable connections without fallback.
- UI: named Codex Responses route, required capability acknowledgement, actual engine label, memory-only key behavior, clear-on-close/Escape and no reused legacy key when a provider changes.
- Blender native dynamic-tool receipts now forward certified actual rendered PNG pixels. Complete raw native receipts remain in the journal; repeated native mesh arrays are projected into hashes/counts on the active wire, with explicit exact-detail retrieval.

### Important cost limitation

The autonomous Codex subprocess does not yet expose K Studio's existing per-model-request monetary reservation boundary. If `K_STUDIO_LOCAL_API_TEST_BUDGET` or `K_STUDIO_OPERATOR_MAX_USD` is configured, the new API route stops before launching inference. This also applies to the preserved native custom-API path. Do not remove a cap to bypass this guard. This candidate is not the completed solution for budget-controlled commercial API delivery.

No monetary saving is established in this phase. The earlier 34.427% text / 17.346% wire reduction belongs to a separate controlled LiteLLM fixture; it is not an automatic Codex price reduction. Synthetic token notifications only validate accounting-field handling and are not a tokenizer or invoice.

## Validation layers

### Controlled App Server peer + production product runtime + actual Blender

The separate scripted App Server subprocess deliberately replaces upstream orchestration/model behavior. The public `configure_codex_responses` / router / production `CodexAppServerRuntime` / tool surface / real Blender remain exercised. This demonstrates wiring and host safety, not autonomous model intelligence or actual Responses HTTP/SSE execution.

The synthetic fixture builds 74 objects, changes six exact allowed rails, preserves 68 others, verifies real saved native r1/r2 and independent fresh-process reopens, and checks original `.blend` SHA is unchanged. The returned image bytes match the saved render SHA. Seven hostile/unapproved/stale/foreign-turn attempts are rejected. Raw topology and projected digests are cross-checked. Source images and provider-bound thread resumes are checked. All usage values in this fixture are explicitly synthetic.

A preliminary acceptance assertion expected full topology on the wire. The implementation intentionally retains it in raw receipts and projects it on the wire. That failed run is preserved, then acceptance checks were corrected to verify both raw data and projection digests, not to discard geometry validation.

### Independent security review

Caught and fixed two real integration gaps before release: inherited native custom-API configuration could bypass monetary-cap admission, and it could accept a different reported provider. Adversarial regressions cover both, along with account changes after a stale router check, secret redaction, no credential migration, no fallback, selected-runtime cancellation and sandbox/network policy.

### Actual installed upstream Codex binary

Codex 0.163.0 successfully initialized and returned effective custom-provider configuration. `thread/start` was blocked before any model call by the host's fixed daemon-directory permission boundary. The directory metadata was checked; it was not changed. No sandbox weakening or alternate path around the restriction was used. Therefore actual upstream model HTTP/SSE, autonomous tool roundtrip and live provider correctness remain **NOT_RUN**, not PASS. See the attached transport probe and evidence.

### Aggregate regression

Final counts and frozen source hashes are in `test-summary.json` once the final run completes. Fresh restored baseline: 1315 passed, 9 skipped, zero failures in 235.35 seconds. An initial baseline archive omitted two historical JSON test fixtures; its one FileNotFoundError is retained as harness evidence. Exact Git fixtures were restored and the baseline rerun passed; no product test was weakened.

## Provenance and use

Remote `main` 564d75c is an ancestor (61 commits behind) of the inspected release-preparation baseline a85c62c; it is not newer work. The prior private 29c00e8 candidate was recovered from the already delivered Library ZIP: SHA256 0026e1e37e27d7e39c476fcc3533d004427562e44b999f6ba0cd8943a4536b85, all 100 manifest entries and 46 source files verified. Local recovery commit 6833577 preserves its source content, not the original commit metadata.

This remains a private candidate. A real-provider acceptance test must use a normally supported authorized host, explicit secure credential setup and a bounded approved spend policy. No endpoint/model is certified merely because its API looks OpenAI-compatible. Source-photo fidelity, independent Blender visual Critic and commercial readiness are not established here. Do not resume closed historical modeling cases.

## Final frozen verification

Final Python: **1375 passed, 9 skipped, zero failures**, 249.45 seconds. Node UI: **118 passed, zero skipped/failures**. Frozen application/test/script hashes rechecked unchanged. Independent controlled Blender: **16/16 checks**, plus its three pytest checks included in the aggregate. Browser visual QA did not start: sandbox socket permission failure and unsuccessful standard escalation; no screenshot or visual pass claimed. Compileall and git diff whitespace checks pass.
