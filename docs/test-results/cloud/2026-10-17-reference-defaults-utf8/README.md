# Contextual image roles and Windows UTF-8 repair

Baseline: `4ff47fb1b85a30f2d65d45ec133fe01b20d30ab8`.
Windows failure evidence: `ac803e58a52e16ef903ef751ba0dcec170295ae8`, `docs/test-results/windows/2026-10-17-su-three-round-fixed-4ff47fb/ERRORS.md`.

## Changes

Uploads default to **automatic, correctable** roles instead of requiring a choice for every image. Role labels remain editable:

- A single first image in a new project defaults to target when current wording does not contradict that inference.
- Clear current target/new-view wording uses the same building as target evidence. Clear model-problem wording assigns issue-location evidence, bound to the uploaded model version.
- Identical normalized image bytes reuse the known role; conflicting roles/descriptions remain uncertain. Reuploaded old issue images retain their historical model revision even if the upload description conflicts and a later message resolves the role. Conflicting historical revisions are not relabeled as the current revision.
- Mixed attachments, non-target/interface screenshots and ambiguous repair wording remain uncertain and require clarification. Filenames are never classification evidence.
- Later explicit wording can reconsider fresh, unsubmitted automatic defaults. Generic “continue” messages preserve a reliable existing default. Manual choices and already-submitted evidence are not silently reclassified.
- Explicit role corrections invalidate the plan and approval scope. Formal planning/execution is gated while roles remain unknown; a later clear message can resolve fresh uncertain attachments before that gate.

The mechanism is conservative context rules and byte-identity matching, not visual understanding. A first-photo default can still need user correction; the visible label supports that correction.

## Windows defect

The reported three HTTP500 errors occurred before modeling because UTF-8 Chinese project JSON was read using the Windows cp936 default. Approval/reference-state and related Blender text I/O now explicitly use UTF-8, including audit writes. Setting PYTHONIOENCODING would only affect standard streams and is not the fix.

The regression emulates cp936 file defaults at pathlib entry points on Linux, first reproduces the implicit decoding failure, then checks the explicit-UTF8 approval/read/write/invalidation/version chain with Chinese and emoji. This is not a claimed native Windows run.

## Verification and limits

See RESULTS.json for exact tests. Existing genuine Blender mechanics tests remain in the full regression; this small change does not introduce new geometry or assert SU/Blender visual parity. Node tests cover automatic upload, explicit override, encoded current context, mixed image count, editable role labels and corrections. No fresh browser GUI or actual Windows/SU rerun is claimed.

No external paid model calls, credentials, deployment or main merge. No private reference images/models/raw logs are published. The next local task should only pull this commit, verify the service/port/directory, restart the correct service and open the page for the owner's own manual test.
