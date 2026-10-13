# Claude Code entry — K Studio

Claude Code must first read [AGENTS.md](AGENTS.md), the **top** of [docs/CURRENT_TASK.md](docs/CURRENT_TASK.md), and the **top** of [docs/HANDOFF.md](docs/HANDOFF.md), then their currently linked authoritative next-task document. Re-check current `main` HEAD; old summaries and this file never supersede a newer owner handoff.

**When the owner asks for an independent product / architecture / Agent audit**, use [docs/CLAUDE_INDEPENDENT_REVIEW_BRIEF_2026-10-13.md](docs/CLAUDE_INDEPENDENT_REVIEW_BRIEF_2026-10-13.md). It is a *read-only review brief*, not approval to execute the current native P0, silently change code, run paid inference, access local private materials, start another building, or merge a PR. Ordinary implementation work still follows the current owner instruction and existing safety gates.

This repository is PUBLIC. Do not add a user's private memory, source reference images, private SKP files, keys, local absolute paths, private-repo contents, account data, or nonpublic competitor materials here. Never publish inferred personal details from a separate private context. Do not make this repository dependent on private memory access for its own audit.

The project's model-facing website Agent, the development-time Codex controller, official open-source Codex Harness, and paid provider inference are separate concepts. Honor the actual recorded model identity and source/GUI/native evidence, not marketing names. A code/CI success is not SketchUp visual or deliverability PASS.
