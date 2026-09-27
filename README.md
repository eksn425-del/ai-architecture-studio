# AI Architecture Studio

AI Architecture Studio is a lightweight architecture workspace that packages a strong agent/model around real design software instead of rebuilding CAD or 3D tools from scratch.

## Product direction

**任务书 + 场地 + 参考案例文字/图片/图纸 + 用户想法**  
→ 网站中的中文对话与项目上下文  
→ 按 Economy / Premium 路由的原生 Agent Runtime  
→ existing MCP / reusable open-source tools  
→ editable SketchUp model  
→ drawing / render / presentation outputs

SketchUp remains the real editable modeling application.

The website is the product shell: inputs, project/session memory, conversation, outputs, version/history, and later packaging/billing.

## Current milestone

**Thesis Parity v1 — Reference-Rich Multimodal Benchmark**

The previous Cost / Quality Router v1 proved that the shared Architecture Skill, guarded Ruby, Kongxing SketchUp tools, screenshots/readback, and Economy/Premium routing can run behind replaceable model providers.

It also exposed an important comparison flaw: the synthetic router benchmark did not reproduce the real multimodal precedent package that made the user's successful graduation-design workflow strong.

The current milestone therefore reproduces the successful workflow's information conditions as closely as practical:

**taskbook + actual site evidence + Jinshan precedent URL + key precedent images/technical drawings + user prompt sequence → website → model → SketchUp/CAD**

The controlled local comparison is:

- premium parity candidate: current Astra-class Codex route at **low** reasoning,
- economy stress candidate: `gpt-6-luna` at **max** reasoning for this benchmark only,
- historical successful direct-Codex thesis output: evaluation reference only.

Both live variants must receive the same files, same images, same Architecture Skill, same Ruby/MCP tools, same prompt sequence, and separate blank disposable SketchUp copies.

See:

- [Thesis Parity v1](docs/THESIS_PARITY_V1.md)
- [Current task](docs/CURRENT_TASK.md)
- [Cost / Quality Router v1](docs/MODEL_ROUTER_V1.md)
- [Decisions](docs/DECISIONS.md)
- [Thesis Astra modeling case](docs/THESIS_MODELING_CASE_STUDY.md)

## Why this change

The thesis benchmark demonstrates the quality level we actually want: iterative work with richer grouped massing, levels, skins, glazing, platforms/connections, site relationships, CAD coordination, and repeated visual checking.

The product should **package that kind of agent capability**, not re-implement a weaker architecture brain one fixed tool at a time.

Reference images and technical drawings are now treated as first-class architecture inputs rather than merely storing a URL/text excerpt. Project-local images in `inputs/reference`, `inputs/site`, and `inputs/brief` are attached to supported multimodal providers; generated output screenshots are deliberately excluded from automatic precedent discovery.

## Reuse policy

Default engineering order:

**Adopt → Fork → Wrap/Compose → Minimal Custom Build**

Current high-value reusable components:

- existing Kongxing SketchUp MCP/plugin — first execution path
- SketchUp Architect Skill — architecture reasoning / precedent workflow
- ArchFlow Studio — project-state, CAD/output, SketchUp scripting patterns
- SAIE — richer SketchUp execution if the existing connector is insufficient
- VBO SkAgent — lightweight fallback / direct Ruby bridge path
- LiteLLM — optional multi-provider adapter for Qwen/other compatible multimodal providers

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
- public reference URL text ingestion with safe fallback messaging
- project-local reference-image discovery for multimodal turns
- persistent conversation/project state
- explicit Economy / Premium route and per-turn model/token/latency metadata
- configurable benchmark-only reasoning overrides
- existing Kongxing MCP reuse
- provider-independent shared SketchUp tool surface
- guarded task-specific Ruby
- real editable SketchUp model control
- viewport capture/readback
- DXF / presentation outputs
- `/showcase` thesis modeling case study

## Local development

From the repository folder on Windows:

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
```

Open `http://127.0.0.1:8787`.

Load or create a project, enter its brief/site/reference context, upload key precedent images/drawings, and use the Chinese conversation panel to discuss the design. Click **打开空白副本并连接 Agent** when ready to model; the workspace creates or reconnects to a disposable SketchUp copy under that project's ignored runtime directory. Continue issuing natural-language modeling and revision requests in the same conversation. Run automated checks with `.\scripts\check.ps1`.

`.\scripts\open_blank_sketchup.ps1` remains available for legacy deterministic-flow troubleshooting.

Optional Qwen setup through LiteLLM:

```powershell
.\scripts\setup.ps1 -InstallModelProviders
$env:ARCH_STUDIO_ECONOMY_PROVIDER = 'litellm'
$env:ARCH_STUDIO_CHINA_REGION = 'international' # or 'beijing'
# Configure DASHSCOPE_API_KEY in the local process/user secret store before starting the app.
```

Economy remains the signed-in local Codex App Server by default and needs no Developer API key. No Qwen request is sent until a usable local DashScope credential is configured.

The old synthetic router benchmark remains available:

```powershell
.\.venv\Scripts\python.exe scripts\model_router_benchmark.py
```

For the current thesis-parity experiment, follow `docs/CURRENT_TASK.md` and `docs/THESIS_PARITY_V1.md`; the taskbook/site/reference package and historical transcript remain private/local and must not be committed.

Benchmark-only Codex effort overrides are explicit environment settings. Defaults remain low unless the experiment says otherwise:

```powershell
$env:ARCH_STUDIO_ECONOMY_MODEL = 'gpt-6-luna'
$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT = 'max'
$env:ARCH_STUDIO_PREMIUM_MODEL = 'gpt-6-astra'
$env:ARCH_STUDIO_PREMIUM_REASONING_EFFORT = 'low'
```

The active milestone requires real local SketchUp/MCP/Codex validation, so Codex handles those local execution steps. ChatGPT handles GitHub review, planning, safe remote edits, and milestone definitions. See [COLLABORATION.md](docs/COLLABORATION.md).

## Thesis modeling benchmark

The sanitized case-study page is available locally at:

`http://127.0.0.1:8787/showcase`

GitHub-readable record:

[docs/THESIS_MODELING_CASE_STUDY.md](docs/THESIS_MODELING_CASE_STUDY.md)

The repository contains only user-approved web-optimized previews. Raw SKP/DWG files, taskbook/source packages, reference-image packages, API keys, historical private transcripts, and private machine paths must not be committed.

## Codex start point

Codex should read only what the current task requires, starting with:

1. `AGENTS.md`
2. `docs/CURRENT_TASK.md`
3. `docs/THESIS_PARITY_V1.md`
4. `docs/THESIS_MODELING_CASE_STUDY.md`
5. `docs/OPEN_SOURCE_COMPONENT_MAP.md`
6. `docs/HANDOFF.md`
