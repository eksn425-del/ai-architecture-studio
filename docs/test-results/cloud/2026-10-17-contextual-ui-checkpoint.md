# Contextual UI cleanup checkpoint

This scoped patch builds on `08b9e8b70166b4672a225c64dd9ecf1c4eec7926` on `trial/readiness-20261016`. Its four code/test files apply cleanly without changing the intervening stage-quality controls. Only those files and this sanitized note are published; screenshots, private inputs and the simulated-provider UI harness remain excluded.

## Changes

- Secondary plan, parameter and execution details are grouped under an expandable section. A pending plan retains a single primary approval action outside that section.
- Model settings are grouped but remain accessible. Reference roles, uploads and sending remain visible.
- Plan details open on entering a new pending-plan context; typing a draft does not continually reopen a section the user collapsed.
- Upload wording now accurately states 25 MiB, with the existing eight-image, image-pixel and normalized-image limits described. Limits themselves are unchanged.

## Verification and limits

The UI worker checked native browser viewports of 1188 x 848 and 645 x 848: no approval for idle state; one primary approval for pending plans; accessible parameter editing, plan download and progress; expandable model settings in the narrow window; visible image-role controls, input and eight-image/25-MiB hints; drafting without forcibly reopening collapsed details. These observations cover the worker's UI snapshot, not new autonomous modeling or live SketchUp acceptance.

The worker's pre-stage-integration suite passed 573 tests with 15 skipped in 33.27 seconds. A separate combined publication regression is recorded below. The previous historical SketchUp text corruption was not reproduced; this patch does not claim to have fixed its unknown cause. Current shared HTML/JavaScript contain no replacement character, and the worker observed readable Chinese in both viewports. Intentional help question marks remain.

No new providers, credentials or dependencies are added. No model inference was rerun for this UI change. Main and deployment remain unchanged. Local regression and UI observations do not establish GitHub CI success or commercial readiness.

Combined publication rerun: **578 passed, 15 skipped, 1 dependency deprecation warning in 41.75 seconds** on 2026-10-17. This includes the preceding stage-quality tests. JavaScript syntax checking also passed. Original UI patch SHA-256: `2c17e5c0f1b0e6696179fffcc2e4b5e9e86d6b21b240283acc0c757da34f155b`.
