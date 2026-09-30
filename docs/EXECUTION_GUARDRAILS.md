# Execution Guardrails — do not repeat the early prototype mistakes

These rules exist because earlier milestones spent too much effort on clean architecture, tool count and synthetic technical passes while the user-visible SketchUp result stayed weak.

## 1. Success-first, not architecture-first

The immediate product proof is visual:

> one user reference image -> developed editable SketchUp model that is recognizably comparable to the source.

Do not declare a milestone successful because MCP connects, tools list, Ruby executes, tests pass, or a white-box fixture exists. Those are prerequisites only.

## 2. Copy a proven working pattern before generalizing

The known successful pattern is direct Codex-style work:

> inspect image -> clarify important unknowns -> parameter card -> approval -> persistent code -> execute -> inspect -> revise same code/model.

Public/open-source donors should be adopted/wrapped before custom equivalents are written. Competitor observations guide architecture; proprietary implementation is not copied.

## 3. Do not rebuild a weaker Codex

The website should package a capable coding Agent harness, not replace it with a tiny bespoke planner/action vocabulary.

For reconstruction:

- persistent project files are first-class;
- coding is the primary project-specific geometry path;
- MCP is a bridge/inspection surface;
- SAIE is a helper library;
- Skill supplies the task method;
- the foundation model stays replaceable.

Legacy `DesignIR -> BuildPlan -> create_mass` must not control normal reconstruction.

## 4. Tool count is not capability

Do not expose the historical full tool surface merely because it exists.

Prefer the smallest sufficient reconstruction profile:

- persistent workspace Ruby execution;
- scene/entity readback;
- camera/view/screenshot;
- selection/transform/undo/lifecycle where available;
- selected SAIE semantic helpers.

Adding a new tool requires a concrete missing capability, not a desire for a cleaner abstraction.

## 5. Clarify uncertainty before spending model/tool budget

For single-image reconstruction, ask only high-impact questions:

- intended use / required views;
- modeling scope;
- any known dimension anchor;
- whether unseen geometry may be inferred;
- desired visible detail level.

Do not ask the user low-value technical questions. If exact dimensions are unknown, propose a coherent estimated baseline and label it as estimated.

## 6. Keep cheap-model context small

Image reconstruction context should include only:

- actual reference image(s);
- dedicated reconstruction Skill;
- confirmed parameter card;
- recent reconstruction conversation;
- current SketchUp readback/screenshots during execution.

Do not leak taskbook/site/program/old DesignIR/benchmark prose into this workflow unless explicitly requested.

## 7. Never use a stronger model to hide a harness problem

First parity target:

> website + GPT-6 Sol Low ~= direct Codex + GPT-6 Sol Low on the same image.

Astra is not a rescue mechanism for missing Skill, Agent, coding workspace or bridge capability.

## 8. Do not interrupt the user for internal engineering chores

Codex/local agents should continue autonomously through ordinary validation issues.

Do not pause and ask the user to run an internal probe, inspect a port, copy a path, or make a reversible engineering choice unless that action is genuinely impossible from the current environment and blocks the next user-visible milestone.

Non-critical external checks must be recorded as `pending_external` and must not stop implementation.

## 9. Real benchmark before expansion

Do not add taskbook+site design, rendering, PPT, Rhino/Revit/Blender, billing or cloud deployment until Image -> SketchUp parity is repeatable.

Use the same known-good reference image for direct-Codex and website comparison. PASS requires developed architecture, screenshot comparison and same-model correction.

## 10. End-of-turn discipline

ChatGPT handles GitHub-only work first. Codex handles Windows/SketchUp/local-runtime work second.

Codex must:

- pull latest main;
- execute the current task rather than redesigning it;
- record evidence/failures honestly;
- update HANDOFF;
- test;
- commit and push;
- stop at the requested milestone.
