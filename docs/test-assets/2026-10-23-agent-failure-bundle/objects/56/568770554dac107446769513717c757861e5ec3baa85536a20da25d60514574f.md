# Architecture Agent Workspace

This directory is the agent's persistent project-coding workspace. Treat it like a small software project, not a scratchpad.

## Image reconstruction loop

1. Inspect the actual source image(s).
2. Clarify only high-impact unknowns that materially change the model.
3. Update `notes/reconstruction_card.md`, classify source coverage in `notes/reconstruction_evidence.json`, keep `notes/facade_schedule.json` as the compact machine-readable facade/roof schedule, and write `notes/construction_strategy.json` with shared parameters, method ownership and verification views.
4. Show the compact parameter/construction plan and wait for approval.
5. After approval, follow the internal construction stages in order: primary form → representative module → replication → variants → finish. These are not extra user approval gates.
6. Author or revise durable `.rb` files under `scripts/`; verify one representative repeated module before copying it.
7. Execute the same files with `sketchup_run_workspace_ruby`, inspect returned screenshots/model state, and correct the same scripts/model rather than restarting.
8. Maintain `qa/visual_qa.md`: compare source first, then current front/rear/left/right/roof/oblique evidence; keep at most three highest-impact mismatches plus a KEEP list.
9. `qa/repair_history.json` is host-owned read-only memory of prior correction attempts. Before repeating a fix after context compaction, read it and avoid methods whose next trusted review still said `still_needs_fix`.

## Architecture-design loop

For later design workflows, record durable design decisions in `notes/design_notes.md`, keep project-specific code under `scripts/`, execute, inspect and revise the same model.

## Tool split

- **Primary for reconstruction:** persistent workspace Ruby for project-specific and repeated geometry.
- **Geometry helpers inside the single writer:** use injected SAIE wall/opening helpers from persistent ProjectRuby when suitable; reconstruction-profile SAIE/Kongxing backend tools remain read-only evidence helpers.
- **Optional ADAI:** read `notes/adai_geometry_contract.md` for this process's verified enabled/disabled state and exact supported profile signatures before writing geometry.
- **Bridge/lifecycle:** Kongxing for verified model identity, viewport/camera/readback and transport.
- **Later engineering outputs:** ArchFlow for validation/DXF/Ruby/review where relevant.

Do not choose a large set of tiny one-off tool calls when a parameterized Ruby/component system better expresses the source. A successful tool call is not a successful model.

## Modeling quality rule

Read `notes/volume_inventory.md` before geometry. Fill its source-to-model table for EVERY visible primary/attached volume, roof and canopy across ALL sources. Record attachment/height relationships, silhouette landmarks, estimated ratios and exact target named paths. Do not infer that a material boundary is a separate storey, or collapse a visible lower annex into the taller main box. Estimates need a visible anchor and cross-view check, not merely "estimated from images".

At the primary-form stage, compare both source-angle silhouettes BEFORE spending effort on plants/furniture. This is an internal continuous-agent check, not another user confirmation gate. After each commit update the same inventory with actual built paths and missing/mismatched regions. The Native host runs a fresh independent read-only Critic on trusted source/current images; its verdict replaces Builder self-review. Prioritize its massing/roof issues and preserve only genuinely correct geometry.

For image reconstruction, a few boxes are not completion when the source contains developed facade/roof geometry. Match silhouette, storeys/bays, major voids, facade depth, repeated modules, roof/canopy and material zones, then compare source-matched screenshots and revise.

At each visual review, inventory every visible primary and attached volume in both source and model before judging details. Missing annexes/lower roofs and wrong silhouettes outrank decoration or template clutter. Do not call these matched merely because the main facade is recognizable. Do not invent extra plants or geometry to hide a template figure: record the lifecycle artifact and preserve the source layout. A correction should address the largest remaining source mismatch, not conceal evidence.

KEEP fingerprints protect unchanged geometry, not every object sharing a correct material or style. If a roof needs a slope change, do not freeze that roof's dimensions or add a duplicate roof merely to satisfy KEEP. Map the review to unaffected named subgroups and correct the target in place; record ambiguous KEEP interpretations before a write.

Never write private source inputs into this workspace. Never modify the user's original SKP/DWG; work only on the verified disposable project model.
