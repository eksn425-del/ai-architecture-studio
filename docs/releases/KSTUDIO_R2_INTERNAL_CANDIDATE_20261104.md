# K Studio R2 internal engineering candidate

Updated 2026-11-05. **Internal candidate, not an accepted public beta.** No new paid inference, public deployment, real charging or main merge occurred. Historical architectural source fidelity remains PARTIAL; this revision has no new paid image-modeling quality verdict.

Source review: [draft PR25](https://github.com/eksn425-del/ai-architecture-studio/pull/25), based on PR24. Packaged desktop code is `3e953b0384ab4e6779d20803aaa827cee25a9760`; `debe2a89f04616ebe4a98e719d1432e9d1239455` adds CI dependency/fixture corrections only. Official DSH Node0.2.1-rc.5, Python SDK0.2.1rc2 and Node24.22.1 are retained. The original K mark, green/warm white/gold palette, serif brand and client layout remain.

## Local artifacts

All artifacts are private owner deliverables under the project-relative `outputs/video-storage/jobs/kstudio-r2-20261104/`; they were not uploaded to public GitHub.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `KStudio-2026.11.04-R2-build04-internal-win-x64.zip` | 426650213 | `2024a64e10356e3661c628e9922b513a94e33e26ede88e262d27d8f4ec522927` |
| `deployment-artifact-04/KStudio-R2-cloud-website-source.zip` | 77545 | `5079dcd0c1fc29bee6192e01209d38412a8d53866730f09478e792fc465b072a` |
| `clean-windows-kit/KStudio-R2-clean-Windows-check-kit.zip` | 16366 | `074e53ccd0bac8218534dcb0e13d046db74855ddb92b06556df074fcdeed539d` |

The desktop ZIP is the complete portable application plus first-party connector; it needs the whole extracted directory. It contains no owner projects, API keys or Codex entitlement. SketchUp itself is not bundled. The cloud ZIP is deployable **source**, not a container image or deployed website. The clean-Windows kit runs with Windows PowerShell5.1 and requires no Python or Codex on a tester's machine.

The separate frozen updater is `updater-build-retry-safe/dist/KStudioUpdate/`; keep that whole folder. Its EXE SHA256 is `a520076f12e2dde208689b275e7c1bbfa19319eade056d6ea8c678aa38d72a40`. Test manifest signatures are deliberately distinct from production Authenticode and production update trust.

## Verified behavior

- Windows core regression: **1653 passed, 20 skipped**. Ubuntu CI: **1687 passed, 46 skipped**; untouched main retains three known failures. All three remote checks passed on `debe2a8`. These environments/counts overlap and must not be added together.
- Actual official SDK two-protocol HTTP fixtures cover tool returns, session resume, interruption, cancellation, retry, subagents and compaction. Optional finite-batch middleware persists dispatch limits across processes/restarts; ordinary BYOK does not enable it.
- Actual packaged EXE initializes SDK/Node/tools without inference. A real client UI saves an encrypted dummy API, and six new project/source uploads are prepared without submitting conversations.
- Final installed `r2-internal-04-seq4` opens from the distinct **K Studio R2（内部候选）** desktop shortcut. Old shortcuts are preserved. Actual build03→04→rollback03→04 retains all37 protected profile files/5,025,613 bytes unchanged. After the update, real UI restores the dummy API and removes it, retains all six source projects, passes connector health and leaves one process after repeated activation. Large-file inventory checks are slow: observed rollback507.265 seconds.
- Uploaded PNG is losslessly normalized: its byte SHA differs from the retained original, but all six uploads have identical bytes and exactly the same768×1024 decoded RGB pixels as the original. The failed initial raw-byte-equality assertion is retained; it is not an image-cropping or loss-of-detail PASS-by-assumption.
- The packaged first-party RBZ was installed through SU2024 Extension Manager; installed files match its bytes. SU normal restart automatically restores connector health without a Ruby command. Only SU24.0.484 has current native evidence; other detected years are not supported-version claims.
- Six native fault cases preserve commit truth. An actual browser-downloaded engineering SKP reopens with matching deep geometry/material fingerprints; a scoped edit on an imported owned copy changes only its intended part. This is not model-driven architectural fidelity acceptance.
- Real local account/device UI, PostgreSQL integer ledger/concurrency and encrypted backup/isolated restore passed. Identity/payment services used signed fixtures, not real merchant or production accounts.
- New website routes and layouts passed local browser checks. The final cloud source archive was independently extracted, hash-checked, migrated twice, audited and served with feedback persistence; unavailable auth/payment/download remain disabled.
- Actual Docker image construction and restricted non-root/read-only/network-none execution passed [GitHub container run41871824820](https://github.com/eksn425-del/ai-architecture-studio/actions/runs/41871824820) at source007511c8. Real HTTP, SQLite migrations/audit and feedback persistence ran inside the image. No image registry push, public deployment or real external identity/payment occurred; this separate check does not replace the local PostgreSQL evidence.

Exact receipts and limitations: [acceptance ledger](../execution/PUBLIC_BETA_ACCEPTANCE.md), [release mechanics](../execution/R2_RELEASE.md), [connector evidence](../execution/R2_CONNECTOR.md), [execution boundary](../execution/R2_EXECUTION_BOUNDARY.md).

## Remaining public-release gates

Real paid model/image benchmarking, a genuinely clean second Windows installation, additional individually qualified SketchUp versions, production signer and update trust, real domain/hosting/IdP/merchant/pricing and operator terms remain unverified. No phone/WeChat/QQ channel, WeChat Pay or Alipay integration is claimed.

Dependency notices contain656 components/865 texts and map183 native binaries. Ten upstream packages lacked original license texts; their declared official standard terms are explicitly labeled, not presented as recovered originals. Microsoft redistribution terms, LGPL/MPL corresponding-source duties, upstream license-scope ambiguity and first-party release terms still require resolution. **Legal clearance remains REVIEW_REQUIRED.**

Production tools restrict exposed file/process/MCP operations, but arbitrary Ruby executes inside the user's SketchUp process. **There is no OS sandbox for that Ruby.** No construction-document, structural or regulatory certification is claimed.

[External steps](../execution/PUBLIC_BETA_BLOCKERS.md) supplies exact commands and required inputs. [Prepared finite modeling batch](../execution/R2_FINITE_TEST_BATCH.md) is awaiting authorization; its six projects are prepared, not tested. Source images and historical models are preserved.
