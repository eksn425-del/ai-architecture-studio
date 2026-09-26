# Fast Assembly v1 — Astra-native Architecture Agent

## Goal

Stop building a weaker in-house architecture brain.

The product should package a strong general agent/model around an architecture workflow and reuse existing open-source/local tooling wherever possible.

Target experience:

**任务书 + 场地 + 参考案例 + 用户想法 → 与 Astra 讨论 → Astra 自由调用 SketchUp/CAD 工具 → 查看模型/截图 → 自主继续修正 → 用户继续对话**

The website is the product shell and project workspace. SketchUp remains the real editable modeler.

## What we keep

Keep the useful work already built:

- Chinese web workspace
- project/file upload
- reference URL ingestion
- project history/conversation
- existing Kongxing SketchUp MCP connection
- project/output persistence
- viewport capture
- DXF / presentation outputs where useful
- `/showcase` thesis benchmark and evidence

## What changes

The old path:

`Astra/Codex → strict DesignIR → strict BuildPlan → fixed create_mass/create_circulation tools`

is no longer the default product path.

It may remain as a legacy deterministic demo/test path, but it must not constrain normal architecture modeling.

New path:

`Web Workspace → Agent Runtime → existing MCP / reusable OSS tools → SketchUp → screenshot/model readback → Agent Runtime`

The agent may write/run project scripts or call richer MCP tools when needed to create complex editable geometry.

## DesignIR role

DesignIR becomes **project memory**, not a geometry cage.

It may store:

- brief and program
- site constraints
- reference principles
- user-confirmed design decisions
- area targets
- important object identities
- current design summary

It must not require all geometry to be axis-aligned rectangles or force the agent through a tiny fixed action list.

## Reuse order

Use the fastest compatible working component.

1. Existing Kongxing SketchUp MCP and installed plugin
2. SketchUp Architect Skill — architecture reasoning / precedent workflow
3. ArchFlow Studio — project-state, CAD, run/output ideas or reusable code
4. SAIE — add richer SketchUp execution only where Kongxing is missing required capability
5. VBO SkAgent — fallback bridge / direct Ruby path
6. Other clearly licensed MIT / Apache / BSD repositories
7. Minimal custom code only for missing glue

Never copy source from a repository without a clear compatible license.

## Product rule

Do not rebuild:

- a CAD engine
- a 3D engine
- a foundation model
- a generic MCP framework
- features already available in a compatible open-source project

Our code should mostly be:

- adapters
- project/session management
- safe orchestration
- architecture-specific prompts/skills
- UI/UX
- packaging/install flow
- billing later

## Benchmark

The thesis Astra workflow is the quality reference.

A successful agent path must be able to move beyond three boxes and support the kind of iterative work documented in `docs/THESIS_MODELING_CASE_STUDY.md`, including richer massing, levels, skins, glazing, platforms/connections, site relationships, and iterative visual checking.

The first Fast Assembly milestone does not need to fully reproduce the thesis. It must prove that the website can launch a **free-form agentic SketchUp session** that is no longer limited by the old rectangle/BuildPlan schema.
