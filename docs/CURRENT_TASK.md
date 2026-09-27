# CURRENT TASK — Quality Lift v1: Astra Low + Architecture Skill + Ruby

## Status: Completed (2026-09-27; see `docs/HANDOFF.md`)

## Objective

Improve modeling quality **without increasing model reasoning effort** and without rebuilding another architecture engine.

The last Fast Assembly v1 milestone proved that the native agent path works, but the output is still only a coarse architectural model compared with the user's successful thesis workflow.

The working hypothesis for this milestone is:

**the main quality gap comes from missing architecture workflow guidance and insufficient free-form SketchUp scripting capability, not from needing a higher reasoning setting.**

Target stack:

**Chinese Web Workspace → current local Astra model at LOW reasoning → thin architecture skill → existing Kongxing MCP + safe task-specific Ruby/project scripts → SketchUp → screenshot/model readback → self-check/revision**

Do not solve this by switching to high/xhigh/max reasoning.

## Before starting

1. Run `git pull --ff-only` and confirm the working tree is clean.
2. Read:
   - `AGENTS.md`
   - `docs/FAST_ASSEMBLY_V1.md`
   - `docs/THESIS_MODELING_CASE_STUDY.md`
   - `docs/HANDOFF.md`
   - `docs/OPEN_SOURCE_COMPONENT_MAP.md`
3. Run the current automated checks once.
4. Keep the current local Astra model identifier unless the local Codex installation itself requires a different valid identifier.

## Priority 1 — lower reasoning effort

The current native-agent runtime writes `model_reasoning_effort = "high"`.

Change the normal product default to:

`model_reasoning_effort = "low"`

Requirements:

- do not use `high`, `xhigh`, `max`, or another higher setting as the quality fix in this milestone,
- allow an environment/config override only for debugging/experiments,
- expose the active model identifier + reasoning effort in local status/HANDOFF so we know exactly what was tested,
- keep credentials local; do not add an API key.

The user's successful thesis workflow is evidence that a low reasoning setting can already produce substantially richer results when the tool/workflow environment is good.

## Priority 2 — reuse the MIT SketchUp Architect Skill

Use `Mentat-Uran/sketchup-architect-skill` as the primary architecture-workflow source.

Do not rewrite its ideas from memory if direct reuse is faster.

Choose the shortest maintainable reuse mode:

- external local dependency/cache, or
- vendor only the files actually needed, preserving the MIT license and attribution.

At minimum, make the native agent receive the useful parts of the skill covering:

- brief / program interpretation,
- precedent principles rather than form copying,
- area / adjacency / circulation / site / level reasoning,
- building as spaces + section + envelope + openings, not decorated boxes,
- named/semantic model elements for later revision,
- inspectable incremental modeling,
- multi-view/model QA and revision,
- project continuity across turns.

Do **not** dump the entire repository into every prompt. Build a thin, relevant skill context.

The normal user should not see or manage the skill manually.

## Priority 3 — give the agent safe task-specific Ruby capability

The architecture skill explicitly recommends task-specific Ruby for precise/repetitive SketchUp geometry.

The current agent should be able to create richer geometry without us adding dozens of fixed `create_*` tools.

Reuse the existing Kongxing connector first.

If its existing project-script/eval capability can execute a project-local Ruby file safely, expose a small host-side helper that lets the agent:

1. provide Ruby source for the current project,
2. write it only under an ignored project-local runtime script directory,
3. execute it only against the verified disposable/current project SketchUp model,
4. capture tool result + model readback + screenshot,
5. revise the same script/model when needed.

This helper is glue around the existing connector, **not a new MCP server**.

Safety:

- never allow arbitrary filesystem targets,
- never modify a source thesis model,
- keep scripts/runtime ignored,
- reject paths outside the active project runtime,
- preserve the active-model gate,
- keep destructive reset/delete operations explicit and scoped.

If Kongxing genuinely cannot support this without rebuilding infrastructure, inspect SAIE's MIT `execute_ruby`/advanced tool path or VBO SkAgent and adopt the smallest compatible existing implementation. Do not build a generic Ruby bridge from scratch.

## Priority 4 — improve the agent loop, not the action vocabulary

One architecture request may require several steps:

- understand program/site/reference,
- decide spatial organization,
- generate/update Ruby or use existing MCP tools,
- execute,
- inspect model state,
- capture useful views,
- critique the result against the brief/reference principles,
- correct geometry,
- reply only after the result is materially coherent.

