# AGENTS.md

This repository uses GitHub as the single source of truth between planning/review and implementation agents.

## Required workflow

1. Read `docs/CURRENT_TASK.md` before implementation.
2. Read only the additional docs needed to understand the current task.
3. Do not change product scope unless the current task explicitly asks for it.
4. Prefer the smallest testable implementation over broad rewrites.
5. Reuse existing open-source infrastructure when it is a good fit; document license and attribution implications.
6. Run relevant checks/tests before finishing.
7. Update `docs/HANDOFF.md` after every completed task.
8. Do not mark work complete when acceptance criteria are not met.

## Safety and repository hygiene

- Never commit API keys, tokens, credentials, secrets, private paths, or proprietary data.
- Never commit the user's private graduation-design assets or copyrighted benchmark packages to this public repository.
- Do not hard-code machine-specific absolute paths.
- Preserve user files and benchmark models.
- Make destructive or irreversible changes only with explicit user approval.

## Autonomy boundary

Solve ordinary engineering problems autonomously.

Ask the user only when:
- a critical input is genuinely missing,
- an irreversible action is required,
- or competing choices would materially change product/design scope.

## Current scope guardrail

The current milestone is the **SketchUp Agent Technical Spike**.

Do not add Rhino, Blender, Revit, full CAD, rendering, payments, authentication, or a full web UI unless `docs/CURRENT_TASK.md` explicitly asks for them.
