# K Studio cloud control plane — candidate deployment

Current R2 operator input table and exact source/Compose startup, migration and
restore commands: [ENVIRONMENT.md](ENVIRONMENT.md). The sanitized source ZIP omits
all `.env` files (including examples); create the private environment from that
table. Container images remain **NOT_BUILT** until the target host builds and tests
them. Source packaging is not public deployment.

This is a separate service from the local SketchUp writer. Do not expose `app.main`
or the connector on a public address. Only the cloud service and website sit behind
the TLS reverse proxy. The PostgreSQL port is never published by Compose.

1. Provision an approved server/domain, PostgreSQL storage and secret store. Review
   hosting eligibility and merchant eligibility before production. Copy `.env.example`
   into private `.env`, use unique secrets and URL-encode the DB password. Never commit it.
2. Configure a mature OIDC provider's discovery URL/client. Register exactly
   `https://YOUR_DOMAIN/auth/callback`; authorize only the intended redirect. Authlib
   performs state/nonce/ID-token validation and PKCE S256. Registration/password recovery
   remain at that provider. No local password table or fake public login exists.
3. Keep `KSTUDIO_PRICES_CONFIRMED=0`, empty platform models and no payment credentials
   until prices, upstream terms and payment account are actually approved. OIDC can
   operate independently. Confirmed integer credit rules use a versioned JSON price table.
4. In this directory: `docker compose --profile maintenance run --rm migrate`, then
   `docker compose up -d app proxy`. Verify `/health/ready` and `/api/public/config`.
   This environment did not have Docker; these container commands are **NOT_RUN**.
5. Configure outbound firewall restrictions, alerting and a scheduled
   `python -m cloud.cli recover-stale` (every minute, stale age 15 minutes). A crash
   before dispatch releases its reservation. A possibly dispatched call stays pending
   reconciliation; there is no automatic billed request replay. Run `cloud.cli audit`
   daily and alert on inconsistent balances, pending jobs older than 15 minutes,
   webhook non-2xx, unavailable DB and disk/backup failures.
6. Test official merchant **test mode** checkout and signed callbacks with that
   merchant's own sandbox. Unit fixtures using the official SDK do not satisfy this.
   Stripe is an adapter candidate, not a claim that the operator is eligible for a
   Stripe account. WeChat/Alipay domestic merchant adapters are not delivered here.
7. Only after staging gates pass, prepare an explicit production change with DNS/TLS,
   operator IdP/admin subject, published terms/privacy/refund/support/contact, confirmed
   prices and signed/reopen-verified desktop artifact. Production promotion was not run.

## Backup and restore

`backup.sh NEW_ARCHIVE.age` uses pg_dump custom format and age encryption. Supply DB
credentials via protected PGPASSFILE, and the backup public recipient via
KSTUDIO_BACKUP_RECIPIENT. Keep the private identity offline/separately controlled.
Store encrypted backups on a second approved storage location; test retention before
adding automated pruning. The candidate does not delete old backups.

For a drill, create an empty `kstudio_restore_*` database, set PGDATABASE to that
isolated target, set KSTUDIO_BACKUP_IDENTITY to the private identity path and run
`restore.sh ARCHIVE.age`. The script refuses other DB names or nonempty targets.
Then use its database URL with `python -m cloud.cli audit`, compare counts and actual
sample account/task/order records, and exercise login + pending-task reconciliation.
Never overwrite production to test restore. A rollback restores the prior app image;
schema 2 adds session refresh columns/indexes without deleting existing data. Do not
roll back data by silently restoring an old snapshot.

The local Windows PostgreSQL 17.11 encrypted restore drill is implemented in
`python -m deploy.restore_drill --bin PG_BIN --output NEW_PRIVATE_DIRECTORY`.
Its test-only trust-auth server is loopback:55439 and MUST NOT become a deployed
database. It generated synthetic identities/payments only. Measured local snapshot
restore time is not a production RTO guarantee. Production RPO depends on the chosen
backup/WAL schedule, and is currently unconfigured.

