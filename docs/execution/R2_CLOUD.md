# R2 cloud execution receipt — 2026-11-04

Implemented in an independent `cloud` package; the existing local FastAPI writer and
its data remain separate. This is a locally tested candidate, not a live SaaS release.

| Area | Implemented and exercised | Remaining gate |
|---|---|---|
| Identity | Authlib OIDC state/nonce/PKCE S256; device approval + single-use PKCE redemption; DPAPI desktop tokens, rotating refresh, stable device revocation | Real operator IdP acceptance; deterministic signed IdP fixture passes |
| Database | SQLAlchemy real PostgreSQL schema and explicit migration, constraints, atomic wallet/ledger/task/order transactions | Deployed HA/managed DB/production monitoring |
| Billing | Integer reserve/settle/release, account scoped idempotency, concurrent-wallet lock, unknown cost pending reconciliation, server price snapshot, model/service split, daily cap | Final commercial prices and provider usage reconciliation feed |
| BYOK | Desktop gate before intent or Builder dispatch; default zero/unconfigured service fee, explicitly accepted paid rule obtains server lease; no upstream Key reaches cloud | Final fee policy and real production tenant |
| Payments | Official Stripe SDK checkout/idempotency and raw signed webhook verification, amount/environment/order binding, duplicate-safe credit and full refund | Real merchant test account/sandbox; partial/spent-credit refund operations |
| Platform gateway | Server whitelist, server-only key, Responses/Chat Completions SSE, output/reservation/daily limits, one active platform task per user, timeout, unknown-usage reservation | Real approved upstream protocol/model tests; production egress firewall |
| Recovery | Stale undispatched release vs stale dispatched pending; no automatic billable replay | Scheduled production worker and alerts |
| Website backend | Config/identity/usage/orders/devices/feedback/status routes and static site fallback; unavailable features honestly disabled | OIDC/payment production credentials and real signed release |
| Deployment | Isolated PostgreSQL/app/TLS proxy Compose, explicit migration, restricted build context, encrypted backup/isolated restore scripts | Docker/server/TLS not run here |

## Local evidence

- Dedicated cloud Python environment on E drive; requirements-cloud.txt contains direct
  pinned runtime packages. Cloud does not import the local SketchUp application.
- Portable PostgreSQL 17.11 official EDB archive downloaded from the PostgreSQL-linked
  vendor download page. Test cluster is bound to 127.0.0.1:55439, synthetic data only.
  Initial Windows Unicode-path initdb failed; verified E-drive ASCII junctions fixed
  that environment issue. No production DB was changed.
- 44 cloud/account tests pass on SQLite and actual PostgreSQL (59 including the 15 updater
  tests), not a dictionary ledger simulation:
  concurrent reservation/no overspend, concurrent idempotency, settlement, price snapshot,
  unknown usage, tenant isolation, CSRF (including malformed Authorization), revocation,
  payment signature/tamper/expiry/environment, duplicate callback/refund, transaction
  rollback, service-only BYOK, streaming mock usage, timeout/429, SSRF, recovery and PKCE.
- Local payment fixtures use a synthetic webhook secret and the real official SDK.
  They are explicitly **not** an official merchant sandbox acceptance result.
- PostgreSQL encrypted dump → new DB restore: exact users/tasks/orders/ledger rows
  matched; wallet audit matched. Counts 1 user / 1 task / 1 order / 3 ledger events.
  Schema 2 rerun also restored one session with refresh hash and one consumed device
  authorization exactly. Backup 0.250 s, restore 0.782 s on this small local fixture.
  Production RPO/RTO NOT_RUN.
  Evidence: `E:/K AI 产品建模网站/outputs/video-storage/jobs/kstudio-r2-20261104/cloud-pg-restore-drill-02/receipt.json`.
  Final combined JUnit: same job root `cloud-release-final.xml`. Private dump/backup key stay local.

## Honest limits

This code does not make the local app multi-tenant, expose a cloud SketchUp writer,
sell credits at provisional prices, enroll a merchant, claim WeChat/QQ/phone login is
connected, or turn a payment return URL into proof of payment. Website order status
comes only from the persisted server ledger. Missing usage is null/pending, not zero.
The real IdP/merchant sandbox, platform paid model call,
public DNS/TLS deployment and clean-machine acceptance still need their separate gates.
See `deploy/README.md` for the smallest real external inputs and exact launch/restore steps.

## Desktop bridge continuation

`app/cloud_account.py` is registered in the actual local workbench. Token/key values
are never returned to its web UI. The browser authorizes a named desktop request only
after the normal Authlib login. A 10-minute device code is bound to a random desktop
S256 verifier, consumed once and replaced by an access token (1 hour) and rotating
refresh token (absolute 30-day device term). Both persist with current-user Windows
DPAPI. Refresh invalidates both old tokens and keeps the device ID stable; revoking
that device invalidates refresh too. Server token hashes only are stored.

The platform option constructs the existing K Harness connection against the server's
OpenAI-compatible gateway, using only the user's device token. Upstream operator keys
stay server-side. Public model IDs are resolved to server-whitelisted upstream models.
The runtime uses request_retries=0; uncertain upstream calls remain reserved and block
further calls until reconciliation. Both streaming and non-streaming SDK requests use
the same gateway ledger. Cancelled streams without final usage remain pending, not zero.

BYOK keys stay in their existing DPAPI vault and call the chosen provider directly.
Charging is off by default, explicitly 0; no fake fee event is written. If an operator
publishes a paid BYOK service rule, the desktop requires explicit acceptance of that
price version and an online server-issued task lease before any intent/Builder call.
The rule is one lease per client conversation request, not a charge per local tool.
Retries recover the same lease; expired leases do not silently create a new charge.
An account/server failure cannot switch platform work to BYOK or another model.
Free local BYOK remains available offline if no paid policy was previously accepted;
accepted paid BYOK requires online authorization. Existing model files are unaffected.

The authorization check runs before read-only intent inference, not merely before the
main Builder. Proven pre-dispatch failures retain their failure history and can safely
retry the same request ID. All failures after dispatch retain the existing uncertain
receipt protection; they are never reclassified as safe retries.

`tests/cloud/test_desktop_account.py` exercises actual Authlib discovery, RSA/JWKS ID
token verification, state/nonce/PKCE, device approval, native Windows DPAPI save/reload,
expired-access refresh, old-refresh rejection, device revoke, both billing paths and
server model whitelist using a deterministic IdP/provider fixture. It makes no live
login, payment or paid model claim. Schema 2 adds refresh columns non-destructively;
run the explicit migration before restarting an existing cloud candidate.

Final standalone-startup regression found that the initial account bridge attempted
to load an empty account vault even when no cloud URL was configured. It now avoids
all account decryption unless a valid cloud endpoint and an actual account file are
present. A configured fresh installation also does not load credentials. The focused
launcher/provider-security regression passes all 36 tests. The final cloud suite
passes 54 SQLite/PostgreSQL tests including absent/unused-vault cases, corrupt native
DPAPI, malformed/mismatched account restoration and failed model-source persistence.
An unreadable or mismatched existing cloud account now blocks all model dispatch,
retains its original encrypted file and requests an explicit account/source choice;
it cannot silently become BYOK or assume an unknown old fee policy was free. A failed
source save restores the previous active router and mode. Receipts:
`launcher-boundary-final.xml` and `cloud-restore-final.xml` in the R2 job directory.
