# K AI Studio — one product, one primary repository

## Owner decision (2026-10-09)

**K AI Studio (also called K Studio / AI Architecture Studio)** is the single ongoing product-development project. The GitHub repository **`eksn425-del/ai-architecture-studio`**, default branch `main`, is its canonical source of truth.

Future user-discovered open-source projects are **candidate components of K AI Studio**, not reasons to restart, fork into another long-running first-party project, or build a separate competing website. Reuse components to improve the same K AI Studio website, Agent harness, professional-software integration, modeling quality and editable outputs. Previous related workflows may inform the design, but do not silently merge unrelated private projects or modify other repositories.

**Adopt → Wrap/Fork → Compose → Minimal Custom Build.**

## Standard intake for each new upstream source

1. Examine the actual code, the needed functions, release/download artifacts, software/OS support and existing equivalents in K AI Studio.
2. Verify license, attribution/source-availability requirements, third-party dependencies and trademark constraints. Never paste proprietary/unlicensed material or assume all open-source licenses are MIT-compatible. For CPAL/copyleft/network-distribution scenarios, preserve license and notices and assess publication obligations before shipping.
3. Integrate the minimum suitable implementation directly into K AI Studio (as an isolated pinned dependency, vendor subtree when permitted, or small compatible adapter). Prefer tested reusable code to new infrastructure. Keep `main` usable and existing project files safe.
4. Expose the capability to the *existing* app/tool/Skill/workspace flow. An upstream package installed but not connected is a **staged component**, not a finished user-facing feature.
5. Preserve the existing host-owned single-writer boundary, project identity, non-destructive edits, KEEP/rollback, user approval, source-evidence constraints, editable native output, and secrets handling. Do not let two separate MCP bridges concurrently mutate one SketchUp document.
6. Add focused tests and the smallest real Windows/SketchUp smoke needed for the changed path. Track support separately for each SketchUp version; 2018–2026 is an adaptation target, **not a blanket compatibility certification**. Avoid mandatory old-vs-new A/B benchmarks when the task is simply continuing product development.
7. Update `docs/CURRENT_TASK.md`, `docs/HANDOFF.md`, `THIRD_PARTY_NOTICES.md` and the relevant component map; push changes to this repository. Describe stages precisely: **studied / fetched / wrapped / exposed / real-machine verified / default-enabled**.
8. If an upstream module is unsuitable, record why and do not force it into the product simply because it is open source.

## Current ADAI example

ADAI 0.5.39's official Skill and Managed MCP distributions can be downloaded through `scripts/install_adai_components.py` with pinned SHA-256 hashes and CPAL-1.0 notices. The optional `ADAIConstructionGeometry` helper is connected to existing guarded ProjectRuby **only** when explicitly enabled with `ARCH_STUDIO_ENABLE_ADAI_GEOMETRY=1`; the separate ADAI Managed MCP remains an isolated test-only component, **not** a second active writer. K Studio's known native SketchUp 2024 path remains the default. This combination is the product's ongoing engineering foundation, while ADAI-assisted real SketchUp quality and 2018–2026 cross-version support remain unverified.

## One-product boundaries

- Keep **this single repository** as K AI Studio's product mainline; a short-lived integration branch and PR are acceptable, but return accepted work to `main`.
- Do not delete or rename other historical repositories without a separate explicit request.
- Do not create a second first-party website just to showcase an open-source library; improvements should appear in K AI Studio.
- An upstream project's name/logo and external license remain theirs; product-facing identity stays **K AI Studio**.
- Shipping an unverified integration as opt-in is allowed when isolated and safe; claiming a new SketchUp version or better reconstruction fidelity requires measured evidence.
