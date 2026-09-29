# AI Architecture Studio

AI Architecture Studio is a lightweight architecture workspace that packages strong existing AI + open-source professional-software automation around real design tools instead of rebuilding CAD or 3D engines from scratch.

## Product direction

The long-term product remains:

**任务书 + 场地 + 参考案例文字/图片/图纸 + 用户想法**  
→ 网站中的中文对话与项目上下文  
→ replaceable Agent Runtime  
→ Skills + composed reusable OSS tools  
→ editable SketchUp / CAD  
→ screenshot/readback/revision  
→ drawing / render / presentation outputs

SketchUp remains the real editable modeling application.

The website is the product shell: inputs, project/session memory, conversation, outputs, version/history, provider routing, and later packaging/billing.

## Current milestone

**Image → SketchUp v1 — first make one reference image reliably become a developed editable SketchUp model with a cost-efficient model.**

Do **not** combine taskbook + site + precedent yet.

The current target is intentionally narrow:

> upload one architectural facade/exterior image  
> → cost-efficient multimodal Sol-class model  
> → dedicated image-reconstruction Skill + mature SketchUp tools  
> → editable SketchUp reconstruction  
> → source-matched screenshot QA  
> → same-model correction

A few white boxes are an automatic failure when the source image visibly contains developed facade/roof geometry.

The user-provided PylonLab demonstration is the immediate visual quality reference: a single facade image becomes a multi-storey SketchUp model with repeated glazing bays, balconies, rails, layered facade depth, a special ground-floor zone, roof pergola/louvers and basic material zoning. The observed `pylon-sketchup2model` Skill appears private; no public source has been established, so no Pylon code is copied.

See:

- [Current task](docs/CURRENT_TASK.md)
- [Image → SketchUp v1](docs/IMAGE_TO_SKETCHUP_V1.md)
- [Handoff](docs/HANDOFF.md)
- [Open-source component map](docs/OPEN_SOURCE_COMPONENT_MAP.md)
- [Decisions](docs/DECISIONS.md)
- [Thesis Astra modeling case](docs/THESIS_MODELING_CASE_STUDY.md)

## Current execution architecture

```text
Web Workspace
  -> workflow router
      -> Image Reconstruction Skill (current focus)
      -> Architecture Design Skill (later/full design)
  -> Agent Runtime
      -> source image as multimodal input
      -> persistent reconstruction card + project workspace
      -> composed tool surface
          -> Kongxing SketchUp MCP (verified local identity/lifecycle)
          -> SAIE semantic tools (wall/opening/slab/roof/query/edit)
          -> persistent workspace Ruby (repeated/custom facade geometry)
          -> optional ArchFlow artifacts
      -> SketchUp
      -> source-matched screenshot / readback / revision
```

The old rectangle-only `DesignIR -> BuildPlan -> create_mass` flow remains a regression/legacy path, not the normal modeling architecture.

## Image reconstruction workflow

The repo now seeds a persistent:

`runtime/projects/<project>/runtime/agent_workspace/notes/reconstruction_card.md`

Before substantial geometry the Agent should record:

- source view type and confidence;
- inferred scale anchor;
- overall proportions;
- floor lines and bay rhythm;
- major solids/voids;
- facade depth stack;
- repeated windows/doors/railings/louvers;
- balcony/canopy/roof logic;
- material/color zones;
- unseen-depth assumptions.

Then build in three passes:

1. **Primary recognizable form** — envelope, levels, bays, large voids, balconies, main roof/canopy.
2. **Facade system** — repeated glazing/door modules, frames, rails, fins/louvers, soffits, piers and material zones.
3. **Visual QA** — source-matched view + oblique view, explicit mismatch list, correction on the same model/scripts.

Tool success alone is never completion.

## Reuse policy

Default engineering order:

**Adopt package → wrap/compose → vendor only the needed licensed module → minimal custom glue**

Current components:

