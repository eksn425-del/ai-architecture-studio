# Current Task — Reuse-First Technical Due Diligence + Environment Audit

## Milestone

**SketchUp Agent Technical Spike — Phase A+B (revised)**

## Why this task changed

A broad GitHub survey found several projects that overlap heavily with the infrastructure we were about to build.

Therefore the current priority is **not** to implement another SketchUp MCP bridge.

The priority is to determine whether we can adopt, fork, compose, or wrap existing open-source projects and get to a usable MVP faster.

Read first:

1. `AGENTS.md`
2. `docs/OPEN_SOURCE_REUSE_SURVEY.md`
3. `docs/TECHNICAL_SPIKE_v0.1.md`
4. `docs/ARCHITECTURE_OVERVIEW.md`

## Objective

Produce a concrete reuse decision for the AI Architecture Studio before any substantial custom connector development.

At the end of this task, choose one of:

- **ADOPT**
- **FORK**
- **COMPOSE**
- **WRAP**
- **BUILD_MINIMAL_CUSTOM**

for each needed layer.

## Candidate set — required

Evaluate at minimum:

### Whole-workflow / orchestration candidate
- `bingxijun/archflow-studio`

### SketchUp execution candidates
- `iamahsanmehmood/saie`
- `vbosolution/vbo-sk-agent`
- `gregtysick/sketchup-agent-control`
- `mhyrr/sketchup-mcp`

### Architecture reasoning candidate
- `Mentat-Uran/sketchup-architect-skill`

### Architecture-pattern reference
- `zhixiangggggggg/sketchup-planfloor-ai-agent`

Do not copy code from repositories without a confirmed compatible license.

## Phase A — Environment Audit

Inspect what is actually accessible from the user's current development machine/session, including where possible:

- Windows version
- Python version/environment
- installed SketchUp version
- SketchUp plugin directory
- Ruby/API constraints
- Codex MCP configuration
- ability to install an RBZ/plugin
- ability to start localhost bridges
- available ports
- existing local project or SketchUp automation code

If something cannot be detected, mark it **UNKNOWN** and provide the shortest verification step.

Do not guess.

## Phase B — Reuse / Architecture Due Diligence

For each required candidate, inspect real code/docs, not only the README.

Compare at minimum:

- license / NOTICE obligations
- project activity and apparent maturity
- Windows support
- SketchUp version support
- Codex compatibility
- installation friction
- local bridge architecture
- object identity / persistent IDs
- query/readback ability
- continuous modification
- screenshot/viewport feedback
- transaction / undo / backup behavior
- state/project model
- CAD integration
- render handoff
- test coverage
- failure recovery
- security model
- how easy it is to embed behind our future Web Workspace

## Special question — ArchFlow

Determine whether `archflow-studio` can serve as our **product/orchestration backbone** rather than merely an inspiration.

Inspect:
- semantic model schema
- project package
- SketchUp Bridge
- CAD Bridge
- Design Core
- run/version records
- validators
- render handoff
- Codex plugin/skill layout

Identify exactly what we would keep, replace, or add.

## Special question — SAIE

Determine whether SAIE can serve as our **SketchUp execution layer**.

Run or inspect the smallest possible proof if environment access allows.

Focus on:
- ping / connection
- scene summary
- object query
- wall/slab/opening tools
- stable entity IDs
- capture view
- save/open/version safety
- transaction behavior

Do not conduct destructive tests against the user's real graduation model.

## Special question — SketchUp Architect Skill

Determine whether its precedent-research + brief-to-design logic can be used as the starting architecture-domain skill instead of writing our own prompt stack.

Map:
- what can be reused directly
- what should become product-owned project context
- what is tied specifically to Codex/Skill runtime

## Required deliverables

Create:

1. `docs/ENVIRONMENT_AUDIT.md`
2. `docs/OPEN_SOURCE_REUSE_EVALUATION.md`
3. `docs/ADOPTION_PLAN.md`

Update:

4. `docs/HANDOFF.md`

## OPEN_SOURCE_REUSE_EVALUATION.md must include

A comparison table with:

- Candidate
- Layer
- Functional overlap
- License
- Maturity evidence
- Integration effort
- Major risks
- Reuse decision
- Reason

Do not use unsupported numeric scores merely for appearance.

## ADOPTION_PLAN.md must contain

A single recommended stack.

Example shape only:

- Orchestration: fork ArchFlow
- SketchUp: adopt SAIE
- Design reasoning: adapt SketchUp Architect Skill
- Product-specific: build Web Workspace + Case-to-Design + Project Context

The final recommendation may differ, but it must be explicit.

Also define:

### KEEP
Existing code/components to preserve.

### REPLACE
Components we should not use and why.

### BUILD
Only genuinely missing pieces we need to implement.

### FIRST LIVE TEST
The single smallest real test to run next.

## Do not do yet

Do **not**:

- build a new generic MCP server from scratch
- rewrite a SketchUp Ruby bridge that an adopted project already supplies
- build the full web UI
- implement Rhino / Blender / CAD / Render product features
- modify the real graduation model
- upload private/copyrighted benchmark assets
- copy unlicensed source code
- start Phase C automatically

## Acceptance criteria

Phase A+B is accepted only if:

- the top open-source alternatives were inspected beyond marketing descriptions
- licenses are explicitly checked
- the recommended architecture minimizes unnecessary custom code
- an explicit adopt/fork/compose/wrap/build decision exists per layer
- ArchFlow and SAIE receive deeper inspection
- unknowns are clearly marked
- no private assets or secrets are committed
- `docs/HANDOFF.md` is updated
- the next live technical test is specific and minimal

## Execution behavior

Use:

inspect → compare → verify → choose → document → handoff

The default bias is **reuse first**.

Do not equate "we could build it" with "we should build it".

When an existing component satisfies the requirement with a compatible license and acceptable risk, prefer reuse.
