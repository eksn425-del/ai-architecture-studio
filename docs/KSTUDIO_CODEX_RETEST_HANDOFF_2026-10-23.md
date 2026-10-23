# KStudio Codex update and retest handoff — 2026-10-23

## Scope and provenance

The owner authorizes publishing the latest code candidate on an independent GitHub branch for local Codex to update and restart testing. This is not authorization to merge main, deploy, purchase services, make paid inference calls, or resume any closed historical modeling case. Preserve original native files and all recorded failures.

The candidate is restored from the verified archive `KStudio_Codex统一API入口_修复与测试_20261023.zip`, SHA-256 `b1ec191d953e02eceddf52dc1840c66fe0ba707ca1b47d17e1808bd5142b8ecd`, on authentic base `a85c62c0f664ad2effc32a49ff4eda885afab4a5`. Archive-documented candidate `f7ffab7386e14b8e0b1a51bc65e8388627a2a257` is provenance, not a claim that its original Git commit object was recovered. Publication has a new commit identity. Raw archives, native models, images, transport logs, XML logs, and recovery-machine metadata are excluded from this code handoff.

## What changed and what was actually tested

- An explicit `codex-responses` route shares the Native Codex App Server runtime. This is Responses/SSE/tools/images compatibility, not universal third-party Chat Completions support. Existing LiteLLM routes and credentials are not automatically migrated.
- Provider/account/model isolation, strict runtime identity, selected-runtime cancellation and dispatch, Blender images and raw/projection receipt parity, shared review context, durable progress and intent checks are included.
- Historical cloud regression: **1375 Python passed, 9 skipped; 118 Node tests passed**, with a **31-test security review** recorded in the candidate evidence. These are prior results, not fresh tests on the owner's computer.
- Controlled scripted App Server plus actual product runtime and actual Blender: **16/16 checks passed**. These are deterministic fixture results, not native Codex reasoning, real-provider quality, independent Critic acceptance, or paid usage measurements.
- Actual Codex upstream thread startup was blocked by the cloud host's socket/isolation boundary before model requests. Real-provider end-to-end quality, cost and commercial acceptance remain **NOT_RUN**. Do not disable sandbox protections to manufacture a pass.
- Per-request monetary reservation is not integrated into the new runtime. A configured monetary cap therefore fails closed. **Do not remove or disable the cap to bypass this restriction.**

See the cloud test README and summary JSON files under `docs/test-results/cloud/2026-10-23-unified-codex-api/`. Some raw evidence remains in the private archive and is intentionally not included here; a missing raw log is not evidence of a fresh rerun.

## Safe update

1. Read `AGENTS.md` and `docs/CURRENT.md`. Record repository path, current branch/HEAD, configured upstream, and `git status --short`. Compare the publication branch against the existing local branch before modifying it.
2. If the worktree is dirty or contains divergent local commits, stop the dependent update and ask how to preserve/reconcile them. Do not reset, clean, overwrite, force-push, or silently stash user work. Prefer a separate worktree for the candidate.
3. Fetch the exact branch and verify its commit. Record the actual new publication SHA, not the archive provenance SHA. Follow the repository's existing environment and dependency instructions; do not change installed modeling software versions silently.

## Retest and acceptance record

### Reproducible offline setup

Install both `requirements.txt` and `requirements-model-providers.txt` into an isolated virtual environment. Provider requirements now explicitly include LiteLLM's MCP extra and HTTPX's SOCKS extra: the publication recheck exposed missing optional imports with LiteLLM 1.106.2 and the cloud's existing SOCKS proxy. Do not disable or remove proxy settings to avoid those errors.

For a restricted cloud or CI home directory, set the existing supported `ARCHFLOW_GENERATED_SCRIPT_DIR` to a writable, task-scoped directory before tests. Do not alter filesystem permissions or redirect another user's files. Example from the repository root on POSIX:

```sh
python -m pip install -r requirements.txt -r requirements-model-providers.txt
mkdir -p "$PWD/.test-runtime/generated-scripts"
ARCHFLOW_GENERATED_SCRIPT_DIR="$PWD/.test-runtime/generated-scripts" LITELLM_LOCAL_MODEL_COST_MAP=True python -m pytest -q
node --test tests/test_*.js
```

Keep `.test-runtime` local; never stage its generated scripts or other test artifacts for publication. Windows users should set the equivalent process environment variable to their own writable scratch directory. See `docs/test-results/cloud/2026-10-23-unified-codex-api/publication-recheck.json` for the actual full-run failures and their subsequent retest; it is not described as a single fresh all-green full run.

1. Run offline Python/Node regression and security tests first. Record commands, versions, exit status, passed/failed/skipped counts and exact commit. Keep failures and skipped tests visible. Distinguish fixture/mock tests from live calls throughout.
2. Verify the selected runtime/provider/account/model identity and session isolation. Test fail-closed identity errors, unsupported budgets, cancellation and dispatch without fallback to another provider or borrowed login.
3. Use a new explicitly scoped synthetic Blender fixture, not a closed owner modeling case. Record the KEEP/protected-object set, intended editable objects, raw receipts and images. Save and independently reopen the native file; compare object counts, protected properties and requested changes. Preserve original native models unchanged.
4. Before any paid/live inference, ask the owner for the exact provider/model/account, task scope, per-run and total budget, and stop conditions. Do not infer approval from historical budgets or the request to restart testing. If the runtime cannot enforce the approved monetary cap, remain blocked; do not remove it.
5. For an authorized live run, retain an actual usage ledger: requests, input/output/cache usage, retries and failures, pricing source and timestamp, billed charge when available. Label missing or unverifiable values **unknown**, never zero. Do not present JSON-size reductions or scripted token fixtures as actual savings.
6. Record the actual UI interaction and visible outcomes if recording is requested/authorized. Do not fabricate, reconstruct or stage a recording as a real run. Use the existing E-drive source project's `outputs/video-storage` and its `scripts/video-workspace.ps1` workflow per repository policy; this code worktree is not a media/cache destination. Confirm the intended source-project path rather than inventing one.
7. Deliver a concise comparison of historical fixture results versus current offline and authorized live results, including unresolved failures and **NOT_RUN** items. No main merge or deployment follows automatically.
