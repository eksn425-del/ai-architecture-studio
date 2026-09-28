# Local Execution Runbook v1 — SAIE 2024 + standalone workspace acceptance

This is the exact local sequence for Codex/Luna Max after ChatGPT's remote changes. Do not improvise a new architecture. Do not run an architecture-quality benchmark in this milestone.

## Goal

Resolve the two remaining OSS Takeover gates with direct evidence:

1. determine whether unmodified upstream SAIE 1.0.0 actually works on this machine's SketchUp 2024.0.484;
2. validate the product's `workspace-write` policy from a normal Windows PowerShell process, not from inside the nested Codex coding host.

The upstream SAIE source revision pinned for this smoke is:

`eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f`

The user repo must not copy/fork SAIE geometry code during this milestone. Use the upstream checkout under ignored `.local/oss/saie`.

---

## Phase A — repository baseline

From the repository root:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Expected before local changes:

- clean worktree after pull;
- repository tests pass;
- no private thesis assets staged.

If tests fail, fix only the concrete regression. Do not roll back the reuse-first architecture.

---

## Phase B — prepare the exact upstream SAIE source

Run:

```powershell
.\scripts\prepare_saie_2024.ps1
```

This script:

- clones/refreshes `iamahsanmehmood/saie` into ignored `.local/oss/saie`;
- checks out the pinned upstream revision;
- installs that checkout editable into the project `.venv`;
- writes ignored evidence to `runtime/saie-compat/source.json`;
- does **not** install a SketchUp plugin unless explicitly requested.

Inspect the printed revision and confirm it matches the pin.

Then run the actual reversible upstream plugin install:

```powershell
.\scripts\prepare_saie_2024.ps1 -InstallPlugin
```

This invokes upstream's own Windows installer with `-Version 2024 -Force`. It does not reimplement or patch the plugin.

If you prefer a development junction and the upstream installer supports it in the local checkout:

```powershell
.\scripts\prepare_saie_2024.ps1 -InstallPlugin -Symlink
```

Do not modify SAIE source just to make the first attempt pass.

---

## Phase C — launch SketchUp 2024 and prove connectivity

1. Close any stale SketchUp instance first if needed.
2. Launch **SketchUp 2024.0.484** normally.
3. Open `Window -> Ruby Console`.
4. Check whether an `Extensions -> SAIE` menu appears.
5. Capture the exact first fatal Ruby error if plugin load fails.

If the plugin loads, the expected bridge startup is a local SAIE WebSocket listener. From the repo PowerShell:

```powershell
.\.venv\Scripts\saie.exe ping
```

If ping succeeds, enable the website adapter only for this shell:

```powershell
$env:ARCH_STUDIO_ENABLE_SAIE = '1'
$env:ARCH_STUDIO_SAIE_COMMAND = (Resolve-Path '.\.venv\Scripts\saie-mcp.exe').Path
.\.venv\Scripts\python.exe scripts\oss_backend_cli.py status
.\.venv\Scripts\python.exe scripts\oss_backend_cli.py list --backend saie
```

Record:

- exact ping output;
- live FastMCP tool count;
- whether `create_wall`, `cut_opening`, `create_slab`, `create_roof`, `modify_wall`, `delete_wall`, `scene_summary`, `inspect_entity`, `verify_model`, `view_snapshot` are present.

The **live MCP list is authoritative**. Do not rely on the old registry file if the live server differs.

If plugin load or ping fails, stop the SAIE branch there and record the exact error in `docs/HANDOFF.md`. Do not start a porting project in this milestone.

---

## Phase D — deterministic SAIE geometry smoke, zero architecture LLM calls

Only after `saie ping` succeeds.

Open a brand-new disposable blank SketchUp model. Do not open the thesis model or any source SKP/DWG.

Run:

```powershell
.\.venv\Scripts\python.exe scripts\saie_2024_smoke.py
```

The script directly drives the **upstream SAIE MCP** and is intentionally deterministic. It does not call Astra, Luna, Sol, Qwen, GLM, or any architecture model.

It attempts, in order:

- ping and scene summary;
- four 6 m walls with stable IDs;
- a true south-wall door opening;
- a slab;
- a 25-degree gable roof;
- model verification and entity inspection;
- inline viewport snapshot;
- same-model east-wall modification;
- north-wall delete and repair;
- final verification and snapshot.

Evidence is written under ignored:

`runtime/saie-compat/smoke-<timestamp>/`

The run is PASS only if all required upstream tools exist and all calls complete without an upstream error. Do not replace a missing/failed upstream capability with a custom repo implementation just to make the smoke green.

After the script completes, visually confirm in SketchUp that the model remains ordinary editable SketchUp geometry.

---

## Phase E — website tool-surface proof

With the SAIE environment variables still set and SketchUp running:

```powershell
.\.venv\Scripts\python.exe scripts\oss_backend_cli.py list --backend saie
```

Then use a tiny local Python inspection or the existing tests to confirm the product-composed tool surface exposes `saie__...` names beside the Kongxing tools. Do not invoke an architecture model.

If a tiny glue bug prevents namespacing/discovery, fix the adapter. Do not rewrite SAIE.

---

## Phase F — standalone `workspace-write` acceptance

The previous attempt from inside Codex/Luna was invalid for final acceptance because the outer coding host forced command execution to read-only.

Codex should **prepare and explain this step**, but the actual command must be launched by the user in a **normal Windows PowerShell window outside Codex**.

From that normal PowerShell:

```powershell
cd <repo-root>
.\.venv\Scripts\python.exe scripts\workspace_write_probe.py
```

The script creates only an ignored synthetic project at:

`runtime/projects/workspace-write-probe/`

It starts the same product Codex App Server configuration with:

- `workspace-write`;
- writable root only at `runtime/agent_workspace`;
- network disabled;
- no MCP/SketchUp tools;
- Luna Low only for a tiny filesystem instruction.

Acceptance requires:

- `inside_probe.txt` exists in `agent_workspace` with `INSIDE_OK`;
- `inputs/outside_probe.txt` does **not** exist;
- no `danger-full-access` workaround.

Evidence is written to:

`runtime/projects/workspace-write-probe/runtime/workspace-write-result.json`

If Codex itself is still the active host, do not pretend to run this step successfully from inside it. Ask the user to execute the one command above in ordinary PowerShell and then inspect the resulting JSON.

---

## Phase G — final local verification and handoff

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md` with a compact evidence table containing:

- repo head SHA;
- SketchUp version;
- pinned SAIE revision/version;
- plugin load PASS/FAIL and exact error if failed;
- `saie ping` PASS/FAIL and exact output/error;
- live tool count;
- deterministic wall/opening/slab/roof/query/view/modify/delete-repair smoke PASS/FAIL;
- ignored evidence directory;
- website `saie__...` discovery PASS/FAIL;
- standalone workspace-write PASS/FAIL/BLOCKED plus result JSON path;
- repository test count;
- remaining blockers.

Then:

```powershell
git add <repo-owned changed files only>
git commit -m "Validate SAIE 2024 compatibility and workspace sandbox"
git push origin main
```

Verify `origin/main` points to the new commit and stop. Do not start a new architecture benchmark.

---

## Hard stop rules

- No Astra call.
- No Luna/Sol architecture-generation benchmark.
- No thesis-quality modeling run.
- No private thesis/source asset in Git.
- No large SAIE fork/port on first failure.
- No custom replacement wall/opening/slab/roof/BIM engine.
- No `danger-full-access` workaround.
- No claiming SAIE is compatible or incompatible without the real plugin-load/ping evidence above.
