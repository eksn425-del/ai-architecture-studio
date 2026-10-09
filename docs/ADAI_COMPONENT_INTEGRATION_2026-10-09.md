# ADAI 0.5.39 opt-in components × SketchUp 2018–2026 compatibility track

> **Integration status: code candidate on `feat/adai-components-su2018-2026`; NOT a nine-version support certificate.**
> Upstream pinned revision: `cd1e02e9f6906945376f73032e9598643fe8eb64`.
> License: **CPAL-1.0** (see upstream `LICENSE` and `NOTICE`).
> Original K Studio `main` and the existing Kongxing SketchUp connector are unchanged by installation.

## What is concretely integrated

1. **Official downloadable ZIPs, not unofficial copies.** `scripts/install_adai_components.py` downloads the upstream 0.5.39 Skill and Managed MCP with hard-coded revision/sha256, checks limits and extraction paths, retains LICENSE/NOTICE, and installs them at ignored `.local/adai/0.5.39/{skill,mcp}`. No third-party package is committed to our source repository.
2. **Real K Studio geometry hook.** After explicit opt-in, `app/project_ruby.py` checks the recorded local SHA-256 of the installed `construction_geometry.rb` and loads the official **ADAIConstructionGeometry** module into our existing guarded transaction. Agent-visible variable is `adai_geometry`, and every geometry write must still use `root.entities` and ProjectRuby's normal revision, KEEP, readback, save and independent Critic protections.
3. **Version discovery and explicit selection.** `--detect-sketchup` checks 2018–2026 candidate Windows paths, including optional `SKETCHUP_2026_EXE` etc.; `scripts/open_blank_sketchup.ps1 -SketchUpYear 2026` explicitly selects the requested installed version through the Windows uninstall registry. Omission preserves the previously preferred 2024/2022 path; it never switches to a new version automatically.
4. **ADAI Managed MCP remains separate.** Downloading its ZIP is **not** authorization to install its RBZ into the current SketchUp profile, write Codex config, or run two mutating bridges against one model. It is available for separately approved/isolated SU2018/19 comparison tests.

## Installation (Windows, local machine)

From the K Studio repository root on this branch:

```powershell
python scripts/install_adai_components.py --list
python scripts/install_adai_components.py --install skill mcp
python scripts/install_adai_components.py --detect-sketchup
python scripts/install_adai_components.py --show-standalone-mcp
python -m pytest -q tests/test_adai_components.py
```

This fetches **both** official release archives and checks them:
- Skill ZIP: `8e1295724b0b28e4e2045cb80365350ff1f5c51a6bc0d4c0337df45c16e42d7c`.
- MCP ZIP: `f76de1ab85a3edf2705eb8ebc67112c42367b0c57ccd9f7956a9d9ed0a1fc0d5`.

The ZIP files are **not uploaded to GitHub**. The installed, attributable code stays on the local computer, and existing user-owned SKP/credentials are untouched. To remove, turn the flag off first, then move/delete only the dedicated `.local/adai/0.5.39` cache after checking it.

For a **throwaway** K Studio session, opt into the installed geometry functions explicitly:

```powershell
$env:ARCH_STUDIO_ENABLE_ADAI_GEOMETRY = '1'
python scripts/start.py --no-browser
```

Agent-side, once the verified bundle is present, use the injected Ruby variable from the project-owned script:
```ruby
# This code is evaluated INSIDE K Studio's guarded ProjectRuby transaction.
# `root` and `adai_geometry` are host-provided; no direct whole-model operations.
adai_geometry.profile(root.entities, 'Roof Trim', [[0,0],[1800,0],[1800,300],[0,300]], 600, 'xz', 0)
```

The following methods are available from ADAI's actual helper, not merely planning labels: `profile`, `profile_with_holes`, `loft_sections`, `shell_grid`, `closed_band`, plus `box`, `sample_profile`, `translation_mm`. Geometry definitions, dimensions, topology rules and allowed material arguments must follow the installed ADAI Skill reference. The source helper's exact content is checked before every modeling transport script when opted in; a changed hash aborts instead of silently loading an untrusted local copy.

### Separate ADAI MCP testing — do not use on the live document

