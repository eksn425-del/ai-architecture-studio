# Third-Party Notices

AI Architecture Studio intentionally composes existing open-source building blocks rather than reimplementing every subsystem. This file records the current reuse boundaries. Upstream licenses remain authoritative.

## SketchUp Architect Skill

- Upstream: `Mentat-Uran/sketchup-architect-skill`
- License: MIT
- Use in this repository: selected source/reference material is vendored under `app/vendor/sketchup_architect/` with the upstream license preserved.

## SAIE — SketchUp Automation & Intelligence Engine

- Upstream: `iamahsanmehmood/saie`
- License: MIT
- Use in this repository: optional external package / MCP backend. SAIE source is not vendored here. `app/oss_backends.py` provides a thin standards-based adapter to an installed upstream MCP server.
- Current upstream compatibility note: SketchUp 2025 is the tested target. Upstream `docs/INSTALL.md` explicitly says SketchUp 2024 may work but is untested, and the upstream Windows installer accepts `-Version 2024`. Local 2024 compatibility must therefore be tested rather than treated as a proven incompatibility.

## Supex

- Upstream: `darwin/supex`
- License: MIT
- Use in this repository: no source is currently vendored. The project is used as a reference for project-local agentic scripting, model introspection, screenshot verification, and advanced geometry architecture. Copy/runtime adoption requires platform compatibility review.

## ArchFlow Studio

- Upstream: `bingxijun/archflow-studio`
- Source license: Apache License 2.0
- Upstream branding/media: separate restrictions apply; do not reuse branding or showcase media merely because source code is Apache-2.0.
- Use in this repository: the upstream source is cloned only into ignored `.local/oss/` by `scripts/install_archflow.ps1` and installed editable. `app/oss_backends.py` wraps the upstream `archflow` CLI for doctor/check/plan/run operations on manifests confined to the generated agent workspace. ArchFlow remains the implementation owner of semantic validation, metrics, DXF/Ruby/review artifact generation; its source is not copied into this repository.

## LiteLLM

- Upstream: `BerriAI/litellm`
- Use in this repository: optional external dependency for provider compatibility; source is not vendored here. See `requirements-model-providers.txt`.

## PlanFloor AI Agent

- Upstream currently tracked as `zhixiangggggggg/sketchup-planfloor-ai-agant` from its public README.
- Reuse license status in this project: not yet verified as compatible.
- Use in this repository: architecture/workflow study only. No source should be copied until a compatible license is confirmed.

## Other surveyed projects

VBO SkAgent and SketchUp Agent Control are retained as fallback/reference candidates under the license status recorded in `docs/OPEN_SOURCE_COMPONENT_MAP.md`. If source is later vendored or copied, add the exact upstream revision, license text, and reuse boundary here in the same commit.
