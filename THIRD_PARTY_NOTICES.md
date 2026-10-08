# Third-Party Notices

AI Architecture Studio intentionally composes existing open-source building blocks rather than reimplementing every subsystem. This file records the current reuse boundaries. Upstream licenses remain authoritative.

## Adopted SketchUp runtime Skill excerpts

- `euphraetes/sketchup-ai-skill`, MIT, revision `10e1e0fb47abcc30c033e6f2046f3252ca4386d3`: selected geometry-validation prose and `safe_normal` example from `sketchup_api_skill.md`.
- `marlinBian/sketchup-agent-harness`, MIT, revision `e431eef6c9a9ee73a611fd68952a6aaa78566b12`: selected project-memory guardrails from `skills/project-runtime-memory/SKILL.md`.
- Excerpts and both upstream licenses are bundled under `app/vendor/sketchup_runtime_skills/`, loaded by the image reconstruction Skill. Local compatibility text clarifies that the host owns Undo and our persistent card/Ruby remain the project representation. Upstream plugin setup, strict method-length requirements and mandatory `design_model.json` are not adopted. The upstream `safe_offset` example is excluded: `Edge#line` is a point/vector pair, while `Array#offset` offsets a point by a vector, not a line by a scalar. These excerpts are guidance, not evidence that image reconstruction quality passed.

## Modeling quality loop sources

- gaoypeng/3dcodebench, Apache-2.0, inspected revision 42c7780ed3fcbd466f17f058f62e7996233777f7: K Studio adapts the bounded visual-critique response/parse pattern from core/visual_critique.py, but changes the critic into a read-only architectural reviewer that returns at most three targeted mismatches and a KEEP list. The upstream benchmark/provider stack is not vendored.
- dcc-mcp/dcc-mcp-sketchup, MIT, inspected revision b7981838eca24996e7e9c2959af1463162022f66: K Studio adapts the post-write expected/actual read-back contract from src/dcc_mcp_sketchup/write_contract.py. K Studio keeps its existing Kongxing transport and performs a post-commit owned-root readback because the current bridge does not yet expose the upstream adapter's pre-commit verification hook.
- The corresponding upstream license texts and provenance note are bundled under app/vendor/modeling_quality_sources/. These adaptations do not imply that K Studio has passed real SketchUp visual acceptance; Windows host validation remains required.

## Local desktop shell

- pywebview 6.2.1 (`r0x0r/pywebview`): BSD license; adopted as a thin native WebView shell around the existing FastAPI/frontend, without copying competitor UI source.
- PyInstaller 6.x: GPL with its distribution exception; build tooling for the local executable, not a new Agent runtime. Upstream license/exception must accompany redistributed build tooling where applicable.
- The generated local package does not include SketchUp, proprietary competitor assets, private project inputs, Codex credentials or the machine's Kongxing installation. Connector/plugin distribution and clean-machine acceptance remain separate release gates.

## SketchUp Architect Skill

- Upstream: `Mentat-Uran/sketchup-architect-skill`
- License: MIT
- Use in this repository: selected source/reference material is vendored under `app/vendor/sketchup_architect/` with the upstream license preserved. Local compatibility patch (2026-10-01) rejects empty owned roots before commit, captures persistent IDs before committing, and avoids unnecessary make_unique on singly instanced groups.

## SAIE — SketchUp Automation & Intelligence Engine

- Upstream: `iamahsanmehmood/saie`
- License: MIT
- Use in this repository: optional external package / MCP backend. SAIE source is not vendored here. `app/oss_backends.py` provides a thin standards-based adapter to an installed upstream MCP server.
- Current upstream compatibility note: SketchUp 2025 is the tested target. Upstream `docs/INSTALL.md` explicitly says SketchUp 2024 may work but is untested, and the upstream Windows installer accepts `-Version 2024`. Local 2024 compatibility must therefore be tested rather than treated as a proven incompatibility.
- Local SketchUp 2024 compatibility uses pinned upstream revision `eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f` plus the small MIT-covered source patch in `patches/saie/saie-2024-compat.patch`. The patch repairs the opening cutter orientation and SketchUp attribute serialization; `scripts/apply_saie_2024_patch.ps1` checks the upstream SHA before applying it. The upstream license remains in the installed SAIE source checkout.

