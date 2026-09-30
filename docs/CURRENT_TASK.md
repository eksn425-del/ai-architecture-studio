# CURRENT TASK — Skill-first Image → SketchUp / Direct-Codex Parity v1

## Status: Ready for Codex local integration

The product direction is now intentionally narrow:

> **one architectural reference image → cheap multimodal/coding model + strong task Skill + persistent Agent harness + thin SketchUp bridge → developed editable SketchUp model**

Do **not** continue taskbook/site/new-design generation in this milestone.

The user has already shown that direct Codex with a cost-efficient model can create developed architecture from one image. Therefore the current problem is not “find a stronger foundation model”; it is **close the Agent-harness / Skill / bridge gap between the website and direct Codex**.

Read first:

1. `AGENTS.md`
2. `docs/SKILL_FIRST_AGENT_REFACTOR_V1.md`
3. `app/reconstruction_runtime.py`
4. `app/image_to_sketchup_skill.py`
5. `app/workflow_context.py`
6. `app/agent_tools.py`
7. `app/reference_assets.py`
8. `app/codex_parity.py`
9. `app/native_agent.py`
10. `app/litellm_runtime.py`
11. `app/main.py`
12. `app/static/index.html`
13. `app/static/studio.js`
14. `docs/HANDOFF.md`

## What ChatGPT already changed remotely

Do not redesign these from scratch:

- added reconstruction lifecycle state to `AgentSession`;
- added `ConversationRequest.agent_action = auto|plan|execute`;
- added `app/reconstruction_runtime.py` with deterministic plan/execute policy, reference-only scope and small context payload;
- changed reference discovery so image reconstruction can use only `inputs/reference/`;
- rewrote the Image → SketchUp Skill as a shorter coding-first method-card workflow;
- changed the persistent Agent workspace to Direct-Codex-style `plan -> persistent Ruby -> execute -> inspect -> revise`;
- added `reconstruction_coding` tool profile in `AgentToolSurface` so image reconstruction no longer exposes the full 80-tool surface;
- made persistent `sketchup_run_workspace_ruby` the primary reconstruction execution tool, with selected SAIE tools as helpers;
- added pure-Python tests for the new policy/profile/reference scope.

These changes are **not accepted until local tests and real SketchUp execution pass**.

---

# TRACK A — validate/fix the remote changes

Start from a clean working tree:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Fix concrete regressions. Do not roll back the skill-first architecture just to satisfy an old test assumption.

Expected behavior to preserve:

- legacy architecture-design path still exists;
- image reconstruction is the current default product workflow;
- original/private SKP/DWG remains protected;
- all live modeling uses a generated/disposable model.

---

# TRACK B — wire plan -> approve -> execute into the website

## B1. main.py reconstruction policy

Use `app/reconstruction_runtime.py` instead of duplicating policy in the endpoint.

For `workflow_mode == "image_reconstruction"`:

1. call `require_reconstruction_reference(project_dir)` before planning/execution;
2. build prompt context from `reconstruction_context_payload(context)` rather than the full taskbook/site/program context;
3. resolve `agent_action` with `build_reconstruction_turn_policy(...)`;
4. first `auto` turn on an idle reconstruction session resolves to **plan**;
5. planning turn receives actual reference `localImage` input and the Image → SketchUp Skill, but **no SketchUp geometry tools**;
6. planning turn must update `notes/reconstruction_card.md` and return a concise geometry/construction plan;
7. after successful plan, set `session.workflow_mode = image_reconstruction` and `session.reconstruction_state = planned`;
8. explicit/approved execute requires:
   - a valid reference image;
   - a ready disposable SketchUp session;
   - `session.reconstruction_state` already `planned` or `building`;
9. execute turn enables the reconstruction coding tool profile and uses the same thread/workspace;
10. after first successful execute set `session.reconstruction_state = building`;
11. subsequent `auto` turns in `building` state continue editing the same model/scripts.

Do not route image reconstruction through DesignIR/BuildPlan.

For `architecture_design`, keep the existing path.

## B2. prompt size

Image reconstruction prompt must stay small.

Do not serialize the full `ProjectContext`. Include only:

- project id/name;
- reference image filenames/status;
- recent reconstruction conversation;
- current SketchUp readback during execution;
- current Image → SketchUp Skill;
- current plan/execute stage.

Do not add a giant benchmark prompt.

---

# TRACK C — wire the coding-first tool profile into both providers

## C1. Codex App Server

Update `CodexAppServerRuntime.respond(...)` to receive an explicit workflow/tool-profile signal (or a similarly clean typed parameter; do not parse arbitrary user text).

For `image_reconstruction` execution:

- call `AgentToolSurface.prepare(..., tool_profile="reconstruction_coding")`;
- discover images using only categories `("reference",)`;
- use `reference_image_label(..., reconstruction=True)`;
- record `tool_profile`, reference categories and actual tool names in ignored agent-event evidence.

For planning:

- no SketchUp dynamic tools;
- still allow the Codex workspace so it can update `notes/reconstruction_card.md`.

## C2. LiteLLM runtime

Mirror the same reference scope and `reconstruction_coding` tool profile. Do not let provider choice change the Skill/tool semantics.

