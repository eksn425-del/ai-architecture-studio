# Handoff — AI Architecture Studio Demo v0.1

## Current milestone

Demo v0.1 is implemented, tested, and exercised against the existing local SketchUp MCP. The requested milestone is complete; no later-stage work was started.

## Architecture chosen

- FastAPI backend, local static HTML/CSS/JavaScript workspace, and a runtime project store under ignored `runtime/`.
- `CodexBrainAdapter` invokes the local Codex CLI for schema-constrained `DesignIR`, `BuildPlan`, and edit plans. If Codex is unavailable, the app writes a recoverable Codex Job Mode package.
- The backend compiles geometry operations and validation IDs from the accepted DesignIR before execution, so connector calls only target stable IDs present in that design.
- `SketchUpAdapter` is a thin stdio client for the user's configured `kongxing_sketchup` MCP. It reads the existing `~/.codex/config.toml` entry and starts the configured server for each operation. The installed Kongxing extension/Bridge remains the SketchUp integration; this repository adds no replacement bridge.
- `open_blank_sketchup.ps1` makes a copy of SketchUp's Simple template in ignored runtime storage. Its `-RubyStartup` helper starts the already-installed extension in the active disposable document.
- Deterministic DXF/SVG generation and an A3 landscape HTML presentation use the shared design state. SketchUp viewport capture supplies the render fallback.

## Open-source reuse

- Reused the existing locally configured Kongxing SketchUp MCP and extension; wrapped their existing tools. Their installed source/configuration was not copied into this repository.
- No source was vendored from SAIE, VBO SkAgent, ArchFlow Studio, or other surveyed repositories. The DXF generator is a small project-local implementation.
- Runtime packages are declared in `requirements.txt`, installed in the local virtual environment, and not vendored: FastAPI (MIT), Uvicorn (BSD-3-Clause), Pydantic (MIT), ezdxf (MIT), python-multipart (Apache-2.0), pypdf (BSD-3-Clause), python-docx (MIT), httpx (BSD-3-Clause), and pytest (MIT). Their upstream license files remain with the installed distributions.

## Completed

- Project context, DesignIR, BuildPlan, ModelState, and OutputManifest schemas and local persistence.
- Brief/site/reference uploads, text extraction for supported brief formats, DXF boundary import, and project/job APIs.
- Codex CLI brain boundary, strict JSON-schema output, deterministic validation, correction retry, and Job Mode fallback.
- Design, Model, Drawing, Render, and Present views in the local workspace.
- Editable site base, three named masses, circulation geometry, model-wide readback, safe copy-save, and two sequential edits against one SketchUp model.
- Basic DXF and SVG, viewport screenshots, and an A3 HTML presentation preview.
- Resume support for a partial build after a save failure without recreating completed geometry.

## Important files

- `app/main.py` — app/API workflow, validation, build/edit/resume, artifacts.
- `app/brain.py` — Codex BrainAdapter and safe operation compilation.
- `app/sketchup_mcp.py` — thin client/adapter for the existing configured MCP.
- `app/models.py`, `app/store.py`, `app/generators.py` — schemas, persistence, drawings and presentation.
- `app/static/` — local workspace UI.
- `scripts/` — setup, launch, SketchUp disposable-copy startup, demo, and check scripts.
- `examples/demo_project/project_context.json` — synthetic seed project.
- `tests/` — schema, upload/store, generator, connector adapter, job, build/edit and resume checks.
- `README.md`, `.gitignore`, `requirements.txt`, `docs/HANDOFF.md`.

## Run instructions (Windows)

From the repository root:

```powershell
.\scripts\setup.ps1
.\scripts\open_blank_sketchup.ps1
.\scripts\dev.ps1
```

Then open `http://127.0.0.1:8787`. Use the seeded Tidal Commons project, prepare the design, confirm that the active document is the disposable blank model, build, and apply the two edits. To restart a stopped extension Bridge manually, use SketchUp's **Extensions → Kongxing AI → Start Local Bridge** menu item.

Run checks with:

