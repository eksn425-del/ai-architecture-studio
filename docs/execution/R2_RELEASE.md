# R2 signed update / rollback implementation

The updater is separate from the desktop writer. `scripts/build_updater.ps1` builds
a standalone onedir `KStudioUpdate.exe` (Python is bundled). It is a candidate utility,
not a formally code-signed consumer installer. No production signing identity exists.

`scripts/release_cli.py install` verifies a signed Ed25519 envelope against independently
provided pinned public keys. It never fetches trust keys from the manifest URL. A public
distribution must embed/review those pins through its independently trusted installer;
the local `--trusted-keys` argument is for controlled candidate operations. Local test
key generation always labels trust `LOCAL_TEST_ONLY` and cannot authorize stable.

Verified fields include schema/platform/channel, UTC-aware expiry, SHA256/exact size,
version/monotonic sequence, minimum updater schema/current sequence and data schema 1.
Stable additionally requires a passed acceptance declaration, formal Authenticode
declaration **and an actual Windows Authenticode validation against a pinned publisher
certificate thumbprint**. A manifest string alone does not prove publisher signing.

Network downloads use HTTPS-only pinned hosts, public DNS destinations and a validated
redirect chain. No environment proxy/auth is inherited. Interrupted artifact bytes
are retained in the install-owned download cache and resumed by HTTP Range; the final
full signed digest is always checked, so mixed/changed server contents cannot activate.

Installation takes OS locks shared with the real desktop profile/runtime plus an
installer lock. Active work defers update rather than killing processes. Separate
runtime profiles must be passed explicitly with `--runtime-dir`. Legacy uninstrumented
applications must be closed normally before adopting this candidate.

ZIP entries reject path traversal, Windows reserved device names/ADS/trailing-dot or
space aliases, duplicates, links/special files, installer/data-owned paths and oversized
expansion. Existing immutable version directories are never overwritten. The staged
inventory is hashed and verified again at activation/rollback. A corrupt stage does
not replace current.json. User projects and encrypted API profiles remain outside
version directories and are not migrated or deleted.

Atomic current/previous pointers retain the old program, and a separate high-water
sequence prevents rollback from resetting anti-replay. Rollback changes code only;
unknown data migrations are rejected. `launch_installed.ps1` reads the selected version
under the same installer lock and passes the unchanged `--data-dir` to KStudio.exe.

## Local candidate commands

```powershell
# Packaging (fresh E-drive output directory)
./scripts/build_updater.ps1 -PythonExecutable PYTHON -OutputRoot NEW_E_OUTPUT
# The whole onedir folder must travel together. No Python install needed afterward.
./KStudioUpdate.exe install --manifest SIGNED_JSON --archive CANDIDATE_ZIP --trusted-keys PINNED_PUBLIC_TRUST_JSON --install-root INSTALL_ROOT --data-dir EXISTING_PROFILE --channel candidate
./KStudioUpdate.exe rollback --install-root INSTALL_ROOT --data-dir EXISTING_PROFILE
```

Signing test metadata is supported by `test-sign --archive ZIP --output NEW_PRIVATE_DIR
--version NAME --sequence NUMBER`. Its private key and test trust stay private/local;
they must not be mislabeled as the production publisher identity. The offline test
URL is deliberately invalid; use `--archive` for this local-only path.

## Verification

Tests in `tests/test_release_channel.py` (15 passing) exercise signature tamper, expiry, channel,
integrity, minimum baseline, traversal/Windows aliases, failed-stage cleanup, actual
OS busy locks, installed file tamper, update/rollback/data preservation, retained
anti-replay sequence, redirect policy and full-hash resumed download. Local fixture
tests are not clean-machine desktop compatibility or public HTTPS distribution proof.
Formal Authenticode credentials, production trust bootstrap, hosted signed channels
and independent Windows/SU acceptance remain release gates.

Packaged updater fixture drill is in `deploy/updater_drill.py`; it invokes the actual
standalone EXE. The local fixture receipt is under the R2 E-drive job root at
`updater-fixture-drill-02/receipt.json`: busy lock refusal, safe repeated install, two immutable version slots,
rollback, unchanged profile hash and installed launcher passed. This used a synthetic
archive, not a real desktop modeling acceptance. Pass `--archive REAL_CANDIDATE_ZIP`
to repeat against the built desktop artifact. Do not copy its private test signing key
into releases. `--desktop-shortcut` is opt-in and preserves the prior desktop link.

Current built updater: R2 job root `updater-build-retry-safe/dist/KStudioUpdate/`.
The whole folder is required; EXE SHA256 is
`a520076f12e2dde208689b275e7c1bbfa19319eade056d6ea8c678aa38d72a40`.
Bundled Python/cryptography/cffi/PyInstaller license texts are under `licenses/`.
Windows reports the EXE `NotSigned`; it is not a formal publisher certificate.

## Actual bundle dependency and license evidence

`scripts/collect_release_licenses.py` supplements the file-hash release inventory.
Run it with the exact build interpreter, actual bundle, its PyInstaller Analysis TOC,
and any separately installed SDK site directory. It copies only recognizable license,
copyright, notice and authors texts, retaining original bytes and SHA256. npm nested
dependencies are attributed independently. Python components hidden in PYZ are matched
against exact distribution-owned source files from the build TOC. Environment packages
without a shipped file/metadata match do not enter the bundled dependency list.

