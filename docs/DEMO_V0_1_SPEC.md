# AI Architecture Studio — Demo v0.1 Spec

## Goal

Build a working local demo that proves the product experience:

**Brief + Site + Reference + User Intent → AI design plan → editable SketchUp model → basic drawing → output preview/presentation**

The demo should feel like the beginning of the real product, not a collection of developer scripts.

## Demo user flow

1. Open the local AI Architecture Studio web app.
2. Create/open one project.
3. Add:
   - project name
   - brief file or text
   - site file/image
   - reference URL and/or reference images
   - user's design intent
4. Click **Prepare Design**.
5. The Brain produces:
   - `project_context.json`
   - `design_ir.json`
   - `build_plan.json`
6. Click/run **Build in SketchUp**.
7. SketchUp creates a real editable model with stable named objects.
8. The system reads back model state and captures a viewport.
9. A second instruction modifies the existing model without rebuilding everything.
10. Generate:
   - a basic DXF drawing from the same design state
   - a simple render/output preview
   - a simple A3 presentation board from project outputs

## UI scope

One project workspace is enough.

Tabs:

- **Design**
- **Model**
- **Drawing**
- **Render**
- **Present**

Use a simple two-column layout:
- left: inputs / chat / actions / status
- right: current artifacts / preview / model screenshot / drawing preview / board preview

Do not spend time on marketing pages, accounts, billing, team features, or complex visual polish.

## Required real capabilities

### Design

The system must be able to store and structure:
- brief
- site context
- references
- user intent
- design decisions

The Codex brain must produce a valid `DesignIR`, not only prose.

### Model

The system must use SketchUp as the actual modeling application.

For the live demo:
- use the user's already configured SketchUp MCP connection if it is usable;
- otherwise reuse/adopt an existing open-source SketchUp connector;
- do not build a generic MCP bridge from scratch unless all reuse options fail.

Minimum live model:
- site/base
- at least 3 named building/massing objects
- at least 1 circulation/public-space object
- stable IDs/names
- real editable SketchUp geometry

Then perform at least two sequential modifications against the same model:
- one height/floor change
- one position/width/size change

Capture/read back the result after each change.

### Drawing

Generate a real basic DXF from `DesignIR` / shared project state.

It does not need to be construction documentation.

Minimum:
- site boundary
- building footprints
- circulation/public space
- object labels if practical

Prefer reusing ArchFlow's ideas/code where license and integration are suitable, otherwise use a small deterministic DXF generator.

### Render

Do not train or build an image model.

Implement a `RenderAdapter` boundary.

For this demo:
- a SketchUp viewport capture is an acceptable guaranteed fallback;
- if a configured image provider is already available locally, optionally generate an AI render;
- no API key may be committed.

The adapter should make later replacement with an image-generation API straightforward.

### Present

Generate one simple A3 landscape presentation from available artifacts.

Minimum content:
- title
- short concept text
- drawing preview
- SketchUp/model image
- render/viewport image

Prefer deterministic layout generation.
HTML/CSS → PDF/PNG is acceptable.
Editable PPTX is optional for Demo v0.1, not a blocker.

## Demo data

Do not commit the user's real graduation assets.

Create a small synthetic example project in `examples/demo_project/`.

Real user assets may be read from ignored local folders only.

## Out of scope

- production cloud deployment
- authentication
- payment
- multi-user collaboration
- Rhino/Blender/Revit
- full AutoCAD control
- construction drawings
- BIM authoring
- code-compliance claims
- autonomous publishing
