# AI Architecture Studio

AI Architecture Studio is a lightweight architecture workspace that packages a strong agent/model around real design software instead of rebuilding CAD or 3D tools from scratch.

## Product direction

**任务书 + 场地 + 参考案例 + 用户想法**  
→ 网站中的中文对话与项目上下文  
→ 按 Economy / Premium 路由的原生 Agent Runtime
→ existing MCP / reusable open-source tools  
→ editable SketchUp model  
→ drawing / render / presentation outputs

SketchUp remains the real editable modeling application.

The website is the product shell: inputs, project/session memory, conversation, outputs, version/history, and later packaging/billing.

## Current milestone

**Cost / Quality Router v1 — GPT-6 Luna Economy + GPT-6 Astra Premium**

Fast Assembly v1 proved that the Chinese web workspace can connect to the existing Kongxing SketchUp MCP and use the shared Architecture Skill, guarded project Ruby, live SketchUp tools, screenshots, and model readback.

Cost / Quality Router v1 keeps that architecture capability provider-independent. Economy defaults to GPT-6 Luna at low reasoning effort; Premium is an explicit one-turn GPT-6 Astra Low choice. Repeated SketchUp tool failures can mark one visible Premium rescue for the next Economy request. A successful Premium turn does not change later routine turns from Economy.

Both tiers use the same project context, architecture Skill, Kongxing MCP tools, guarded Ruby tool, screenshot inspection, and SketchUp quality loop:

**Web Workspace → Model Router → interchangeable provider adapter → shared architecture/tool runtime → SketchUp**

See:

- [Cost / Quality Router v1](docs/MODEL_ROUTER_V1.md)
- [Current task](docs/CURRENT_TASK.md)
- [Decisions](docs/DECISIONS.md)
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
- explicit Economy / Premium route and per-turn model/token/latency metadata
- existing Kongxing MCP reuse
- provider-independent shared SketchUp tool surface
- real editable SketchUp model control
- viewport capture
- DXF / presentation outputs
- `/showcase` thesis modeling case study

## Local development

From the repository folder on Windows:

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
```

Open `http://127.0.0.1:8787`.

Load or create a project, enter its brief/site/reference context, and use the Chinese conversation panel to discuss the design. Click **打开空白副本并连接 Agent** when ready to model; the workspace creates or reconnects to a disposable SketchUp copy under that project's ignored `runtime/` directory. Continue issuing natural-language modeling and revision requests in the same conversation. Run automated checks with `.\scripts\check.ps1`.

`.\scripts\open_blank_sketchup.ps1` remains available for the legacy deterministic build flow and connector troubleshooting.

Optional Qwen setup through LiteLLM:

```powershell
.\scripts\setup.ps1 -InstallModelProviders
$env:ARCH_STUDIO_ECONOMY_PROVIDER = 'litellm'
$env:ARCH_STUDIO_CHINA_REGION = 'international' # or 'beijing'
# Configure DASHSCOPE_API_KEY in the local process/user secret store before starting the app.
```

Economy remains the signed-in local Codex App Server by default and needs no Developer API key. No Qwen request is sent until a usable local DashScope credential is configured.

Run the controlled Luna/Astra SketchUp comparison with:

```powershell
.\.venv\Scripts\python.exe scripts\model_router_benchmark.py
```

The benchmark reads examples/model_router_v1/input.json, opens separate disposable SketchUp copies, and stores raw run metrics/screenshots under ignored runtime/. Matched-view screenshots and the reviewed comparison are summarized in docs/HANDOFF.md.

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
