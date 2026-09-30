# CURRENT TASK — Image → SketchUp Direct-Codex Parity v2

## Status: Ready for Codex local integration after ChatGPT remote refactor

The user paused the previous Codex run. Start only from the latest `main`.

## Single product goal

> **one architectural reference image → Sol Low + strong task Skill + Direct-Codex-like coding harness + thin SketchUp bridge → developed editable SketchUp model comparable to the known-good direct Codex result**

Do not expand into taskbook/site/new-design/render/PPT in this milestone.

Read first:

1. `AGENTS.md`
2. `docs/EXECUTION_GUARDRAILS.md`
3. `docs/SKILL_FIRST_AGENT_REFACTOR_V1.md`
4. `app/reconstruction_runtime.py`
5. `app/image_to_sketchup_skill.py`
6. `app/codex_parity.py`
7. `app/workflow_context.py`
8. `app/agent_tools.py`
9. `app/reference_assets.py`
10. `app/native_agent.py`
11. `app/litellm_runtime.py`
12. `app/main.py`
13. `app/static/index.html`
14. `app/static/studio.js`
15. `docs/HANDOFF.md`

## What ChatGPT already changed remotely

Do not redesign these from scratch:

- reconstruction session lifecycle now supports `idle -> clarifying -> planned -> building`;
- requests support `agent_action = auto|clarify|plan|execute`;
- default `auto` policy is:
  - idle -> clarify;
  - clarifying -> plan/parameterize;
  - planned/building -> execute/continue;
- explicit execute before an approved plan is rejected;
- Image → SketchUp Skill now follows:
  **inspect -> clarify high-impact unknowns -> parameter card -> approval -> persistent Ruby -> execute -> inspect -> revise**;
- reconstruction card is now a parameter baseline with KNOWN / ESTIMATED / ASSUMED values;
- persistent workspace Ruby remains the primary project-specific geometry path;
- SAIE is a helper library, not the orchestration center;
- reconstruction context must remain reference-only and small;
- Sol Low remains the parity model;
- external workspace-write probe is non-blocking and must not interrupt the user during ordinary implementation.

These remote changes are not accepted until local tests and real SketchUp execution pass.

---

# TRACK A — validate the remote refactor

Run:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Fix concrete regressions. Do not roll back the Skill-first / coding-first architecture just to satisfy stale tests.

Expected product invariants:

- legacy architecture-design path still exists;
- image reconstruction is the current product focus;
- original/private SKP/DWG is never modified;
- all live reconstruction uses a generated/disposable model;
- no Astra calls.

Do not pause the user for an internal probe or reversible setup issue. Record non-critical blockers and continue.

---

# TRACK B — wire the full reconstruction lifecycle into `main.py`

For `workflow_mode == "image_reconstruction"`, use `app/reconstruction_runtime.py` as host policy.

## B1. First turn — CLARIFY

- require at least one `inputs/reference` image;
- actual reference image reaches the model as multimodal input;
- no SketchUp geometry tools;
- no taskbook/site/program context;
- ask at most four concise questions covering only high-impact unknowns:
  1. intended use / multi-angle requirement;
  2. model scope;
  3. any known dimension anchor;
  4. unseen-geometry permission / desired visible detail;
- do not ask what the user already supplied;
- successful turn sets `reconstruction_state = clarifying` and increments `clarification_rounds`.

## B2. Second turn — PARAMETERIZE / PLAN

When state is `clarifying`, normal `auto` resolves to `plan`.

- use the image plus user answers;
- update `notes/reconstruction_card.md`;
- clearly label dimensions/assumptions as KNOWN / ESTIMATED / ASSUMED;
- return a compact parameter/construction plan;
- do not edit SketchUp;
- successful turn sets `reconstruction_state = planned`;
- UI must make approval explicit.

## B3. Approval / EXECUTE

Explicit `agent_action="execute"` is valid only after `planned`.

- verify disposable SketchUp model identity;
- enable `reconstruction_coding` tool profile;
- use same Agent thread/workspace;
- use approved parameter card;
- persistent workspace Ruby is primary;
- selected SAIE helpers are secondary;
- after successful first execution set `reconstruction_state = building`;
- later `auto` turns continue modifying the same scripts/model.

