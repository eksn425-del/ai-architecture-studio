# Collaboration Model — ChatGPT + Codex + GitHub

## Source of truth

GitHub is the shared project memory and source of truth.

Chat messages are for discussion; decisions, tasks, code, and handoff status belong in the repository.

## ChatGPT responsibilities

ChatGPT owns work that can be completed safely from the connected GitHub/web environment:

- product strategy and roadmap
- competitor / open-source research
- architecture decisions
- reviewing commits and diffs
- reviewing `docs/HANDOFF.md`
- defining `docs/CURRENT_TASK.md`
- editing repository documentation
- making safe remote code/text changes that do not require access to local SketchUp, localhost, private runtime assets, or local secrets
- deciding whether a Codex result is ACCEPT / REWORK / NEXT

ChatGPT cannot directly verify the user's running Windows desktop, localhost app, installed SketchUp, Kongxing extension, local MCP process, ignored `runtime/` files, or private local assets.

## Codex responsibilities

Codex owns tasks that require the user's local development environment:

- running the application locally
- Windows / PowerShell work
- installing or updating dependencies
- starting and testing SketchUp
- calling local MCP/connector tools
- real model creation/editing/readback
- browser/localhost verification
- working with ignored private/local files
- debugging environment-specific failures
- running local test suites

Codex should also implement code changes when those changes cannot be safely validated without the local environment.

## Handoff cycle

### 1. ChatGPT turn

- inspect `origin/main`
- review the last Codex handoff
- make safe remote fixes when appropriate
- define the next task in `docs/CURRENT_TASK.md`

### 2. Codex turn

Before work:

```powershell
git pull --ff-only
git status
```

Then:

- read `AGENTS.md`
- read `docs/CURRENT_TASK.md`
- implement
- test locally
- update `docs/HANDOFF.md`
- commit
- push to `origin/main`

### 3. Review turn

The user tells ChatGPT that Codex pushed.

ChatGPT then reviews GitHub directly and either:

- **ACCEPT**
- **REWORK** — ChatGPT updates the task
- **NEXT** — ChatGPT defines the next milestone

## Conflict rule

Do not let ChatGPT remote-edit and Codex local-edit the same code at the same time.

For this solo project, a simple turn-based `main` workflow is faster than mandatory pull requests.

If the project later has multiple developers/agents working concurrently, switch implementation work to branches + pull requests.

## Why this model

This mirrors modern coding-agent workflows where repository context, task state, diffs, and review stay attached to GitHub rather than being manually copied between chats.