Do not expand the legacy rectangular DesignIR/BuildPlan action list.

DesignIR remains optional project memory only.

## Priority 5 — A/B quality benchmark at LOW reasoning

Run a controlled local benchmark using the **same model + same low reasoning effort + same input** so the effect of skill/tooling is visible.

Use a sanitized thesis-style brief/site/reference package or an equivalent private local benchmark. Do not commit private source files.

### Baseline A

- current native-agent workflow,
- LOW reasoning,
- no new architecture skill injection,
- current MCP tools only.

### Variant B

- same current Astra model,
- same LOW reasoning,
- thin SketchUp Architect Skill context,
- safe task-specific Ruby/project-script capability,
- same inputs.

Capture comparable viewpoints for both.

The purpose is to answer:

**Does architecture skill + scripting materially improve output quality at the same low reasoning level?**

Do not compare low vs high in this milestone.

## Quality acceptance — no more “it is a building now” bar

Variant B must be visibly beyond the previous coarse pavilion benchmark.

For the benchmark, aim to demonstrate several of the following without hard-coding the exact solution:

- program-driven multiple spaces/volumes rather than generic wings,
- meaningful plan/section/level relationships,
- non-trivial roof/envelope/stepped/curved/non-orthogonal geometry where appropriate,
- real openings / facade rhythm rather than only solid masses,
- circulation or vertical circulation that relates to levels,
- public-space/site/entry relationships,
- platforms/bridges/courtyards/terraces where justified,
- semantic groups/components that can be revised locally,
- multi-view inspection and at least one agent-initiated correction.

The reference target is the *quality logic* of the thesis Astra workflow, not literal copying of the thesis form.

## Priority 6 — keep existing Fast Assembly v1 product pieces

Do not break:

- Chinese workspace,
- native agent session continuity,
- project/file/reference input,
- existing Kongxing MCP reuse,
- active disposable-model safety gate,
- screenshot/model readback,
- same-model natural-language revision,
- `/showcase`,
- legacy deterministic path as isolated fallback/tests.

## Tests

Keep existing tests passing and add only focused tests for:

- default reasoning effort is low,
- optional safe config override,
- architecture skill loader/context construction,
- project-local Ruby script path restrictions,
- active-model gating for script execution,
- same-model script revision lifecycle,
- baseline/variant benchmark metadata persistence.

Do not create a large new geometry ontology or dozens of fixed modeling tools.

## Acceptance criteria

Mark PASS / PARTIAL / FAIL in `docs/HANDOFF.md`.

1. Native product default uses the current Astra model at **low** reasoning effort.
2. Active model + reasoning setting are recorded in local status/HANDOFF.
3. MIT SketchUp Architect Skill is reused directly or selectively with correct license/attribution.
4. The native agent receives a thin architecture skill context rather than a giant generic prompt dump.
5. The agent can use safe task-specific Ruby/project scripts through an existing connector/reused OSS path.
6. No new generic MCP/SketchUp bridge is built.
7. A/B benchmark uses the same model, same low reasoning, same input; only skill/tool environment changes.
8. Variant B is visibly and architecturally richer than baseline A and the prior coarse Fast Assembly benchmark.
9. Variant B performs model/screenshot inspection and at least one correction before completion.
10. Follow-up natural-language revision changes the same model without full rebuild.
11. Existing Chinese workspace/session/project safety features still work.
12. Private thesis assets, credentials, machine paths, raw SKP/DWG and runtime Ruby scripts are not committed.
13. `docs/HANDOFF.md` contains the A/B setup, screenshots/evidence, reused upstream source/license, exact local model/reasoning setting, and remaining quality gaps.
14. Completed work is committed and pushed to `origin/main`.

## What NOT to do

- Do not raise reasoning effort to solve quality.
- Do not add another long competitor report.
- Do not implement dozens of bespoke `create_*` geometry tools.
- Do not build another MCP server.
- Do not retrain/fine-tune a model.
- Do not replace SketchUp with a browser modeler.
- Do not add auth/payments/cloud deployment/Rhino/Blender/Revit.

## Final step

Run checks and the real local A/B SketchUp benchmark, update `docs/HANDOFF.md`, commit, push to `origin/main`, verify the remote SHA, and stop.