The installed `mcp` package contains `launch.cjs` and a `su_mcp.rbz` bridge. `--show-standalone-mcp` prints a verified, non-activated server command/args plus the plugin location. ADAI's own guide uses Node.js 18+, Python 3.10+, standalone MCP configuration and a SketchUp plugin installed manually. To compare:
1. Use **a separate SU profile/machine or test environment** and a disposable model — never the user's original and never simultaneously alongside the live Kongxing bridge.
2. Locate `launch.cjs`, the bundled Skill/NOTICE and `su_mcp.rbz` under the downloaded `.local/adai/0.5.39/mcp` tree.
3. Use upstream `INSTALL.md` from the installed ZIP to set up that separate connector.
4. Run a single-version complete build→view→save→reopen→edit test before considering an adapter.
5. Do not automate a wholesale MCP swap until competing model-identity, transaction, tool namespace and license behavior is independently reconciled.

## SketchUp compatibility matrix — target is 2018–2026

| SketchUp year | Known evidence before this adoption | ADAI geometry through K Studio | Release status |
|---|---|---|---|
| 2018 | ADAI upstream claims adapter target; not this build's full real test | pending installed-version smoke | NOT VERIFIED |
| 2019 | ADAI upstream: selected SU2019 geometry tests | pending K Studio bridge and geometry smoke | NOT VERIFIED |
| 2020 | No equivalent real K Studio verification | pending | NOT VERIFIED |
| 2021 | No equivalent real K Studio verification | pending | NOT VERIFIED |
| 2022 | Historical K Studio launcher fallback, not full quality acceptance | pending | NOT VERIFIED |
| 2023 | No equivalent real K Studio verification | pending | NOT VERIFIED |
| 2024 | K Studio/Kongxing real editable model, save/reopen confirmed (without ADAI) | pending new-helper smoke | **Existing K Studio baseline**, ADAI unverified |
| 2025 | No equivalent real K Studio verification | pending | NOT VERIFIED |
| 2026 | No equivalent real K Studio verification | pending | NOT VERIFIED |

ADAI's own `docs/COMPATIBILITY.md` calls SU2024/25 `planned_not_implemented`; it does not certify 2026. Version discovery / launching alone is **not** evidence of functional bridge or quality support.

## Required Windows Codex smoke per version

Use a version actually installed on the test host; never fake a PASS for missing versions:

1. `--detect-sketchup`, explicit `-SketchUpYear YEAR -PrepareOnly` using a disposable SKP from **that year's version**. Confirm extension startup & model identity, no cross-version override.
2. Without ADAI flag: verify original Kongxing-only creation, IDs/revisions, canonical screenshots, SKP download/native reopen/edit.
3. With `ARCH_STUDIO_ENABLE_ADAI_GEOMETRY=1`: test **profile with holes**, **loft sections**, **shell grid**, **closed band**, and repeat instance in separately named owned groups; record geometry counts, mm bounds, visual quality and faults.
4. Deliberately corrupt a test-installed helper hash and confirm the host refuses to load it; restore the clean official ZIP, don't weaken verification.
5. Run existing v2.8 protected KEEP negative transaction test (must roll back before commit) and v2.9 repair-memory test before merging into default product.
6. Run the same source villa through baseline vs added geometry methods; human inspect six host-certified views, roof/facade defects, editability and token/latency cost.
7. Record `PASS`, `PARTIAL`, `FAIL`, `NOT_RUN` **per SU version**. A passed test on 2024 proves nothing about 2018 or 2026.

## Licensing boundaries

ADAI is **CPAL-1.0**, including source obligations, attribution and network-use provisions. The downloaded packages retain their unmodified original `LICENSE` and `NOTICE`. If K Studio publicly redistributes, modifies or embeds any ADAI-covered code, do a specific CPAL review of the resulting distribution, source availability and user-visible attribution before shipping. Do not represent the downloaded MCP or Skill as owned/relabeled K Studio source. ADAI name/logo is not licensed as our brand.

**This branch has not run Windows/SketchUp tests.** No official ZIP binary was fetched in the ChatGPT remote environment. These commands allow a real Windows runner to fetch and verify the exact upstream artifacts.
