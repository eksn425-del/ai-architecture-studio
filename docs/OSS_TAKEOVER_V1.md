# OSS Takeover v1 — stop rebuilding the SketchUp engine

## Why this milestone exists

The reference-rich thesis benchmark established a product-level failure that should not be solved by spending more premium-model quota:

- the website's Astra Low run completed the tool loop but remained visually and geometrically below the user's successful direct Codex/Astra thesis workflow;
- Luna Max was operationally unusable in the same long context before it reached building generation;
- Sol Medium completed only site/road turns before the experiment was stopped, so its building quality is still unknown;
- the current product has surveyed mature open-source SketchUp/CAD systems but has actually reused much less of their execution code than intended.

The next milestone is therefore **execution-stack migration, not another model benchmark**.

Do not spend Astra quota in this milestone. Do not run Luna/Sol architecture-quality benchmarks until the OSS execution stack is materially richer.

## Product boundary

The product should own:

- Chinese web UX;
- project/session memory;
- taskbook/site/reference ingestion;
- user-controlled precedent fidelity;
- model/provider routing;
- tool composition and safety boundary;
- output/history/version packaging.

The product should **not** own a bespoke replacement for mature SketchUp geometry, CAD export, inspection, roof/opening/wall, BIM metadata, or agentic-code runtimes when compatible OSS already exists.

Target architecture:

```text
Web Workspace
  -> Model / Agent Harness
      -> Architecture Skill / project context
      -> composed OSS execution surface
          -> Kongxing (verified local identity/lifecycle bridge)
          -> SAIE (mature declarative SketchUp tools)
          -> Supex-style project scripting / introspection where compatible
          -> ArchFlow semantic CAD/output pieces
      -> SketchUp / CAD
      -> screenshots + readback + revision
```

## Reuse decision order

**Adopt package -> wrap adapter -> vendor only the needed licensed module -> minimal custom glue.**

A new custom geometry tool is allowed only after documenting that the reusable candidates cannot provide the capability.

## 1. SAIE — first execution takeover candidate

Upstream: `iamahsanmehmood/saie`

License: MIT.

Why it matters:

- upstream documents 67+ MCP tools;
- walls and real openings;
- polygon slabs and roofs;
- components, materials, layers and BIM attributes;
- model query / deep scan / verification;
- canonical screenshots and live view;
- clash/report utilities;
- DXF parsing;
- batch operations;
- optional raw Ruby, which the product should keep blocked because project Ruby already has a guarded boundary.

Important compatibility fact: current upstream documentation targets SketchUp 2025. The user's local installed version must be checked before enabling it. Do not silently install/enable a plugin into an incompatible SketchUp version.

Repository changes already prepared by ChatGPT:

- `app/oss_backends.py` can wrap an installed standards-compliant MCP server through the official Python MCP SDK;
- `app/agent_tools.py` now composes optional OSS tools as namespaced tools such as `saie__create_wall` beside the existing Kongxing tools;
- whole-document lifecycle tools and raw `execute_ruby` are blocked from the imported SAIE surface;
- `scripts/setup.ps1 -InstallSaie` installs the upstream Python/MCP package but deliberately does not auto-enable the SketchUp plugin;
- enable only after local validation with `ARCH_STUDIO_ENABLE_SAIE=1`.

The local task is to install the matching upstream SketchUp plugin, prove `saie ping`, inspect the actual tool list, and validate that both SAIE and Kongxing see the same disposable model.

## 2. Supex — restore agentic coding capability instead of imitating it badly

Upstream: `darwin/supex`

License: MIT.

Useful upstream patterns:

- full SketchUp Ruby API execution;
- project-local, git-versioned modeling scripts;
- model introspection and screenshots;
- Ruby REPL/runtime;
- VCAD sidecar for BRep operations such as booleans, fillet, chamfer, shell, extrude, revolve, sweep, loft and patterns.

Current compatibility limitation: upstream describes the project as early-stage, primarily tested on macOS with SketchUp 2026 / Claude Code. Do **not** attempt to install the whole runtime on the user's Windows machine in this milestone unless local inspection finds a supported path.

What to copy now:

