# Codex Demo Runbook

## Mission

Build and, where the local environment allows, run **AI Architecture Studio Demo v0.1** in one implementation cycle.

This is not another research-only task.

Codex should inspect quickly, choose the fastest reuse path, implement, test, and produce demo evidence.

## Start order

Read:

1. `AGENTS.md`
2. `docs/CURRENT_TASK.md`
3. `docs/DEMO_V0_1_SPEC.md`
4. `docs/DEMO_ARCHITECTURE.md`
5. `docs/SCHEMAS_V0_1.md`
6. `docs/OPEN_SOURCE_COMPONENT_MAP.md`

Use `docs/OPEN_SOURCE_REUSE_SURVEY.md` only when deeper candidate context is needed.

## Working style

Do not stop to ask ordinary engineering questions.

Make the simplest reasonable choice and record it.

Do not spend most of the run writing documents. The majority of effort should produce working code.

## Brain for this demo

Codex itself is the temporary reasoning engine.

The demo code must isolate this with a BrainAdapter/job boundary.

If Codex can safely be invoked locally by the app, wire it behind the adapter.

If not, use job-package mode:
- backend creates a request
- active Codex session reads it
- Codex writes `DesignIR` and `BuildPlan`
- UI/backend reads results

For the required seeded demo, Codex may directly create the structured artifacts itself and then execute the SketchUp step.

## SketchUp for this demo

First inspect the user's already-working Codex MCP setup.

If it works, use it.

Only install/adopt SAIE/VBO/another connector if the existing MCP does not provide the minimum live operations.

Do not modify the user's original graduation model.

Use a blank model or a disposable copy.

## Required demo evidence

When environment permits live SketchUp:

- a screenshot showing the generated model
- a second screenshot after sequential edit #1
- a third screenshot after sequential edit #2
- model readback/state JSON
- a saved disposable SKP path recorded locally (do not commit SKP)
- generated DXF
- generated presentation preview

Commit only safe/sanitized evidence such as small screenshots if they reveal no private project data.

## Completion

Update `docs/HANDOFF.md` with:
- architecture chosen
- OSS reused
- files added/changed
- exact run instructions
- tests/checks
- live SketchUp result
- what is real vs mocked/fallback
- remaining blockers
- next recommended step

Then commit and stop.
