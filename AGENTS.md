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

## Safety and repository hygiene

- Never commit API keys, tokens, credentials, secrets, or private machine paths.
- Never commit the user's private graduation-design assets, private SKP/DWG files, or copyrighted reference packages.
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

## Product rule

The product is **not** a new CAD/3D engine.

The intended architecture is:

**Web Workspace → Brain/Agent → Local Connector/MCP → SketchUp**

SketchUp remains the real editable modeling application.

## Current brain rule

During the local prototype stage, Codex may act as the temporary AI brain. The codebase should keep reasoning behind a `BrainAdapter`-style boundary so a real model API can replace Codex later without rewriting the product workflow.

Do not add Rhino/Revit/Blender support, payments, authentication, or production cloud infrastructure unless `docs/CURRENT_TASK.md` explicitly includes them.
