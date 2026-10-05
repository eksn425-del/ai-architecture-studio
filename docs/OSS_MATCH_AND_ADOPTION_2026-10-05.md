# SketchUp OSS matching → screening → adopted code

User requested actual code reuse after failed villa reconstruction. Fresh GitHub searches: SketchUp MCP, sketchup agent, sketchup ai modeling, sketchup reconstruction, sketchup image reconstruction, sketchup multi agent, Supex, Stultus, SAIE, sketchup architect skill. Eight candidates cloned and inspected at pinned commits (below); other search hits are not quality-validated. SEO interpreted as SU/SketchUp from the conversation.

| Candidate / inspected commit | Agent arrangement seen in source | Match and real quality evidence | Decision |
|---|---|---|---|
| [SAIE](https://github.com/iamahsanmehmood/saie) eff6f41 | Optional synchronous single BuilderAgent tool loop; MCP also serves external agents | High for semantic geometry. MIT. Windows documented; 2025 targeted, 2024 may work but untested. House pipeline/docs exist; no independently reproduced source-matched villa benchmark. LIMITATIONS records multiple boolean-cut failures. | **Adopted wall geometry subset now**; complete plugin/backend stays optional until desktop compatibility proof. |
| [Stultus](https://github.com/B-A-community/stultus) bfb0c01 | Shared tools with selected Claude/Codex provider; not a dedicated multi-agent reconstruction team | High for selection/local editing and scene evidence. Apache-2.0. README reports live SU2024 cube loop; that does not establish villa reconstruction accuracy. | **Adopted mm/XYZ bounds subset now**; use before/after IDs and sizes in transactions. Keep existing Kongxing. |
| [Supex](https://github.com/darwin/supex) 66c9eed | MCP/CLI/Ruby platform for external coding agent; no intrinsic multi-agent planner/builder/reviewer loop found | High coding-workspace fit. MIT. Explicit early-stage/macOS-only testing; VCAD sidecar is broader than this Windows repair. | Keep existing persistent coding workflow; do not port the full runtime/VCAD into Windows without evidence. |
| [SketchUp Agent Harness](https://github.com/marlinBian/sketchup-agent-harness) e431eef | Claude/Codex adapters over shared design-model truth, rules, tools and Skills | Medium. MIT. Early bathroom/floor-plan slice, explicitly not survey-quality imports. No comparable developed villa benchmark established. | Study validation/versioned evidence; do not constrain free-form reconstruction to its bathroom model or replace the bridge. |
| [VBO SkAgent](https://github.com/vbosolution/vbo-sk-agent) be6f833 | Bridge for external agent, MCP or file transport; does not arrange a multi-agent team | Medium connectivity fallback. MIT. Ruby/stdout/backtrace transport, not a demonstrated source-fidelity solver. | No replacement while Kongxing already works. |
| [Image2SketchUp](https://github.com/lengbingbing66/Image2SketchUp) eaecaf2 | Deterministic CV→IR→BuildPlan pipeline; active LLM adapter explicitly disabled | Medium input/evidence match, weak developed geometry match. MIT. Explicit simple masses/panel opening markers, simplified roofs, no public live demo. | Do not regress to a smaller geometry vocabulary; its evidence/output distinctions remain useful. |
| [SketchUp Code](https://github.com/jasperhartong/sketchup-code) 2651c4f | External Cursor/Claude agent over file bridge; baseline/diff refactor workflow | Medium local-edit verification match. MIT. Actual skeleton-dimensions plugin is documented, not house reconstruction benchmark. SU2026 actively tested; 2024+ expected. | Keep existing bridge; readback diff principle fits newly adopted evidence. No source copied this round. |
| [CAD automation](https://github.com/mihir-jai/cad-automation) fecca3c | Sequential multi-provider fallback, **not** collaborating multi-agents | Low. No repository license file found. Self-described production-ready is not proof; templates/GUI/code execution do not show villa parity. | No code copied. |

## What is actually reused

1. SAIE `_read_centerline` / `_build_wall_group`, copied into app/vendor/saie/wall_geometry.rb, MIT/LICENSE and pinned UPSTREAM retained. Model-global lifecycle code not imported. Injected `saie_wall.call(params)` validates string-key millimetre parameters and adds the group only under the existing owned root. Example:

```ruby
wall = saie_wall.call({"name"=>"rear-wall", "centerline"=>[[10000,8000],[0,8000]],
                      "thickness_mm"=>200, "height_mm"=>3200, "elevation_mm"=>0})
```

This creates a **solid segment**. Openings require surrounding wall segments or separately verified construction; do not cover openings with an uncut solid wall. Custom geometry/Ruby freedom remains available. No new mandatory IR or custom engine.

2. Stultus `bounds_mm` / `pt_mm` / `mm`, copied into app/vendor/stultus/bounds.rb, Apache-2.0 LICENSE/AUTHORS/NOTICE retained. Sizes derive from min/max XYZ rather than SketchUp's confusing bounding-box width/height/depth order. Every actual host transaction now captures `owned_before` and `owned_after`: direct-child persistent IDs, names, locks, millimetre bounds and root bounds. Object list limit 200 is explicitly marked truncated; do not declare full ID preservation if truncated. Child coordinates are relative to owned root; root bounds are in its model parent. This is numerical evidence, not image QA PASS.

## Why no multi-agent rewrite

The inspected close matches mainly rely on an external coding agent or a single tool loop, persistent code and trustworthy readback. No inspected evidence establishes that agent count itself solves unit errors, topology or dishonest visual QA. Adopt these helpers first and measure real results with the same DeepSeek; a separate reviewer could later be tested but is not claimed implemented or validated here.

## Validation / desktop handoff

Cloud: system Ruby 3.3.8 installed only in ignored runtime from Debian packages. Ruby test doubles verify copied wall footprint stays at y=8000mm, x-span, positive extrusion, thickness/elevation conversion, validation and owned target; copied Stultus bounds preserve XYZ and persistent ID. These are arithmetic/ownership tests, **not** SketchUp topology tests. Python suite: 204 passed, 2 Windows skips, 3 dependency warnings; Ruby syntax checks pass. Also ran the pinned SAIE test_units.py and test_geometry.py: 21 passed (pure math, not live SketchUp). No new live DeepSeek inference or actual SKP produced this round.

Local Codex must pull main, first use a disposable blank to verify one helper wall against measured mm bounds and normal; confirm before/after reports survive execution/readback. Then use the existing villa reconstruction project, repair real walls/openings/roof and perform a one-child edit. Publish all-view screenshots and before/after IDs/bounds, record intervention/time/usage, download/reopen/edit SKP and push results. Do not describe this OSS adoption as a quality pass until that evidence exists.
