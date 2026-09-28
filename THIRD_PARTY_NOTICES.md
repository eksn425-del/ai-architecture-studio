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
- Current upstream compatibility note: upstream documentation targets SketchUp 2025; local compatibility must be verified before enabling the backend.

## Supex

- Upstream: `darwin/supex`
- License: MIT
- Use in this repository: no source is currently vendored. The project is used as a reference for project-local agentic scripting, model introspection, screenshot verification, and advanced geometry architecture. Copy/runtime adoption requires platform compatibility review.

## ArchFlow Studio

- Upstream: `bingxijun/archflow-studio`
- Source license: Apache License 2.0
- Upstream branding/media: separate restrictions apply; do not reuse branding or showcase media merely because source code is Apache-2.0.
- Use in this repository: implementation-level evaluation for semantic project state, validation/metrics, DXF/output, generated SketchUp Ruby, standard views and run records. Concrete modules may be adopted/wrapped with attribution as recorded in future commits.

## LiteLLM

- Upstream: `BerriAI/litellm`
- Use in this repository: optional external dependency for provider compatibility; source is not vendored here. See `requirements-model-providers.txt`.

## PlanFloor AI Agent

- Upstream currently tracked as `zhixiangggggggg/sketchup-planfloor-ai-agant` from its public README.
- Reuse license status in this project: not yet verified as compatible.
- Use in this repository: architecture/workflow study only. No source should be copied until a compatible license is confirmed.

## Other surveyed projects

VBO SkAgent and SketchUp Agent Control are retained as fallback/reference candidates under the license status recorded in `docs/OPEN_SOURCE_COMPONENT_MAP.md`. If source is later vendored or copied, add the exact upstream revision, license text, and reuse boundary here in the same commit.
