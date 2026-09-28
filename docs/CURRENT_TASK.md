# CURRENT TASK — OSS Takeover v1: validate and finish mature SketchUp/CAD migration

## Status: Ready for Codex/local execution

## Objective

Stop spending model quota to compensate for a weak execution stack.

The last reference-rich benchmark showed that the website's Astra path is still materially below the user's successful direct Codex/Astra thesis workflow, Luna Max is operationally too slow in the current long-context loop, and Sol building quality remains unproven. The next milestone is therefore **open-source execution capability migration**, not another model-quality benchmark.

ChatGPT has already implemented the GitHub-only part of this migration. Read `docs/REMOTE_CHANGESET_V1.md` and `docs/OSS_TAKEOVER_V1.md` before changing code locally.

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
   - `docs/CURRENT_TASK.md`
   - `docs/REMOTE_CHANGESET_V1.md`
   - `docs/OSS_TAKEOVER_V1.md`
   - `docs/HANDOFF.md`
   - `docs/OPEN_SOURCE_COMPONENT_MAP.md`
   - `THIRD_PARTY_NOTICES.md`
4. Run `scripts/check.ps1` once. The current remote changes have not been executed on the user's Windows runtime yet, so fix any real API/syntax/regression issue you find rather than assuming the remote code is already locally validated.
5. Do not overwrite or publish private thesis assets/runtime files.

## Priority 1 — validate ChatGPT's remote migration code

The repository now already includes:

- `app/oss_backends.py`: standards-based MCP SDK wrapper for optional SAIE plus a project-scoped ArchFlow CLI adapter;
- `app/agent_tools.py`: composed/namespaced OSS tool surface;
- `app/native_agent.py`: project-local `workspace-write` Codex harness with network disabled and a narrow writable root;
- `app/architecture_skill.py`: user-controlled strong precedent adaptation + OSS-before-custom-Ruby guidance;
- `scripts/setup.ps1 -InstallSaie` pinned by default to current upstream SAIE `1.0.0`;
- `scripts/install_archflow.ps1`: ignored upstream ArchFlow checkout + editable install;
- `scripts/oss_backend_cli.py`: no-LLM backend inspection/call utility;
- `tests/test_oss_takeover.py`;
- `docs/OSS_TAKEOVER_V1.md` and `docs/REMOTE_CHANGESET_V1.md`.

Validate locally:

- Python syntax/imports and current tests;
- optional backends disabled by default;
- Kongxing-only path unchanged when SAIE/ArchFlow are disabled;
- App Server accepts the current `workspaceWrite` payload/config on Windows;
- no secret/path leakage;
- no taskbook/site/reference/source asset becomes writable or committed.

Fix ordinary issues directly. Do not roll back the reuse-first direction just to preserve an old test assumption.

## Priority 2 — prove the dedicated writable Codex workspace

The GitHub code already creates:

`runtime/projects/<project-id>/runtime/agent_workspace/`

and configures Codex App Server `workspace-write` with that directory as the explicit writable root, network disabled, and the App Server cwd/runtime root set to that generated workspace.

Local Codex must prove:

- a harmless generated file can be created/edited inside `agent_workspace`;
- a write attempt into the project `inputs/` tree is denied;
- taskbook/site/reference/source directories are not writable roots;
- the verified disposable SketchUp model boundary still works after the sandbox change;
- no `danger-full-access` is used.

This is a validation/fix task, not a request to design a second sandbox.

## Priority 3 — inspect the actual local SketchUp version before enabling SAIE

SAIE upstream package metadata is currently version `1.0.0`, and the current upstream FastMCP server documents SketchUp 2025.

Record:

- installed SketchUp version(s);
- active Kongxing plugin/version if discoverable;
- whether SketchUp 2025 is available on this workstation.

Then choose:

### If a compatible SketchUp 2025 environment is available

1. Run `scripts/setup.ps1 -InstallSaie`.
2. Install the **upstream SAIE SketchUp plugin** using upstream instructions; do not invent a replacement plugin.
3. Prove `saie ping` / bridge connectivity.
4. Set `ARCH_STUDIO_ENABLE_SAIE=1` only after the upstream bridge works.
5. Use the **live FastMCP tool list as authoritative**. Do not hard-code the older `tools/registry.py` list; current upstream `mcp_server/server.py` exposes the richer mm-based tool surface.
6. Verify the website discovers namespaced `saie__...` tools.

### If only an incompatible SketchUp version is available

Do not force-install or rewrite SAIE for that version in this milestone.

Instead:

- inspect SAIE source for the narrowest compatible modules/schemas/Ruby operations that can be reused legally;
- record the exact compatibility blocker;
- keep Kongxing as the active SketchUp bridge while completing the ArchFlow/workspace parts.

## Priority 4 — deterministic SAIE/Kongxing capability smoke, with zero architecture LLM calls

If SAIE is locally compatible, build a disposable deterministic smoke model by calling the real upstream tools directly from Python/CLI/tests — **not through Astra/Luna/Sol**.

Minimum evidence:

- wall network;
- at least one true door/window opening;
- slab;
- non-flat roof (gable/shed/hip if exposed by the live upstream server);
- stable semantic/AI IDs;
- `scene_summary` / entity inspection / model verification or equivalent live queries;
- inline snapshot or canonical screenshot;
- one modify/delete/repair cycle on the same model;
- model remains editable in SketchUp.

