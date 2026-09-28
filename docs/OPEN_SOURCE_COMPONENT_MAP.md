# Open-Source Component Map — OSS Takeover v1

This document is now an implementation map, not a competitor-reading list.

Rule: **Adopt package → wrap/compose → vendor only the needed licensed module → minimal custom glue.**

## 1. SAIE — primary execution takeover candidate

Repository: `iamahsanmehmood/saie`

License: MIT.

Current upstream documentation describes:

- 67+ MCP tools;
- wall creation/modification and true door/window openings;
- polygon slabs and pitched/gable/shed/hip roofs;
- components, materials and layers;
- BIM metadata and entity queries;
- deep scan / model verification / reports / clash detection;
- view control, snapshots, canonical captures and live view;
- DXF parsing;
- batch operations;
- optional raw Ruby.

Upstream currently targets SketchUp 2025. Local compatibility must be proven before enabling it.

### Current repository integration

ChatGPT already added an opt-in package adapter rather than reimplementing SAIE:

- `app/oss_backends.py` wraps standards-compliant installed MCP servers through the official Python MCP SDK;
- `app/agent_tools.py` exposes imported tools under names such as `saie__create_wall`;
- whole-document lifecycle tools and raw `execute_ruby` are blocked from the imported surface;
- `scripts/setup.ps1 -InstallSaie` installs the upstream package only;
- `ARCH_STUDIO_ENABLE_SAIE=1` enables discovery after the local SketchUp plugin is verified.

### Local decision still required

Codex must inspect the actual installed SketchUp version and upstream package/plugin version, install the real SAIE plugin when compatible, prove bridge connectivity, list the actual tool surface, and run a deterministic no-LLM geometry smoke.

Do not clone/rewrite SAIE's wall/opening/slab/roof engine inside this repo.

## 2. Existing Kongxing SketchUp MCP — keep as verified identity/lifecycle bridge

The existing local Codex → Kongxing → SketchUp path already provides:

- verified disposable-model identity/path/GUID checks;
- existing local named tools;
- viewport capture;
- transport for guarded project Ruby;
- model checkpoint/save-copy behavior.

It remains valuable even if SAIE supplies richer semantic geometry.

Target relationship:

**Kongxing = verified local bridge/lifecycle + fallback tools**  
**SAIE = mature semantic modeling/query/view capability**

Do not remove Kongxing just to make the stack look cleaner.

## 3. Supex — agentic coding and advanced geometry reference/reuse candidate

Repository: `darwin/supex`

License: MIT.

Upstream documents:

- full SketchUp Ruby API execution;
- project-local modeling scripts under version control;
- model introspection and screenshots;
- Ruby runtime / REPL;
- SKP/OBJ/STL/image export;
- VCAD sidecar with BRep operations such as booleans, fillet, chamfer, shell, extrude, revolve, sweep, loft and patterns.

Current upstream caveat: early-stage, primarily tested on macOS with SketchUp 2026 / Claude Code.

### Reuse decision

For the current Windows milestone, reuse the **workflow architecture** immediately:

- dedicated writable agent workspace;
- persistent generated scripts;
- execute → introspect → screenshot → revise loop.

Do not port the entire Supex/VCAD stack to Windows unless upstream already contains a supported path that local Codex can adopt with little work.

## 4. ArchFlow Studio — semantic CAD/state/output takeover candidate

Repository: `bingxijun/archflow-studio`

License: Apache-2.0 for source. Upstream branding/media have separate restrictions.

Upstream currently documents:

- parsed requirements drafts;
- semantic `building_model.json` source of truth;
- project package / immutable run records;
- validation and metrics;
- semantic DXF;
- generated SketchUp Ruby;
- standard-view data and human review reports;
- CAD bridge and render handoff.

### Reuse decision

Stop treating ArchFlow as inspiration only. Local Codex must inspect importable modules/CLI entry points and adopt/wrap concrete code for any of these that can replace our legacy rectangle-only drawing/output path with little glue.

Do not fork the whole application.

## 5. SketchUp Architect Skill — keep for design reasoning, not execution primitives

Repository: `Mentat-Uran/sketchup-architect-skill`

License: MIT.

Already vendored selectively with license preservation.

Useful areas:

- brief/program reasoning;
- adjacency and plan/section coordination;
- precedent research/adaptation;
- model continuity and revision;
- Ruby modeling guidance;
- visual/model QA.

Current product override: user-requested strong precedent adaptation is allowed. The Skill must not flatten a deliberate reference into generic boxes merely to satisfy generic anti-copy wording.

## 6. VBO SkAgent — lightweight fallback

Repository: `vbosolution/vbo-sk-agent`

License: MIT according to the existing survey.

Useful if the active local bridge is blocked:

- Codex-oriented live control;
- MCP HTTP + file fallback;
- direct Ruby path;
- trust/safety workflow.

Do not add it while Kongxing + SAIE already cover the required path.

## 7. SketchUp Agent Control — safety pattern source

Repository: `gregtysick/sketchup-agent-control`

Useful patterns:

- read-only inspection first;
- persistent IDs;
- fixed commands;
- backup/undo;
- visual evidence.

Borrow patterns only where they fill a real gap.

## 8. PlanFloor AI Agent — study-only until license is verified

Repository currently tracked as `zhixiangggggggg/sketchup-planfloor-ai-agant` in upstream README references.

Public README describes:

```text
natural language
→ intent and room parsing
→ template / CP-SAT solver
→ independent validation
→ wall topology + openings
→ transactional SketchUp execution
→ independent readback
```

It also describes 16 SketchUp Skills covering boxes, floors, walls, doors, windows, rooms, whole-house layouts, furniture, inspection, execution and repair.

No compatible top-level license has been established in this project. Study architecture/tool boundaries only. Do not copy source until license is confirmed.

## 9. LiteLLM — provider compatibility only

Repository: `BerriAI/litellm`

The project already uses an optional LiteLLM dependency for provider adaptation. Keep it limited to model/provider request/response compatibility. Do not let model routing distract from the current execution-stack gap.

## Current takeover order

1. Validate ChatGPT's remote OSS composition code.
2. Check local SketchUp version.
3. If compatible, install and prove real SAIE package/plugin.
4. Run deterministic no-LLM SAIE/Kongxing smoke model.
5. Restore a project-local writable Codex agent workspace using App Server `workspace-write`, with source inputs excluded from writable roots.
6. Inspect/adopt concrete ArchFlow CAD/state/output modules.
7. Take Supex workflow patterns; only take runtime code if platform-compatible.
8. Study PlanFloor architecture without copying unlicensed code.
9. Only then run a cheap model orchestration test.
10. Reserve Astra for one final parity check after the tool gap is closed.

## Takeover rule

If Codex is about to implement a wall/opening/slab/roof/BIM/query/view/CAD subsystem from scratch, it must first show why the corresponding reusable component above cannot be adopted or wrapped.
