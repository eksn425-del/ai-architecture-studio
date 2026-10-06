# Windows continuation — 2026-10-06

## Latest update: GitHub transport and installed credential persistence repaired

User then requested a single DeepSeek default. Source browser now exposes only DeepSeek V4.1 Flash password/save-as-default/remove; [empty-Key settings screenshot](deepseek-default-settings.jpg) contains no credential or private project history. Fresh DOM inspection confirmed no provider/effort selectors, “尚未配置” state and disabled remove button. Cache version was bumped after finding browser cached previous JS with the new HTML. Windows DPAPI test additionally verifies blank-password resave after restart keeps the saved credential. Full suite 204 passed/2 skipped; no live paid inference. Account cloud sync and distributed platform-owned presets are not implemented in this local milestone.

Rebuilt the frozen package, synchronized its final static resources, reran actual EXE fake-Key save/restart/remove smoke successfully, installed the versioned package and updated desktop shortcut. Installed static JS hash matches source; shortcut defaults to standalone DeepSeek. JavaScript syntax and four credential tests passed. Public screenshot shows only the empty configuration window; real user Key was not entered by the agent.

Git used direct HTTPS while Windows had a working local Mihomo HTTP proxy. A command-scoped proxy restored pull; then a repository-local GitHub-only proxy setting restored normal pull/push/remote SHA verification. This machine setting is not committed, does not change Windows networking or the model API route, and depends on that local proxy remaining available. Previous continuation commit `7aaa92d` was pushed and confirmed on origin/main.

The desktop shortcut still targeted an October 4 frozen package. Archive inspection proved `app.local_credentials` was absent there, despite updated repository source. This establishes a concrete cause of repeated credential loss in the installed app. Rebuilt the current PyInstaller desktop package; added `scripts/install_desktop.ps1`, which checks the frozen credential module, installs a versioned folder, preserves previous builds/data, and updates the desktop shortcut with a shared data directory and standalone DeepSeek default. Installed locally; original projects and runtime junction preserved. Old packages/root EXE remain available for rollback but are not the desktop shortcut target.

Actual frozen EXE validation used a separate disposable profile and a fake Key, never a real credential or provider call: start EXE → POST local model settings → assert encrypted file exists and contains no plaintext fake Key → terminate only test EXE → launch same EXE/profile → confirm configured model/effort restored without exposing Key → remove saved credential → assert file removed. All assertions passed. The updated installed app started and reports ready, `deepseek/deepseek-flash`, `windows-dpapi`, no restore error. Its real credential remains unconfigured: an old memory-only Key cannot be recovered. User must enter it once in the updated app before paid reconstruction resumes; real-Key restart/inference remains pending.

Latest validation: PowerShell installer syntax parse passed; actual install/shortcut preservation passed; full repository suite **204 passed, 2 skipped, 2 dependency warnings**. No new villa inference/quality pass claimed.

## Earlier blocked continuation (historical)

Local baseline: `5a76e73`. Two `git pull --ff-only` attempts failed connecting to github.com:443; latest remote state could not be confirmed. No modeling implementation was changed during this continuation.

## Completed local evidence

- Previous continuation executed the adopted SAIE helper inside a dedicated blank SketchUp 2024 model through the existing Kongxing bridge and ProjectRubyExecutor.
- String-key millimeter parameters: centerline `[[10000,8000],[0,8000]]`, thickness 200, height 3200, elevation 0. A positive-Z face-normal assertion passed.
- [Sanitized transaction readback](owned-wall-smoke.json): before had zero owned children; after had one unlocked `QA_REAR_WALL`, persistent ID 37845. XYZ bounds min `[0,7900,0]`, max `[10000,8100,3200]`, size `[10000,200,3200]` mm; `truncated=false` in both snapshots.
- Returned to the existing dedicated six-view benchmark model. This was an engineering helper smoke, not website-generated villa reconstruction or visual quality acceptance.
- Repository suite at this baseline: 204 passed, 2 skipped, 2 dependency warnings. Windows DPAPI targeted rerun: 4 passed, using fake credentials in isolated test directories, no paid API call.
- Local service restarted on port 8787; dedicated six-view model and live MCP identity were verified. Provider status shows `credential_configured=false`, `credential_restore_error=false`, storage `windows-dpapi`.
- Repository, installed application and default desktop profile had no saved `provider.dpapi` file. Installed application runtime junction resolves to the repository runtime, so these two profiles are not separate credentials stores. No secret was read or logged. Real-key persistence remains unverified until the user configures this updated build and restart is tested.

## Incomplete gates

- Six-view repair through the same DeepSeek route, source-matched screenshots, unchanged unrelated IDs, download/reopen/actual edit remain pending. Existing [villa quality failure](../2026-10-05/README.md) is unchanged.
- Clipboard automation timed out before a visible pasted attachment; this is inconclusive, not proof of a product regression or a pass.
- Actual browser stale-plan invalidation and checkpoint recovery remain pending; automated tests do not replace them.
- Clean new-computer installation remains `pending_external`.

## Next reproducible actions

1. Restore GitHub connectivity, pull latest main and reread CURRENT_TASK before code changes.
2. User enters DeepSeek Key locally. Verify encrypted file existence and provider status without exposing the Key, then restart and verify restoration.
3. Repair existing six-view wall units, window counts and roof through the website; compare real views, then verify local edit IDs and reopened SKP editability.
4. Complete remaining browser gates, publish sanitized evidence and push/verify the final remote commit. No private SKP, machine path, account or credential is included here.
