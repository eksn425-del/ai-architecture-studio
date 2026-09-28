# CURRENT TASK — OSS Takeover v1 rework: execute SAIE 2024 smoke + standalone workspace acceptance

## Status: Ready for Codex/Luna Max local execution

ChatGPT has already completed the GitHub-side planning and scaffolding for this rework. Codex should **execute and validate**, not rediscover the plan or redesign the architecture.

Read in this order:

1. `AGENTS.md`
2. `docs/OSS_TAKEOVER_V1_REVIEW.md`
3. `docs/LOCAL_EXECUTION_RUNBOOK_V1.md`
4. `docs/HANDOFF.md`
5. `THIRD_PARTY_NOTICES.md`

## Hard budget / scope rule

- **Do not call Astra.**
- Do not run Luna/Sol architecture-generation benchmarks.
- Luna Max is the **coding/local-integration agent only**.
- No thesis-quality building test in this milestone.
- Use only disposable/generated SketchUp models and ignored `.local/` / `runtime/` files.

## What ChatGPT already implemented remotely

Do not reimplement these unless a concrete local bug is found:

- optional SAIE MCP adapter in `app/oss_backends.py`;
- namespaced OSS composition in `app/agent_tools.py`;
- project-local Codex `agent_workspace` / `workspace-write` configuration in `app/native_agent.py`;
- strong precedent adaptation policy in `app/architecture_skill.py`;
- adopted ArchFlow CLI backend and installer;
- pinned SAIE 2024 preparation script: `scripts/prepare_saie_2024.ps1`;
- deterministic no-LLM SAIE geometry smoke: `scripts/saie_2024_smoke.py`;
- standalone App Server sandbox acceptance probe: `scripts/workspace_write_probe.py`;
- exact local runbook: `docs/LOCAL_EXECUTION_RUNBOOK_V1.md`.

The SAIE source pin selected for this compatibility test is:

`eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f`

This is upstream SAIE 1.0.0 code reviewed by ChatGPT. Do not silently test a different source revision.

## Step 0 — pull and baseline

Run exactly:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Confirm the worktree is clean before local edits. If a repository test fails, fix the concrete regression only.

## Step 1 — prepare exact upstream SAIE source

Run:

```powershell
.\scripts\prepare_saie_2024.ps1
```

Expected behavior:

- checkout under ignored `.local/oss/saie`;
- exact pinned commit checked out detached;
- editable install into repo `.venv`;
- ignored metadata at `runtime/saie-compat/source.json`.

Verify the printed revision equals the pin above.

## Step 2 — install unmodified upstream plugin into SketchUp 2024

Run:

```powershell
.\scripts\prepare_saie_2024.ps1 -InstallPlugin
```

This intentionally calls upstream's own `install_plugin.ps1 -Version 2024 -Force`.

Then:

1. launch **SketchUp 2024.0.484** normally;
2. inspect `Window -> Ruby Console`;
3. check whether `Extensions -> SAIE` exists;
4. if load fails, capture the exact first fatal Ruby error and stop the SAIE branch;
5. do **not** start a large compatibility port.

Why this test is required: upstream installation docs say SketchUp 2025 is tested but **2024 may work**, and the upstream Windows installer explicitly accepts `-Version 2024`.

## Step 3 — connectivity gate

Only if the plugin loads, run from the repo PowerShell:

```powershell
.\.venv\Scripts\saie.exe ping
```

If ping succeeds:

```powershell
$env:ARCH_STUDIO_ENABLE_SAIE = '1'
$env:ARCH_STUDIO_SAIE_COMMAND = (Resolve-Path '.\.venv\Scripts\saie-mcp.exe').Path
.\.venv\Scripts\python.exe scripts\oss_backend_cli.py status
.\.venv\Scripts\python.exe scripts\oss_backend_cli.py list --backend saie
```

Record:

- exact ping output;
- live tool count;
- whether the live list includes `create_wall`, `modify_wall`, `delete_wall`, `cut_opening`, `create_slab`, `create_roof`, `scene_summary`, `inspect_entity`, `verify_model`, `view_snapshot`.

The live FastMCP list is authoritative. Do not hard-code the old registry file.

## Step 4 — deterministic real SketchUp modeling smoke, no architecture LLM

Only if Step 3 succeeds.

Open a completely disposable blank SketchUp model. Do not open any thesis/source model.

Run:

