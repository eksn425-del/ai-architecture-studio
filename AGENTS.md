# AGENTS.md

## Owner decision — external-source learning must change real user experience (2026-10-10)

**Do not mistake research / downloaded source / installed Skill / isolated smoke for an improvement to the product.** K AI Studio now follows TWO complementary loops: **continually adopt licensed and useful external methods into stable product capabilities**, then **select a suitable actual method per real task and verify that it ran**. This is not specific to 3D: the same rule applies to future CAD, website, video and workflow products. Read [continuous capability adoption policy](docs/CONTINUOUS_CAPABILITY_ADOPTION_2026-10-10.md).

For modeling, consult `app/oss_method_catalog.py` and the host's actual capabilities. The `construction_strategy` for each new wall/opening/profile/roof should record a concrete `method_id` + meaningful `selection_reason`. The guarded writer wraps SAIE and opt-in ADAI calls and returns `oss_method_ledger`/`oss_method_adoption` read back from the current root. **Zero wrapped calls ≠ product used; execution ≠ visual quality achieved.** Check real geometry, KEEP and source-matched screenshots. If custom Ruby or a fallback is more appropriate, record the specific compatibility, license, topology or previous failure reason instead of adding a token ADAI call.

When the user discovers an external project, identify concrete code/methods worth adopting, license and platform constraints, the production integration point and real acceptance evidence. Finish the same product loop: study → integrate → expose → execute → assess user impact; defer or reject unsuitable upstream material. Do not build another first-party site, collect uncalled helpers or invent upstream usage. Latest actionable issue: [OSS adoption Issue #3](https://github.com/eksn425-del/ai-architecture-studio/issues/3).

For the **NEXT Codex test** use the user's **new architectural reference image(s)**, not the previous café or villa. Follow [new-image test plan](docs/NEXT_ARCHITECTURE_TEST_WITH_OSS_ADOPTION_2026-10-10.md) and upload `model/oss-method-ledger.json` and `model/oss-method-adoption.json` along with all regular per-run GitHub evidence. If images are not present, request the input before executing an arbitrary older test.

## Single-product owner decision (2026-10-09)

**K AI Studio / K Studio / AI Architecture Studio is the one continuing product.** This `eksn425-del/ai-architecture-studio` repository and its default `main` branch are the canonical product source. When the user shares any new open-source project, inspect it as a potential **component to integrate into this same website**; do not spin up a competing first-party website/project by default. Choose Adopt → Wrap/Fork → Compose → Minimal Custom Build, with license compliance, model quality, rollback, Windows/SketchUp compatibility and evidence-first validation. Short-lived branches/PRs are fine, but accepted work returns to `main`. See [one-product open-source policy](docs/ONE_PRODUCT_OPEN_SOURCE_POLICY.md).

**ADAI 0.5.39** is already available as optional pinned CPAL-1.0 download and verified geometry hook. It is part of K Studio's integrated engineering direction; its optional geometry runtime remains **off by default** until real SU evidence supports enabling it. The separate ADAI MCP is not connected to the live model by installation alone. Do not demand a legacy K Studio versus ADAI A/B benchmark before continuing product development, but require minimal safety smokes for changed geometry paths. SketchUp 2018–2026 remains an incremental target, not a certified claim.

## Persistent real-test GitHub evidence requirement (owner decision, 2026-10-09)

**Every future nontrivial local Agent/SketchUp modeling or integration test — PASS, PARTIAL, FAIL, or BLOCKED — must end with a NEW evidence folder committed and pushed to the SAME K AI Studio repository under `docs/test-results/windows/YYYY-MM-DD-<run>/`.** Follow [`docs/TEST_EVIDENCE_PROTOCOL.md`](docs/TEST_EVIDENCE_PROTOCOL.md). This is not optional and cannot be satisfied by a short Codex text summary or pointers to ignored local runtime files.

When a model is actually built: commit the **real six current-revision certified screenshot PNGs** (front/rear/left/right/roof/oblique), their camera/revision sidecars, source-angle PNG, actual model/readback/KEEP receipts, browser-download/native-reopen/edit proof, planner constraints, Critic/reviewer truth, sanitized errors, `run.json`, `metrics.json`, and a Chinese README describing visually observed mismatches. Include the source image only if approved for public posting (otherwise point to the existing public test-assets source). If no model commits because of a blocker, upload genuine failure/metrics with `geometry_committed=false` and explicit missing-image reason, NOT fake images.

The uploader must record the **real model ID and reasoning effort** plus tool counts, latency and token measurements (unavailable tokens are `null`, not zero); exact commit/model/SketchUp version, human interventions, and honest QA status. Explicitly distinguish independent read-only Critic vs Builder self-review. Redact all secrets, machine-private paths, user-owned SKP/DWG, private images and personal data. Before pushing, run `python scripts/validate_test_evidence.py <run-folder> --write-manifest` followed by a normal validation call; publish the SHA256 manifest. Push `origin/main` and verify remote commit so ChatGPT can inspect **actual evidence and screenshots** on the next turn.

For this round specifically, the user requests **GPT-6 Luna Max via Codex native modeling where available**; check the actual supported model ID. If not available, use the highest-capability model actually available in Codex and **report the fallback**; do not invent a Luna Max run or silently use historical DeepSeek/Sol Low. See `docs/NEXT_NATIVE_TEST_GPT6_LUNA_MAX_2026-10-09.md`.

This repository uses GitHub as the single source of truth between ChatGPT planning/review and Codex local implementation.

## Required workflow

1. Before starting local work, run `git pull --ff-only` and confirm the working tree is clean.
2. Read `docs/CURRENT_TASK.md` first.
3. Read `docs/EXECUTION_GUARDRAILS.md` before any substantial implementation or local benchmark.
4. Read only the linked product/architecture docs needed for the current task.
5. Execute the current task end-to-end; do not stop after analysis unless a real blocker prevents implementation.
6. Prefer reuse over rebuilding infrastructure:
   **Adopt → Fork/Wrap → Compose → Minimal Custom Build**.
7. Run relevant tests/checks and, when available, a real SketchUp smoke/quality test.
8. Update `docs/HANDOFF.md` before finishing.
9. Commit the work with a clear message.
10. **Push the completed commit to `origin/main` before reporting completion.** A local-only commit is not considered handed off.
11. Confirm `origin/main` contains the completed commit.
12. Do not start a new milestone that is not in `docs/CURRENT_TASK.md`.

## Repository ownership / turn-taking

To avoid conflicts, ChatGPT and Codex do not edit the same repository state at the same time.

- **ChatGPT turn:** remote GitHub review, product/architecture decisions, task definition, safe text/code edits that do not require local runtime validation.
- **Codex turn:** local Windows/SketchUp/MCP work, dependency installs, PowerShell execution, localhost/browser verification, real model tests, and code changes that require local execution.
- When Codex starts a task, it should pull the latest remote state and treat that state as authoritative.
- While Codex is actively implementing a task, ChatGPT should avoid overlapping code edits on `main`.
- When Codex finishes, it must commit + push + update `docs/HANDOFF.md`; ownership then returns to ChatGPT for review.

See `docs/COLLABORATION.md` for the full division of responsibilities.

## Success-first execution rule

The current prototype previously over-valued clean architecture, tool count and synthetic PASS states while user-visible SketchUp output remained weak. Do not repeat that pattern.

For the current product focus:

- user-visible reconstruction quality is the milestone outcome;
- connectivity/tests/tool discovery are prerequisites, not product success;
- do not replace a proven direct-Codex-like coding loop with a smaller custom planner/action vocabulary;
- do not switch to a stronger model merely to hide missing Skill/Agent/MCP capability;
- do not ask the user to perform internal engineering chores unless they truly block the next user-visible milestone and cannot be done from the current environment;
- non-critical external checks must be recorded as `pending_external` and work should continue.

`docs/EXECUTION_GUARDRAILS.md` is normative for the current milestone.

## Assembly-first / OSS takeover rule

This project is optimized for **speed to usable product**, not for proving that we can rebuild every subsystem ourselves.

Before writing new infrastructure, geometry code, CAD output code, or architecture-specific tool code:

1. inspect the already surveyed reusable components at implementation level,
2. confirm license and local compatibility,
3. install/adopt the upstream package or wrap the smallest useful module,
4. compose it into the existing tool surface,
5. write only the missing glue.

A new custom geometry tool requires a short explanation of why SAIE / ArchFlow / Supex / the existing connector cannot provide the capability.

Do not spend a milestone creating a cleaner custom replacement for a working connector, agent runtime, CAD exporter, architecture skill, geometry primitive, model-inspection layer, or output pipeline.

## Current product focus — Image → SketchUp first

The current milestone is intentionally narrower than full architecture design.

Target:

**one user-provided architectural image → cost-efficient multimodal model → dedicated reconstruction Skill + mature SketchUp tools → developed editable SketchUp model → source-matched screenshot QA → same-model revision**

Do not combine taskbook + site + precedent into a new design until this image-reconstruction workflow is repeatable.

For `image_reconstruction`:

- the uploaded image is the visual target, not merely a precedent;
- do not weaken requested fidelity with blanket anti-copy wording;
- first clarify only high-impact unknowns: intended use/views, scope, any known dimension, unseen-geometry inference permission, visible detail level;
- then fill/update `notes/reconstruction_card.md` with KNOWN / ESTIMATED / ASSUMED parameters before substantial geometry;
- show the parameter/construction plan for user approval before editing SketchUp;
- build recognizable primary form first, then facade depth/repeated systems/material zones, then visually compare and revise;
- a few white boxes are an automatic failure when the source visibly contains developed facade/roof geometry;
- use one representative repeated module and component/instance repetition where possible;
- tool-return success alone is not completion.

The first quality benchmark uses the Economy Sol route and starts at low reasoning. Do not call Astra unless a future `CURRENT_TASK.md` explicitly authorizes it.

## Product architecture rule

The product is **not** a new CAD/3D engine and is **not** a weaker in-house architecture model.

Target architecture:

**Web Workspace → replaceable Agent Runtime → workflow-specific Skill/context → persistent coding workspace → thin professional-software bridge + reusable helpers → SketchUp / CAD → screenshot/model readback → revision**

SketchUp remains the real editable modeling application.

The website manages inputs, project/session context, conversation, outputs, and product UX.

The agent/model should retain broad reasoning and coding freedom. Do not force normal modeling through the old tiny `DesignIR → BuildPlan → create_mass` action set.

`DesignIR` may remain as project memory / structured state, but it must not be the mandatory geometry generator or restrict all geometry to axis-aligned rectangles.

## Reuse priorities

Prefer according to actual capability fit rather than historical order:

1. **existing Kongxing SketchUp MCP/plugin** for verified disposable-model identity, lifecycle, existing local readback/view tools, and guarded transport.
2. **persistent workspace Ruby / Direct-Codex-style coding loop** for project-specific/repeated reconstruction geometry.
3. **SAIE (MIT)** for mature SketchUp semantic helpers when locally compatible: walls/openings/slabs/roofs/components/materials/BIM attributes/query/view/batch/DXF utilities.
4. **Supex (MIT)** for agentic project-script / introspection patterns and advanced geometry ideas when platform-compatible; do not port the whole macOS/SketchUp-2026 stack to Windows without a clear supported path.
5. **Stultus (Apache-2.0)** for portable patterns around Codex/Claude → Ruby execution → scene readback → screenshot → revision/Undo on SketchUp 2024. Reuse only pieces that improve the current stack; do not replace a working connector just to copy architecture.
6. **ArchFlow Studio (Apache-2.0 source)** for later semantic project state, DXF/output, generated Ruby, metrics and run-record pieces.
7. **SketchUp Architect Skill (MIT)** for later/full architectural reasoning, continuity and precedent workflow.
8. **VBO SkAgent (MIT)** as a lightweight fallback if the active local execution path is blocked.
9. other clearly licensed MIT/Apache/BSD code.
10. minimal custom implementation only for missing glue.

**ADAI SketchUp Skill + Managed MCP is CPAL-1.0.** The owner approved optional reuse of the pinned official distributions (see `app/adai_components.py` and `docs/ADAI_COMPONENT_INTEGRATION_2026-10-09.md`). Retain upstream LICENSE/NOTICE and fulfill all applicable source/attribution requirements when distributing or deploying covered material; do not indiscriminately vendor ADAI code or silently replace the existing Kongxing writer. The geometry helper is enabled only by explicit flag; ADAI's separate MCP is staged for isolated testing.

The observed Pylon `pylon-sketchup2model` demonstration is a product-quality reference from user-provided screenshots only; no public source has been established.

Building-Xuezhang desktop/SU automation is an observed competitor reference. Its public/user-provided workflow may guide product behavior (clarify → parameterize → approve → execute → continue editing), but proprietary implementation must not be copied.

PlanFloor AI Agent is architecture-study-only unless a compatible reuse license is verified. Its workflow/Skill boundaries may be studied; do not copy unlicensed source.

Never copy source from a repository without a clear compatible license.

## Precedent / source fidelity rule

Do not impose a blanket “make it unlike the reference” rule.

For `image_reconstruction`, the source image is the target appearance to reconstruct as editable geometry.

For later `architecture_design`, the user owns the precedent-fidelity decision:

- if the user asks for principles only, abstract the principles;
- if the user asks for a strong formal adaptation, concrete massing, silhouette, roof, bridge/platform, facade rhythm and spatial-sequence logic may be carried over and transformed to fit the real site/program/constraints.

Taskbook/site/regulatory constraints still win in design mode. Do not claim unverified technical compliance.

## Current prototype brain rule

During local prototype work, Codex/Astra/Sol/Luna may act as the temporary native agent when the current task explicitly requires it.

The product must preserve a replaceable runtime boundary so a production model/API path can be plugged in later without rewriting the web workspace or project storage.

Do not interpret a model benchmark failure as proof that the model is bad until the same input evidence and execution capability are available. Conversely, do not use a stronger/more expensive model as a substitute for missing tools or workflow guidance.

## Agentic-coding workspace rule

Direct Codex succeeded partly because it had a real coding harness. The product may restore that pattern only through a dedicated generated workspace:

- use an ignored per-project agent workspace under runtime;
- if Codex App Server uses `workspace-write`, make only that generated workspace writable;
- keep network disabled for modeling turns unless a future task explicitly changes this;
- taskbook/site/reference/source files are not writable roots;
- original repository/source code is not a writable modeling root;
- dynamic SketchUp tools still require the verified disposable model boundary;
- never use `danger-full-access` for the modeling runtime;
- for image reconstruction, keep `notes/reconstruction_card.md` and persistent Ruby source under `scripts/` so the same parameters/model can be revised across turns.

## Safety and repository hygiene

- Never commit API keys, tokens, credentials, secrets, or private machine paths.
- Never commit the user's private graduation-design source assets, private SKP/DWG files, taskbook/source packages, or copyrighted reference packages unless the user explicitly approved a sanitized public derivative.
- Runtime/user project data belongs under ignored local runtime folders.
- Never modify the user's original model. Use a blank/disposable model or a copy.
- Prefer localhost-only bridges for local software control.
- Preserve required open-source license and NOTICE files when code is reused or vendored.
- Optional OSS backends must not expose whole-document open/save/clear or raw arbitrary execution if the website already owns a safer lifecycle boundary.

## Autonomy boundary

Solve ordinary engineering decisions autonomously. Do not repeatedly ask the user for implementation details.

Ask only when:
- a critical product input is missing and no safe fallback exists,
- an irreversible/destructive action is required,
- or a choice would materially change product scope or user-visible reconstruction assumptions.

Do **not** interrupt the user for internal probes, reversible local setup choices, routine test failures, tool discovery, or non-critical environment checks. Record those as evidence/pending work and continue whenever possible.

Do not add Rhino/Revit/Blender support, payments, authentication, or production cloud infrastructure unless `docs/CURRENT_TASK.md` explicitly includes them.
