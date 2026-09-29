# Selected Supex agent workflow guidance

Source: `darwin/supex` agent guide at revision `66c9eed0921c418be3f1bd4ef5f100f6b5f2ad4c` (release v0.3.0), MIT license. Only the transferable workflow guidance is vendored; the Supex runtime is not.

## File-based Ruby loop

- Prefer project `.rb` files for non-trivial SketchUp automation.
- Execute, inspect model state/screenshots, then edit and re-run the same file.
- Group and name geometry; avoid loose root faces/edges; keep repeatable scripts safe to re-run.

## Geometry quality

- Prefer profile-first extrusion over fragile boolean chains when practical.
- Verify face orientation; avoid coplanar overlaps and tiny accidental edges.
- Apply materials after geometry is verified.

## Visual QA

- Inspect multiple useful views, including top/plan, side/elevation and isometric.
- Revise the source file when proportions, orientation or topology are wrong.

## Workflow split

- Use SketchUp/Ruby for scene operations and project-specific geometry.
- Use deterministic/parametric sources for repeatable authored forms when available.
- Keep source files as durable state so the agent can continue across turns.
