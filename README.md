# AI Architecture Studio

AI Architecture Studio is a lightweight architecture workspace that packages a strong agent/model around real design software instead of rebuilding CAD or 3D tools from scratch.

## Product direction

**任务书 + 场地 + 参考案例 + 用户想法**  
→ 网站中的中文对话与项目上下文  
→ Astra/Codex native agent  
→ existing MCP / reusable open-source tools  
→ editable SketchUp model  
→ drawing / render / presentation outputs

SketchUp remains the real editable modeling application.

The website is the product shell: inputs, project/session memory, conversation, outputs, version/history, and later packaging/billing.

## Current milestone

**Fast Assembly v1 — Astra-native Architecture Agent**

The previous Product Alpha v0.2 proved that the Chinese web workspace can connect to the existing Kongxing SketchUp MCP, build/edit a live SketchUp model, generate DXF, capture viewport images, and persist project state.

However, the old default modeling path over-constrained the agent through a tiny rectangular `DesignIR → BuildPlan → create_mass` workflow. That path remains useful as a legacy deterministic demo/test, but it is no longer the intended product architecture.

The current milestone replaces it with a free-form agentic path:

**Web Workspace → Native Agent Runtime → existing SketchUp MCP / reusable OSS tools → SketchUp → screenshot/model readback → agent continuation**

See:

- [Fast Assembly v1 strategy](docs/FAST_ASSEMBLY_V1.md)
- [Current task](docs/CURRENT_TASK.md)
- [Thesis Astra modeling benchmark](docs/THESIS_MODELING_CASE_STUDY.md)

## Why this change

The thesis benchmark demonstrates the quality level we actually want: iterative work with richer grouped massing, levels, skins, glazing, platforms/connections, site relationships, CAD coordination, and repeated visual checking.

The product should **package that kind of agent capability**, not re-implement a weaker architecture brain one fixed tool at a time.

## Reuse policy

Default engineering order:

**Adopt → Fork → Wrap/Compose → Minimal Custom Build**

Current high-value reusable components:

- existing Kongxing SketchUp MCP/plugin — first execution path
- SketchUp Architect Skill — architecture reasoning / precedent workflow
- ArchFlow Studio — project-state, CAD/output, SketchUp scripting patterns
- SAIE — richer SketchUp execution if the existing connector is insufficient
- VBO SkAgent — lightweight fallback / direct Ruby bridge path

Only reuse source with a clear compatible license and preserve required attribution/NOTICE files.

## What we do not build

Unless a future task explicitly requires it, this project does not build:

- a browser CAD engine
- a new 3D modeling engine
- a foundation model
- a generic MCP framework
- a custom replacement for a working open-source/local connector

Most project code should stay focused on glue, adapters, project/session management, safe orchestration, architecture-specific workflow/skills, and product UX.

## Current product foundation

The existing local product already includes:

- Simplified-Chinese workspace
- brief/site/reference/user-intent inputs
- public reference URL ingestion with safe fallback to screenshots/images
- persistent conversation/project state
- existing Kongxing MCP reuse
- real editable SketchUp model control
- viewport capture
- DXF / presentation outputs
- `/showcase` thesis modeling case study

## Local development

From the repository folder on Windows:

```powershell
.\scripts\setup.ps1
.\scripts\open_blank_sketchup.ps1
.\scripts\dev.ps1
```

Open `http://127.0.0.1:8787`.

The active milestone requires real local SketchUp/MCP validation, so Codex handles those local execution steps. ChatGPT handles GitHub review, planning, safe remote edits, and milestone definitions. See [COLLABORATION.md](docs/COLLABORATION.md).

## Thesis modeling benchmark

The sanitized case-study page is available locally at:

`http://127.0.0.1:8787/showcase`

GitHub-readable record:

[docs/THESIS_MODELING_CASE_STUDY.md](docs/THESIS_MODELING_CASE_STUDY.md)

The repository contains only user-approved web-optimized previews. Raw SKP/DWG files, taskbook/source packages, reference-image packages, API keys, and private machine paths must not be committed.

## Codex start point

Codex should read only what the current task requires, starting with:

1. `AGENTS.md`
2. `docs/CURRENT_TASK.md`
3. `docs/FAST_ASSEMBLY_V1.md`
4. `docs/THESIS_MODELING_CASE_STUDY.md`
5. `docs/OPEN_SOURCE_COMPONENT_MAP.md`
6. `docs/HANDOFF.md`
