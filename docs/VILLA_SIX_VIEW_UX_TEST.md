# Six-view villa: real website usage test — 2026-10-01

## Scope and execution

User requested mouse/keyboard operation of the local website, six views of one villa, a new disposable SketchUp model, inferred interiors and a small environment, with iterative product fixes. Started from clean main `ed4e9c8`. Existing Kongxing transport was reused. Only GPT-6.1 Sol Low was invoked through the website Codex App Server; no Astra and no outer-agent geometry authoring. All reference assets, screenshots, transcripts, generated Ruby and SKP remain ignored locally.

Browser flow: create session → multi-select six extracted PNGs → type natural requirements → analyze → answer the floor-count contradiction → view saved parameter card → connect SketchUp through the website button → check connection through UI → approve → inspect output → send same-model interior check → recover and retest. No direct HTTP modeling request was substituted for browser submission.

The six model inputs are recorded as text plus six localImage items on every native turn. Modeling uses the generated coding workspace with workspace-write and networkAccess=false. The sources contradict one another: front/oblique have four storeys, rear/sides have three. As proxy user, approved one coherent four-storey baseline and raised rear ground as an explicit inference. This cannot be called an exact six-view geometric replica.

## Observed failures and fixes

- File chooser originally allowed only one file. Added real multiple selection, sequential upload progress, per-file failure accounting, eight-image cap, and complete source previews.
- Pending user messages were absent during long turns. Added immediate transcript entry and waiting reply; composer now locks during processing.
- First execution exceeded 900 seconds after revision 4. Previously the UI returned to waiting for approval and lost native execution-thread/metrics. Exceptions now carry partial metadata; host attempts a guarded checkpoint, marks interruption explicitly and reloads state after errors.
- Approval discarded composer text. It now respects additional execution instructions when present.
- Interior patch used a replacement-only tool as though incremental. The implicit root clear plus inspection/patch source caused missing groups; an empty root could be deleted on commit, followed by a post-commit persistent_id error. Agent Undo attempts removed the generated villa. This was a real continuity failure, not successful interior QA.
- Existing Ruby tool now declares replace versus edit. replace requires a full reconstruction script; edit retains the same existing script root for a separate patch file. Empty owned roots are rejected before commit. Captured PID precedes commit; single-instance groups avoid needless make_unique. SketchUp Entities uses length, not empty?, validated during local retries.
- Checkpoints now guard owned-root existence/content before overwriting a prior file, check save_copy return, and create a pre-turn recovery snapshot. Added host-owned recovery button using the existing bridge, restricted to this project’s generated model copies. It preserves the failed copy and can rebind a delayed native open after a save dialog. A save dialog was encountered and handled with native mouse input on the disposable file; fully unattended recovery is not claimed.
- A broad source edit accidentally regressed active identity inspection with NameError; corrected and added an adapter-level regression, beyond the fake-SU endpoint tests.
- Collected tool screenshots appear in a model gallery. Sanitized local Markdown links with spaces/angle brackets; errors have persistent user guidance.

## Timing and evidence so far

| Turn | Outcome | Latency | Dynamic tool calls / failures |
|---|---|---:|---:|
| Six-image clarification | completed; no SU editing | 311.203 s | 0 / 0 |
| Parameter plan | completed; no SU editing | 267.641 s | 0 / 0 |
| First execute | timeout after revision 4 | ~900 s | 27 / 3 |
| Continuation | revision 7, six views, saved SKP | 678.906 s | 24 / 1 |
| Interior check | timeout, continuity failure and Undo | 903.766 s | 14 / 3 |
| First archived-source recovery | rolled back due Entities.empty? compatibility bug | recorded locally | 4 / 1 |
| Successful archived-source recovery | new owned root, revision 1 | 307.844 s | 3 / 0 |
| Corrected incremental interior edit | same owned root, revision 2 | 639.875 s | 8 / 0 |
| Final six-angle readback | completed, no geometry changes | 454.844 s | 15 / 0 |

Provider region is Codex-managed and not exposed. Token usage was unavailable (null), not zero; no invented dollar cost. Tool counts exclude coding/command items. Failed runs remain part of the evidence. Initial developed output contains four elevations, low hip roof, glazing/frames, balconies, louvers, garage, stairs, partitions, basic furniture, pool, retaining terrain, road and sparse planting. It has substantial fidelity differences in materials, landscape, entry/garage and the approved terrain inference. Formal Direct-Codex parity and commercial first-run readiness are not accepted on this test alone.

## Recovery and corrected continuous editing

After the continuity failure, a full archived source (not outer-agent geometry) restored the developed building through the website. New root 111487 / revision 1: 307.844 s, 3 dynamic calls, no failures. A subsequent edit used a separate patch, the same script_id and root, and reached revision 2: 639.875 s, 8 dynamic calls, no failures. Stair supports, roof-directed extra flights, landing gaps, partition collisions, door leaves and bathroom access were corrected. A real interior stair view and exterior panorama were inspected; exterior remained developed. This is evidence that the repaired incremental route works, not evidence that the earlier root loss never happened.

The earlier manual SKP backup was taken too late and also contained the empty state. Recovery therefore used the preserved complete generated script. New pre-turn backups pair the model with its Ruby-state snapshot and guard owned roots before overwrite. Recovery views/downloads are refreshed and pending native-dialog recovery is tracked, rather than treating every recovery-named file as already restored.

Final six-angle readback was completed and inspected. The repaired recovery button was exercised on the actual generated model: native opening timed out on a SketchUp save dialog, then succeeded after handling that dialog and clicking the website button again. The restored building retains root 111487 / revision 2 and the matched Ruby-state snapshot. Specific Chinese guidance now explains this manual step; fully unattended recovery is not accepted.

The website SKP download completed (836,594 bytes), with SHA-256 matching the project artifact: `3e033535e0ef16383cf6660b247f3fe8521f1d0de2837da3c7b8b60cbe151281`. Historical gallery images include failed/intermediate views and must not all be treated as final-model screenshots. Final screenshot stays ignored locally. Tests: 103 passed, JS syntax and diff whitespace checks passed.

Next review should prioritize shorter bounded model turns, visible tool progress and native-dialog recovery before broadening scope. These remain observed product gaps, not additional milestones implemented here.
