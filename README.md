# AI Architecture Studio

AI Architecture Studio is a lightweight architecture workspace that packages strong existing AI + open-source professional-software automation around real design tools instead of rebuilding CAD or 3D engines from scratch.

## Product direction

**任务书 + 场地 + 参考案例文字/图片/图纸 + 用户想法**  
→ 网站中的中文对话与项目上下文  
→ replaceable Agent Runtime  
→ Architecture Skill + composed reusable OSS tools  
→ editable SketchUp / CAD  
→ screenshot/readback/revision  
→ drawing / render / presentation outputs

SketchUp remains the real editable modeling application.

The website is the product shell: inputs, project/session memory, conversation, outputs, version/history, provider routing, and later packaging/billing.

## Current milestone

**OSS Takeover v1 — migrate mature SketchUp/CAD capability before any new model benchmark**

The reference-rich thesis experiment produced the result that matters most for the current architecture:

- website Astra Low executed successfully but remained materially below the user's successful direct Codex/Astra thesis workflow;
- Luna Max was operationally too slow in the same long-context loop before reaching building generation;
- Sol Medium completed site/road work only, so its building quality remains unproven;
- the repository had surveyed mature open-source SketchUp/CAD projects, but the runtime still relied much more heavily on our own narrow glue/tooling than intended.

The next milestone therefore stops spending model quota and migrates mature execution capability first.

See:

- [OSS Takeover v1](docs/OSS_TAKEOVER_V1.md)
- [Current task](docs/CURRENT_TASK.md)
- [Open-source component map](docs/OPEN_SOURCE_COMPONENT_MAP.md)
- [Decisions](docs/DECISIONS.md)
- [Thesis Astra modeling case](docs/THESIS_MODELING_CASE_STUDY.md)

## Current execution architecture

```text
Web Workspace
  -> Agent Runtime
      -> project context + Architecture Skill
      -> composed tool surface
          -> Kongxing SketchUp MCP (verified local identity/lifecycle)
          -> optional SAIE MCP tools (semantic modeling/query/view)
          -> guarded project Ruby (project-specific geometry only)
          -> future ArchFlow CAD/state/output pieces
      -> SketchUp
      -> screenshot / model readback / revision
```

The old rectangle-only `DesignIR -> BuildPlan -> create_mass` flow remains a regression/legacy path, not the normal modeling architecture.

## Reuse policy

Default engineering order:

**Adopt package → wrap/compose → vendor only the needed licensed module → minimal custom glue**

Current priority components:

- **SAIE (MIT)** — mature walls/openings/slabs/roofs/components/materials/BIM/query/view/batch/DXF tool surface; upstream currently targets SketchUp 2025, so local compatibility must be verified before enabling.
- **Kongxing SketchUp MCP** — existing verified local identity/lifecycle bridge and fallback named tools.
- **Supex (MIT)** — agentic project-script / introspection patterns and advanced-geometry ideas; upstream currently describes macOS/SketchUp 2026 as the primary tested path, so do not port the whole stack to Windows without a supported route.
- **ArchFlow Studio (Apache-2.0 source)** — semantic project state, DXF/output, generated Ruby, metrics, standard views and run records.
- **SketchUp Architect Skill (MIT)** — architectural reasoning, precedent workflow, model continuity and QA.
- **VBO SkAgent (MIT)** — lightweight fallback/direct-control candidate.
- **PlanFloor AI Agent** — architecture-study-only until a compatible top-level reuse license is verified.

Do not build a new geometry primitive or professional-software subsystem when a compatible reusable implementation already exists.

## Remote changes already prepared for OSS Takeover

- `app/oss_backends.py` — optional standards-based MCP SDK wrapper for installed OSS servers.
- `app/agent_tools.py` — composes optional namespaced OSS tools beside Kongxing instead of reimplementing them.
- `app/architecture_skill.py` — no longer lets blanket anti-copy guidance suppress a user-requested strong precedent adaptation.
- `scripts/setup.ps1 -InstallSaie` — opt-in install of upstream SAIE Python/MCP package; it does **not** silently install/enable an incompatible SketchUp plugin.
- `tests/test_oss_takeover.py` — composition and safety-boundary regression tests.

When SAIE is locally verified, enable it with:

```powershell
$env:ARCH_STUDIO_ENABLE_SAIE = '1'
```

The website then exposes upstream tools under names such as `saie__create_wall`, while blocking imported whole-document lifecycle operations and raw `execute_ruby` from bypassing the website's own model boundary.

## Precedent fidelity

Reference images and technical drawings are first-class architecture input.

The user controls how closely a precedent should influence form:

- principles-only request → abstract principles;
- strong adaptation request → concrete massing, silhouette, roof, bridge/platform, facade rhythm and spatial sequence may be transferred and transformed to the real site/program.

Taskbook/site constraints still win. The product should not flatten a deliberately strong reference into generic boxes merely to appear less similar.

## What we do not build

Unless a future task explicitly requires it, this project does not build:

- a browser CAD engine;
- a new 3D modeling engine;
- a foundation model;
- a new generic MCP framework;
- another custom wall/opening/roof/BIM engine;
- a custom replacement for a working open-source/local connector;
- a Windows port of a large experimental stack merely for architectural cleanliness.

Most project code should stay focused on glue, adapters, project/session management, safe orchestration, context, workflow UX, packaging, and delivery.

## Current product foundation

The local product includes:

- Simplified-Chinese workspace;
- brief/site/reference/user-intent inputs;
- public reference URL text ingestion;
- project-local reference-image discovery for multimodal turns;
- persistent conversation/project state;
- explicit Economy / Premium routing;
- existing Kongxing MCP reuse;
- provider-independent shared SketchUp tool surface;
- guarded task-specific Ruby;
- optional namespaced OSS MCP tool composition;
- real editable SketchUp model control;
- viewport capture/readback;
- legacy DXF / presentation outputs;
- `/showcase` thesis modeling case study.

## Local development

From the repository folder on Windows:

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
```

Open `http://127.0.0.1:8787`.

Run automated checks with:

```powershell
.\scripts\check.ps1
```

Optional model-provider dependencies:

```powershell
.\scripts\setup.ps1 -InstallModelProviders
```

Optional SAIE package install:

```powershell
.\scripts\setup.ps1 -InstallSaie
```

SAIE upstream currently targets SketchUp 2025. Do not set `ARCH_STUDIO_ENABLE_SAIE=1` until its SketchUp plugin is installed locally and the upstream bridge passes its own connectivity check.

## Budget rule for the current milestone

Do **not** call Astra and do not run a Luna/Sol thesis-quality benchmark during OSS Takeover v1.

The current local work is package/tool installation, deterministic SketchUp smoke tests, App Server workspace integration, ArchFlow/Supex code reuse, and automated tests. Luna Max may be used by the user as the **coding agent** implementing this milestone, but it should not spend quota generating the architecture benchmark.

## Thesis modeling benchmark

The sanitized case-study page is available locally at:

`http://127.0.0.1:8787/showcase`

GitHub-readable record:

[docs/THESIS_MODELING_CASE_STUDY.md](docs/THESIS_MODELING_CASE_STUDY.md)

Raw SKP/DWG files, taskbook/source packages, private reference-image packages, API keys, historical private transcripts, and machine paths must not be committed.

## Codex start point

Codex should start with:

1. `AGENTS.md`
2. `docs/CURRENT_TASK.md`
3. `docs/OSS_TAKEOVER_V1.md`
4. `docs/HANDOFF.md`
5. `docs/OPEN_SOURCE_COMPONENT_MAP.md`
6. `docs/DECISIONS.md`