- the architecture pattern: editable project scripts + execute + inspect + revise;
- the idea of a dedicated writable agent workspace separated from source project assets;
- introspection-before-and-after execution;
- advanced geometry kernel as a future candidate, not a requirement for this Windows milestone.

The current website's App Server runs too close to a read-only tool-calling harness compared with the successful direct Codex workflow. Local Codex should implement a **dedicated writable agent workspace** using Codex `workspace-write`, with network disabled and writable roots limited to an ignored project-local agent workspace. Do not make the original taskbook/site/reference directories writable.

## 3. ArchFlow Studio — use real CAD/state/output code, not only the ideas

Upstream: `bingxijun/archflow-studio`

License: Apache-2.0 for source; upstream branding/media have separate restrictions.

Useful upstream pieces documented today:

- parsed requirements draft;
- semantic `building_model.json`;
- validation / metrics;
- semantic DXF;
- generated SketchUp Ruby;
- standard views and human-review artifacts;
- immutable run/project records;
- CAD and render handoff.

The local task should identify importable Python modules or CLI/package entry points for **semantic DXF / model-state / output manifest** work and adopt them directly where they replace our legacy rectangle-only drawing path. Do not fork the full application just for conceptual similarity.

## 4. PlanFloor AI Agent — architecture pattern only until license is clear

Upstream: `zhixiangggggggg/sketchup-planfloor-ai-agant`

Current public README documents a staged pipeline:

```text
natural language
-> intent / room parsing
-> template or CP-SAT solver
-> independent validation
-> wall topology + openings
-> transactional SketchUp execution
-> independent model readback
```

It also describes 16 SketchUp Skills for boxes, floors, walls, doors, windows, rooms, whole-house layouts, furniture, inspection, execution and repair.

No compatible top-level reuse license has been established in this project. Study architecture and tool boundaries only; do not copy source until local Codex confirms a compatible license.

## 5. SketchUp Architect Skill — reasoning aid, not geometry engine

Continue using the vendored MIT skill, but do not let generic anti-copy guidance suppress a user-requested strong precedent adaptation.

The website now adds an explicit policy: when the user asks to strongly adapt a named precedent, concrete massing, roof/silhouette, bridge/platform, facade rhythm and spatial sequence may be transferred and then transformed to the real site/program. Taskbook/site constraints still win.

## Current code migration rules

1. **Kongxing remains the verified identity/lifecycle bridge** until a replacement proves safer and more capable on the user's machine.
2. **SAIE adds mature semantic modeling/query tools** when locally verified.
3. **Guarded project Ruby remains available for genuinely project-specific geometry**, but it should no longer be the first answer for walls/openings/slabs/roofs that a mature backend already exposes.
4. **No new `create_xxx` tool in our repo** if SAIE/ArchFlow/Supex already solves the same primitive.
5. Imported tools must keep stable semantic IDs when upstream supports them.
6. Generated screenshots/readback must be used for QA; model/tool success flags alone are not enough.
7. Source taskbook/site/reference files remain immutable; agent-generated code goes to an ignored writable workspace.
8. No premium model call is required to install, inspect, test tool schemas, run deterministic tool smoke tests, or validate geometry operations.

## Local milestone evidence

Before any new architecture-quality model benchmark, Codex must provide all of the following:

- current SketchUp version and compatibility decision for SAIE;
- upstream SAIE version / commit or package version;
- successful local plugin connection or a concrete blocker;
- actual imported tool names exposed to the website;
- deterministic smoke model built **without an LLM** using mature imported operations: at minimum walls + opening + slab + non-flat roof or another non-box operation + semantic query + screenshot;
- same-model query/readback proving stable IDs;
- one deterministic modify/delete/repair cycle;
- ArchFlow reuse decision with exact modules/CLI pieces selected or rejected;
- dedicated writable agent-workspace decision/test;
- automated tests passing;
- `docs/HANDOFF.md` updated with PASS/PARTIAL/FAIL evidence.

Only after the execution stack passes this gate should a cheap model be asked to orchestrate it. The next model test should start with the cheapest practical route; Astra is reserved for one final parity check after the tooling gap is closed.
