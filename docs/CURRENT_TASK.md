# CURRENT TASK — OSS Takeover v1: migrate mature SketchUp/CAD capability

## Status: Ready for Codex/local execution

## Objective

Stop spending model quota to compensate for a weak execution stack.

The last reference-rich benchmark showed that the website's Astra path is still materially below the user's successful direct Codex/Astra thesis workflow, Luna Max is operationally too slow in the current long-context loop, and Sol building quality remains unproven. The next milestone is therefore **open-source execution capability migration**, not another model-quality benchmark.

Read `docs/OSS_TAKEOVER_V1.md` first.

### Hard budget rule for this milestone

- **Do not call Astra.**
- Do not run Luna/Sol architecture-generation benchmarks.
- Luna Max may be used as the local **coding/implementation agent** executing this task, but it should not spend quota designing/building the thesis benchmark.
- Installation, schema inspection, deterministic tool smoke tests, unit tests and local integration tests do not require an architecture LLM.

## Before starting

1. `git pull --ff-only`
2. Confirm worktree is clean and remote HEAD includes ChatGPT's OSS Takeover commits.
3. Read:
   - `AGENTS.md`
   - `docs/OSS_TAKEOVER_V1.md`
   - `docs/HANDOFF.md`
   - `docs/DECISIONS.md`
   - `docs/OPEN_SOURCE_COMPONENT_MAP.md`
4. Run `scripts/check.ps1` once and fix any regression introduced by the remote changes before continuing.
5. Do not overwrite or publish private thesis assets/runtime files.

## Priority 1 — validate ChatGPT's remote migration code

The repository now includes:

- `app/oss_backends.py`: optional standards-based MCP SDK wrapper;
- `app/agent_tools.py`: composed/namespaced OSS tool surface;
- `app/architecture_skill.py`: user-controlled strong precedent adaptation policy;
- `scripts/setup.ps1 -InstallSaie`: opt-in upstream package install;
- `tests/test_oss_takeover.py`;
- `docs/OSS_TAKEOVER_V1.md`.

Validate locally:

- Python syntax/imports;
- current tests;
- optional backend disabled by default;
- Kongxing-only path remains unchanged when SAIE is disabled;
- no secret/path leakage;
- no source project asset becomes writable or committed.

Fix ordinary issues directly; do not roll back the reuse-first direction just to preserve an old test assumption.

## Priority 2 — inspect the actual local SketchUp version before installing SAIE

SAIE upstream currently documents SketchUp 2025.

Record:

- installed SketchUp version(s);
- active Kongxing plugin/version if discoverable;
- whether SketchUp 2025 is available on this workstation.

Then choose:

### If a compatible SketchUp 2025 environment is available

1. Run the opt-in SAIE package install (or install the exact upstream package in the repo venv).
2. Install the upstream SAIE SketchUp plugin using upstream instructions; do not invent a replacement plugin.
3. Prove `saie ping` / bridge connectivity.
4. Set `ARCH_STUDIO_ENABLE_SAIE=1` only after the upstream bridge works.
5. Verify the website discovers namespaced `saie__...` tools.

### If only an incompatible SketchUp version is available

Do not force-install or rewrite SAIE for that version in this milestone.

Instead:

- inspect SAIE source for the narrowest compatible modules / schemas / Ruby operations that can be reused legally;
- record the compatibility blocker;
- move to Priority 3/4 and keep Kongxing as the active bridge.

## Priority 3 — deterministic SAIE/Kongxing capability smoke, with zero architecture LLM calls

If SAIE is locally compatible, build a disposable deterministic smoke model by calling tools directly from Python/tests/CLI — **not through Astra/Luna/Sol**.

Minimum evidence:

- wall network;
- at least one true door/window opening;
- slab;
- roof that is not just another flat box when upstream supports it;
- stable semantic/AI IDs;
- model query or deep scan;
- screenshot/canonical view;
- one modify/delete/repair cycle on the same model;
- model remains editable in SketchUp.

Prefer SAIE's existing batch / verification / attributes / view tools. Do not recreate them in our repo.

If an upstream tool is unavailable in the installed package, document the exact version/tool list rather than inventing a fake equivalent.

## Priority 4 — restore a real agentic-coding workspace without exposing source inputs

The successful direct Codex workflow had more coding freedom than the website's current read-only harness. Supex demonstrates the useful pattern: project-local scripts, execute, inspect, revise.

Implement a **dedicated ignored writable Agent workspace** under the runtime project, for example:

`runtime/projects/<project-id>/runtime/agent_workspace/`

Requirements:

- Codex App Server may use `workspace-write` only for this generated workspace;
- network remains disabled;
- taskbook/site/reference input directories are not writable roots;
- original repository/source files are not writable from the modeling turn;
- generated helper Ruby/Python/JSON can persist across turns in this workspace;
- dynamic SketchUp tools still require the verified disposable model boundary;
- do not switch to `danger-full-access`.

Use the current Codex App Server `workspaceWrite` / writable-roots protocol rather than inventing a filesystem sandbox.

