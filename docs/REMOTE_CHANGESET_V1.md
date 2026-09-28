# Remote Changeset v1 — what ChatGPT already changed

This file is the local validation handoff for OSS Takeover v1. Codex should validate and extend these changes rather than reimplement them.

## Runtime changes already on `main`

### 1. Composed reusable tool surface

`app/oss_backends.py`

- adds a standards-based stdio MCP adapter using the official Python MCP SDK;
- SAIE is opt-in with `ARCH_STUDIO_ENABLE_SAIE=1`;
- imported SAIE raw `execute_ruby` and whole-document lifecycle tools are blocked;
- adds an optional `ArchFlowCLIBackend` with `doctor`, `check_project`, `plan_run`, and `run` tools;
- ArchFlow tools operate only on manifests under `runtime/agent_workspace/` and reject `pipeline.execute_sketchup=true`;
- ArchFlow is opt-in with `ARCH_STUDIO_ENABLE_ARCHFLOW=1`.

`app/agent_tools.py`

- composes OSS tools beside Kongxing instead of recreating their operations;
- namespaces imported tools (`saie__...`, `archflow__...`);
- passes project scope to OSS backends;
- Kongxing-only behavior remains when optional backends are disabled.

### 2. Direct-Codex-like writable coding harness

`app/native_agent.py`

- replaces the historical read-only modeling App Server sandbox with a dedicated generated workspace:
  `runtime/projects/<project-id>/runtime/agent_workspace/`;
- App Server uses `workspace-write` with network disabled;
- the only explicit writable root is the generated agent workspace;
- taskbook/site/reference inputs are outside that root;
- the App Server working directory/runtime workspace root is the generated workspace;
- dynamic SketchUp edits still pass through the verified disposable model boundary;
- an execution override makes the actual composed dynamic tool list authoritative, so old Kongxing-only wording cannot suppress `saie__*` tools.

This uses the current public Codex App Server `workspaceWrite`/`writableRoots` policy rather than a home-grown filesystem sandbox. Local Windows acceptance is still required.

### 3. Precedent fidelity fix

`app/architecture_skill.py`

- user-requested strong precedent adaptation is explicitly allowed;
- the agent may transfer and transform concrete massing, silhouette, roof, bridge/platform, facade rhythm and spatial sequence when the user requests strong reference fidelity;
- generic anti-copy language must not collapse a requested reference-rich scheme into boxes;
- mature semantic OSS tools are preferred before Kongxing primitives and guarded project Ruby.

### 4. Install / no-LLM utilities

- `scripts/setup.ps1 -InstallSaie` installs the upstream SAIE Python/MCP package but deliberately does not auto-enable the SketchUp plugin.
- `scripts/install_archflow.ps1` clones upstream ArchFlow Studio into ignored `.local/oss/archflow-studio`, installs it editable into the repo venv, and prints the `ARCHFLOW_CORE_SKILL` path.
- `scripts/oss_backend_cli.py` lists/calls enabled SAIE or ArchFlow backend tools without invoking an architecture model.

### 5. Tests / legal hygiene

- `tests/test_oss_takeover.py` covers OSS tool composition, project-scoped dispatch, blocked SAIE lifecycle/raw-Ruby tools, precedent fidelity, workspace-write policy, old Kongxing-only instruction override, and ArchFlow manifest scoping.
- `THIRD_PARTY_NOTICES.md` records current license/reuse boundaries.
- `docs/OSS_TAKEOVER_V1.md`, `docs/OPEN_SOURCE_COMPONENT_MAP.md`, `AGENTS.md`, `README.md` and `docs/CURRENT_TASK.md` have been switched to the reuse-first milestone.

## Local work Codex still owns

Do these in order and do not run a thesis/model-quality benchmark:

1. Pull main and run the full automated test suite. Fix any syntax/API mismatch from the remote changes.
2. Confirm the local Codex App Server accepts the new `workspace-write` payload/config on Windows and can create/edit a harmless file inside `agent_workspace` while failing to write to project `inputs/`.
3. Record the exact installed SketchUp version(s).
4. If SketchUp 2025 is available/compatible, install the upstream SAIE SketchUp plugin, prove `saie ping`, enable SAIE, list real tools, and run the deterministic no-LLM wall/opening/slab/roof/query/screenshot/modify smoke.
5. If SAIE cannot run because of SketchUp version compatibility, do not rewrite SAIE; record the blocker and identify the smallest reusable upstream code path.
6. Run `scripts/install_archflow.ps1`, set the printed `ARCHFLOW_CORE_SKILL`, prove `archflow doctor --json`, then enable `ARCH_STUDIO_ENABLE_ARCHFLOW=1` and verify `archflow__...` tools appear in the website tool surface.
7. Use a tiny generated ArchFlow project in `agent_workspace` to prove upstream validation/metrics/DXF/Ruby artifact generation without an architecture LLM. Do not execute the generated Ruby against a private source model.
8. Inspect Supex for cross-platform pieces/patterns only; do not port its full macOS/VCAD stack unless upstream already supports the local environment cleanly.
9. Inspect PlanFloor architecture and license; copy no source without a compatible license.
10. Update `docs/HANDOFF.md`, commit, push `origin/main`, verify remote SHA, then stop.

## Budget rule

No Astra call. No Luna/Sol architecture-generation benchmark. The user's Luna Max may be used as the **coding agent** performing this local implementation/validation work only.
