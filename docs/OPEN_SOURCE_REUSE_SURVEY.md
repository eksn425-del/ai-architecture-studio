# Open-Source Reuse Survey v0.1

Date: 2026-09-24

## Why this document exists

Before implementing the SketchUp Agent Technical Spike from scratch, we searched GitHub broadly for projects that already implement parts of — or nearly the whole of — the intended AI Architecture Studio workflow.

The operating rule is now:

**Adopt / fork / compose proven open-source components first. Build custom infrastructure only where a verified product gap remains.**

This survey is intentionally focused on code and architecture reuse, not feature inspiration.

---

## Tier A — Highest-value candidates

### 1. ArchFlow Studio

Repository: https://github.com/bingxijun/archflow-studio

License: Apache-2.0 for source code. Project branding/media have separate restrictions; preserve required notices.

Why it matters:

ArchFlow is the closest public repository found to the overall AI Architecture Studio system concept.

Its documented workflow already connects:

- design requirements
- site CAD data
- sourced regulatory evidence
- a semantic building model
- CAD output
- SketchUp model generation
- view capture
- AI-assisted concept rendering
- Codex orchestration
- project/run records and approval gates

Its central source of truth is `building_model.json`.

Its architecture is split into:
- CAD Bridge
- Design Core
- Orchestrator

It can generate semantic DXF, SketchUp Ruby, standard views, review/metrics artifacts, and render handoff data.

### Reuse hypothesis

**Candidate product/orchestration backbone.**

Do not recreate project packaging, run records, semantic model generation, validation, CAD/SketchUp handoff, or render-handoff concepts until ArchFlow has been tested and its internal architecture inspected.

Potential gaps relative to our product:
- user-facing Web Workspace
- precedent/case-to-design workflow
- long-lived conversational design UX
- product-specific project history and billing
- broader continuous editing UX

---

### 2. SAIE — SketchUp Automation & Intelligence Engine

Repository: https://github.com/iamahsanmehmood/saie

License: MIT

Why it matters:

SAIE is a comparatively broad SketchUp execution layer. Its README describes a strict declarative JSON-RPC contract with a SketchUp bridge and a large MCP tool surface.

Documented capabilities include:
- model/scene inspection
- create/modify/delete walls
- openings
- slabs and roofs
- components
- layers/materials
- BIM metadata
- screenshots/canonical views
- reports and clash detection
- DXF parsing
- model open/save
- project lifecycle
- live browser view
- batch operations
- optional raw Ruby execution

### Reuse hypothesis

**Primary candidate for the SketchUp connector/execution layer.**

If its integration is stable on the user's Windows + SketchUp environment, we should prefer adapting SAIE over writing another Ruby bridge, socket protocol, model query layer, screenshot layer, and dozens of basic tools.

Key due-diligence questions:
- real-world stability
- test coverage
- state identity semantics
- transaction / undo safety
- compatibility with Codex
- API/tool surface quality
- whether it is easy to embed rather than only use as a standalone package

---

### 3. VBO SkAgent

Repository: https://github.com/vbosolution/vbo-sk-agent

License: MIT

Why it matters:

A lightweight AI-agent bridge for SketchUp with explicit OpenAI Codex support.

Documented transports:
- MCP HTTP
- file-based fallback

Documented properties:
- AI-written Ruby execution
- stdout/error capture
- multi-instance awareness
- safety confirmation
- session trust
- SketchUp 2017+ compatibility
- fast local MCP bridge

### Reuse hypothesis

**Fastest fallback for proving Codex ↔ SketchUp live control.**

This may be valuable if SAIE is too heavy or difficult to integrate.

It is less deterministic than our preferred production architecture because arbitrary Ruby execution is a central capability, but it can dramatically shorten the first proof-of-connection.

---

### 4. SketchUp Architect Skill

Repository: https://github.com/Mentat-Uran/sketchup-architect-skill

License: MIT

Why it matters:

This is unusually close to the proposed Design Copilot logic.

Its stated scope includes:
- real architectural precedent research
- turning sparse briefs into program / area / organization / circulation / site logic
- adapting precedent principles rather than copying recognizable forms
- precise editable SketchUp Desktop modeling
- model audit
- protected revisions
- save/reopen/export evidence
- architectural reasoning and QA

### Reuse hypothesis

**Primary candidate for the architecture-domain reasoning/skill layer.**

Instead of writing architectural-agent prompting and case-study methodology from zero, inspect whether this Skill can be:
- used directly,
- adapted,
- or decomposed into project-specific architectural reasoning modules.

---

## Tier B — Strong architectural references, but not necessarily code to copy

### 5. SketchUp PlanFloor AI Agent

Repository: https://github.com/zhixiangggggggg/sketchup-planfloor-ai-agent

License: no top-level license file was detected during initial review. Treat as **study-only until reuse rights are clarified**.

