# Product & Architecture Decisions

## D-001 — Product form

**Status:** Accepted

Use a hybrid architecture:

**Web Workspace + Local Professional-Software Connector**

The web layer will eventually manage project context, chat, files, results, and history. Local connectors/plugins will control professional design software.

## D-002 — First professional software

**Status:** Accepted

Start with **SketchUp**.

Reason: it matches the first benchmark workflow and is widely used by architecture students and junior designers.

## D-003 — First technical milestone

**Status:** Accepted

Do not build the full web product first.

Validate:

Project Context  
→ Agent  
→ SketchUp  
→ Model  
→ Inspect  
→ Modify

## D-004 — Development model routing

**Status:** Accepted

- GPT-5.6 Sol High: product planning, architecture decisions, and review.
- GPT-6 Luna Max or another execution agent: implementation, testing, repetitive engineering work.
- Astra is not required for routine development.

## D-005 — Public repository safety

**Status:** Accepted

Do not commit private graduation-design files, copyrighted reference packages that cannot be redistributed, API keys, secrets, proprietary company materials, or private machine paths.

## D-006 — Human-in-the-loop

**Status:** Accepted

Major design-direction changes require user approval. Ordinary recoverable engineering actions should be handled autonomously.


## D-007 — Reuse-first engineering policy

**Status:** Accepted

Before implementing any major subsystem, search for compatible open-source implementations and evaluate license, maturity, safety, and integration cost.

Decision order:

**Adopt → Fork → Compose/Wrap → Minimal Custom Build**

Custom infrastructure is justified only when existing projects cannot meet the requirement or create unacceptable product/technical risk.

Current high-priority reuse candidates:
- ArchFlow Studio — orchestration/product backbone candidate
- SAIE — SketchUp execution layer candidate
- SketchUp Architect Skill — architecture reasoning/precedent workflow candidate
- VBO SkAgent — lightweight live-control fallback

The product's intended differentiation is above the connector layer: case-to-design, architectural project context, workflow UX, continuous model-aware iteration, and end-to-end student/junior-designer delivery.


## D-008 — Demo v0.1 architecture

**Status:** Accepted

Build a local end-to-end product demo rather than another research-only spike.

Architecture:

**Web Workspace → BrainAdapter → Local Connector/MCP → SketchUp**

SketchUp remains the real editable modeler. The web app is the product interface, not a replacement CAD engine.

## D-009 — Codex as temporary demo brain

**Status:** Accepted

For Demo v0.1, Codex itself may perform the architectural reasoning and tool orchestration.

The product code must isolate reasoning behind a BrainAdapter/job boundary so a production model API can replace Codex later without rewriting project state or downstream execution.

## D-010 — Existing MCP first

**Status:** Accepted

The user's already-working Codex → MCP → SketchUp connection is the first integration candidate.

Do not replace it unless it lacks required capabilities.

Fallback order:
1. existing local MCP
2. SAIE
3. VBO SkAgent
4. other compatible OSS
5. minimal custom bridge only as last resort

## D-011 — Demo vertical slice

**Status:** Accepted

Demo v0.1 must attempt the complete thin slice:

DesignIR → editable SketchUp model → sequential edits → basic DXF → viewport/render artifact → simple A3 presentation.

This milestone prioritizes a working integrated demo over extensive additional planning documents.
