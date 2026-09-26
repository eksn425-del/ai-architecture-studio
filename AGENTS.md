# AGENTS.md

This repository uses GitHub as the single source of truth between ChatGPT planning/review and Codex local implementation.

## Required workflow

1. Before starting local work, run `git pull --ff-only` and confirm the working tree is clean.
2. Read `docs/CURRENT_TASK.md` first.
3. Read only the linked product/architecture docs needed for the current task.
4. Execute the current task end-to-end; do not stop after analysis unless a real blocker prevents implementation.
5. Prefer reuse over rebuilding infrastructure:
   **Adopt → Fork → Wrap/Compose → Minimal Custom Build**.
6. Run relevant tests/checks and, when available, a real SketchUp smoke test.
7. Update `docs/HANDOFF.md` before finishing.
8. Commit the work with a clear message.
9. **Push the completed commit to `origin/main` before reporting completion.** A local-only commit is not considered handed off.
10. Confirm `origin/main` contains the completed commit.
11. Do not start a new milestone that is not in `docs/CURRENT_TASK.md`.

## Repository ownership / turn-taking

To avoid conflicts, ChatGPT and Codex do not edit the same repository state at the same time.

- **ChatGPT turn:** remote GitHub review, product/architecture decisions, task definition, safe text/code edits that do not require local runtime validation.
- **Codex turn:** local Windows/SketchUp/MCP work, dependency installs, PowerShell execution, localhost/browser verification, real model tests, and code changes that require local execution.
- When Codex starts a task, it should pull the latest remote state and treat that state as authoritative.
- While Codex is actively implementing a task, ChatGPT should avoid overlapping code edits on `main`.
- When Codex finishes, it must commit + push + update `docs/HANDOFF.md`; ownership then returns to ChatGPT for review.

See `docs/COLLABORATION.md` for the full division of responsibilities.

## Assembly-first rule

This project is now optimized for **speed to usable product**, not for proving that we can rebuild every subsystem ourselves.

Before writing new infrastructure or architecture-specific tool code:

1. check the already surveyed reusable components,
2. inspect the actual license,
3. adopt/fork/wrap the fastest compatible implementation,
4. write only the missing glue.

Do not spend a milestone creating a cleaner custom replacement for a working connector, agent runtime, CAD exporter, or architecture skill.

## Product architecture rule

The product is **not** a new CAD/3D engine and is **not** a weaker in-house architecture model.

Target architecture:

**Web Workspace → Astra/native agent runtime → existing MCP / reusable OSS tools → SketchUp / CAD software**

SketchUp remains the real editable modeling application.

The website manages inputs, project/session context, conversation, outputs, and product UX.

The agent/model should retain broad reasoning and tool-use freedom. Do not force normal architecture modeling through the old tiny `DesignIR → BuildPlan → create_mass` action set.

`DesignIR` may remain as project memory / structured state, but it must not be the mandatory geometry generator or restrict all geometry to axis-aligned rectangles.

## Reuse priorities

Prefer, in order of practical fit:

1. the user's already-working Kongxing SketchUp MCP/plugin,
2. SketchUp Architect Skill for architecture reasoning/precedent workflow,
3. ArchFlow Studio for reusable project-state/CAD/output pieces,
4. SAIE for richer SketchUp execution when the existing connector is insufficient,
5. VBO SkAgent as a lightweight fallback,
6. other clearly licensed MIT/Apache/BSD code,
7. minimal custom implementation only for missing glue.

Never copy source from a repository without a clear compatible license.

## Current prototype brain rule

During local prototype work, Codex/Astra may act as the temporary native agent and may directly use the configured local MCP/tooling when the current task requires it.

The product should still preserve a replaceable runtime boundary so a production model/API path can be plugged in later without rewriting the web workspace or project storage.

## Safety and repository hygiene

- Never commit API keys, tokens, credentials, secrets, or private machine paths.
- Never commit the user's private graduation-design source assets, private SKP/DWG files, taskbook/source packages, or copyrighted reference packages unless the user explicitly approved a sanitized public derivative.
- Runtime/user project data belongs under ignored local runtime folders.
- Never modify the user's original model. Use a blank/disposable model or a copy.
- Prefer localhost-only bridges for local software control.
- Preserve required open-source license and NOTICE files when code is reused.

## Autonomy boundary

Solve ordinary engineering decisions autonomously. Do not repeatedly ask the user for implementation details.

Ask only when:
- a critical input is missing and no safe fallback exists,
- an irreversible/destructive action is required,
- or a choice would materially change product scope.

Do not add Rhino/Revit/Blender support, payments, authentication, or production cloud infrastructure unless `docs/CURRENT_TASK.md` explicitly includes them.