- **SAIE (MIT)** — mature walls/openings/slabs/roofs/components/materials/BIM/query/view/batch/DXF surface. A small local compatibility patch is already validated for the tested SketchUp 2024.0.484 wall/opening/slab/roof/query/edit path.
- **Kongxing SketchUp MCP** — existing verified local identity/lifecycle bridge and named-tool fallback.
- **ArchFlow Studio (Apache-2.0 source)** — semantic state, validation/metrics, DXF/output, generated Ruby and review artifacts where useful.
- **Supex (MIT)** — persistent project-script / execute → inspect → revise patterns and exact-entity introspection ideas.
- **Stultus (Apache-2.0)** — useful public reference for Codex/Claude controlling SketchUp 2024 through Ruby execution, scene readback, screenshots, Undo-scoped steps, selection context and continued sessions. Reuse only portable pieces that improve the current stack; do not replace a working connector just to copy its architecture.
- **SketchUp Architect Skill (MIT)** — retained for later/full architecture reasoning and design continuity.
- **ADAI SketchUp Skill + Managed MCP (CPAL-1.0)** — study its source-first reconstruction, method/task-card, guided/autonomous, visual-evidence and experience-pack ideas. Do not copy covered source into this commercial repository without an explicit license/compliance decision.
- **Pylon `pylon-sketchup2model`** — visual product reference only from user-provided screenshots; no public source established.

Do not build a new geometry primitive or professional-software subsystem when a compatible reusable implementation already exists.

## Current product foundation

The local product includes:

- Simplified-Chinese workspace;
- project-local reference-image discovery for multimodal turns;
- explicit Economy / Premium routing;
- existing Kongxing MCP reuse;
- optional namespaced SAIE and ArchFlow composition;
- guarded task-specific Ruby;
- persistent project-local writable Codex agent workspace;
- `notes/reconstruction_card.md` for image-driven reconstruction;
- real editable SketchUp model control;
- viewport capture/readback;
- same-file/same-model script revision;
- legacy DXF / presentation outputs;
- `/showcase` thesis modeling case study.

## What we do not build

Unless a future task explicitly requires it, this project does not build:

- a browser CAD engine;
- a new 3D modeling engine;
- a foundation model;
- a new generic MCP framework;
- another custom wall/opening/roof/BIM engine;
- a replacement for working open-source/local connectors;
- a large Windows port of an experimental stack merely for architectural cleanliness.

Most project code should stay focused on glue, adapters, project/session management, safe orchestration, context, workflow UX, packaging, and delivery.

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

When the locally validated SAIE backend is enabled:

```powershell
$env:ARCH_STUDIO_ENABLE_SAIE = '1'
```

The website composes upstream tools under names such as `saie__create_wall` beside Kongxing and the guarded workspace-Ruby path.

## Budget rule for the current milestone

Do **not** call Astra for Image → SketchUp v1.

The first real reconstruction benchmark must use the Economy Sol route, starting at low reasoning. Only if the multimodal/tool workflow is proven correct and Sol Low cannot follow the guided Skill may one Sol Medium retry be used. Record both separately.

The goal is specifically to prove that a relatively inexpensive model becomes useful because the product supplies the reconstruction method, tool recipes, persistent parameters and screenshot feedback loop.

## Later roadmap

After image reconstruction is repeatable:

**taskbook + site + precedent images + user intent**  
→ precedent grammar / reference reconstruction  
→ adapt to real constraints  
→ create a new design  
→ editable SU / CAD / render / presentation.

That later phase must reuse the Image → SketchUp reconstruction stack rather than starting another modeling engine.

## Codex start point

Codex / Sol should start with:

1. `AGENTS.md`
2. `docs/CURRENT_TASK.md`
3. `docs/IMAGE_TO_SKETCHUP_V1.md`
4. `docs/HANDOFF.md`
5. `app/image_to_sketchup_skill.py`
6. `app/reference_assets.py`
7. `app/codex_parity.py`
8. `app/main.py`
9. `app/static/index.html`
10. `app/static/studio.js`

Raw user reference images, generated SKP/screenshots, private thesis/source packages, API keys, historical private transcripts, and machine paths must not be committed.