## Supex

- Upstream: `darwin/supex`
- Adopted guidance revision: `66c9eed0921c418be3f1bd4ef5f100f6b5f2ad4c` (v0.3.0)
- License: MIT
- Use in this repository: selected agent-workflow guidance is vendored under `app/vendor/supex_agent_guide/` with the upstream MIT license preserved. The adopted behavior is file-based Ruby authoring, execute/inspect/revise loops, project persistence, organized geometry and multi-view visual QA.
- Runtime boundary: the Supex macOS/SketchUp-2026 runtime, REPL, VCAD sidecar/viewer and transport stack are **not** copied into this repository because they are not currently a proven Windows/SketchUp-2024 fit. AI Architecture Studio implements only the minimal glue needed to apply the reusable workflow to its existing guarded Kongxing/SAIE/ArchFlow stack.

## ArchFlow Studio

- Upstream: `bingxijun/archflow-studio`
- Source license: Apache License 2.0
- Upstream branding/media: separate restrictions apply; do not reuse branding or showcase media merely because source code is Apache-2.0.
- Use in this repository: the upstream source is cloned only into ignored `.local/oss/` by `scripts/install_archflow.ps1` and installed editable. `app/oss_backends.py` wraps the upstream `archflow` CLI for doctor/check/plan/run operations on manifests confined to the generated agent workspace. ArchFlow remains the implementation owner of semantic validation, metrics, DXF/Ruby/review artifact generation; its source is not copied into this repository.

## LiteLLM

- Upstream: `BerriAI/litellm`
- Use in this repository: optional external dependency for provider compatibility; source is not vendored here. See `requirements-model-providers.txt`.
- Public source review on 2026-10-02: `7d50a31eb5b080c29438f97be7701e117938ce88`. Upstream root LICENSE grants MIT to non-enterprise source; `enterprise/` has separate licensing. This project uses the SDK, not enterprise-covered features. No new LiteLLM source was vendored in this review.

## PlanFloor AI Agent

- Upstream currently tracked as `zhixiangggggggg/sketchup-planfloor-ai-agant` from its public README.
- Reuse license status in this project: not yet verified as compatible.
- Use in this repository: architecture/workflow study only. No source should be copied until a compatible license is confirmed.

## Building-Xuezhang desktop observation

- Use: read-only observation of user-accessible installation structure, tool schemas and the user's local execution history.
- No compatible redistribution license for the competitor's own SketchUp Skill/bridge/application was established. No proprietary source, prompts, generated project scripts or private assets were copied into this repository.
- License files in bundled third-party runtimes apply to those individual packages only. Later reuse must obtain and attribute the corresponding upstream package; it does not authorize copying the enclosing application.

## Other surveyed projects

VBO SkAgent and SketchUp Agent Control are retained as fallback/reference candidates under the license status recorded in `docs/OPEN_SOURCE_COMPONENT_MAP.md`. If source is later vendored or copied, add the exact upstream revision, license text, and reuse boundary here in the same commit.

## markdown-it 14.1.0

MIT licensed upstream `markdown-it/markdown-it`, npm distribution 14.1.0 (package shasum `3c3c5992883c633db4714ccb4d7b5935d98b7d45`). Only upstream browser minified bundle and LICENSE are vendored in `app/static/vendor/markdown-it/`. Used for safe chat/parameter Markdown rendering with HTML disabled and restricted links/images.

The full pywebview BSD license is retained at `app/vendor/pywebview/LICENSE`. Desktop packaging excludes private runtime project data and locally installed proprietary connector/plugin files.
