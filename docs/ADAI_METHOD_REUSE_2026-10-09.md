# ADAI SketchUp Skill + Managed MCP reuse review — 2026-10-09

Upstream inspected: `laowang-wy/adai-sketchup-skill-mcp` main at `cd1e02e9f6906945376f73032e9598643fe8eb64` (0.5.39).

## License boundary

The upstream repository is CPAL-1.0. K Studio is public and already composes MIT/Apache components. This change therefore studies ADAI's public source and architecture but **does not copy or vendor CPAL source files**. The useful ideas below are independently implemented in K Studio terminology. If a future personal-only branch wants to vendor ADAI code verbatim, keep it isolated and satisfy CPAL attribution/source obligations explicitly.

## What ADAI does better than our current loop

1. It turns "how to build this form" into a first-class construction decision instead of leaving every pass to free-form Ruby improvisation.
2. It separates a complete primary form from a representative repeatable module, then replication, variants/detail and finish.
3. Shared geometric facts are treated as shared parameters/host relationships instead of being guessed independently by walls, openings, roofs and copies.
4. Visual review is change-focused: review the thing just changed plus its host/interfaces before spending effort on unrelated views.
5. Existing-object corrections keep the original object scope and method rather than making overlapping replacement geometry.
6. Its current helper catalog exposes several geometry families (profile extrusion, holes, section/mesh/shell-like construction, instances) rather than using boxes for every shape.

## What K Studio already has that remains stronger for our target

- one verified ProjectRuby writer;
- post-write expected/actual receipts;
- host-certified canonical six-view evidence;
- independent read-only visual Critic;
- source-fidelity modes and evidence ledger;
- structured facade schedule;
- active-context compaction;
- KEEP path regression guard;
- recoverable checkpoints and native SKP reopen/edit evidence.

So this milestone does **not** replace our runtime with ADAI's Managed MCP.

## Adopted now

K Studio adds `notes/construction_strategy.json` as compact project-local modeling memory:

- fixed internal stage order: primary form → representative module → replication → variants → finish;
- shared parameters with provenance;
- each visible system chooses one construction method;
- systems record exact owned target paths and verification views;
- dependency names must resolve to shared parameters;
- strategy survives active-context compaction.

The Planner must write the strategy in the same plan turn as reconstruction card/evidence/facade schedule. The Builder must follow it internally without asking for new approval between stages.

Recommended method routing:

- continuous facade with rectangular windows/doors → `continuous_wall_with_openings`;
- constant cross-section canopy/parapet/trim → `profile_extrusion` or custom owned Ruby;
- changing roof/curved/section-varying geometry → `loft_or_mesh` / custom owned Ruby;
- repeated mullions/louvers/windows/furniture → `prototype_instance` after one representative module is correct;
- unusual project-specific geometry → `custom_owned_ruby`.

Important: method names are planning contracts, not claims that a new geometry engine exists. Current executable helpers remain the proven K Studio/SAIE-owned subset plus guarded custom Ruby.

## Next local validation

Run `docs/QUALITY_LOOP_V2_7.md`. The key question is whether externalizing construction method/stage/shared-parameter decisions reduces full-root improvisation, wall/roof regressions and token/tool waste on the same six-view villa.
