# R3 implementation checkpoint — 2026-11-07

Implementation continues on codex/kstudio-r3-launch-20261105, [PR27](https://github.com/eksn425-del/ai-architecture-studio/pull/27), preserving the R2 baseline, original installations/configurations/models and failed tests. Cloud account encryption/device restore, recent-auth, WeChat Native signing/ledger recovery, gateway budgets, website gates and deployment/backup operations are implemented. [Engineering evidence](test-results/windows/2026-11-07-r3-launch-candidate/README.md): local PostgreSQL 203 passed / 0 skipped; CI PostgreSQL 202 passed / 1 skipped and actual restricted Docker service passed. These are engineering results, not live Authing/customer payment/public deployment.

**Real local BYOK modeling is now PARTIAL, not NOT_RUN.** [Native evidence](test-results/windows/2026-11-07-r3-native-byok-delivery/README.md): actual K Studio UI and BAI DeepSeek Responses/Low built the text-only 12×8m two-storey pavilion to r8; beta01 failed its final host screenshot destination check after preserving geometry. beta02 core 802c4b2fe98de8bcd966f6c6cf7e99162f566fe7 fixed capture, resumed the pending plan with unchanged encrypted API settings, and completed the porch-only r9 edit. Ten protected groups retained identical deep geometry/material hashes. Actual UI download and SketchUp 2024 reopen passed byte/deep-hash equality. Railing detail and rear-wall/stair visual defects remain; no building-quality or regulatory PASS.

The paid test is stopped with **56 settled + 1 unknown provider attempts**. A provider stream first returned TRANSPORT Connection error with synthetic zero usage; the official SDK retry was refused by the host unknown-liability guard before another reservation. There was **no 58th provider dispatch**. Total usage/cost remain unknown, not zero; do not reset/replay the batch or continue paid work automatically. The subsequent diagnostics fix retains refusal details and the stop guard; offline regressions 26 Python + 7 Node passed without new paid/native calls. This fix is not a successful rail rerun.

beta03 core `790d7f099939228b9828a6524eeccf94f374f7be`, version **2026.11.07-R3-beta03 / sequence10**, is installed on E. Actual GUI installation, Start-menu startup and initial empty-API/account-state checks passed; all207 existing profile files remained present and201 small-file hashes were unchanged before startup. Host readback confirmed executable/data-dir/TEMP/TMP and six WebView profile paths on E. Program copy C→E verified140,911 files /2,190,840,011 bytes with complete SHA equality; old version slots and original R2 remain preserved. **Deleting the verified C program copy was rejected by automatic tool policy (`blocked by policy`); no deletion ran, and the C copy remains.** See [installer](test-results/windows/2026-11-07-r3-launch-candidate/receipts/installer-beta03.json), [runtime paths](test-results/windows/2026-11-07-r3-launch-candidate/receipts/runtime-on-e.json), and [migration result](test-results/windows/2026-11-07-r3-launch-candidate/receipts/program-migration-final.json). This is existing-PC acceptance, not clean-Windows certification.

**Public commercial Beta remains BLOCKED_EXTERNAL.** [Exact external inputs/resumption](execution/KSTUDIO_R3_EXTERNAL_INPUTS_STATUS_20261107.md). No real public URL/download, production identity/SMS/payment or customer charge is claimed. Local installation/verification is complete; C-copy removal is blocked by policy and production needs the listed external inputs; do not revive closed private building cases or promote local/fixture acceptance to production.

Historical material below retains its original scope.

---
# R3 launch handoff — 2026-11-05

## Work completed in this handoff

Reviewed PR25 at `7376f40f678e81618cbd9b470e2f5ba39debeaac`, installed build05c documentation and current cloud/auth/device/payment/deploy source. Prepared the [R3 launch execution book](execution/KSTUDIO_R3_LAUNCH_EXECUTION_20261105.md), [owner input sheet](execution/KSTUDIO_R3_OPERATOR_INPUTS_20261105.md), and [Codex startup prompt](execution/KSTUDIO_R3_CODEX_START_20261105.md). Engineering, QA and first-user-perspective reviewers checked the task for feasibility and bounded acceptance. This was source/document review, not a live first-user test.

Chosen route: Tencent mainland CVM + existing Compose/FastAPI/PostgreSQL/Caddy, COS distribution, Authing-hosted phone/PC WeChat via existing OIDC, WeChat Native payments, BAI platform plus account-owned BYOK. Preserve the existing desktop visuals and Agent runtime.

## Next owner: local Codex implementation

Follow the execution book end-to-end on an isolated R3 implementation branch. Finish all available work before presenting one consolidated external-input blocker list. No main merge, live deployment, production SMS/WeChat/payment, clean Windows test, new paid inference, or new installer was performed by this handoff. Actual environment resources and secrets must be supplied through existing authorized private configuration; never publish them.

The owner now authorizes launch implementation and deployment. Historical pause/no-paid/build04 text below is archival, not the active instruction. Applicable prior BAI test permission is preserved within its actual scope; never infer permission for unlimited cloud purchase, auto-recharge or customer charges. Installed R2 build05c remains an internal candidate until new acceptance actually passes.


**Implementation started 2026-11-07:** preserving the latest R2 build07 fixes and evidence below; R3 production remains NOT_DEPLOYED pending implementation and verified external inputs. Raw videos from the Nov7 simple-house test were subsequently deleted at the owner's request; historical hashes/screenshots/models remain, and that geometry case is closed.

---

# Latest 2026-11-07 handoff

Read [CURRENT](CURRENT.md) and [build07 evidence](test-results/windows/2026-11-07-progressive-building-and-recovery/README.md) first. One-time progressive-building batch complete; preserve root19/r7 and earlier r8. No paid loop. Internal candidate, not public-release acceptance. Historical handoff follows unchanged.

---

# Public continuation

**Owner update 2026-11-05:** keep the installed internal candidate and defer paid testing. Six prepared projects remain NOT_RUN; no paid request is authorized. Do not automatically resume the batch or repeatedly request permission. Earlier pending-authorization text below is historical.

Start with [CURRENT](CURRENT.md), [R2 candidate/artifacts](releases/KSTUDIO_R2_INTERNAL_CANDIDATE_20261104.md) and [execution](execution/PUBLIC_BETA_EXECUTION.md). The isolated branch now provides installed internal build04, real updater/data-preservation receipts, deployable cloud source, restricted-container CI and clean-Windows kit. Final public-beta acceptance is not established. Six same-source live-test projects await finite-batch authorization; no new paid inference occurred. Exact external actions are in [blockers](execution/PUBLIC_BETA_BLOCKERS.md). [2026-11-03 release notes](releases/KSTUDIO_LOCAL_CANDIDATE_20261103.md) remain the historical baseline. Preserve prior failures and do not transfer old model success to this revision. Private images/models/credentials/raw logs remain local.
