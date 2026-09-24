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

**Demo v0.1 — end-to-end local product demo**

For this demo, Codex itself acts as the temporary AI brain.

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