Why it matters:

It implements a strong constrained-agent pattern:

Natural language  
→ intent/room parsing  
→ template or CP-SAT planning  
→ independent validation  
→ wall/opening topology  
→ transactional SketchUp execution  
→ model readback and independent verification

It also uses:
- Agent Skills
- canonical JSON schemas
- pre-execution gates
- transaction/abort behavior
- deterministic geometry
- post-commit verification

### Reuse hypothesis

Even if code cannot be copied, its **architecture pattern** is highly relevant to safe architectural execution:
AI proposes a structured BuildPlan; deterministic code validates and executes it.

This aligns closely with our principle:

**Explore Loose, Produce Strict.**

---

### 6. SketchUp Agent Control

Repository: https://github.com/gregtysick/sketchup-agent-control

License: MIT

Why it matters:

A safety-first local bridge aimed at Codex/AI coding agents.

Important ideas:
- read-only first
- strict named commands
- persistent IDs
- atomic JSON queue
- backups
- one undoable SketchUp operation per approved command
- visual evidence
- no arbitrary Ruby by default

### Reuse hypothesis

Useful reference for production safety, object identity, undo, backups, and controlled command schemas.

---

### 7. minimal SketchUp MCP implementations

Examples:
- https://github.com/mhyrr/sketchup-mcp
- https://github.com/sheares/sketchup-mcp
- https://github.com/hueflowstudio/hueflow-sketchup-mcp

These demonstrate the common architecture:

MCP client  
→ Python MCP server  
→ local TCP bridge  
→ SketchUp Ruby extension  
→ SketchUp Ruby API

They are useful as implementation references, but we should not default to building yet another minimal bridge if SAIE / ArchFlow / VBO already satisfy the need.

Notes:
- Hueflow declares MIT and repackages prior SketchUp MCP work.
- sheares/sketchup-mcp is a very small v0 personal project and is described as generative rather than agentic.
- always verify the exact license before copying source.

---

## Future connectors — do not implement now

### Rhino

Official / high-value:
https://github.com/mcneel/RhinoAI

License: MIT

McNeel now provides an official Rhino MCP platform for AI agents to create/edit Rhino models.

Conclusion:
**Do not build a Rhino connector from scratch later unless the official platform cannot support a required workflow.**

Additional community option:
https://github.com/jingcheng-chen/rhinomcp

It includes viewport capture, document queries, geometry tools, Grasshopper operations, undo/redo, scripting, and Codex setup.

### Blender

A mature ecosystem of Blender MCP repositories already exists, e.g.:
https://github.com/ahujasid/mcp-for-blender

Conclusion:
Blender support should later be integration work, not foundational bridge invention.

### AutoCAD / CAD

Multiple MCP projects already exist, including:
- https://github.com/zh19980811/Easy-MCP-AutoCad
- https://github.com/AnCode666/multiCAD-mcp
- https://github.com/puran-water/autocad-mcp

Conclusion:
Do not start by writing a CAD bridge from zero. Evaluate existing connectors when CAD becomes a real MVP requirement.

---

## Current product-level conclusion

We did **not** find one repository that obviously provides the exact desired commercial product:

Reference Case + Brief + Site + User Intent  
→ Conversational Design Copilot  
→ Editable SketchUp Scheme  
→ Continuous Editing  
→ Drawings  
→ Render  
→ Presentation  
→ polished lightweight Web Workspace

However, a large share of the technical stack already exists.

The strongest composition hypothesis is currently:

### Product/orchestration backbone
**ArchFlow Studio**

plus

### SketchUp execution layer
**SAIE** (preferred to evaluate first)

with

### architecture reasoning / precedent workflow
**SketchUp Architect Skill**

and possibly

### fast proof-of-connection fallback
**VBO SkAgent**

Our differentiation should therefore move upward from "we built a SketchUp MCP bridge" to:

- case-to-design
- brief/site/reference synthesis
- architectural project state
- simple user-facing workspace
- model-aware conversational iteration
- student/junior-designer workflow
- render/drawing/presentation continuity
- lower-friction packaging and onboarding

---

## License rule

Before copying, vendoring, forking, or redistributing code:

1. confirm the repository license,
2. retain required copyright/license notices,
3. follow NOTICE/attribution requirements,
4. do not copy code from a repository with no explicit reuse license,
5. separate trademark/logo/media rights from source-code rights.

"Public on GitHub" does not automatically mean "free to copy commercially."

---

## Engineering rule going forward

For every major subsystem, Codex must answer in this order:

1. Does a compatible open-source implementation already exist?
2. Is its license compatible?
3. Can we adopt it directly?
4. Can we fork/extend it?
5. Can we wrap it behind our own interface?
6. Only if the above fail: implement from scratch.

This rule should be enforced before substantial custom engineering.
