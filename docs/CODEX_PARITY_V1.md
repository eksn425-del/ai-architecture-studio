# Codex Parity v1 — reproduce the successful direct-Codex modeling harness

## Why this exists

The current website can call strong models and can control SketchUp, but the user's successful thesis workflow in direct Codex still produces materially richer and more precise architecture than the website runtime.

The gap is no longer treated as a simple model-quality problem. Direct Codex gives the model a coding harness: durable files, iterative script editing, live execution, inspection, screenshots, debugging and continuation across turns. The website previously exposed mostly one-shot semantic tools plus inline Ruby. That encourages rough massing and weak continuation.

Codex Parity v1 changes the product from a one-shot tool caller into a persistent project-coding environment around SketchUp.

## Target architecture

```text
Brief + site + precedent text/images/drawings + user intent
        ↓
Architecture Skill + precedent-fidelity policy
        ↓
Persistent agent workspace
  notes/design_notes.md
  scripts/*.rb
  qa/*
        ↓
Tool chooser
  ordinary semantic elements → SAIE / mature OSS tools
  document identity/lifecycle → Kongxing
  semantic DXF/review artifacts → ArchFlow
  project-specific complex form → persistent workspace Ruby
        ↓
SketchUp disposable project model
        ↓
model readback + multiple screenshots
        ↓
agent critique
        ↓
edit the same files / same model and re-run
```

## Open-source capability adopted

The project continues to reuse `Mentat-Uran/sketchup-architect-skill` for architectural reasoning.

Codex Parity v1 also adopts the central agentic workflow pattern documented by MIT-licensed `darwin/supex`:

- keep non-trivial SketchUp automation in project files;
- execute files rather than relying on long disposable snippets;
- inspect model state and screenshots after execution;
- revise and re-run the same source;
- keep geometry organized and idempotent where practical;
- use multiple views for visual debugging.

Only selected workflow guidance is vendored under `app/vendor/supex_agent_guide/`; the macOS/SketchUp-2026 Supex runtime and VCAD stack are not copied because they are not currently a proven Windows/SketchUp-2024 fit.

## Remote implementation already added by ChatGPT

### Persistent workspace

`app/codex_parity.py` seeds:

```text
runtime/projects/<project>/runtime/agent_workspace/
├─ README.md
├─ .architecture-studio.json
├─ notes/
│  └─ design_notes.md
├─ scripts/
└─ qa/
```

Existing agent-written files are never overwritten by the seeding step.

### File-based Ruby execution

`app/workspace_ruby.py` resolves only `.rb` files inside `agent_workspace/scripts/` and passes their source into the existing guarded `ProjectRubyExecutor`.

`app/agent_tools.py` now exposes:

`sketchup_run_workspace_ruby`

with `script_id` + a relative `scripts/<name>.rb` path.

This is intentionally a thin bridge. It does not create a second Ruby engine and does not expose arbitrary host filesystem execution.

### Skill behavior

`app/architecture_skill.py` now explicitly tells the modeling agent to:

- read the persistent workspace guide;
- keep durable design decisions;
- use semantic OSS tools for ordinary construction;
- use persistent Ruby files for project-specific complex forms;
- inspect multiple views;
- revise the same model/script instead of stopping at first-pass rough massing.

Selected Supex workflow guidance is also loaded into the architecture context under its MIT license.

## What parity does NOT mean

Parity does not mean rebuilding Codex itself.

It means preserving the parts of the successful direct-Codex workflow that matter for architecture:

- durable coding state;
- files the model can revise;
- a broad professional-software tool surface;
- execution/debug/readback loops;
- multimodal precedent input;
- multi-view visual QA;
- same-model continuation.

## Quality ladder

### Pass 0 — design basis

Before geometry, synthesize:

- brief/program constraints;
- site/access constraints;
- precedent grammar;
- user-requested precedent fidelity;
- target levels/section/circulation;
- major open decisions.

Store durable conclusions in `notes/design_notes.md`.

### Pass 1 — spatial/form skeleton

Build enough geometry to establish:

- site relationship;
- multiple volumes where appropriate;
- floor/vertical hierarchy;
- circulation/public-space relationship;
- primary roof/silhouette language.

Do not call this completion.

### Pass 2 — architectural development

Develop the same model with:

- openings and facade rhythm;
- stairs/ramps/bridges/platforms;
- meaningful roof/section geometry;
- entrances/service/public routes;
- major indoor/outdoor relationships.

### Pass 3 — visual QA and correction

Capture useful plan/top, elevations/sides and isometric views. Check against the brief and precedent grammar. Fix material defects by revising the same source/model.

The product should not report a developed-building task complete after a single rough-massing pass.

## Model strategy

Do not spend Astra quota while the harness itself is still under validation.

Use Sol in Codex as the coding/local-integration agent for the current implementation work. Once the deterministic parity harness is proven, the first expensive architecture comparison should use the same strong model on both sides:

- direct Codex reference workflow;
- website Codex-parity workflow.

Only after the same-model parity gap is acceptably small should Luna/Qwen/GLM/Sol economy-model quality be measured.

## Acceptance before the next architecture benchmark

1. SAIE compatibility patch finishes the deterministic wall/opening/slab/roof/query/edit smoke or is explicitly isolated as a non-blocking optional defect.
2. The persistent agent workspace is created automatically and preserves existing files.
3. A Ruby file authored under `agent_workspace/scripts/` can be executed through `sketchup_run_workspace_ruby` on a verified disposable model.
4. Editing that same file and re-running it increments the existing project-script revision/root rather than creating an unrelated model.
5. The agent/tool stack can collect multiple useful model views after a pass.
6. Existing semantic tools remain available; file-based Ruby does not replace SAIE/Kongxing/ArchFlow.
7. Repository tests pass and no private thesis files are committed.
8. No architecture-quality Astra benchmark is run as part of this foundation milestone.
