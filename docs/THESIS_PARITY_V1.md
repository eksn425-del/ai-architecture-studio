# Thesis Parity v1 — Reference-Rich Multimodal Benchmark

## Why this benchmark exists

The previous Cost / Quality Router benchmark used a synthetic text-heavy brief with no real precedent image package. That is not equivalent to the workflow that produced the user's successful graduation-design result.

The next benchmark must reproduce the **information conditions** of the successful workflow before drawing conclusions about model quality.

The question is:

> Can AI Architecture Studio, when given the same taskbook/site/precedent evidence and the same SketchUp tool environment, approach the quality of the user's successful direct Codex/Astra workflow?

This benchmark is about **product parity**, not a generic foundation-model leaderboard.

## Reference target

The historical successful direct-Codex graduation-design run is the external quality reference.

Its final SketchUp/CAD screenshots may be used for **evaluation only**. Do not feed the historical final model screenshots, final CAD, or finished geometry back into the model as precedent input unless the user confirms they were also part of the original successful input. That would make the comparison circular.

Codex should read the user's historical local Codex conversation/session when the user makes it available, reconstruct the actual prompt sequence and input order, and write only a sanitized workflow trace into ignored runtime or a safe summary in `docs/HANDOFF.md`. Do not publish private transcripts, hidden reasoning, private paths, source SKP/DWG, or copyrighted image bundles.

## Private/local benchmark inputs

The benchmark package should be local and ignored by Git.

Required input classes:

1. **Graduation taskbook** — the user's current 文教中心 taskbook.
2. **Site evidence** — the actual site CAD/DXF/coordinate data and any site images used in the successful workflow.
3. **Precedent URL** — ECADI Jinshan Neighbourhood Center:
   `https://www.ecadi.com/index.php?m=index&a=news&id=175`
4. **Precedent image/technical package** — the key images from that page that materially informed the successful design. At minimum include several of:
   - overall/bird's-eye massing views,
   - exterior perspective views showing the mountain-like envelope,
   - lower-level lane/courtyard spatial views,
   - elevated bridge/platform views,
   - program/functional diagram,
   - structural-system diagram,
   - first-floor plan,
   - second-floor plan.
5. **User intent** — the user's own design ideas and adaptation instructions.
6. **Historical prompt sequence** — reconstructed from the direct Codex graduation-design conversation when available.

All reference images used by the website must be uploaded/staged under the project's `inputs/reference/` directory. The runtime now discovers project-local images there and sends them as first-class multimodal inputs to the selected model. Generated output screenshots under `outputs/` are deliberately excluded from automatic precedent discovery.

## Taskbook constraints to preserve

Use the actual local taskbook as source of truth. The current benchmark should at minimum record/check these stated constraints rather than silently changing them:

- FAR target/limit: `< 1.82` / taskbook table value 1.82.
- Building height limit: 24 m.
- Total building area: 28,400 m².
- Above-grade counted area: about 20,900 m².
- Planned site area in the taskbook: 11,490.510 m².
- Building footprint: `< 5,520 m²`.
- Building density: `< 48.05%`.
- Green ratio: 20%.
- Program:
  - cultural activity center: 8,000 m²,
  - library: 4,000 m²,
  - community sports center: 8,000 m²,
  - reception center: 900 m²,
  - underground parking / partial wartime civil defense: 7,500 m².

If the actual site CAD area or another source conflicts with the taskbook, record the conflict and which source each model used. Do not silently reconcile it.

## Precedent principles to evaluate

The Jinshan precedent should not be treated as a shape to copy blindly. The benchmark should check whether the model actually understands and adapts the following evidence:

- clustered/settlement-like composition rather than one generic box,
- lower-level lane/courtyard/water-town spatial logic,
- upper-level mountain/bridge/platform logic,
- multiple masses linked by elevated public circulation,
- meaningful voids, courtyards, terraces and public-space sequence,
- coherent envelope/opening rhythm rather than decorated solids,
- program distributed through volumes,
- plan/section relationships supported by the precedent drawings,
- adaptation to the user's own site, entries, roads, program and height/FAR limits.

## Controlled variants

Run from separate blank disposable SketchUp copies with the same uploaded local benchmark package and the same user-message sequence.

### A — Premium parity candidate

