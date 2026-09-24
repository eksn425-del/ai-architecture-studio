# Demo Architecture v0.1

## Product architecture

```text
Browser / Web Workspace
        |
        v
Local Backend
        |
        +---- Project Store / State
        |
        +---- BrainAdapter
        |       |
        |       +---- NOW: CodexBrainAdapter / Codex job mode
        |       |
        |       +---- LATER: Model API adapter
        |
        +---- SketchUpAdapter
        |       |
        |       +---- existing local MCP if usable
        |       +---- SAIE / VBO / other compatible OSS fallback
        |       |
        |       v
        |    SketchUp plugin/bridge
        |       |
        |       v
        |    SketchUp Desktop
        |
        +---- DrawingAdapter -> DXF
        |
        +---- RenderAdapter -> viewport now / image API later
        |
        +---- PresentationAdapter -> HTML/PDF/PNG
```

## Key principle

The website is the product interface. SketchUp is the real modeling engine.

We are not building a browser-native CAD/SketchUp replacement.

## BrainAdapter

The rest of the application must not depend directly on a specific model vendor.

Suggested interface:

- `prepare_project(context) -> DesignIR`
- `plan_build(design_ir) -> BuildPlan`
- `plan_edit(design_ir, model_state, user_instruction) -> EditPlan`
- `summarize_decisions(...) -> text/structured summary`

### Demo brain mode

For Demo v0.1, Codex itself is allowed to be the brain.

Implementation priority:

1. If the local Codex environment exposes a safe, documented non-interactive invocation usable by the demo, wrap it behind `CodexBrainAdapter`.
2. Otherwise implement **Codex Job Mode**:
   - web/backend writes a job under `runtime/jobs/<job_id>/`
   - Codex reads the request and writes structured results
   - UI/backend polls job status/results
   - Codex also performs the live SketchUp tool calls during the demo
3. Include a deterministic/mock brain only for automated UI tests; it must not be presented as the real architecture brain.

Later, a model API replaces this adapter without changing project state or SketchUp execution.

## Project state

Each local project lives under:

```text
runtime/projects/<project_id>/
  inputs/
  state/
    project_context.json
    design_ir.json
    build_plan.json
    model_state.json
    output_manifest.json
  outputs/
    model/
    drawings/
    renders/
    presentation/
  logs/
```

The whole `runtime/` tree is ignored by Git.

## SketchUpAdapter

Do not expose vendor-specific MCP tool names to the rest of the app.

Suggested internal operations:

- `ping()`
- `get_model_info()`
- `create_mass(spec)`
- `create_circulation(spec)`
- `modify_object(stable_id, patch)`
- `get_object(stable_id)`
- `capture_view()`
- `save_as(path)`

Map these operations to the existing MCP/connector chosen on the user's machine.

### Reuse order

1. Existing working MCP already configured for the user's Codex + SketchUp.
2. SAIE if compatible and stable.
3. VBO SkAgent if a lighter Codex-oriented bridge is faster.
4. Other MIT/Apache-compatible connector.
5. Minimal custom bridge only if the above fail.

## Stable IDs

Every important design object should carry a stable ID such as:

- `MASS_01`
- `MASS_02`
- `MASS_03`
- `PUBLIC_STREET_01`

Prefer connector-supported attributes/persistent IDs. If unavailable, use robust object names plus a local mapping and document the limitation.

## DrawingAdapter

Input: `DesignIR`

Output: basic DXF.

The drawing layer should be deterministic and should not depend on image generation.

## RenderAdapter

Input:
- model screenshot/current camera
- design intent
- render options

Output:
- image artifact + metadata

Demo fallback: SketchUp viewport capture.

Future: OpenAI or another image-generation API.

## PresentationAdapter

Input:
- project title/concept
- model screenshot
- drawing preview
- render/viewport image

Output:
- A3 landscape HTML
- PDF/PNG if local tooling supports export

Keep layout deterministic. The brain can decide content hierarchy later; code should place assets reliably.
