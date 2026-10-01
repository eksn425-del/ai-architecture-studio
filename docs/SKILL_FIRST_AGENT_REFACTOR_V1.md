# Skill-first Agent Refactor v2

## Why this refactor exists

The repository proved connectivity, safety, OSS reuse and deterministic SketchUp execution, but those engineering wins did not automatically create good architecture.

The decisive evidence is now consistent across the user's direct Codex tests and competitor/product examples:

- direct Codex + a cost-efficient model can already create developed SketchUp architecture from one image;
- the website with the same model class was materially worse;
- adding more fixed tools did not close the gap;
- strong products use a task Skill + persistent Agent harness + software bridge, not one secret foundation model;
- good reconstruction products reduce uncertainty **before** building by clarifying scope/scale/inference/detail and turning the image into an explicit parameter baseline.

The product center therefore becomes:

> **replaceable model + strong task Skill + persistent coding Agent + thin professional-software bridge**

## Old mental model

```text
Model
  -> broad project prompt
  -> many MCP/OSS tools
  -> SketchUp
```

Problems:

- too much context for a cheap model;
- overlapping tools encouraged shallow one-off calls;
- fixed action vocabularies reduced coding freedom;
- success was measured by connectivity more than final visual quality;
- exact uncertainties were left for the model to invent during execution.

## Target mental model

```text
Reference image
      |
      v
Task Skill
inspect -> clarify -> parameterize -> approve
      |
      v
Replaceable multimodal/coding model
      |
      v
Persistent coding Agent harness
write/revise files -> execute -> inspect -> correct
      |
   +--+------------------+
   |                     |
   v                     v
workspace Ruby        SAIE helpers
(project-specific)    (ordinary semantics)
   |                     |
   +----------+----------+
              v
      thin SketchUp bridge
identity + execution + readback + screenshot + lifecycle
              |
              v
          SketchUp
```

The moat should sit in **Skill + Agent workflow + project continuity + software-bridge UX**, not in hard dependence on one foundation model.

## Current milestone: one image -> developed editable SketchUp

Do not combine taskbook/site/program yet.

Input:

- one or more images under `inputs/reference/`;
- one short user reconstruction request.

Output:

- user-confirmed reconstruction assumptions/parameters;
- developed editable SketchUp model;
- persistent scripts/components;
- source-matched screenshot;
- oblique screenshot;
- at least one visual correction on the same model.

A few white boxes are a failure even if every tool call succeeds.

## Reconstruction interaction

### Stage 1 — Clarify

The Agent first inspects the image and asks only questions whose answers materially change the model. Maximum four concise questions.

Priority:

1. intended use / source-view-only vs multi-angle editing;
2. model scope;
3. any known dimension anchor;
4. permission to infer unseen geometry and desired visible detail.

Do not ask low-value micro-detail questions. Do not ask again when the user already answered.

### Stage 2 — Parameterize / Plan

Use image + user answers to write `notes/reconstruction_card.md`.

The card must clearly separate:

- **KNOWN** — user/source-provided dimensions or facts;
- **ESTIMATED** — visual proportional estimates used as a modeling baseline;
- **ASSUMED** — conservative rules for unseen geometry/detail.

Then produce a compact geometry/construction plan and wait for user approval.

### Stage 3 — Execute

After approval, the same project/workspace/model continues. On the locally verified Codex App Server protocol, dynamic tools are registered only at `thread/start`; `thread/resume` cannot add them. The first transition from tool-free planning to execution therefore starts a tool-equipped native thread, carrying the approved parameter card and project conversation. Subsequent execution revisions resume that execution thread. Do not claim native thread identity is unchanged across this boundary.

The execution Agent:

1. authors/revises persistent Ruby under `agent_workspace/scripts/`;
2. uses `sketchup_run_workspace_ruby` as the primary project-specific modeling path;
3. uses selected SAIE tools only when they simplify ordinary semantic construction/query/edit;
4. uses the connector for model identity, view/readback and safe transport;
5. builds recognizable primary form;
6. adds repeated facade systems/material zones;
7. captures source-matched + oblique screenshots;
8. states concrete mismatches;
9. revises the same scripts/model.

## Tool-surface rule

Image reconstruction should not expose the historical full tool surface.

`reconstruction_coding` should expose only what improves the direct-Codex-like workbench:

- persistent workspace Ruby;
- real available scene/entity/model readback;
- camera/view/screenshot;
- selection/transform/undo/lifecycle where available;
- selected SAIE wall/opening/slab/roof/query/view helpers.

Hide legacy massing/road actions, ArchFlow/CAD tools and unrelated backends in this milestone.

Tool count is not product capability.

## Context rule

Cheap-model reconstruction context should contain only:

- actual reference image(s) as multimodal input;
- dedicated reconstruction Skill;
- reconstruction parameter card;
- recent reconstruction conversation;
- current SketchUp readback/screenshots during execution.

Exclude unless explicitly requested:

- taskbook;
- site;
- program;
- unrelated precedent URL text;
- old DesignIR/BuildPlan;
- generated outputs as source references;
- large internal benchmark prose.

## Model rule

The workflow must stay model-independent.

The first parity target is deliberately:

> **website + GPT-6 Sol Low ~= direct Codex + GPT-6 Sol Low**

Do not use Astra to mask missing Skill, coding-harness or bridge capability.

## Reuse rule

Use licensed donors according to fit:

- Kongxing: existing verified local bridge/lifecycle/readback;
- SAIE (MIT): ordinary semantic construction/query helpers;
- Supex (MIT): persistent-code / execute-inspect-revise ideas and portable modules;
- Stultus (Apache-2.0): SketchUp 2024 coding/readback/screenshot/undo patterns;
- ArchFlow (Apache-2.0): later semantic/CAD/artifact pipeline;
- SketchUp Architect Skill (MIT): later full-design reasoning;
- ADAI (CPAL-1.0): study task/method-card, guided/autonomous and experience-pack ideas without copying covered source;
- Pylon / Building-Xuezhang: product/workflow references from observed behavior, not proprietary code donors.

## Competitor lesson now adopted

Observed competitor teaching behavior shows a useful sequence:

> image -> ask high-impact questions -> user answers -> AI proposes coherent estimated dimensions/assumptions -> user confirms -> modeling begins -> continued edits reuse the same model.

This is a product mechanism, not a proprietary implementation detail. Our host should implement the same general workflow with our own code and licensed/open components.

## User-interruption rule

Internal engineering checks must not become user workflow.

- run what can be run autonomously;
- if a non-critical external check cannot run inside Codex, record `pending_external` and continue;
- do not stop the task merely to ask the user to run a sandbox probe, inspect a port, or make a reversible setup choice;
- only surface a request when it truly blocks the next user-visible reconstruction milestone and cannot be resolved otherwise.

## Acceptance

Use the same known-good source image for:

A. direct Codex + Sol Low

B. website + Sol Low

PASS requires B to be recognizably comparable in developed architectural detail, with persistent coding evidence, source-matched screenshots and same-model visual correction.

Connection success, test success, tool count, or a white-box model are not acceptance.
