# Skill-first Agent Refactor v1

## Why this refactor exists

The current repository proved connectivity, safety, OSS reuse and deterministic SketchUp execution, but the product-quality gap remained obvious:

- direct Codex + a cost-efficient model can already create developed SketchUp architecture from an image;
- the website, using the same class of model, often produced weak or no geometry;
- adding more fixed tools did not close that gap;
- the strongest public/observed competitor pattern is not "one secret foundation model" but **task Skill + persistent Agent harness + professional-software bridge**.

The product therefore changes its center of gravity.

## Old mental model

```text
Model
  -> long architecture prompt
  -> many MCP/OSS tools
  -> SketchUp
```

This over-emphasized tool count and under-emphasized the coding Agent loop. It also overloaded cheap models with overlapping actions and broad project context.

## Target mental model

```text
Replaceable multimodal/coding model
             |
             v
Task Skill / Method Cards
             |
             v
Persistent coding Agent harness
plan -> approve -> write/revise files -> execute -> inspect -> correct
             |
      +------+------+
      |             |
      v             v
workspace Ruby    SAIE helpers
(project-specific) (ordinary semantic elements)
      |             |
      +------+------+
             v
Thin SketchUp bridge / MCP
identity + execution + readback + view + undo/lifecycle
             |
             v
         SketchUp
```

The product moat should sit in the **Skill + Agent workflow + project continuity + software bridge UX**, not in a hard-coded dependency on one model.

## Current milestone: one image -> developed editable SketchUp

Do not combine taskbook/site/program yet.

Input:

- one or more reference images under `inputs/reference/`;
- one short user instruction.

Output:

- recognizable editable SketchUp model;
- persistent scripts/components;
- source-matched screenshot;
- at least one visual correction on the same model.

A few white boxes are a failure even if every tool call succeeds.

## Product interaction: plan -> approve -> execute

The first reconstruction turn should behave like a professional modeling assistant rather than immediately emitting geometry.

### Plan

The Agent:

1. inspects the actual multimodal image;
2. fills `notes/reconstruction_card.md`;
3. derives proportions, levels, bays, solids/voids, facade depth, repeated modules, roof/canopy and material zones;
4. proposes a compact geometry/construction plan;
5. waits for user approval.

SketchUp geometry tools are withheld during this planning turn.

### Approve

The user may:

- approve execution;
- modify parameters/assumptions;
- cancel.

### Execute

After approval the same thread/workspace:

1. authors/revises persistent Ruby in `agent_workspace/scripts/`;
2. uses `sketchup_run_workspace_ruby` as the primary project-specific modeling path;
3. uses selected SAIE tools only as helpers for ordinary semantic construction/query/edit;
4. uses the existing connector for model identity, camera/view/readback and safe transport;
5. inspects returned screenshots/model state;
6. revises the same scripts/model until source-defining mismatches are corrected.

## Tool-surface rule

Image reconstruction should not expose the whole historical 80-tool surface.

`reconstruction_coding` profile should expose:

- a small set of Kongxing readback/view/camera/selection/transform/undo-style tools actually present;
- selected SAIE wall/opening/slab/roof/query/view helpers;
- `sketchup_run_workspace_ruby`;
- no legacy `create_mass/create_road` path;
- no raw `sketchup_eval_project_file` to the model;
- no ArchFlow/CAD tools during this milestone;
- no transient inline `sketchup_run_project_ruby` in the reconstruction profile.

The exact live tool list must be verified locally; do not invent tool names that the installed connector does not expose.

## Context rule

Cheap-model reconstruction context must be small.

Include:

- source image(s) as actual multimodal input;
- Image -> SketchUp Skill;
- `reconstruction_card.md` and persistent workspace state;
- only recent reconstruction conversation;
- current SketchUp readback when executing.

Exclude unless explicitly requested:

- taskbook;
- site;
- program;
- unrelated precedent URL text;
- old DesignIR/BuildPlan;
- generated output screenshots as source reference.

## Model rule

The reconstruction workflow must be model-independent.

Use a replaceable provider boundary. Quality should come first from Skill/Harness/Bridge. A stronger model can remain an optional premium tier, but it must not be required to compensate for a weak Agent environment.

For the first local parity test use the same cheap model/effort that succeeds in direct Codex, so the comparison isolates the website harness rather than model intelligence.

## What has already been implemented remotely

- `app/models.py`
  - reconstruction lifecycle state on `AgentSession`;
  - explicit `agent_action = auto|plan|execute` on `ConversationRequest`.
- `app/reconstruction_runtime.py`
  - deterministic plan/execute policy;
  - reference-only image scope;
  - small reconstruction context payload;
  - low-effort preference metadata.
- `app/reference_assets.py`
  - category-scoped image discovery;
  - reconstruction-specific source label.
- `app/image_to_sketchup_skill.py`
  - independent, source-first, coding-first method cards;
  - explicit planning/approval and three-pass QA loop.
- `app/codex_parity.py`
  - workspace README/card updated for Direct-Codex-style persistent coding.
- `app/agent_tools.py`
  - `reconstruction_coding` tool profile;
  - persistent workspace Ruby is primary;
  - selected SAIE helper tools only;
  - broad ArchFlow/legacy massing tools hidden in reconstruction.
- focused tests for the above pure-Python behavior.

These changes still require local integration and test execution before they are accepted.

## Local investigation: competitor desktop package

The user will provide access to the installed/installer package they legitimately possess.

Codex may inspect only what is locally accessible through ordinary installation/files/process/network-local behavior. The goal is architectural comparison, not copying proprietary covered source or bypassing licensing/DRM.

Record observed facts separately from inference:

- installer/file layout;
- SketchUp `.rbz`/Ruby plugin structure if legitimately readable;
- local ports/processes;
- MCP protocol/tool schemas exposed at runtime;
- whether the bridge is thin or contains substantial geometry logic;
- how the desktop app selects Skills/models;
- plan/approval/execution state;
- whether execution appears script-driven or fixed-tool-driven;
- readback/screenshot/undo/model-lifecycle behavior;
- model/provider independence.

Do not copy proprietary implementation into this repository. Use public/open-source donors for code and competitor observations only to guide architecture.

## Acceptance test

Use the **same reference image** for:

A. direct Codex + cheap model/effort (existing successful reference)

B. website + same model/effort + Image Reconstruction Skill + Direct-Codex-like harness

Compare only end results and workflow evidence:

- silhouette/proportion;
- levels/bays;
- roof/canopy;
- facade depth;
- repeated windows/rails/louvers;
- material zoning;
- editability/naming;
- source-matched screenshot;
- visual self-correction;
- time/cost/tool failures.

If B is still materially worse, inspect missing Agent-harness capability before changing foundation model or adding another generic MCP.
