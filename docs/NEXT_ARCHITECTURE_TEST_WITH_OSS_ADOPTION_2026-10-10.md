# Codex NEXT — new building image + real OSS adoption (2026-10-10)

## Input and scope

User will send **NEW building reference image(s)** to the local Codex session. Do not start old white-villa/cafe modeling by default; do not invent a source file or substitute a different old building. If images aren't attached yet, prepare and verify the environment and then ask for **those reference images** before launching the new-build Agent. The source files remain private unless the user expressly permits publication.

This is the **same one K AI Studio** `eksn425-del/ai-architecture-studio`, latest `origin/main`, user-facing website + SU2024 + Kongxing single writer. Use the actual Codex available `gpt-6-luna` / `max` (or tell the user and record the fallback). Don't run another standalone MCP against the same model. Keep native editable SKP, KEEP and root identity.

## Priority 0 — complete and validate the actual OSS-to-product loop

1. Pull latest main and review `AGENTS.md`, `docs/CURRENT_TASK.md`, `docs/CONTINUOUS_CAPABILITY_ADOPTION_2026-10-10.md`, [Issue #3](https://github.com/eksn425-del/ai-architecture-studio/issues/3), and last café runs including their **real FAIL/PARTIAL**.
2. `scripts/check.ps1`, plus targeted tests for `app/oss_method_catalog.py`, `app/oss_method_runtime.rb`, `app/project_ruby.py`, `app/agent_tools.py`, and `app/construction_strategy.py`. **Real SU2024 smoke of the updated wrapped methods** on a disposable sketch, confirm the returned `oss_method_ledger` is `committed_readback`, the relevant `saie.*` and/or `adai.*` event is `returned`, script SHA/revision/root PID match, and no event is fabricated by source-text scanning. Missing/zero method calls must stay non-product-used. Do not add a separate active ADAI MCP. Pin/license checks stay in effect.
3. Check **next-run planning**: for each source-backed wall/void/roof/profile/repetition system, save concrete `method_id` and `selection_reason` in the existing construction strategy. Prefer an actually compatible verified OSS implementation by geometry suitability; check the real signature. For custom Ruby state the concrete reason a known helper is unsuitable. If method is enabled only behind `ARCH_STUDIO_ENABLE_ADAI_GEOMETRY=1`, enable it for the isolated approved test process and verify; if not compatible, use existing fallback and report actual error. Do not arbitrarily call ADAI just to tick a box.
4. Build from **user's newly supplied actual image(s)** in a NEW K AI Studio project: source → inspect inputs → one concise parameter approval → single main geometry pass → source-matched QA → up to two bounded KEEP-protected targeted corrections → native SKP download / open / mouse-edit copy / save / reopen. Preserve visible scale and facade/roof/opening features; when unknown, mark dimensions ESTIMATED. Do not overwrite the user's original SKP, and don't use old café or villa instead.
5. After each geometry write capture host-issued ledger and compare it with intended method decisions. Debug any `selected_but_not_invoked`, missing audit events or untracked custom primitive; ensure actual source-backed geometry was made and read back. Test zero-call and guarded rollback negative path. Do not declare visual improvement from merely seeing event `returned`.
6. Capture six host-certified CURRENT canonical PNG images and at least one reference-aligned perspective; use a genuinely independent read-only Critic when available (no writer tools) and human image-inspection notes; don't claim quality PASS if source fidelity is incomplete. Prevent repeated roof layering, reference-mismatched outbuildings, baseline replay mismatch and runaway 10M-input-token 30-min Native turns; preserve original failures. Favor structural repair of defects rather than workaround scenes or occluding objects.
7. Check bounded phases, duration/tool failure count, actual input/output tokens (or null if unavailable), warnings. New blank replay must match persistent source geometry within declared tolerances; a saved screenshot alone is not proof of reproducibility.

## Every test must be uploaded to GitHub, including failures

Choose a new factual directory `docs/test-results/windows/2026-10-10-<actual-building-shortname>/` (use execution date if different; no overwritten old results).

Read and follow `docs/TEST_EVIDENCE_PROTOCOL.md`. At minimum: `README.md` with PASS/PARTIAL/FAIL and shortcomings, `run.json`, `metrics.json`, `errors.json`, source-angle PNG, **six authentic current-revision host-certified views with sidecars**, planning schema validation, write receipts, owned object readback/KEEP, downloaded SKP hash/native reopen/edit, independent/self-review disclosure, and before/after close-ups. No geometry committed? Write real BLOCKED/FAIL, **not fake images**.

**New mandatory proof files:**
- `model/oss-method-ledger.json`: export actual `oss_method_ledger` from the newest committed ProjectRuby run's verified current-root readback, including real method IDs/events and source SHA/revision/PID. If 0 actual wrapper events, report `events: []`.
- `model/oss-method-adoption.json`: export the host's `oss_method_adoption` (chosen method/selection reason/actual event counts/was `product_used`/effect still unverified).
- In `README.md` include a short **external-source adoption table** (source / what we planned / why selected or rejected / actual invoked? / real visual outcome / fallback / next fix), not just “installed ADAI”.

For multiple committed revisions save individual method ledgers/readbacks where helpful; final two required files must reflect the **latest verified build**, not reuse an older disconnected smoke. Run `python scripts/validate_test_evidence.py <new-folder> --write-manifest` and then `python scripts/validate_test_evidence.py <new-folder>`; copy actual images into Git rather than linking ignored runtime paths. Public repository: never push private image, original SKP, DPAPI/token, file paths or personal data.

**Definition of done**: a user-facing new-building attempt executed through actual K AI Studio with real method-choice reason, host-wrapped invocation evidence or explicit no-OSS/fallback, source-based visual inspection, editable native SKP when geometry commits, honest quality report and all GitHub artifacts. Failures and blockers count as evidence but NOT product quality PASS.

After local debugging, run regression tests, update `docs/CURRENT_TASK.md` and `docs/HANDOFF.md`, commit/push `origin/main`, verify remote SHA and provide link to report directory. Do not begin CAD, renders, video or PPT; don't add more OSS intake projects until this usage loop is proven.

## Important distinctions

- `researched` / `installed` / `smoke_verified` / `product_used` / `effect_verified` are separate, no inferred promotion.
- Method calls in a committed root prove that a method executed; they **do not prove** it created the intended geometry group nor improved architectural fidelity. For fidelity, trace named child groups + source pixels and human/independent Critic.
- Current code offers method-aware tool instructions, plan metadata and real-call wrapping. It is **not yet SU2024-proven** and not a fully automatic deterministic geometry dispatcher. Codex must validate/repair compatibility, and report any remaining gap honestly.