## C3. reconstruction tool profile

Verify the live tool names rather than inventing them.

The desired profile is deliberately small:

- Kongxing readback/view/camera/selection/transform/undo-style tools that actually exist;
- selected SAIE query/view + ordinary wall/opening/slab/roof helpers;
- `sketchup_run_workspace_ruby`;
- no legacy `sketchup_create_mass` / `sketchup_create_road`;
- no raw `sketchup_eval_project_file` exposed to the model;
- no ArchFlow/CAD tools for this milestone;
- no transient inline `sketchup_run_project_ruby` in reconstruction mode.

If an allowlisted name does not exist locally, simply omit it; do not add a fake compatibility tool.

---

# TRACK D — product UI: copy the useful competitor interaction pattern

Image reconstruction should visibly be a two-step workflow:

### Step 1 — 分析图片 / 生成建模计划

The user uploads the reference image and sends a short request.

The UI shows the Agent plan and indicates that SketchUp has not been modified yet.

### Step 2 — 批准执行

Add a clear `批准执行` control after `reconstruction_state == planned`.

It sends `agent_action="execute"` using the same conversation thread/workspace.

After execution begins, ordinary follow-up messages should continue with `agent_action="auto"` and modify the same model.

Also show reconstruction state in the UI:

- 待分析
- 等待批准
- 建模/修改中

Do not require taskbook/site fields in image reconstruction mode. Keep them visually secondary/collapsed for this mode if practical without a large redesign.

---

# TRACK E — workspace-write prerequisite

The previous nested Codex host blocked the App Server write probe. Do not bypass it.

From an **ordinary PowerShell outside the Codex host**, run the existing standalone probe. Use Sol Low for parity unless the script requires an explicit flag:

```powershell
.\.venv\Scripts\python.exe scripts\workspace_write_probe.py --model gpt-6-sol --effort low
```

Required:

- write inside `agent_workspace` succeeds;
- write outside the allowed workspace is denied/absent.

If this still fails, diagnose supported Codex sandbox configuration before running the expensive/full reconstruction turn.

---

# TRACK F — inspect the Building-Xuezhang desktop package/SketchUp plugin locally

The user plans to provide or install the desktop package they legitimately possess.

This is an **architecture observation task**, not a proprietary-code copying task.

Inspect ordinary accessible installation/runtime facts and record **facts separately from inference**:

- desktop installation/file layout;
- model selector / Skill selector behavior;
- local processes and localhost ports;
- `su_mcp.rbz` / installed SketchUp Ruby plugin structure if ordinarily readable;
- MCP initialize/tools/list schemas exposed at runtime;
- whether tool surface is thin (execute/readback/view) or contains large geometry-specific logic;
- plan -> approval -> execution state behavior;
- model context/readback/continued-edit behavior;
- screenshot/view/undo/save-copy lifecycle;
- whether different foundation models appear to reuse the same SU Skill/bridge.

Do **not**:

- bypass license/DRM/access controls;
- decompile protected binaries merely to extract proprietary logic;
- copy proprietary Skill/source into this public repository.

The purpose is to compare our architecture against observable product behavior and decide what open-source/public implementation pieces we still need.

Write the result to a new repo doc such as:

`docs/COMPETITOR_DESKTOP_ARCHITECTURE_OBSERVATION.md`

with sections `Observed facts`, `Inference`, `Implications for our product`.

---

# TRACK G — real parity benchmark

Only after Tracks A–E pass.

Use the **same reference image** that already produced a good result in direct Codex.

A = existing direct Codex + GPT-6 Sol Low reference result.

B = website + GPT-6 Sol Low + current Image Reconstruction Skill + reconstruction coding tool profile.

Do not call Astra.

Use one short instruction, not a giant prompt:

> 按这张参考图尽可能完整地还原成可编辑的 SketchUp 模型。先分析并给我建模计划，我批准后再执行；完成后按原图视角检查并修正明显差异。

Required evidence for B:

- actual source image reaches model as multimodal input;
- reconstruction card filled;
- plan produced before geometry;
- user/host approval gate crossed;
- persistent `.rb` file(s) authored;
- same scripts/model revised rather than restarted;
- source-matched screenshot;
- oblique screenshot;
- Agent states concrete mismatches;
- at least one visual self-correction;
- organized/named editable geometry;
- model/effort/time/token/tool-call/failure evidence.

PASS only if final image is recognizably comparable to the direct-Codex reference in developed architectural detail. Connection/tool success alone is not acceptance.

Automatic FAIL:

- only rough white boxes;
- no facade depth/repeated systems when visible in source;
- no screenshot comparison;
- no persistent coding evidence;
- silently switching to Astra.

---

# Tests/checks

Add or fix tests for:

- plan/execute state transitions;
- execute rejected before plan approval;
- reference image required;
- reconstruction context excludes taskbook/site;
- reference-only multimodal scope;
- reconstruction tool profile filtering;
- planning turn has no SketchUp tools;
- execution turn uses `reconstruction_coding`;
- UI sends `agent_action` and exposes approval control;
- architecture-design path remains backward compatible.

Then run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md`, commit, push `origin/main`, verify remote SHA, then **stop** and wait for ChatGPT review.
