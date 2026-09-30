# AI Architecture Studio

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

The key evidence is practical: direct Codex with a cost-efficient coding model can already produce developed SketchUp architecture from one reference image. The website must therefore first reproduce the useful parts of that Agent environment rather than invent another weaker planner.

## Current milestone

**Skill-first Image → SketchUp / Direct-Codex Parity v1**

Immediate target:

> one architectural reference image  
> → cost-efficient multimodal/coding model  
> → dedicated Image Reconstruction Skill  
> → plan / approval  
> → persistent Ruby + thin SketchUp bridge + SAIE helpers  
> → editable developed SketchUp model  
> → source-matched screenshot QA  
> → same-model correction

Do **not** combine taskbook + site + precedent into new design yet.

A few white boxes are an automatic failure when the source contains developed roof, facade, balcony, opening, railing/louver or material-depth systems.

See:

- [Current task](docs/CURRENT_TASK.md)
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
Image Reconstruction Skill / method cards
      |
      v
Persistent coding Agent harness
plan -> approve -> write/revise files -> execute -> inspect -> correct
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
identity / transport / readback / camera / view / lifecycle
                |
                v
             SketchUp
                |
                v
source-matched screenshot -> visual mismatch -> same-model revision
```

The old rectangle-only `DesignIR -> BuildPlan -> create_mass` flow remains a legacy regression path, not the normal modeling architecture.

## Reconstruction interaction

### 1. Analyze / plan

The Agent receives the real reference image as multimodal input, fills:

`runtime/projects/<project>/runtime/agent_workspace/notes/reconstruction_card.md`

and derives:

- scale/proportion assumptions;
- floor levels and bay rhythm;
- solids / voids;
- facade depth stack;
- repeated window/door/rail/louver systems;
- balcony/canopy/roof logic;
- material zones;
- persistent script/component strategy.

It proposes a compact geometry plan and waits for approval. SketchUp geometry tools are withheld during this planning turn.

### 2. Approve / execute

After approval the same Agent thread/workspace authors or revises persistent Ruby under `agent_workspace/scripts/` and executes it through the verified disposable SketchUp session.

### 3. Inspect / revise

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
- raw `sketchup_eval_project_file` exposed to the model;
- ArchFlow/CAD tools;
- broad overlapping tool catalogs that make cheap models choose among dozens of equivalent operations.

The exact live tool list is verified locally. Never add fake compatibility tool names merely to match a document.

## Context philosophy

Cheap-model reconstruction context should stay small:

Include:

- actual `inputs/reference/` images as multimodal input;
- Image Reconstruction Skill;
- reconstruction card / persistent workspace state;
- recent reconstruction conversation;
- SketchUp readback during execution.

Exclude unless explicitly requested:

- taskbook;
- site;
- program;
- old DesignIR/BuildPlan;
- unrelated precedent text;
- generated outputs as source images.

## Reuse policy

Default engineering order:

**Adopt package → wrap/compose → vendor only the needed licensed module → minimal custom glue**

Current code donors / references:

- **SAIE (MIT)** — mature walls/openings/slabs/roofs/query/view/edit helpers; the tested SketchUp 2024 path uses a small compatibility patch.
- **Kongxing SketchUp MCP** — verified local identity/lifecycle/transport bridge.
- **Supex (MIT)** — persistent project-script / execute → inspect → revise pattern and introspection ideas.
- **Stultus (Apache-2.0)** — public reference for Codex/Claude controlling SketchUp through Ruby execution, scene readback, screenshots, Undo-scoped steps, selection context and continued sessions.
- **ArchFlow Studio (Apache-2.0)** — later semantic validation/DXF/output/review pieces.
- **SketchUp Architect Skill (MIT)** — later/full architecture reasoning and design continuity.
- **ADAI SketchUp Skill + Managed MCP (CPAL-1.0)** — workflow concepts only unless a separate licensing decision permits source reuse.
- **Pylon / competitor desktop products** — visible quality/workflow references only when source is not publicly reusable.

Do not rewrite a geometry primitive, connector, Agent runtime or professional-software subsystem when a compatible reusable implementation already exists.

## Current remote refactor

ChatGPT has already prepared repo-side changes for the current local integration round:

- reconstruction lifecycle (`idle -> planned -> building`);
- explicit `agent_action = auto|plan|execute`;
- `app/reconstruction_runtime.py` for deterministic plan/execute policy and small context;
- reference-only source-image scope;
- shorter coding-first Image Reconstruction Skill;
- Direct-Codex-style persistent workspace instructions;
- `reconstruction_coding` tool profile;
- focused regression tests;
- exact Codex local tasks in `docs/CURRENT_TASK.md`.

These changes are not accepted until local Windows + SketchUp tests pass.

## Product research rule

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

When locally validated SAIE is enabled:

```powershell
$env:ARCH_STUDIO_ENABLE_SAIE = '1'
```

## Current benchmark rule

Do **not** call Astra for this milestone.

Use the same reference image and the same cost-efficient model/effort that already succeeds in direct Codex. Compare direct Codex vs website. If the website is materially worse, inspect missing Agent-harness capability before changing the foundation model or adding another MCP.

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
2. `docs/CURRENT_TASK.md`
3. `docs/SKILL_FIRST_AGENT_REFACTOR_V1.md`
4. `docs/HANDOFF.md`
5. local Windows / SketchUp integration
6. optional competitor-desktop architecture observation described in `CURRENT_TASK.md`

Raw user reference images, generated SKP/screenshots, private source packages, API keys, private transcripts and machine paths must not be committed.
