# Open-Source Component Map for Demo v0.1

This document turns the earlier survey into implementation priorities.

## 1. Existing local SketchUp MCP — first choice

The user already has a Codex → MCP → SketchUp workflow that can model in SketchUp.

Codex must inspect the actual local configuration first.

If it already supports:
- create/edit geometry
- model query/readback
- stable enough object targeting
- viewport capture or equivalent evidence

then **reuse it for the demo**.

Do not replace a working local bridge merely to standardize architecture.

## 2. SAIE — preferred reusable SketchUp execution candidate

Repository:
https://github.com/iamahsanmehmood/saie

Initial survey found:
- MIT license
- broad SketchUp tool surface
- scene/model query
- walls/openings/slabs/roofs
- attributes/metadata
- screenshots/canonical views
- model lifecycle
- batch operations
- localhost-oriented bridge/security options

Use it if it shortens the demo and is compatible with the user's environment.

Do not vendor the entire project unless needed. Prefer package/adaptor integration when practical.

## 3. VBO SkAgent — fast Codex-oriented fallback

Repository:
https://github.com/vbosolution/vbo-sk-agent

Initial survey found:
- MIT license
- explicit OpenAI Codex support
- MCP HTTP + file-based fallback
- direct Ruby execution
- safety confirmation/session trust

Use it when the priority is proving live Codex ↔ SketchUp control quickly and the existing MCP/SAIE route is blocked.

Because arbitrary Ruby execution is powerful, keep it localhost-only and use blank/disposable test models.

## 4. ArchFlow Studio — reuse concepts/code selectively

Repository:
https://github.com/bingxijun/archflow-studio

Initial survey found:
- Apache-2.0 source
- semantic `building_model.json`
- project package/run records
- CAD bridge
- SketchUp generation
- semantic DXF
- render handoff

For Demo v0.1, inspect and reuse only pieces that clearly save time:
- project package/state ideas
- semantic-model conventions
- DXF generation
- run/output manifests

Do not fork the whole product merely because it overlaps conceptually.

## 5. SketchUp Architect Skill — architecture reasoning reference/reuse candidate

Repository:
https://github.com/Mentat-Uran/sketchup-architect-skill

Initial survey found:
- MIT license
- brief/program reasoning
- precedent research
- design adaptation rather than direct copying
- editable SketchUp workflow
- model audit and revision rules

Use its methods/rules to shape the Codex brain's DesignIR generation.

For the demo, keep the reasoning layer lightweight. Do not import a large prompt stack blindly.

## 6. SketchUp Agent Control — safety reference

Repository:
https://github.com/gregtysick/sketchup-agent-control

Useful ideas:
- read-only first
- persistent IDs
- fixed commands
- backups
- undoable operations
- visual evidence

Borrow architecture ideas as needed. Do not duplicate functionality already supplied by the chosen connector.

## 7. PlanFloor AI Agent — study-only unless license becomes clear

Repository:
https://github.com/zhixiangggggggg/sketchup-planfloor-ai-agent

Its staged pattern is valuable:

natural language → structured plan → validation → transactional execution → readback.

Initial survey did not find a clear top-level reuse license, so do not copy source code until Codex confirms reuse rights.

## Demo rule

The fastest compatible working path wins.

Do not spend the demo milestone creating an ideal generalized connector abstraction before anything works.
Create only the small adapter needed to isolate the chosen connector from the rest of the demo.
