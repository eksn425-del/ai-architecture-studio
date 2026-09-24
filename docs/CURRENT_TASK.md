# Current Task — Phase A + B

## Milestone

**SketchUp Agent Technical Spike**

## Objective

Before writing the connector, determine the actual environment and select the smallest viable SketchUp integration architecture.

This task is **research + audit + technical decision**, not large-scale implementation.

## Phase A — Environment Audit

Inspect what is actually available in the execution environment.

Record, where accessible:

- operating system
- Python version and environment
- SketchUp version
- SketchUp Ruby environment / extension constraints
- Codex / MCP / agent configuration
- existing local SketchUp MCP or plugin code
- existing project instructions / skills / prompts that could conflict
- how local/private benchmark assets can be referenced without committing them

If something cannot be detected, mark it **UNKNOWN** and explain how to verify it. Do not guess.

## Phase B — Existing Connector Evaluation

At minimum evaluate:

**sheares/sketchup-mcp**

Also identify one or two credible alternatives if they materially help comparison.

Assess:

- architecture
- Windows compatibility
- SketchUp-version compatibility
- install complexity
- security / local exposure
- model-query capability
- continuous-edit capability
- screenshot / viewport capability
- failure/reconnect behavior
- extensibility
- license and attribution implications
- what can be reused versus what should be implemented ourselves

A likely architecture pattern to assess is:

LLM / MCP Client  
→ Python MCP Server  
→ local bridge  
→ SketchUp Ruby Extension  
→ SketchUp Ruby API

Do not assume this architecture is correct before evaluation.

## Required deliverables

Create:

1. `docs/ENVIRONMENT_AUDIT.md`
2. `docs/SKETCHUP_MCP_EVALUATION.md`

Then update:

3. `docs/HANDOFF.md`

## Decision required at the end

Recommend exactly one next-step architecture for Phase C+D.

The recommendation must state:

- components to reuse
- components to build
- communication method
- minimal first tool set
- primary technical risks
- whether a local proof-of-connection should precede all other work

## Do not do yet

Do **not**:

- build the full connector
- build the web UI
- implement Rhino / Blender / CAD / Render
- modify the user's original graduation model
- upload private benchmark files
- introduce a large generic tool framework
- add features only because they may be useful later

## Acceptance criteria

Phase A+B is accepted only if:

- environment assumptions are explicit
- unknowns are clearly marked
- reusable components are identified
- the connector recommendation is justified
- license/attribution issues are checked
- unresolved technical risks are listed
- no destructive changes are made
- no secrets/private assets are committed
- `docs/HANDOFF.md` is updated

## Execution behavior

Use:

inspect → research → compare → decide → document → verify → handoff

Solve ordinary research/engineering ambiguities autonomously.

Ask the user only if critical information cannot be inferred or safely deferred.

## Completion status

Do not start Phase C automatically.

Finish Phase A+B, commit the deliverables, and stop for review.
