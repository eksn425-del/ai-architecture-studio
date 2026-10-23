# Cloud Agent contract repair — 2026-10-23

## Scope and ownership

The owner requested cloud-only code repair followed by tests in the assistant's Blender environment, explicitly excluding the owner's computer. This branch starts at `a85c62c0f664ad2effc32a49ff4eda885afab4a5`. No user-PC changes, native SketchUp execution, live provider inference, main merge, or deployment occurred. Repository publication is a separate pending confirmation.

## Repairs

- `app/review_context.py` now builds one host-owned independent-review context for both Native Codex and LiteLLM API routes: source roles and fingerprints, actual captures, requirement lifecycle, exact current host-granted instruction, approved scope and race validation. Supplemental source/facade evidence is shared too. Images reused by evidence pairs are attached once.
- Invalid/stale scope exposes only audit metadata and a raw-scope digest, never its old plan prose as authority. Original history remains untouched.
- Cached review reuse invalidates when user intent or scope changes without a geometry change. The write gate also checks current review intent immediately before mutation.
- `app/review_progress.py` persists feature/intent history across prepares/restarts. Same-revision rereads do not count; omission does not resolve a requirement. Repeated text/desired states are advisory, not proof geometry failed to improve. An independently provided host geometry digest enables verified repeat/cycle detection; existing SU writer receipts do not yet supply a complete geometry digest, so the production SU path remains advisory here. Different request text is conservatively a new goal; no universal NLP equivalence claimed.
- Blender has an **opt-in host-only** exact edit contract. All backend instances honor installed scope, protect every pre-existing non-target object, check current scene/source/intent and policy integrity, and validate protected native geometry before commit. Only the host can install/rebind it; it is not a model tool or automatic natural-language approval feature. Legacy sessions with no installed contract retain their prior behavior.

## Test evidence and limitations

`before-reproduction.json` is a fresh reproduction on unchanged baseline source: both changed intent and invalidated scope incorrectly retained a review. The corresponding new tests pass on the candidate.

`blender-evidence.json` documents actual Blender 4.3.2 execution, not a mock native backend: a synthetic 74-object facade fixture, six targeted rail edits, 68 unchanged objects; original and candidate saved and reopened in fresh Blender processes. Original .blend byte hash remains unchanged. KEEP update/delete, undeclared write IDs, stale instruction and stale review revision are rejected without changing saved scene/model bytes. Original 800px renders were inspected.

The review responses are scripted test envelopes. This is **not** proof of independent LLM visual quality, autonomous reconstruction from owner photos, natural-language approval quality, real-provider cost, CNY 5/building, or SketchUp parity. Existing historical r22 quality verdicts are not upgraded by this repair.

Unit fixtures that previously omitted explicit target roles/required reviewer envelopes were updated to the actual stricter shared contract, retaining their original model-identity, no-writer, usage and rejection assertions.

## Reproduction

Use Python 3.12, Blender 4.3.2, `requirements.txt`, `requirements-model-providers.txt`, plus the recorded test-environment extras `mcp` and `socksio`. Use a fresh writable test HOME; do not write to the user's desktop/home or install provider credentials. Set `LITELLM_LOCAL_MODEL_COST_MAP=True` to use the library's packaged price metadata during offline tests, not blocked external retrieval. The provider-wire tests intercept transport locally.

- `python -m pytest -q` (full candidate and unchanged-baseline suites, JUnit results recorded separately).
- `python -m pytest -q tests/test_shared_review_contract.py tests/test_durable_review_progress.py tests/test_blender_edit_contract.py`.
- `python -m pytest -q tests/test_cloud_blender_contracts.py` (starts actual cloud Blender).
- Run each `tests/test_ui_*.js` with Node; compile changed Python; `git diff --check`.

Initial environment and fixture failures, and one full-run interruption on blocked remote LiteLLM price metadata, are retained in private delivery logs. They are not silently labeled passes. No access restriction was bypassed. Final candidate: **1253 passed, 9 skipped, 0 failures**. Unchanged baseline under the same offline environment: **1200 passed, 9 skipped, 0 failures**. There are 53 additional passing cases and no new failing IDs. 50 focused new-contract cases and 114 JavaScript assertions also pass. See `test-summary.json` for skip reasons. Two dependency warnings remain; Windows/Ruby/optional web-search tests are not mislabeled passes.

## Remaining work

Real-provider quality/cost and native SU acceptance remain NOT_RUN. Full semantic building-plan execution, arbitrary-image fidelity, adaptive global-versus-local review frequency, and production SU geometry-grounded convergence are not solved by this patch. Any paid run or work on the owner's computer requires applicable new scope/authorization. Preserve current single-writer, source/identity, KEEP, snapshot and rollback safeguards.
