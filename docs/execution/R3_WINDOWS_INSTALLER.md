# R3 Windows installer engineering — 2026-11-07

The mature installation shell is NSIS3.13, using its zlib compressor. The upstream [license](https://nsis.sourceforge.io/License) and [scripting reference](https://nsis.sourceforge.io/Docs/Chapter4.html) were checked. The supplied compiler ZIP was verified by the parent task (`ba63dffc4410ee89193e1cb5a41989991bd77c61068da17e3156d136b7b0b3d8`). The compiler is a build tool, not a runtime prerequisite for users. Its COPYING text is included with the installed product. This does not clear licenses for the entire frozen application.

`scripts/build_installer.py` inventories the actual frozen bundle, rejects links, private credential/model extensions and missing runtime/connector/native guard files, and generates exact NSIS payload/uninstall commands. It never embeds a user's data directory. Outputs must go to a new directory outside the bundle. The compiler produces one setup EXE and a size/SHA256 receipt. It always labels this build **unsigned internal candidate / public_release_ready=false**; code signing and public distribution clearance must be performed and separately evidenced before enabling a public download.

Normal install is per-current-user, no administrator elevation, fixed `%LOCALAPPDATA%\Programs\KStudioR3` with an independent `%LOCALAPPDATA%\KStudioR3` profile. Existing R2 installations/profiles are untouched. Windows x64 is required. No Python, Node, Codex, Docker, Ruby command entry or editing JSON is required of the installing user. The application still checks its actual WebView2 and legal SketchUp prerequisites.

The start-menu shortcut uses the existing stable version-slot launcher and `current.json`. A desktop shortcut is optional rather than silently replacing the owner's R2 icon. Repair reruns the same installer; installing a higher sequence creates a new slot and preserves older slots. A recorded highest sequence rejects older installers. Installing into an unrecognized pre-existing directory or a linked path is rejected. Uninstall uses only the generated exact file list and nonrecursive empty-directory removal; unknown files, older rollback slots, the separate profile, and tiny ownership/high-water records are retained. Those records let later reinstall recognize an intentionally retained installation. It never recursively erases a user-selected folder or profile. Removing personal data is not part of this installer.

Engineering fixture tests are distinct from application delivery: the fixture used a harmless Windows executable and a marker text, **not the actual R3 application**. Actual fixture compile/install/repair/upgrade/downgrade/uninstall completed; payload repair restored its SHA, downgrade returned3, and uninstall retained a profile sentinel, unknown file and earlier slot. An initial silent downgrade displayed a modal instead of returning; the installer was corrected with explicit silent defaults and the failure preserved in the receipt. Five deterministic source/bundle safety tests also passed. A final full frozen R3 bundle compile, clean Windows installation and native modeling are separate acceptance items; do not relabel the fixture as them.

Example once a reviewed frozen R3 bundle exists (all paths are operator-supplied):

```powershell
python scripts/build_installer.py --bundle <frozen-KStudio-directory> --output <new-E-drive-job-output> --nsis <verified-NSIS-directory> --version r3-internal-01 --sequence 8 --source-sha <full-source-commit>
```

`--engineering-fixture-root` deliberately marks an engineering-only artifact and restricts its fixed install target to a dedicated sibling within the build job. Never distribute that fixture as K Studio.