## Configuration examples — synthetic values only

Prices (not a sales offer):

```json
{"version":"owner-confirmed-price-id","byok_service_enabled":false,"byok_task_units":5,"packages":{"example":{"label":"Example","amount":100,"currency":"usd","credits":100}}}
```

Models (enabled only after actual provider acceptance):

```json
{"deepseek":{"enabled":false,"verified":false,"protocol":"chat-completions","base_url":"https://provider.example.invalid/v1","upstream_model":"provider-model-id","key_env":"KSTUDIO_PLATFORM_PROVIDER_KEY","max_output_tokens":8192,"reservation_units":100,"daily_units":1000,"price":{"version":"owner-confirmed-price-id","service_units":5,"input_units_per_million":100,"output_units_per_million":200}}}
```

Only the server supplies endpoint/model/key env. The browser cannot supply an upstream
URL or obtain its key. No redirects or environment HTTP proxies are followed. DNS
private-address denial is defense in depth; deploy outbound firewall/DNS controls.
One platform task per account runs at a time. Per-request reservation and output caps,
daily integer-credit cap, timeout, and per-process request rate limiting apply. Run
one worker until a distributed rate limiter is introduced. No auto retry after a
possibly billed dispatch, including ambiguous 429/5xx/timeouts; usage stays unknown,
never fabricated as zero. Admin reconciliation requires an allowlisted OIDC subject
and a traceable provider invoice reason. Full refunds with unspent credits reconcile;
partial/spent-credit refunds require operator handling and are not a complete refund UI.

## Hosting eligibility evidence (checked 2026-11-04)

Alibaba Cloud documents that public mainland-China hosting requires ICP filing through
the service provider; Hong Kong/overseas nodes do not use that filing route. This is not
a conclusion that a particular K Studio operator/business is approved. Determine the
operator's legal entity, commercial-service requirements, domain registration and data
handling with the selected provider before publishing. Do not display a made-up filing
number, merchant identity, payment success or production status.

- https://help.aliyun.com/en/icp-filing/basic-icp-service/user-guide/icp-filing-application-overview
- https://www.alibabacloud.com/help/en/icp-filing/basic-icp-service/product-overview/icp-filing-requirements-for-a-regular-website
- https://docs.stripe.com/webhooks
- https://docs.stripe.com/api/checkout/sessions/create
- https://www.postgresql.org/download/windows/

## Remaining external inputs

Server/domain and approved region; real operator identity/filing/contact; an OIDC client;
eligible payment merchant test credentials and signed webhook secret; approved final
prices and operator platform API credentials/terms; production code-signing identity;
an independent clean Windows/SU machine. These are not bypassed with local fixtures.

## Desktop connection

Set the desktop's operator-owned `KSTUDIO_CLOUD_PUBLIC_URL` to the same approved HTTPS
origin. Its existing account panel starts device authorization, opens the normal
website and polls outbound HTTPS. No desktop inbound port or callback is exposed.
The existing BYOK key vault is independent from cloud DPAPI credentials. Selecting a
platform model does not overwrite any saved BYOK key. Normal cloud login never grants
the website access to native modeling tools.

Schema 2 migrates schema 1 sessions by adding nullable refresh-hash/expiry columns and
indexes without removing data. Device refresh uses a single-use rotating secret with
a 30-day absolute term and stable device revoke ID. Access tokens last one hour.
If refresh delivery is uncertain, reauthenticate rather than reuse a consumed proof.
BYOK service charging remains disabled unless both prices and the separate service
enabled flag are explicitly confirmed. A paid policy must specify the task-lease fee,
one-hour validity and failure/cancellation terms before publication. The platform
test price table charges its service component per metered provider request; this is
not yet an owner-approved commercial pricing model or a promised per-building quote.