Add focused tests for path construction and sandbox payload. Perform one no-model or trivial local smoke to prove the App Server accepts the policy; do not run a thesis build.

## Priority 5 — ArchFlow: adopt actual CAD/state/output code where it replaces ours

Inspect `bingxijun/archflow-studio` (Apache-2.0) at the implementation level, not only README level.

Find the smallest directly reusable modules/entry points for:

- semantic building/project state;
- semantic DXF generation;
- metrics/validation;
- run/output manifest;
- generated SketchUp Ruby / standard-view artifacts if they materially reduce our code.

Choose **Adopt / Wrap / Reject with reason** for each item.

If a module can replace the legacy rectangle-only drawing/export path with little glue, integrate it now and preserve upstream attribution/license requirements.

Do not fork the entire ArchFlow application.

## Priority 6 — Supex: take the workflow pattern; only take runtime code if Windows-compatible

Inspect `darwin/supex` (MIT) for:

- project script lifecycle;
- model introspection;
- screenshot verification;
- Ruby runtime/REPL concepts;
- VCAD integration boundaries.

Current upstream docs say macOS/SketchUp 2026 is the primary tested path. On this Windows milestone:

- do not waste time porting the whole product;
- do not add Rust/VCAD build complexity unless a clearly supported Windows path already exists;
- reuse small cross-platform MIT modules only if they immediately save code;
- otherwise record the exact patterns we implemented via the Codex writable workspace.

## Priority 7 — inspect PlanFloor architecture, but do not copy unlicensed source

Inspect `zhixiangggggggg/sketchup-planfloor-ai-agant` for its staged planning/validation/transaction/readback design and its 16 Skill boundaries.

Unless a compatible reuse license is found, copy **no source code**.

Record reusable architectural ideas only.

## Priority 8 — tool-selection guidance for future cheap models

Once the richer surface is live, update the Agent developer instructions/Skill context so future models are told to prefer mature semantic tools in this order:

1. existing semantic OSS tool (SAIE/other imported backend),
2. existing Kongxing named tool,
3. guarded project Ruby for project-specific geometry,
4. never create a new custom host tool during a modeling turn.

Do not add dozens of new `create_xxx` functions to our codebase.

## Priority 9 — tests and evidence

Required automated/local checks:

- `scripts/check.ps1`;
- focused OSS-tool composition tests;
- Kongxing-only regression path;
- SAIE tool discovery when enabled (if locally compatible);
- deterministic geometry smoke with no architecture model call (if locally compatible);
- App Server dedicated workspace-write smoke;
- source/private asset isolation;
- `git diff --check`.

## Acceptance criteria

1. Existing Kongxing-only workflow still works when optional OSS backends are disabled — PASS/FAIL.
2. SAIE compatibility decision is based on actual local SketchUp/upstream version — PASS/PARTIAL/FAIL.
3. If compatible, real SAIE MCP/plugin is installed and website exposes real namespaced tools — PASS/FAIL/N/A with blocker.
4. If SAIE runs, deterministic no-LLM smoke demonstrates mature wall/opening/slab/roof/query/view operations — PASS/FAIL/N/A with blocker.
5. No raw SAIE `execute_ruby` or whole-document lifecycle tool bypasses our project boundary — PASS/FAIL.
6. Dedicated Codex writable agent workspace works without making source inputs writable — PASS/FAIL.
7. ArchFlow implementation is inspected and at least one real adopt/wrap decision is executed where practical — PASS/PARTIAL/FAIL.
8. Supex patterns are inspected; no unnecessary Windows port/reimplementation is started — PASS/FAIL.
9. PlanFloor source is not copied without a compatible license — PASS/FAIL.
10. Strong precedent adaptation is no longer suppressed by a blanket anti-copy rule — PASS/FAIL.
11. No Astra call and no architecture-quality model benchmark is performed in this milestone — PASS/FAIL.
12. Tests pass, HANDOFF is updated, work is committed and pushed to `origin/main` — PASS/FAIL.

## What NOT to do

- Do not call Astra.
- Do not run another thesis-quality model benchmark yet.
- Do not choose a new model based on this milestone.
- Do not build our own wall/opening/roof/BIM engine if SAIE already provides it.
- Do not build a new generic MCP server.
- Do not replace the working Kongxing identity/lifecycle bridge unless the replacement proves locally better.
- Do not port the entire Supex stack to Windows just because it is interesting.
- Do not copy PlanFloor code without a compatible license.
- Do not make taskbook/site/reference/source directories writable to the model.
- Do not commit private thesis files, runtime models, screenshots, credentials or machine paths.

## Final step

Update `docs/HANDOFF.md` with:

- exact local SketchUp version;
- exact SAIE package/plugin version or compatibility blocker;
- imported tool list/count and deterministic smoke evidence;
- writable-agent-workspace evidence;
- ArchFlow adopt/wrap/reject decisions and changed files;
- Supex/PlanFloor findings;
- test results;
- remaining blockers.

Commit, push to `origin/main`, verify the remote SHA, then stop for ChatGPT review. Do not begin a model-quality benchmark after push.
