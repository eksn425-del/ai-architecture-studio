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
