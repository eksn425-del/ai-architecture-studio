# CURRENT TASK — OSS Takeover v1 rework: SAIE 2024 compatibility + standalone workspace validation

## Status: Ready for one focused local rework

Read `docs/OSS_TAKEOVER_V1_REVIEW.md` first.

Do **not** start another architecture-quality benchmark. Do **not** call Astra. Luna Max may be used only as the coding/local integration agent.

## Why this rework exists

The previous local run correctly completed the ArchFlow migration and preserved the Kongxing path, but two gates remain unresolved.

1. **SAIE was classified too early as blocked.** Upstream `docs/INSTALL.md` says SketchUp 2025 is tested while **2024 may work but is untested**, and upstream `scripts/install_plugin.ps1` explicitly supports `-Version 2024 -Force`. The workstation's SketchUp 2024.0.484 therefore needs one real reversible compatibility attempt before SAIE is called incompatible.
2. **Codex workspace-write was tested from inside a nested Codex/Luna coding host whose outer policy forced read-only.** The product policy shape is correct, but standalone Windows acceptance still needs a test outside that host. Do not weaken the sandbox to make the nested-host test pass.

## Before starting

1. `git pull --ff-only`
2. Confirm the worktree is clean.
3. Read:
   - `AGENTS.md`
   - `docs/OSS_TAKEOVER_V1_REVIEW.md`
   - `docs/HANDOFF.md`
   - `THIRD_PARTY_NOTICES.md`
4. Run `scripts/check.ps1` once.
5. Use only disposable/generated models and ignored `.local/` / `runtime/` paths.

## Priority 1 — real SAIE 1.0.0 compatibility smoke on SketchUp 2024

Use the actual upstream source; do not reimplement SAIE.

Clone or refresh upstream `iamahsanmehmood/saie` under an ignored path such as:

`.local/oss/saie`

Pin/record the tested upstream revision and SAIE version.

Install the Python package from that checkout or use the existing project venv, then use the **upstream** Windows plugin installer with SketchUp 2024 explicitly selected. Upstream itself documents:

```powershell
.\scripts\install_plugin.ps1 -Version 2024 -Force
```

Prefer a reversible copy/symlink install and keep a record of which files were installed.

Then launch SketchUp 2024 and check the Ruby Console / Extensions menu.

### Minimum connectivity gate

Prove, in order:

1. the plugin loads without a fatal Ruby error;
2. the local SAIE bridge starts;
3. `saie ping` succeeds;
4. the live MCP server lists tools;
5. `ARCH_STUDIO_ENABLE_SAIE=1` makes namespaced `saie__...` tools appear in the website tool surface.

If any step fails, stop there and capture the **exact** error. A real load/API incompatibility is then a valid blocker. Do not patch large parts of SAIE during this milestone.

### Deterministic no-LLM geometry smoke

Only if connectivity succeeds, open a completely disposable blank SketchUp model and call upstream tools directly — no Astra/Luna/Sol architecture generation.

Minimum evidence:

- wall network;
- one real door/window opening;
- slab;
- non-flat roof if exposed by the live server;
- stable semantic/AI IDs;
- scene/entity/model verification query;
- snapshot/canonical view;
- one modify operation;
- one delete/repair cycle on the same model;
- resulting SketchUp entities remain editable.

Use the live upstream tool schemas as authoritative. Do not hard-code the older registry list.

If the smoke passes, keep SAIE optional and namespaced. Do not replace Kongxing's verified model-identity/lifecycle boundary until a separate decision proves that is better.

## Priority 2 — standalone workspace-write acceptance

The previous failure occurred inside a Codex-managed coding host whose outer command policy was read-only. Do not try to escape that outer policy.

Prepare a small deterministic probe/script that can be run from a **normal Windows PowerShell session outside Codex/Luna** and that exercises the same product App Server configuration:

- `workspace-write`;
- the single generated `runtime/agent_workspace` writable root;
- network disabled;
- a harmless write inside the workspace should succeed;
- a harmless write into a synthetic sibling `inputs/` sentinel should fail;
- no private project input is touched;
- no `danger-full-access`.

If Codex itself cannot execute this standalone test because it is trapped inside the outer read-only host, leave the script/instructions ready and record that the user must run it from normal PowerShell. Do not falsely mark it PASS.

## Priority 3 — verification

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md` with:

- exact SAIE upstream revision/version;
- whether SAIE actually loaded in SketchUp 2024;
- exact `saie ping` result or exact Ruby/bridge error;
- live tool count if connected;
- deterministic wall/opening/slab/roof/query/view/edit smoke result if connected;
- standalone workspace-write probe status;
- tests and remaining blockers.

Commit and push `origin/main`, verify the remote SHA, then stop for ChatGPT review.

## Do not do

- no Astra call;
- no architecture-quality benchmark;
- no large SAIE fork/port unless a very small compatibility fix is proven necessary first;
- no new custom wall/opening/roof/BIM engine;
- no new generic MCP server;
- no `danger-full-access` workaround;
- no private thesis/source assets in Git.