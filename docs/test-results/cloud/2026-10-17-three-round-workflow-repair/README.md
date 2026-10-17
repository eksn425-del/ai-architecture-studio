# Three-round workflow repair

Base: `9a44706e7e4730944db218d363fe6a44c7a6eed0` on `trial/readiness-20261016`.
Observed SU acceptance report: `afc91f7fef6a7df594beb9737a98351eefc4df8e`, `docs/test-results/windows/2026-10-17-su-three-round-9a44706/`.

## Fixed and checked

- Requirements now have traceable active/resolved/superseded lifecycle. Same-direction refinements and equivalent descriptions need explicit prior identity/evidence instead of identical prose. Typed opposite intent remains rejected without a newer feature-specific user-approved design scope. Resolved constraints remain protected; omission is not resolution.
- The host captures the displayed follow-up plan, feature list and reference-byte/role/turn manifest. Approval requires the same normalized UTF-8 plan SHA, exact source manifest and current card. New plans and changed references invalidate old permissions. Initial/unscoped plans do not grant override permissions. Windows CRLF/CR and LF canonicalize identically in browser and Python. Independent Critic checks stale scope at entry and in flight.
- Explicit pause, stop, no-approval, discussion-only and plan-before-execute messages precede stale execution actions. Scoped KEEP instructions and approved direct edits remain executable. These are tested deterministic rules, not exhaustive natural-language understanding.
- Saving a new delivery requires a new persisted geometry revision in the current turn. An old revision plus failed/read-only calls no longer creates a new successful candidate. Prior models remain available; no-op status is explicit.
- UI readiness uses recorded responses matching the current project/provider/model/effort. Connection-dialog stale callbacks/cancellation/project switches are guarded. Results open only from host geometry/checkpoint flags. Scoped plans are shown before approval; failed loads and project changes clear approval hashes. A missing-project optional-chain error was also fixed.

## Real Blender verification

A deterministic assistant and Critic-envelope fixture exercised the actual K Studio HTTP conversation/tool pipeline and native Blender save/reopen across three rounds:
1. Create eight rail segments, a 2.740 m window, and a protected wall.
2. Display and approve a scoped dark-gray vertical-bar railing change (three separated bars per segment). All eight positions/heights and unrelated window/wall remain unchanged.
3. Display and approve window height 2.192 m, fixed 1 m lower edge, and 0.548 m upper infill. All rail segments and the protected wall remain unchanged.
Wrong approval hashes were rejected before provider/tool calls. Each native file reopened successfully. This checks integration, lifecycle and dimensions; it is not the original SU image, autonomous vision reasoning, or visual-fidelity acceptance.

## Limits and retained failures

- Original new SU reference, model, screenshots and raw arguments remain local to the owner and were not available for independent visual review. The original SU three-round case must still be rerun on the new code.
- Four reported invalid tool arguments have no confirmed schema defect in the available sanitized evidence. Existing validation remains. The uncertain script-token rejection was not reclassified or bypassed.
- Node UI regression tests and HTTP tests ran. A fresh normal cloud-browser smoke could not connect to the test server (`ERR_CONNECTION_REFUSED`); no fresh GUI pass is claimed.
- No external model calls, credentials, paid provider quota, deployment or main merge occurred. No private source images/models/raw logs are included in this publication.
- The legacy checkpoint test fixture was corrected to increment its simulated committed revision rather than claim a geometry write from tool-name strings. Separate zero-write/no-checkpoint regression remains.

See RESULTS.json for exact final test results. Code-review clearance is distinct from SU visual-quality acceptance.