Prefer SAIE's existing batch / verification / attributes / view tools. Do not recreate them in our repo.

If an upstream tool is unavailable in the installed package, document the exact version/tool list rather than inventing a fake equivalent.

## Priority 5 — validate the direct ArchFlow adoption already added remotely

ChatGPT has already inspected the implementation and wrapped the upstream Apache-2.0 `archflow` CLI rather than copying its CAD engine. The upstream pipeline contains semantic model validation/metrics, semantic DXF generation, generated SketchUp Ruby and review/run artifacts.

Local steps:

1. Run `scripts/install_archflow.ps1`.
2. Set the `ARCHFLOW_CORE_SKILL` path printed by the script.
3. Prove `archflow doctor --json`.
4. Set `ARCH_STUDIO_ENABLE_ARCHFLOW=1`.
5. Verify `archflow__doctor`, `archflow__check_project`, `archflow__plan_run`, and `archflow__run` appear in the composed website tool surface.
6. Create a tiny generated ArchFlow project **inside `agent_workspace` only**.
7. Without any architecture LLM, prove upstream validation/metrics/DXF/generated-Ruby/review outputs.
8. Do not execute generated ArchFlow Ruby against the user's private thesis/source model during this milestone.

If the wrapper needs a small Windows/path/API fix, make that glue fix. Do not rewrite ArchFlow's semantic DXF/validation/generator code.

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
- otherwise record that its key project-script pattern is now represented by our isolated `agent_workspace` harness.

## Priority 7 — inspect PlanFloor architecture, but do not copy unlicensed source

Inspect the current upstream location/redirect for the PlanFloor AI Agent and its staged planning/validation/transaction/readback design and Skill boundaries.

Unless a compatible reuse license is found, copy **no source code**.

Record reusable architectural ideas only.

## Priority 8 — verify future cheap-model tool guidance

The remote Architecture Skill/runtime now tells future models to prefer:

1. mature namespaced semantic OSS tool when available (`saie__...` / other adopted backend),
2. existing Kongxing named tool,
3. guarded project Ruby for genuinely project-specific geometry,
4. never invent a new custom host tool during a modeling turn.

Verify this survives the local App Server path. Do not add dozens of new `create_xxx` functions to our codebase.

## Priority 9 — tests and evidence

Required automated/local checks:

- `scripts/check.ps1`;
- focused OSS-tool composition tests;
- Kongxing-only regression path;
- SAIE live tool discovery when enabled (if locally compatible);
- deterministic geometry smoke with no architecture model call (if locally compatible);
- App Server dedicated workspace-write smoke;
- ArchFlow doctor + deterministic semantic artifact smoke;
- source/private asset isolation;
- `git diff --check`.

## Acceptance criteria

1. Existing Kongxing-only workflow still works when optional OSS backends are disabled — PASS/FAIL.
2. Dedicated Codex `workspace-write` harness works on Windows while project inputs remain non-writable — PASS/FAIL.
3. SAIE compatibility decision is based on actual local SketchUp/upstream version — PASS/PARTIAL/FAIL.
4. If compatible, real SAIE MCP/plugin is installed and website exposes real namespaced tools — PASS/FAIL/N/A with blocker.
5. If SAIE runs, deterministic no-LLM smoke demonstrates mature wall/opening/slab/roof/query/view/edit operations — PASS/FAIL/N/A with blocker.
6. No raw SAIE `execute_ruby` or whole-document lifecycle tool bypasses our project boundary — PASS/FAIL.
7. ArchFlow CLI is actually adopted locally and deterministic validation/metrics/DXF/Ruby/review artifacts are proven in `agent_workspace` — PASS/PARTIAL/FAIL.
8. Supex patterns are inspected; no unnecessary Windows port/reimplementation is started — PASS/FAIL.
9. PlanFloor source is not copied without a compatible license — PASS/FAIL.
10. Strong precedent adaptation is no longer suppressed by a blanket anti-copy rule — PASS/FAIL.
11. No Astra call and no architecture-quality model benchmark is performed in this milestone — PASS/FAIL.
12. Tests pass, HANDOFF is updated, work is committed and pushed to `origin/main` — PASS/FAIL.

## What NOT to do

- Do not call Astra.
- Do not run another thesis-quality model benchmark yet.
- Do not choose a new architecture model based on this milestone.
- Do not build our own wall/opening/roof/BIM engine if SAIE already provides it.
- Do not rebuild ArchFlow semantic DXF/validation/Ruby generation.
- Do not build a new generic MCP server.
- Do not replace the working Kongxing identity/lifecycle bridge unless the replacement proves locally better.
- Do not port the entire Supex stack to Windows just because it is interesting.
- Do not copy PlanFloor code without a compatible license.
- Do not make taskbook/site/reference/source directories writable to the model.
- Do not commit private thesis files, runtime models, screenshots, credentials or machine paths.

## Final step

Update `docs/HANDOFF.md` with:

- exact local SketchUp version;
- workspace-write acceptance evidence;
- exact SAIE package/plugin version or compatibility blocker;
- imported live tool list/count and deterministic smoke evidence;
- ArchFlow doctor/artifact evidence;
- Supex/PlanFloor findings;
- test results;
- remaining blockers.

Commit, push to `origin/main`, verify the remote SHA, then stop for ChatGPT review. Do not begin a model-quality benchmark after push.