Do not route this flow through DesignIR/BuildPlan.

---

# TRACK C — make the execution environment closer to direct Codex

For image reconstruction, the model should see a small coherent workbench, not the historical 80-tool menu.

Preferred surface:

- `sketchup_run_workspace_ruby`;
- actual available scene/entity/model readback;
- camera/view/screenshot;
- selection/transform/undo/lifecycle if actually exposed;
- selected SAIE query/view and ordinary wall/opening/slab/roof helpers.

Hide for this milestone:

- legacy create_mass/create_road flow;
- ArchFlow/CAD tools;
- broad unrelated OSS tools;
- transient inline project Ruby when persistent workspace Ruby is available;
- any invented compatibility tool not present in the live connector.

Codex App Server and LiteLLM must receive the same reconstruction semantics. Provider choice must not change Skill/tool meaning.

---

# TRACK D — UI should behave like a modeling assistant, not a developer console

Image reconstruction UX:

1. **上传参考图 / 描述目标**
2. **AI澄清关键问题**
3. **建模参数与假设**
4. buttons: `修改参数` / `批准并开始建模`
5. **建模/修改中**
6. show source-matched result and allow natural-language follow-up edits.

Display state in user language:

- 待分析
- 等待补充信息
- 等待批准
- 建模/修改中

Do not expose sandbox/workspace/probe/MCP implementation details in normal UX.

---

# TRACK E — competitor desktop observation is optional and non-blocking

If the legitimately installed Building-Xuezhang desktop package / `su_mcp.rbz` is locally available, inspect ordinary accessible behavior/files/processes/runtime schemas and write:

`docs/COMPETITOR_DESKTOP_ARCHITECTURE_OBSERVATION.md`

Separate:

- Observed facts
- Inference
- Implications for our product

Useful questions:

- is the SU plugin a thin bridge or geometry-heavy engine?
- what MCP tools are exposed?
- is execution script-driven or fixed-tool-driven?
- how are plan/approval/continued edits represented?
- do multiple foundation models reuse the same Skill/bridge?
- screenshot/readback/undo/save lifecycle?

Do not bypass DRM/access controls, decompile protected binaries, or copy proprietary Skill/source.

If the package is unavailable, write `pending_external` in HANDOFF and continue. Do not stop or ask the user solely for this track.

---

# TRACK F — workspace-write probe is no longer a blocking prerequisite

Do not pause the user to request normal PowerShell execution.

If you can run the standalone probe from a normal shell context yourself, do it. Otherwise record:

`workspace_write_probe: pending_external`

and continue all non-dependent implementation/testing.

Only surface this to the user later if the real website reconstruction is actually blocked because persistent workspace files cannot be written.

---

# TRACK G — real parity benchmark

Only after the website lifecycle/tool wiring is functioning.

Use the same reference image that already produced a good result in direct Codex.

A = known-good direct Codex + GPT-6 Sol Low result.

B = website + GPT-6 Sol Low + latest reconstruction Skill + latest Agent harness.

Do not use Astra.

User instruction should stay short; do not hide weak orchestration behind a giant benchmark prompt.

Required evidence for B:

- real source image reaches model;
- clarify turn occurred;
- parameter card exists and includes explicit estimates/assumptions;
- approval gate occurred;
- persistent `.rb` file(s) authored;
- same scripts/model revised rather than restarted;
- source-matched screenshot;
- oblique screenshot;
- concrete mismatch statement;
- at least one visual self-correction;
- organized/editable geometry;
- model/effort/time/token/tool-call/failure evidence.

PASS requires the final SketchUp result to be recognizably comparable to the direct-Codex reference in developed architectural detail.

Automatic FAIL:

- only rough white boxes;
- visible facade/roof systems omitted;
- no screenshot comparison;
- no persistent coding evidence;
- no same-model correction;
- silent model upgrade to Astra;
- declaring success based only on tool/test connectivity.

---

# End-of-task

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md` with:

- exact code changes;
- local tests;
- real SketchUp evidence;
- remaining blockers;
- any `pending_external` items;
- parity benchmark result if reached.

Then commit, push `origin/main`, verify remote SHA, and stop. Do not start rendering/PPT/full-design work automatically.
