# K AI Studio（AI Architecture Studio）

> **唯一主产品 / Single product mainline:** [K AI Studio](https://github.com/eksn425-del/ai-architecture-studio) 将后续适配的开源 Skill、MCP、几何模块和专业软件自动化能力，持续整合进同一个网站与 GitHub 主仓库。新开源项目是 K AI Studio 的候选能力组件，不再另做一套相似的网站。完整原则见 [One Product / Open Source Policy](docs/ONE_PRODUCT_OPEN_SOURCE_POLICY.md)。

## ADAI 0.5.39 integrated option (experimental; disabled by default)

K AI Studio supports **opt-in**, integrity-checked downloads of the upstream ADAI Skill and its Managed MCP, with the official CPAL-1.0 license and attribution retained. Only the installed Skill's construction geometry can be enabled inside our existing guarded ProjectRuby bridge; the separate Managed MCP is **not** activated automatically. SketchUp **2018–2026 is a validation target, not a certified compatibility claim**; original verified K Studio baseline remains SketchUp 2024. See [ADAI component adoption and version matrix](docs/ADAI_COMPONENT_INTEGRATION_2026-10-09.md).

## Windows 用户开始使用

1. 安装 [Python 3.11 或更新版本](https://www.python.org/downloads/windows/)，安装时勾选 **Add Python to PATH**。
2. 从 GitHub 的 **Code → Download ZIP** 下载最新 main，完整解压后双击根目录 **Start K Studio.cmd**。首次启动会安装项目和 DeepSeek / GLM 依赖，然后打开本地网页；请保持启动窗口打开。再次使用仍双击此文件。
3. 在页面点击 **连接 AI 模型**，选择 DeepSeek 或 GLM，填入自己的 API Key。Key 仅保存在服务内存，重启后需要重填。
4. 新建会话 → 上传同一建筑的图片或六视图整图 → 描述目标 → 补充需求 → 检查并修改计划。没有实测尺寸可以采用估算；建模前不需要连接 SketchUp。计划可下载保存。
5. 在 Windows 上准备好 SketchUp 2024 与已有 Kongxing 插件后，再按 **连接 SketchUp** 教学打开独立模型并批准建模。插件未随仓库分发；下载本仓库不等于已安装插件。

本轮已真实测试 DeepSeek 的图片/文字对话与计划流程。实际 SketchUp 建模与干净 Windows 安装仍待用户验证；图片里的门窗等细节可能误读，请先核对计划。完整使用说明见 [USER_GUIDE](docs/USER_GUIDE.md)。


AI Architecture Studio is a lightweight architecture workspace that packages strong existing AI + professional-software automation around real design tools instead of rebuilding CAD or 3D engines from scratch.

## Product direction

Long term:

**任务书 + 场地 + 参考案例文字/图片/图纸 + 用户想法**  
→ 中文项目工作区 / 方案讨论  
→ replaceable Agent Runtime  
→ task Skills + persistent coding harness + professional-software bridge  
→ editable SketchUp / CAD  
→ AI render / diagrams / presentation outputs

SketchUp remains the real editable modeling application.

The website is the product shell: project inputs, conversation, project memory, approval states, outputs, history, provider routing and later packaging/billing.

## Core product thesis

The foundation model is **replaceable**. The durable product capability should be:

> **Agent Harness × Task Skill × Professional Software Bridge**

A stronger model may improve quality, but the product should not depend on one premium model to compensate for a weak workflow.

The practical evidence is already strong: direct Codex with a cost-efficient coding model can create developed SketchUp architecture from one reference image. The website must therefore reproduce the useful parts of that Agent environment rather than invent another weaker planner.

## Current milestone

**Image → SketchUp / Direct-Codex Parity v2**

Immediate target:

> one architectural reference image  
> → Sol Low / replaceable cost-efficient model  
> → dedicated Image Reconstruction Skill  
> → clarify high-impact unknowns  
> → parameter card with KNOWN / ESTIMATED / ASSUMED values  
> → user approval  
> → persistent Ruby + thin SketchUp bridge + SAIE helpers  
> → editable developed SketchUp model  
> → source-matched screenshot QA  
> → same-model correction

Do **not** combine taskbook + site + precedent into new design yet.

A few white boxes are an automatic failure when the source contains developed roof, facade, balcony, opening, railing/louver or material-depth systems.

See:

- [Current task](docs/CURRENT_TASK.md)
- [Execution guardrails](docs/EXECUTION_GUARDRAILS.md)
- [Skill-first Agent refactor](docs/SKILL_FIRST_AGENT_REFACTOR_V1.md)
- [Image → SketchUp v1](docs/IMAGE_TO_SKETCHUP_V1.md)
- [Handoff](docs/HANDOFF.md)
- [Open-source component map](docs/OPEN_SOURCE_COMPONENT_MAP.md)
- [Decisions](docs/DECISIONS.md)

## Target execution architecture

```text
Reference image(s)
      |
      v
Image Reconstruction Skill
inspect -> clarify -> parameterize -> approve
      |
      v
Replaceable coding/multimodal model
      |
      v
Persistent coding Agent harness
write/revise files -> execute -> inspect -> correct
      |
      +-------------------+
      |                   |
      v                   v
workspace Ruby          SAIE helpers
project-specific        ordinary semantic elements
      |                   |
      +---------+---------+
                v
       thin SketchUp bridge
identity / transport / readback / camera / screenshot / lifecycle
                |
                v
             SketchUp
                |
                v
source-matched screenshot -> visual mismatch -> same-model revision
```

The old rectangle-only `DesignIR -> BuildPlan -> create_mass` flow remains a legacy regression path, not the normal modeling architecture.

## Reconstruction interaction

### 1. Clarify

The Agent receives the real reference image as multimodal input and asks only questions that materially change reconstruction, normally no more than four:

- source-view-only vs multi-angle / later editing;
- model scope;
- any known dimension anchor;
- permission to infer unseen geometry and desired visible detail.

If the user already supplied an answer, do not ask it again. Unknown exact dimensions should not block progress.

### 2. Parameterize / plan

The Agent writes:

`runtime/projects/<project>/runtime/agent_workspace/notes/reconstruction_card.md`

The card separates:

- **KNOWN** — source/user-provided facts;
- **ESTIMATED** — coherent visual dimensions used as a modeling baseline;
- **ASSUMED** — conservative unseen-geometry/detail rules.

It also records levels/bays, solids/voids, facade depth, repeated components, roof/canopy, material zones and the persistent-script strategy.

The user can modify parameters or approve execution. SketchUp geometry is not edited during clarification/planning.

### 3. Execute

After approval the same Agent thread/workspace authors or revises persistent Ruby under `agent_workspace/scripts/` and executes it through the verified disposable SketchUp session.

Persistent code is the primary project-specific geometry mechanism. SAIE is a helper library, not the orchestration center.

### 4. Inspect / revise

The Agent must inspect actual source-matched and oblique screenshots, state concrete visual mismatches, revise the same scripts/model and capture again.

Tool success alone is never completion.

## Tool philosophy

Image reconstruction uses a deliberately **small coding-first tool profile**.

Primary:

- `sketchup_run_workspace_ruby` for project-specific/repeated geometry.

Helpers:

- selected SAIE wall/opening/slab/roof/query/view operations;
- Kongxing model identity, view/camera/readback/transform/undo-style operations actually exposed locally.

Hidden in reconstruction mode:

- legacy `create_mass/create_road` path;
- raw project-file eval exposed to the model;
- ArchFlow/CAD tools;
- broad overlapping tool catalogs that make cheap models choose among dozens of equivalent operations.

Tool count is not product capability. Never add fake compatibility tool names merely to match a document.

## Context philosophy

Cheap-model reconstruction context should stay small:

Include:

- actual `inputs/reference/` images as multimodal input;
- Image Reconstruction Skill;
- reconstruction parameter card / persistent workspace state;
- recent reconstruction conversation;
- SketchUp readback/screenshots during execution.

Exclude unless explicitly requested:

- taskbook;
- site;
- program;
- old DesignIR/BuildPlan;
- unrelated precedent text;
- generated outputs as source images;
- long benchmark prose.

## Reuse policy

Default engineering order:

**Adopt package → wrap/compose → vendor only the needed licensed module → minimal custom glue**

Current code donors / references:

- **Kongxing SketchUp MCP** — verified local identity/lifecycle/transport/readback bridge.
- **SAIE (MIT)** — mature walls/openings/slabs/roofs/query/view/edit helpers; the tested SketchUp 2024 path uses a small compatibility patch.
- **Supex (MIT)** — persistent project-script / execute → inspect → revise pattern and introspection ideas.
- **Stultus (Apache-2.0)** — public reference for Codex/Claude controlling SketchUp through Ruby execution, scene readback, screenshots, Undo-scoped steps, selection context and continued sessions.
- **ArchFlow Studio (Apache-2.0)** — later semantic validation/DXF/output/review pieces.
- **SketchUp Architect Skill (MIT)** — later/full architecture reasoning and design continuity.
- **ADAI SketchUp Skill + Managed MCP (CPAL-1.0)** — workflow concepts only unless a separate licensing decision permits source reuse.
- **Pylon / Building-Xuezhang** — visible quality/workflow references only when source is not publicly reusable.

Do not rewrite a geometry primitive, connector, Agent runtime or professional-software subsystem when a compatible reusable implementation already exists.

## Lessons now encoded in the repo

The prototype previously made several mistakes: tool-count chasing, synthetic white-box acceptance, broad context, premature generalization and asking the user to perform internal engineering probes.

`docs/EXECUTION_GUARDRAILS.md` now makes the corrective rules explicit:

- success-first, not architecture-first;
- copy proven working patterns before generalizing;
- do not rebuild a weaker Codex;
- do not use a stronger model to hide a harness problem;
- do not interrupt the user for non-critical internal checks;
- real visual parity before product expansion.

## Competitor/product research rule

Observed public/user-provided competitor workflows may guide product behavior. For example, a useful general pattern is:

> image → clarify important unknowns → AI proposes coherent estimated dimensions/assumptions → user confirms → modeling begins → continued edits reuse the same model.

When inspecting a competitor desktop package the user legitimately possesses, separate:

- **observed facts** — files, runtime processes, local ports, MCP tool schemas, visible approval flow;
- **inference** — likely internal responsibilities;
- **our implementation** — only public/open-source or independently authored code.

Do not bypass licensing/DRM or copy proprietary Skill/source into this public repository.

## What we do not build now

- browser CAD/3D engine;
- foundation model;
- another generic MCP framework;
- another wall/opening/roof engine;
- full taskbook/site/new-design workflow before image reconstruction parity;
- render/PPT pipeline before the modeling loop is commercially useful.

## Local development

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
.\scripts\check.ps1
```

Open `http://127.0.0.1:8787`.

Linux / Cloud development (web and Agent testing; automatic SketchUp launch requires Windows):

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-model-providers.txt
.venv/bin/python scripts/dev.py
.venv/bin/python -m pytest -q tests
```

Use the UI's model settings to supply DeepSeek credentials in memory. For a managed
secret, set `ARCH_STUDIO_API_KEY_ENV=DEEPSEEK_API_KEY` along with
`ARCH_STUDIO_ECONOMY_PROVIDER=litellm`, `ARCH_STUDIO_API_MODEL=deepseek/deepseek-flash`,
`ARCH_STUDIO_API_BASE=https://api.deepseek.com`, and
`ARCH_STUDIO_ECONOMY_REASONING_EFFORT=low`. Do not put the key in a launch command.
Official DeepSeek requests inherit environment proxy/CA settings on Linux and
ignore them on Windows by default; `ARCH_STUDIO_API_TRUST_ENV=1` or `0` explicitly
overrides that choice. Cloud tests do not establish SketchUp model quality.

When locally validated SAIE is enabled:

```powershell
$env:ARCH_STUDIO_ENABLE_SAIE = '1'
```

## Current benchmark rule

Do **not** call Astra for this milestone.

Use the same reference image and the same Sol Low setting that already succeeds in direct Codex. Compare direct Codex vs website. If the website is materially worse, inspect missing Agent-harness capability before changing the foundation model or adding another MCP.

## Later roadmap

Only after Image → SketchUp is repeatable:

**taskbook + site + precedent images + user intent**  
→ scheme discussion / precedent grammar  
→ adapt to real constraints  
→ editable SU/CAD  
→ AI render  
→ diagrams / PPT / PDF.

The later architecture workflow must reuse the same Skill/Agent/bridge foundation rather than starting another modeling engine.

## Codex start point

1. `AGENTS.md`
2. `docs/EXECUTION_GUARDRAILS.md`
3. `docs/CURRENT_TASK.md`
4. `docs/SKILL_FIRST_AGENT_REFACTOR_V1.md`
5. `docs/HANDOFF.md`
6. local Windows / SketchUp integration
7. optional competitor-desktop architecture observation described in `CURRENT_TASK.md`

Raw user reference images, generated SKP/screenshots, private source packages, API keys, private transcripts and machine paths must not be committed.