```powershell
& BUILD_PYTHON scripts/collect_release_licenses.py --bundle ACTUAL_ONEDIR --analysis-toc Analysis-00.toc --output FRESH_E_EVIDENCE --sdk-site SDK_SITE --node-license NODE_LICENSE --node-version 24.22.1 --project-license LICENSE
```

Outputs include CycloneDX 1.6 JSON, component/evidence inventory, original license texts,
an exact observed bundled Python version list and a separate build environment snapshot.
Neither version list is a resolver or source hash lock. Absolute private environment
paths, direct_url metadata, keys and unrelated configuration are not exported.
Missing texts/declarations, reciprocal license declarations and native binary vendor
notices remain explicit review items. This is evidence collection, not legal clearance.

Four collector tests pass, including supplemental source hash tamper rejection.
`scripts/fetch_license_supplements.py` can retrieve absent npm license texts from the
exact public registry gitHead, plus explicitly identified official Python release
tags. Failed lookups remain missing; it never substitutes the current default branch.
Pass its `supplements.json` via `--supplements` to merge verified source bytes/provenance
into a fresh inventory. No downloaded package is installed or executed.

The actual frozen updater and its TOC were inspected in
`updater-sbom-01`: five components, ten license texts, no missing component text and
59 native binary entries requiring vendor notice review. This updater-only receipt
does not substitute for collecting the final desktop bundle.

Final desktop `build-r2-03` evidence is `desktop-sbom-03`: 656 observed components,
851 original license/notice texts, 93 observed Python pins, 14 components with missing
texts and 181 native binary entries requiring vendor-notice review. The corrected SDK
distribution metadata identifies `deepseek-harness-sdk==0.2.1rc2` and preserves its MIT
text; DSH is `0.2.1-rc.5` and Node is declared `24.22.1`.

`scripts/export_release_notices.py` exported `third-party-notices/` into that real
bundle: 855 files, 4,338,047 bytes. It includes the public CycloneDX SBOM, component
versions/declarations, source text hashes, verified public source references, original
texts and bundled-version list. The build-source file map and full build-environment
snapshot remain private in the external evidence directory. Public notices were
scanned for personal Windows user paths/name and Codex storage paths with no matches.
Missing license texts remain `REVIEW_REQUIRED`; this is not complete license clearance.

The real build-03 ZIP (425,651,232 bytes; SHA256
`d6eaeb044ee034b8958fbfeb9497d485dcd64005b5b7e33733b02e5d7c085e6c`)
then passed the actual frozen updater drill in `actual-updater-drill-03`: busy lock
refusal, two immutable installations of that same archive, safe repeated installs,
rollback, retained versions/profile and installed launcher. A separately copied,
same-size, one-byte-corrupted archive was rejected with current/versions/profile
unchanged (`actual-updater-corrupt-03`). The failed archive is retained privately.
This used explicit local test signing and is not a production signing/clean-PC claim.

Build-04 dependency evidence was regenerated from its actual bundle and TOC in
`desktop-sbom-04`. It has 656 components, 93 observed Python pins and 865 license-term
texts. Four of the previous 14 missing entries now have precise upstream or parent
package evidence; ten upstream originals remain absent and have **explicitly labeled
official standard terms** for the declared license. Zero absent text bytes must not
be reported as zero missing upstream originals or license clearance. Declaration,
copyright/scope evidence and original-gap flags remain in the public notices.

`binary-license-map.json` maps all 183 native files: 25 CPython, 75 Python distribution,
one Node and 24 npm files to collected notices; 52 Microsoft runtime/WebView files to
specific redistribution-terms review; four LGPL/MPL files to corresponding-source/
obligation review; and two first-party executables to publisher signing. There are no
unmapped binary engineering placeholders, but these mappings do not grant distribution
rights. Exact operational release gates are in `PUBLIC_BETA_BLOCKERS.md`.

## Real build-03 to build-04 upgrade, rollback and signed reissue

`actual-updater-upgrade-04/receipt.json` records the frozen updater operating on the
same installation/profile after real UI preparation of six pending projects, uploaded
references and an encrypted dummy API connection (no inference). All 37 protected
data files / 5,025,613 bytes retained exactly the same SHA256 at every stage. Browser
cache and OS lease files are excluded; project/settings/credential data are included.
The before-file manifest stays private, not in the public source or release archive.

Build-04 ZIP: 426,650,213 bytes, SHA256
`2024a64e10356e3661c628e9922b513a94e33e26ede88e262d27d8f4ec522927`.
Sequence 3 installed actual different code, then explicit rollback restored build-03
slot 1 while preserving highest sequence 3. The same build-04 ZIP was newly signed
with sequence 4 and a new immutable version name, then installed as final. This is
an explicit new test release number, not bypassing anti-replay or editing a pointer.
All four version directories remain. Every command returned success; no timeout or
weakened verification was used. Serial verification of ~70,000 files is slow: the
first actual upgrade took 325.797 seconds and rollback 507.265 seconds on this host.
This is a real installation-performance limitation, not a native modeling failure.

The executable changed from build-03
`3499df806444401a420d172882fc2b6caf876c5175fc300ea717c6d34db94268`
to build-04
`59e5ba64951f812806c79923429b1014c8e7b5a1d36055623ada84038b5c0647`.
Final installed version is `r2-internal-04-seq4`, highest sequence 4. The separate
desktop UI launch/restore check is performed after this updater receipt; the script
does not claim that GUI/native acceptance itself. Signing is still LOCAL_TEST_ONLY
and Authenticode unsigned, with no clean-machine or public-distribution claim.
