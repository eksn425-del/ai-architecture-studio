# AI Architecture Studio

A lightweight AI architecture workspace that turns project inputs into an editable design workflow.

## Product flow

**Brief + Site + Reference + User Intent**  
→ AI design reasoning  
→ editable SketchUp model  
→ basic drawing  
→ render/output  
→ presentation

The product is not a browser CAD engine. SketchUp remains the real editable modeling application.

## Current milestone

**Product Alpha v0.2 — Chinese conversational architecture workspace**

Codex acts as the temporary AI brain. A single Chinese conversation area refines the structured design before modeling and sends targeted edits to the existing model afterward. Public HTTP/HTTPS references are read with a size limit and private-network protection; unreadable pages prompt for screenshots or images.

The target architecture is:

**Web Workspace → BrainAdapter → Local Connector/MCP → SketchUp**

Later, a real model API can replace the Codex brain behind the same adapter.

## Start here

Codex should read:

1. [AGENTS.md](AGENTS.md)
2. [docs/CURRENT_TASK.md](docs/CURRENT_TASK.md)
3. [Demo v0.1 Spec](docs/DEMO_V0_1_SPEC.md)
4. [Demo Architecture](docs/DEMO_ARCHITECTURE.md)
5. [Schemas](docs/SCHEMAS_V0_1.md)
6. [Open-Source Component Map](docs/OPEN_SOURCE_COMPONENT_MAP.md)
7. [Codex Demo Runbook](docs/CODEX_DEMO_RUNBOOK.md)

## Run the local demo (Windows)

From the repository folder, run:

```powershell
.\scripts\setup.ps1
.\scripts\open_blank_sketchup.ps1
.\scripts\dev.ps1
```

Open `http://127.0.0.1:8787`. The demo seeds a synthetic waterfront cultural-house project; no graduation-design files are read or modified. `open_blank_sketchup.ps1` copies SketchUp's Simple template into ignored `runtime/` before opening it, then starts the already-installed Kongxing extension through SketchUp's RubyStartup entry point.

In the workspace:

1. Add project text or files, then use **讨论与修改** to refine the design in Chinese, or use **生成方案**. The local Codex CLI writes `DesignIR` and `BuildPlan`, then the app writes a basic DXF, SVG plan preview, and A3 HTML board.
2. Confirm the active SketchUp document is disposable and click **在 SketchUp 中建模**. The app reuses the existing `kongxing_sketchup` MCP from `~/.codex/config.toml`. If the bridge needs restarting later, use **Extensions → Kongxing AI → Start Local Bridge** in SketchUp.
3. Continue in the same conversation to make a targeted change to an existing mass or straight public route. Width, depth, height, floors, and position edits preserve the stable object ID and do not rebuild the model. The app reads SketchUp state and captures the viewport after build and edits.

All uploads, generated projects, jobs, model files, screenshots, and local Codex schema files stay under ignored `runtime/` or `artifacts/`. To run checks, use `.\scripts\check.ps1`.

The Codex CLI runs with a read-only sandbox for design reasoning. If it is unavailable, the app writes a Codex Job Mode request under `runtime/jobs/` for the active Codex session. It never presents the test fake as the product brain.

## Reuse policy

Prefer:

**Adopt → Fork → Wrap/Compose → Minimal Custom Build**

High-value candidates already identified include:
- existing user SketchUp MCP setup
- SAIE
- VBO SkAgent
- ArchFlow Studio
- SketchUp Architect Skill

## Repository safety

This is a public repository.

Do not commit:
- API keys or credentials
- private graduation-design files
- private SKP/DWG files
- copyrighted reference packages
- proprietary company data
- machine-specific private paths

Runtime project data belongs under ignored local folders.
