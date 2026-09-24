# AGENTS.md

This repository uses GitHub as the single source of truth between planning/review and Codex implementation.

## Required workflow

1. Read `docs/CURRENT_TASK.md` first.
2. Read the linked demo/architecture docs needed for the current task.
3. Execute the current task end-to-end; do not stop after analysis unless a real blocker prevents implementation.
4. Prefer reuse over rebuilding infrastructure:
   **Adopt → Fork → Wrap/Compose → Minimal Custom Build**.
5. Run tests/checks and, when available, a real SketchUp smoke test.
6. Update `docs/HANDOFF.md` before finishing.
7. Commit the work with a clear message.
8. Do not start a new milestone that is not in `docs/CURRENT_TASK.md`.

## Safety and repository hygiene

- Never commit API keys, tokens, credentials, secrets, or private machine paths.
- Never commit the user's private graduation-design assets, private SKP/DWG files, or copyrighted reference packages.
- Runtime/user project data belongs under ignored local runtime folders.
- Never modify the user's original model. Use a blank/disposable model or a copy.
- Prefer localhost-only bridges for the demo.
- Preserve required open-source license and NOTICE files when code is reused.

## Autonomy boundary

Solve ordinary engineering decisions autonomously. Do not repeatedly ask the user for implementation details.

Ask only when:
- a critical input is missing and no safe fallback exists,
- an irreversible/destructive action is required,
- or a choice would materially change product scope.

## Product rule

The demo is **not** a new CAD/3D engine.

The intended architecture is:

**Web Workspace → Brain/Agent → Local Connector/MCP → SketchUp**

SketchUp remains the real editable modeling application.

## Current demo rule

For Demo v0.1, Codex itself may act as the temporary AI brain. The codebase must isolate that behind a `BrainAdapter`-style boundary so a real model API can replace Codex later without rewriting the product workflow.

Do not build Rhino/Revit/Blender support, payments, authentication, or a production cloud deployment in this milestone.