```powershell
.\scripts\check.ps1
```

## Tests / checks

- `scripts/check.ps1` — **10 passed**. One upstream Starlette deprecation warning remains for using `httpx` with `starlette.testclient`.
- Local API status reported the app ready, Codex CLI available, and the existing SketchUp MCP configured.
- The real API flow generated 6 DesignIR objects, a 7-operation compiled BuildPlan, two drawing artifacts, and one presentation artifact.
- Generated DXF reopened through ezdxf and contained 7 `LWPOLYLINE` entities.
- Brief upload test verified both the file and its path in `ProjectContext`.

## Acceptance criteria

1. Local web app launches — **PASS** (`127.0.0.1:8787`, FastAPI health endpoint and workspace served).
2. Synthetic project can be created/loaded — **PASS**.
3. Inputs are stored into ProjectContext — **PASS** (upload persistence check).
4. Codex produces structured DesignIR and BuildPlan for the seeded demo — **PASS** (live Codex CLI; safe operation IDs are compiled from DesignIR).
5. Existing SketchUp connection is reused — **PASS** (configured Kongxing MCP and installed extension; no replacement server built).
6. Live SketchUp creates 3 editable named masses plus circulation — **PASS** (3 masses, site base, route; 5 mapped objects and 6 model entities including SketchUp's template person).
7. Two sequential edits operate on the same model — **PASS** (reading mass raised from 2 to 3 floors; workshop moved +3 m in X; connector IDs and model name remained stable).
8. Model state/readback is persisted — **PASS** (same-model readback, five stable-ID mappings, edit patches and copy-save path persisted).
9. Real basic DXF is generated — **PASS** (site, mass footprints and route; DXF reopened and parsed).
10. Render/viewport artifact is produced — **PASS** (initial and after each edit).
11. A3 presentation preview is generated — **PASS** (HTML preview includes drawing and viewport image).
12. Private assets/secrets are not committed — **PASS** (runtime, artifacts, `.skp`, and `.dwg` ignored; only synthetic project is tracked).
13. Open-source licenses/notices are respected — **PASS** (no external source code vendored; dependency licenses remain with their upstream distributions).
14. HANDOFF has exact run instructions and honest evidence — **PASS**.

## Live SketchUp evidence

- Used a copied SketchUp Simple template named `blank-disposable-20260926-220355.skp` in ignored runtime storage. Its SHA-256 matched the installed Simple template after both edits; it remained a disposable blank source model. The generated project model is saved separately at `runtime/projects/demo-cultural-center/outputs/model/demo-cultural-center.skp` through SketchUp's `Model#save_copy` API.
- The existing MCP reported model `blank-disposable-20260926-220355`, units `inch`, and 6 entities throughout the build and both edits. Five generated objects had stable IDs: `site-base`, `reading-mass`, `workshop-mass`, `gallery-mass`, and `public-route`.
- After edit 1, `reading-mass` was 3 floors / 10.8 m. After edit 2, `workshop-mass` origin was `[39, 30, 0]` m. No geometry was regenerated for either edit.
- Viewport evidence is local and ignored: `outputs/renders/model-initial.png`, `outputs/renders/edit-058faf37.png`, and `outputs/renders/edit-d605ce4f.png`.
- One initial save attempt found that the installed extension did not provide the called `Model#save_as` method. The adapter now calls `Model#save_copy`, which is the SketchUp model API for saving a copy without changing the active model path. The partial-build resume path completed the live save without duplicate geometry.

## Known issues / limits

- Render output is the SketchUp viewport, not a photorealistic AI render.
- Connector readback is model-level (model name, units, entity count and bounds); per-object values are maintained by the app's stable-ID/entity-ID map.
- The demo uses schematic rectangular massing and a synthetic site. It is not a BIM authoring system.
- Automated checks emit one Starlette `TestClient`/httpx deprecation warning; all 10 checks pass.

## Blockers

None for Demo v0.1.

## Recommended next step

Stop at Demo v0.1 as requested. Any later milestone should be explicitly started by the user.
