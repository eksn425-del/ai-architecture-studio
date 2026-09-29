# Selected Supex agent workflow guidance

Source: `darwin/supex` agent guide at revision `66c9eed0921c418be3f1bd4ef5f100f6b5f2ad4c` (release v0.3.0), MIT license. This repository vendors only the workflow ideas needed by AI Architecture Studio; it does not vendor the Supex runtime.

## File-based Ruby loop

- Prefer project `.rb` files for non-trivial SketchUp automation.
- Execute the file, inspect model state and screenshots, then edit and re-run the same file.
- Keep helpers organized rather than emitting one large disposable snippet.
- Group geometry; avoid loose root edges/faces.
- Name groups/components for Outliner clarity and use components for repeated geometry.
- Keep scripts idempotent or otherwise safe to revise and re-run.

## Geometry quality

- Prefer profile-first geometry and extrusion over fragile chains of complex booleans when the form allows it.
- Verify face orientation and push/pull direction.
- Avoid coplanar overlaps and tiny accidental edges.
- Apply materials after the geometry has been visually verified.

## Visual QA

- Use multiple views rather than one screenshot.
- Include useful plan/top, elevation/side and isometric views.
- Inspect the target geometry after meaningful changes and revise the source file when proportions, orientation or topology are wrong.

## Workflow split

- Use direct SketchUp/Ruby control for scene/model operations and one-off project-specific geometry.
- Use deterministic/parametric geometry sources for repeatable authored forms when available.
- Keep project source files as durable state so the agent can continue the same modeling task across turns.
