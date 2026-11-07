# K Studio R3 cloud control plane — candidate deployment

The current operator contract is [ENVIRONMENT.md](ENVIRONMENT.md); sanitized values
are in [environment.template](environment.template). Copy the template into a private
host file, protect it, then use `deploy/ops.py --env-file ...`. Source packages exclude
all `.env` files. This is implemented candidate engineering, not a live commercial launch.

Only `cloud.main:create_app` and `website` belong behind the HTTPS proxy. Never expose
local `app.main` or the SketchUp connector. Compose does not publish PostgreSQL's port.
Schema **3** migrates earlier data without dropping account/order history.

## Deployment gates

1. Configure the approved server/domain, DNS/TLS, private secret mount, database password,
   session secret and exact source SHA/image. Database and credentials stay private.
2. Configure the real Authing OIDC client and its phone/WeChat channels. The callback is
   exactly `https://DOMAIN/auth/callback`. Authlib checks signatures/state/nonce and PKCE;
   recent authentication uses signed IdP auth_time. Device login uses outbound HTTPS.
   There is no local password table or fabricated SMS/WeChat success.
3. Keep registration/platform/payment/download switches closed until their actual gates
   pass. Confirm real pricing, provider terms, public operator/privacy/refund/support
   information and release/signing/license/clean-Windows evidence.
4. Run `python3 deploy/ops.py check --env-file PRIVATE --commercial`, then `deploy` with
   the same arguments, followed by `health` and `audit`. Deploy refuses a dirty/mismatched
   checkout. It builds app/migrate/maintenance, migrates, and starts app/proxy/maintenance.
5. The maintenance worker runs every minute with a PostgreSQL advisory lock: recover
   unstarted stale reservations, reconcile already verified payment inbox events and audit
   balances. Unknown dispatched calls are held for reconciliation, never automatically
   replayed. Connect actual alerting for audit failure, old pending work, webhook failure,
   disk exhaustion and failed backups. No external alert service is claimed configured.
6. R3 implements WeChat Native checkout/callback/refund routes and durable verified-event
   recovery. Real eligible merchant verification is still required. Synthetic signed SDK
   tests are not real payment acceptance. Stripe remains a separate existing adapter.
7. Validate real first login, BYOK consent/sync/revocation, platform metering, merchant
   callbacks, signed installer, first SU model and native download/reopen before opening Beta.

This Windows host has no Docker; local Compose execution is **NOT_RUN**. CI builds and
isolated container smoke may be run independently; use the actual run artifacts for
that commit. Neither source packaging nor container smoke means production was deployed.

## Backup, restore and rollback

```sh
python3 deploy/ops.py backup --env-file PRIVATE --output /private-backups/new.age
python3 deploy/ops.py restore-drill --env-file PRIVATE --archive /private-backups/new.age --target-db kstudio_restore_20261107
python3 deploy/ops.py rollback --env-file PRIVATE --previous-image VERIFIED_PREVIOUS_IMAGE
```

Backup uses **pg_dump inside the private Compose db container**, piped into official age.
Only Python and age are needed on the operator host, not a published DB port or host PG
password file. `KSTUDIO_BACKUP_RECIPIENT` is the age public recipient. Restore uses a
separately controlled `KSTUDIO_BACKUP_IDENTITY` host file. Optional
`KSTUDIO_AGE_EXECUTABLE` names the host age executable.

Archive publication is exclusive; no old archive is overwritten. Restore fully verifies
the age ciphertext before SQL, creates a NEW explicit `kstudio_restore_*` database,
restores in one transaction and verifies all tables, balances and every vault credential.
An existing target is refused, never dropped. Failure preserves the independent database
for investigation. Temporary plaintext is removed after restore, in a private directory.
No restored database is automatically switched into production.

Vault master keys and age identities are NOT in the database archive. Keep every required
vault version, backup identity and operator configuration in separately protected recovery
storage. Without those keys, encrypted records cannot be recovered. Snapshot backups do
not include native SKP, footage or WAL/PITR. Configure actual offsite retention, schedule,
RPO/RTO and recovery contacts; this candidate never prunes earlier backups automatically.

Rollback changes app/maintenance images, preserving volumes. Confirm schema compatibility
before rollback. Do not restore an older database over new orders to revert application code.

The real local PostgreSQL17.11/age/vault/payment-inbox drill and its preserved failures are
recorded in [R3 backup/restore evidence](../docs/execution/KSTUDIO_R3_BACKUP_RESTORE_20261107.md).
The test-only server is loopback and uses synthetic identities/payments. It must never be
used as production; local timing is not a production RTO guarantee.

## Configuration examples — synthetic, disabled values

Prices (not a sales offer):

```json
{"version":"owner-confirmed-price-id","byok_service_enabled":false,"byok_task_units":5,"packages":{"example":{"label":"Example","amount":100,"currency":"cny","credits":100}}}
```

Models (enable only after actual provider acceptance and price confirmation):

```json
{"deepseek":{"enabled":false,"verified":false,"protocol":"chat-completions","base_url":"https://provider.example.invalid/v1","upstream_model":"provider-model-id","key_env":"KSTUDIO_BAI_PLATFORM_KEY","max_output_tokens":8192,"reservation_units":100,"daily_units":1000,"turn_budget_units":300,"max_turn_requests":30,"price":{"version":"owner-confirmed-price-id","service_units":5,"input_units_per_million":100,"output_units_per_million":200}}}
```

Only the server supplies endpoint/model/key environment. The browser cannot obtain the
platform key. Stable `X-KStudio-Turn-ID` carries one visible turn across model calls and
subagents; budget ceilings are enforced server-side across session restarts. There is no
silent provider fallback. Unknown usage stays unknown. A provider error after possible
dispatch is not automatically retried. Server DNS/private-address checks complement, but
do not replace, deployment outbound firewall/DNS controls. Use one worker pending actual
multi-worker rate-limit qualification.

## Desktop and personal keys

Configured fresh cloud desktops start with platform mode and an explicit login/model
selection path; standalone existing owner installs retain BYOK. Cloud login never exposes
local modeling tools to the website. Each account receives isolated project and DPAPI key
storage. Switching while modeling or an unknown native write is active is refused.

Personal cloud Key storage requires explicit consent. AES-256-GCM AAD binds user, record
and key version. Lists/metadata exports contain no Key. Recent browser authentication and
an explicit selected device issue a one-use 120-second restore grant; the device must
confirm local restore and is not automatically switched to that Key. Deleted/replaced
cloud records revoke stale local synced copies on next validation. Ordinary login does
not silently download all credentials. Private-data deletion revokes sessions/vault data
while explicitly retaining financial/audit records; it is not a complete legal account erasure.

## Container engineering check and remaining external inputs

`.github/workflows/r2-cloud-container.yml` is the retained CI workflow name. It builds the
current Dockerfile in an ephemeral Ubuntu runner, without registry push or production
credentials. Build downloads dependencies; the running smoke has network disabled. UID10001,
read-only filesystem, restricted tmpfs, dropped capabilities and no-new-privileges are
checked. Actual image IDs and installed versions are recorded; mutable base tags are not
immutable supply-chain locks. Smoke covers schema migration, ledger and recovery plus
HTTP website routes; it does not assert real OIDC, merchant, model API or SU success.

Remaining external gates include approved hosting/domain and entity details, IdP channels,
eligible merchant credentials, approved pricing/provider terms, signing identity,
license/distribution clearance and independent clean Windows/SketchUp acceptance. Mainland
public hosting eligibility and applicable filing must be confirmed with the chosen provider;
never display a fabricated filing number or production status.
