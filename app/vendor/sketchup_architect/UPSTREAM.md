# Upstream provenance

The files in this directory are selectively vendored from [`Mentat-Uran/sketchup-architect-skill`](https://github.com/Mentat-Uran/sketchup-architect-skill), pinned to commit `8be9ec80359cd90a7cfc5d9b03d2b0cf86188772`.

The upstream project is licensed under the MIT License. Its original `LICENSE` file is retained unchanged. The selected architecture, continuity, Ruby modeling, and QA references are used by `app/architecture_skill.py`, which extracts a small set of sections instead of adding the full skill repository to each model prompt. The upstream transaction/audit helpers are retained unchanged and called through the existing Kongxing SketchUp connector.

No upstream MCP server, browser modeler, or desktop-control subsystem is included.
