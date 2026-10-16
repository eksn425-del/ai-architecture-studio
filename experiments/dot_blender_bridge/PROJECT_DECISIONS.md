# Project decisions: Blender experiment, 2026-10-16

This is a project-only decision record. It contains no raw conversation or private credentials. It describes this experiment, not all historical K Studio discussions.

## Backend choice

Use an independent Linux Blender environment to reduce dependence on a local SketchUp desktop for Blender-specific development and tests. Keep the active SketchUp/SU implementation unchanged. Blender results do not establish SketchUp compatibility; a future product may support separate native backends with shared planning and review concepts.

## Agent and inference scope

Reuse actual K Studio tool discovery, provider-schema conversion, tool-call parser and dispatch. Adapt the bounded geometry tools and instructions explicitly for Blender. For this round, assistant decisions are exchanged through files and reviewed against real scene outputs. No live model API, paid inference or autonomous production Agent is claimed.

The original SU reconstruction profile does not admit Blender creation/edit tools. The experiment therefore uses isolated full discovery and adapted backend instructions. Do not silently insert Blender tools into production SU prompts or describe this seam as an unchanged Agent.

## Completed stages and decisions

1. Inspect repository instructions/base and preserve active SU work.
2. Connect the real K Studio tool surface to an isolated stdio MCP Blender backend.
3. Run fixed transport/geometry fixtures, distinguish these from model-selected design.
4. Assistant selects a synthetic pavilion: 6x4 m slab, four 2.8 m columns and roof.
5. Execute creation, native inspection and six renders; inspect actual oblique image.
6. Assistant selects roof-only enlargement to 6.8x4.8 m, creating 0.4 m overhang.
7. Enforce host-approved roof edit, stale-state digest and exact protection of five other parts.
8. Save/reopen/render, inspect actual final image, verify bounds and identities.
9. Reproduce saved decisions in a fresh run, explicitly label this as replay.

## Evidence and failures

The implementation checkpoint `ec80814f5ed0a934c23b19f5e522b27e837997ae` retains 14 integration checks, 16 final pavilion checks and three negative controls. Fresh replay passes the final and negative-control checks. Keep original logs/results/images immutable when adding later rounds.

The first render failed because denoising support was unavailable. Disable denoising explicitly, preserve that failure and retain separately recorded passing reruns. Low-sample image noise remains. Test counts are not architecture-quality benchmarks.

## Recovery and next decision

See HANDOFF.md for exact base, implementation checkpoint, setup, repeatable commands, evidence map, failure accounting and remaining work. A replacement environment needs the repository base plus these experiment files; the Blender model can then be regenerated without original cloud paths or API credentials.

Current scope remains named axis-aligned box assemblies, supervised decisions and native Blender checks. Complex geometry, hierarchical KEEP, production UI, independent Critic, source reconstruction and native SketchUp delivery require additional implementation/testing.

The repository was verified public. Explicit approval for the public experiment branch was subsequently received. The authorized Git push passed review but failed because this checkout has no Git credentials. The already connected GitHub app reports push permission; publication uses its supported blob/tree/commit/branch operations without creating or extracting credentials. Verify the remote commit before reporting success.
