# CURRENT TASK — Fast Assembly v1: Astra-native Architecture Agent

## Status: Ready to execute

## Objective

Replace the product's restrictive box-modeling path with a **native agentic SketchUp workflow** that behaves much closer to the successful thesis Astra workflow.

The target loop is:

**任务书 + 场地 + 参考案例 + 用户想法 → 网站对话 → Astra/Codex native agent → existing SketchUp MCP / reusable OSS tools → real editable model → screenshot/readback → agent self-check/correction → continue conversation**

This is a fast assembly milestone. Do not build another architecture engine.

## Before starting

1. `git pull --ff-only`
2. Confirm the working tree is clean.
3. Read:
   - `AGENTS.md`
   - `docs/FAST_ASSEMBLY_V1.md`
   - `docs/THESIS_MODELING_CASE_STUDY.md`
   - `docs/OPEN_SOURCE_COMPONENT_MAP.md`
   - `docs/HANDOFF.md`
4. Run the current checks once.

## Core product decision

The old default path:

`Codex/Astra → strict DesignIR → strict BuildPlan → fixed create_mass/create_circulation`

is now **legacy/demo logic**, not the main product architecture.

Do not keep extending that fixed action list.

`DesignIR` may remain as project memory and structured context, but it must not force all geometry to rectangles or act as the only way to model.

## Priority 1 — reuse before code

Do a short implementation-focused reuse pass, not another long research report.

### Existing connector first

Inspect the user's already-working `kongxing_sketchup` MCP and actual tool list.

If it already exposes the generic/project-script capability used in the thesis workflow, keep it as the main execution path.

Do not replace a working connector.

### Reuse candidates

Check these only for code/skills that directly save implementation time:

- `Mentat-Uran/sketchup-architect-skill` — architecture reasoning / precedent workflow
- `bingxijun/archflow-studio` — project state, CAD/output, SketchUp scripting patterns
- `iamahsanmehmood/saie` — richer SketchUp tool execution if Kongxing lacks a required capability
- `vbosolution/vbo-sk-agent` — fallback direct Ruby / bridge path

Before copying source, verify the current repository license. Preserve required license/NOTICE/attribution.

If a candidate does not immediately help this milestone, skip it. Do not integrate code just to increase reuse count.

Document the final reuse choice briefly in `docs/HANDOFF.md`.

## Priority 2 — add a native AgentRuntime

Create a separate runtime path for **free-form agentic modeling**.

The normal web conversation should be able to hand the current project context and user message to a local Codex/Astra agent that retains access to the configured SketchUp MCP/tooling.

The agent must be allowed to:

- reason over the brief/site/reference/user conversation,
- decide its own sequence of SketchUp operations,
- use richer existing MCP tools or safe project Ruby scripts when needed,
- inspect model state / screenshots,
- perform more than one tool call for one user request,
- correct its own result before replying when practical.

Do not force the agent to emit a tiny fixed `BuildPlan` first.

### Implementation rule

Prefer the shortest working route supported by the local Codex environment.

If the Codex CLI can be safely launched with the user's configured MCP servers/tools, wrap that behind a new `NativeAgentRuntime` / equivalent boundary.

If the CLI cannot provide a reliable tool-enabled session non-interactively, use the smallest recoverable local-session/job handoff that lets the active Codex session perform the tool loop. Do not invent a new MCP protocol.

Keep the existing deterministic BrainAdapter path only for tests/legacy fallback.

## Priority 3 — make the web UI use the native agent path

The Chinese conversation panel becomes the primary interaction.

User flow:

1. upload / enter project inputs,
2. talk with the agent,
3. click/start an agentic modeling session on a disposable SketchUp copy,
4. continue giving natural-language design instructions,
5. receive concise Chinese responses plus updated model screenshot/status.

The normal product path must no longer present “three rectangles + fixed edit buttons” as the main modeling experience.

The old example buttons may be hidden under a legacy/demo section or removed from the primary flow.

## Priority 4 — use project memory, not a geometry cage

Keep structured state only where it helps continuity:

- brief/program requirements
- site constraints
- reference principles
- user-confirmed decisions
- target areas/metrics
- stable names/IDs where useful
- current design summary
- session history

The agent is free to create richer SketchUp geometry that cannot be represented by the old rectangular object schema.

Do not block valid geometry just because it is not expressible in `SCHEMAS_V0_1.md`.

## Priority 5 — thesis-style benchmark

Use a **local/private benchmark copy** of the thesis workflow. Do not commit private source assets.

The benchmark should use the same style of inputs that made the thesis Astra workflow successful:

- real or sanitized task requirements
- real/sanitized site context
- reference precedent principles/images available locally
- user design intent

From a blank/disposable SketchUp model, prove that the new native-agent path can create something materially richer than the old box demo.

### Minimum evidence

The benchmark result should include, in one agentic session:

- multiple building volumes / groups,
- at least one non-trivial form beyond an axis-aligned rectangular box (for example sloped/stepped/curved/non-orthogonal geometry),
- more than one level or vertical relationship,
- at least one platform/bridge/public-space/site relationship,
- screenshot/model inspection,
- at least one agent-initiated correction or user-requested revision against the same model.

Do not hard-code these exact forms into the app. They must come from the agent/tool loop.

The thesis showcase is the quality reference, not a file to overwrite.

## Priority 6 — keep useful existing product pieces

Do not break:

- Chinese web workspace
- file/reference input
- project persistence
- existing Kongxing MCP connection
- viewport capture
- safe disposable-model workflow
- `/showcase`
- DXF/presentation outputs where still compatible

If an old feature depends on the legacy rectangle schema, isolate it instead of forcing the new agent back into that schema.

## Tests

Keep the existing automated tests passing where they still represent valid product behavior.

Add focused tests for:

- native runtime/session lifecycle
- web conversation → native agent request
- safe disposable-model gating
- persistence of agent messages/session metadata
- legacy path remaining isolated

Do not write dozens of tests for a geometry ontology we are no longer using.

## Acceptance criteria

Mark each PASS / PARTIAL / FAIL in `docs/HANDOFF.md`.

1. Normal product UI uses the native agent path rather than the fixed box BuildPlan as its primary modeling route.
2. The native agent can access the already-configured SketchUp MCP/tooling without a newly invented connector.
3. One user request may result in multiple agent-chosen SketchUp operations.
4. The agent can inspect screenshot/model state and continue or correct the same model.
5. The local benchmark produces geometry materially richer than the old three-box demo.
6. At least one non-trivial form, vertical relationship, and platform/connection/site relationship are demonstrated.
7. A follow-up natural-language request modifies the same model rather than rebuilding it from scratch.
8. Chinese web/project/file/conversation experience still works.
9. Private thesis assets, API keys, machine paths, and raw SKP/DWG sources are not committed.
10. Any reused source has a verified compatible license and preserved attribution/NOTICE requirements.
11. `docs/HANDOFF.md` records exactly what was reused, what is real, what remains legacy, and the local benchmark evidence.
12. Completed work is committed and pushed to `origin/main`.

## What NOT to do

- Do not add more fixed `create_*` actions just to cover every architecture shape.
- Do not build a new generic MCP server.
- Do not build a browser CAD/3D engine.
- Do not retrain or fine-tune a model.
- Do not spend the milestone on another competitor report.
- Do not add auth, payments, deployment, Rhino, Blender, or Revit.
- Do not claim quality based only on automated mocks; run the real local SketchUp benchmark.

## Final step

Update `docs/HANDOFF.md`, run the relevant checks and real SketchUp benchmark, commit, push to `origin/main`, confirm the remote SHA, and stop.