- local Codex provider,
- actual model ID reported by the user's environment for the successful premium/Astra-class route,
- reasoning effort: **low**,
- same Architecture Skill,
- same Kongxing tool surface,
- same guarded project Ruby,
- same reference images and taskbook/site inputs.

The repository's current configured premium ID is `gpt-6-astra`. If the user's local Codex UI exposes a different concrete model ID for the successful historical session, record the resolved ID honestly rather than renaming it in documentation.

### B — Economy stress candidate

- `gpt-6-luna`,
- reasoning effort: **max** for this benchmark only,
- otherwise identical Architecture Skill / Ruby / MCP / multimodal input package.

Do not change the product's normal default merely to run this experiment. Use the explicit benchmark/config override.

### C — Historical direct-Codex result

Evaluation reference only. Do not rebuild or overwrite it.

## Before the real benchmark

First prove that the website actually delivers the intended multimodal context:

1. upload/stage the taskbook and site files;
2. upload/stage the selected Jinshan reference images;
3. confirm the agent turn records/diagnostics show the intended image filenames/count;
4. confirm both A and B receive the identical image set;
5. confirm the model can describe salient differences between at least two reference images before building;
6. only then start SketchUp generation.

If multimodal input is not actually reaching the model, stop and fix that before judging model quality.

## Modeling sequence

Reproduce the historical prompt order as closely as possible. If the old transcript contains many iterations, preserve the meaningful sequence instead of collapsing everything into one mega-prompt.

A typical sequence may include:

1. understand taskbook + site + precedent;
2. state/adopt precedent principles and site adaptations;
3. establish program/area/entry/road/height logic;
4. create the first editable SketchUp scheme;
5. inspect multiple views;
6. refine massing/envelope/openings/platform/bridge/site relationships;
7. make at least one targeted same-model natural-language revision;
8. produce/check CAD/drawing outputs where the current workflow can do so without falling back to the legacy rectangle schema.

Do not force this order if the historical conversation shows a different successful order; fidelity to the actual successful workflow is more important.

## Evaluation

Do not use entity count as the primary score. Review matched views and actual model structure.

Record at least:

1. **Taskbook fit** — area/program/height/FAR/site constraints.
2. **Precedent understanding** — spatial principles transferred rather than superficial form copying.
3. **Site adaptation** — entrances, public path, service/garage access, orientation and outdoor spaces.
4. **Massing quality** — cluster logic, vertical hierarchy, non-trivial geometry, silhouette.
5. **Plan/section logic** — spaces, levels, circulation and core relationships.
6. **Envelope/detail** — real openings, facade rhythm, slabs/roofs/platforms/bridges/stairs.
7. **Model editability** — named/semantic elements and targeted same-model revisions.
8. **Visual QA** — screenshots actually inspected and corrected.
9. **CAD/drawing continuity** — drawings correspond to the generated model where tested.
10. **Latency/usage** — actual values only when exposed; never invent cost/token numbers.

## Pass conditions

### Premium parity

The website premium run should be judged against the historical successful direct-Codex result, not against the old three-box demo.

A useful pass means it reproduces the **quality class** of the historical result: detailed, coherent, site-adapted, editable architecture with recognisable Jinshan-derived spatial logic and strong taskbook compliance. It does not have to copy the historical geometry exactly.

If the website premium run is still materially worse, identify the missing capability/input/loop from the historical direct workflow and migrate that capability before blaming reasoning effort.

### Luna Max

Luna Max does not need to equal the premium run to be commercially useful. Record whether the reference-rich multimodal package moves it from the previous architecture-quality failure into a stable usable range. If it still fails, the next question becomes whether a heavier staged workflow can compensate.

## Current code support added before this benchmark

- Project-local images under `inputs/reference`, `inputs/site`, and `inputs/brief` are now discovered in a stable reference-first order.
- Generated outputs are excluded from precedent discovery.
- The local Codex App Server route sends those images as native `local_image` turn inputs.
- The optional LiteLLM route sends the same images as multimodal `image_url` data payloads.
- Economy and Premium Codex reasoning efforts now have explicit environment overrides so the controlled `Luna max` vs `Astra low` test does not require hard-coding a new product default.

These changes still require Codex/local validation on Windows before the benchmark is accepted.