```powershell
.\.venv\Scripts\python.exe scripts\saie_2024_smoke.py
```

The script already contains the exact smoke sequence. Do not replace it with an improvised prompt.

It attempts:

1. `ping` / `scene_summary`;
2. four 6 m walls with stable IDs;
3. one true door opening;
4. slab;
5. 25-degree gable roof;
6. verify + inspect;
7. inline snapshot;
8. same-model wall modification;
9. wall delete + repair;
10. final verify + snapshot.

Expected ignored evidence:

`runtime/saie-compat/smoke-<timestamp>/`

After the script, visually inspect SketchUp and confirm the geometry is still normal editable SketchUp entities.

**Do not write a custom wall/opening/slab/roof implementation if an upstream tool fails.** Record the exact upstream failure instead.

## Step 5 — website namespaced-tool proof

With SAIE still enabled in that PowerShell session, prove the website adapter sees the live backend and exposes `saie__...` names beside the existing Kongxing surface.

Use existing adapter/test code; a tiny deterministic Python inspection is allowed. Do not invoke an architecture model.

If there is a small adapter/schema mismatch, fix only that glue. Do not rewrite SAIE.

## Step 6 — standalone workspace-write acceptance

The earlier nested Codex test is not final evidence because the outer Codex/Luna host forced command execution to read-only.

Codex should **not try to bypass that outer host policy**.

The repo now includes the exact standalone probe:

`scripts/workspace_write_probe.py`

This command must ultimately be launched from a **normal Windows PowerShell session outside Codex/Luna**:

```powershell
cd <repo-root>
.\.venv\Scripts\python.exe scripts\workspace_write_probe.py
```

It uses a tiny `gpt-6-luna` Low filesystem-only turn and only a synthetic ignored project. It verifies:

- write inside `agent_workspace` succeeds;
- write into synthetic project `inputs/` remains blocked;
- network stays disabled;
- no `danger-full-access`.

Codex should prepare/explain this command. If it cannot execute it outside its own nested host, leave it for the user and mark the gate **BLOCKED PENDING USER POWERSHELL RUN**, not FAIL and not PASS.

Expected evidence:

`runtime/projects/workspace-write-probe/runtime/workspace-write-result.json`

## Step 7 — no extra architecture experimentation

Do not, after SAIE/workspace testing:

- run the Jinshan thesis benchmark;
- call Astra;
- ask Luna/Sol to design a building;
- compare model quality;
- add another custom MCP server;
- build another custom geometry engine.

This milestone is finished once compatibility/integration evidence is collected.

## Final verification

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md` with an evidence table containing:

- final repo SHA before your commit;
- exact SketchUp version;
- SAIE source revision and version;
- plugin load PASS/FAIL with exact error if failed;
- `saie ping` PASS/FAIL with exact output/error;
- live tool count;
- SAIE deterministic wall/opening/slab/roof/query/view/modify/delete-repair PASS/FAIL;
- ignored evidence directory;
- website `saie__...` discovery PASS/FAIL;
- standalone workspace-write PASS/FAIL/BLOCKED and result JSON path if available;
- `scripts/check.ps1` result;
- remaining blocker(s).

Then commit only repo-owned changes:

```powershell
git add <repo-owned changed files only>
git commit -m "Validate SAIE 2024 compatibility and workspace sandbox"
git push origin main
```

Verify `origin/main` points to the pushed SHA and **stop** for ChatGPT review.

## Acceptance criteria

1. Baseline repository checks pass — PASS/FAIL.
2. Exact pinned SAIE upstream source is prepared — PASS/FAIL.
3. SAIE plugin is actually attempted on SketchUp 2024.0.484 — PASS/FAIL.
4. Plugin-load and `saie ping` outcome is backed by exact local evidence — PASS/FAIL.
5. If connected, real no-LLM geometry smoke proves wall/opening/slab/roof/query/view/edit on the same disposable model — PASS/FAIL/N/A after real blocker.
6. If connected, website exposes live namespaced `saie__...` tools — PASS/FAIL/N/A after real blocker.
7. No SAIE source fork/reimplementation is introduced merely to pass the smoke — PASS/FAIL.
8. Workspace-write probe is either genuinely run outside Codex or explicitly left pending for the user — PASS/FAIL/BLOCKED.
9. No Astra call and no architecture-quality benchmark — PASS/FAIL.
10. HANDOFF, tests, commit, push and remote SHA verification complete — PASS/FAIL.
