# CURRENT TASK — Image → SketchUp v1

## Status: Ready for Codex / Sol local integration

The product focus has changed deliberately.

**Do not continue full taskbook/site/precedent architecture design yet.**

The immediate product target is:

> **one architectural reference image → cost-efficient multimodal model + strong Skill/MCP → developed editable SketchUp reconstruction**

The quality reference is the user-provided PylonLab demonstration: a single facade image becomes a recognizable multi-storey SketchUp model with glazing modules, balconies, rails, layered facade depth, ground-floor special treatment, roof pergola/louvers and basic materials. We do not have Pylon's private Skill source and must not pretend we do.

ChatGPT has already completed the GitHub-side work it can safely do remotely. **Sol is the local coding/integration executor for this milestone.**

---

## Read in this exact order

1. `AGENTS.md`
2. `docs/IMAGE_TO_SKETCHUP_V1.md`
3. `docs/HANDOFF.md`
4. `app/image_to_sketchup_skill.py`
5. `app/reference_assets.py`
6. `app/codex_parity.py`
7. `app/native_agent.py`
8. `app/main.py`
9. `app/static/index.html`
10. `app/static/studio.js`
11. `tests/test_image_to_sketchup.py`
12. `tests/test_reference_assets.py`

Also review the already-integrated execution stack:

- SAIE compatibility patch and tools;
- `app/agent_tools.py`;
- `app/workspace_ruby.py`;
- `sketchup_run_workspace_ruby`;
- Kongxing readback/view tools.

---

# What ChatGPT already changed

Do not redo these from scratch:

- added `app/image_to_sketchup_skill.py` with a source-first, three-pass reconstruction workflow;
- added explicit `ConversationRequest.workflow_mode` with `image_reconstruction` / `architecture_design`;
- changed reference-image guidance so reconstruction images are allowed to be the actual visual target instead of being weakened into generic precedent principles;
- upgraded the persistent Agent workspace to seed `notes/reconstruction_card.md`;
- documented the milestone in `docs/IMAGE_TO_SKETCHUP_V1.md`;
- added focused tests for the reconstruction Skill/workspace/reference label.

Your job is to finish the host/UI wiring, run local tests, and perform one real low-cost reconstruction benchmark.

---

# Hard scope / cost rules

- **Do not call Astra.**
- Do not run the thesis/Jinshan benchmark.
- Do not combine taskbook + site + precedent in this milestone.
- Do not add another generic MCP server.
- Do not add a new custom wall/opening/slab/roof engine already covered by SAIE.
- Use Sol as the website reconstruction model for the real benchmark; start with **low reasoning**.
- If and only if the full image/tool pipeline is proven correct but Sol Low cannot reliably follow the guided workflow, one Sol Medium retry is allowed. Record both separately. Do not silently raise reasoning.
- Use only disposable/generated SketchUp models.
- Do not commit the user's reference image or generated SKP/screenshots unless they are explicitly sanitized public fixtures. Keep benchmark evidence under ignored `runtime/` and summarize it in `HANDOFF.md`.

---

# TRACK A — wire explicit reconstruction mode end-to-end

## A1 — baseline

Run:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Fix concrete regressions from ChatGPT's remote changes first.

## A2 — backend workflow routing

Wire `ConversationRequest.workflow_mode` through the `/api/projects/{project_id}/conversation` path.

For `workflow_mode == "image_reconstruction"`:

1. import/use `load_image_to_sketchup_skill_context()` instead of the broad architecture-design Skill;
2. pass a reconstruction-specific prompt/developer instruction;
3. make the Agent treat uploaded reference image(s) as the **visual target to reconstruct**, not merely precedent inspiration;
4. explicitly tell it to ignore taskbook/site/program fields unless the user asks for them;
5. require use of `notes/reconstruction_card.md` before substantial geometry;
6. require the three-pass workflow from `docs/IMAGE_TO_SKETCHUP_V1.md`;
7. keep the same persistent thread/model/workspace across revisions;
8. include `workflow_mode` in conversation metadata / handoff evidence.

For `architecture_design`, preserve the existing behavior.

Do not route reconstruction through legacy DesignIR/BuildPlan.

## A3 — multimodal proof

Before spending a real reconstruction turn, prove that a file uploaded to:

`inputs/reference/`

reaches the Codex App Server as a real `localImage` input during `image_reconstruction`.

Requirements:

- at least one real reference image;
- filename/order visible in logs or controlled diagnostic evidence;
- generated output screenshots must **not** be rediscovered as source images;
- no fake OCR/text description substituted for the actual multimodal image.

If necessary, add a small test/diagnostic helper. Do not log private image bytes.

## A4 — UI mode selector

Add an explicit workflow selector to the web UI near the model tier:

- `图片 → SketchUp 复刻` (`image_reconstruction`) — make this the UI default for the current milestone;
- `建筑方案设计` (`architecture_design`) — retain as secondary/legacy path.

`studio.js` must send `workflow_mode` in the conversation request.

When reconstruction mode is selected, update the visible helper text so the user understands the minimal flow:

1. upload one reference image;
2. start the disposable SketchUp Agent session;
3. say e.g. `按这张图尽可能还原成可编辑 SketchUp 模型`;
4. the Agent will inspect, build, screenshot and revise.

Do not require taskbook/site inputs in this mode.

---

# TRACK B — strengthen the cheap-model reconstruction harness

## B1 — independent method-card behavior

Use the repo-owned `notes/reconstruction_card.md` as an operational card, not decoration.

Before geometry the Agent must fill at least:

- view type/confidence;
- assumed scale anchor;
- overall proportions;
- floor count/levels;
- bay/grid rhythm;
- major solids/voids;
- facade depth stack;
- repeated modules;
- balcony/canopy/roof logic;
- material/color zones;
- unseen-depth assumptions.

The card must persist into later turns and be revised rather than recreated.

## B2 — execution strategy

Prefer:

1. SAIE for ordinary semantic construction/query/edit;
2. persistent workspace Ruby for repeated facade systems and custom geometry;
3. Kongxing for verified document identity/lifecycle/view operations;
4. ArchFlow only if directly useful.

For repeated facade elements:

- build one representative module;
- inspect it;
- use SketchUp component definitions/instances or an equivalent shared recipe;
- drive repetition from shared parameters.

Do not model every window/rail/louver as an unrelated one-off object if a repeated module is obvious.

## B3 — inspect public donor projects, but do not restart architecture design

Review current public code only for directly reusable reconstruction mechanics:

### Stultus — Apache-2.0

Inspect portable code/ideas around:

- `execute_ruby`;
- scene readback;
- viewport screenshot;
- one-step Undo/transaction;
- selection/entity context;
- continued Codex session.

Reuse only pieces that improve our current Windows + SketchUp 2024 stack. Do not replace the working connector merely because Stultus has another bridge.

### Supex — MIT

Keep/reuse the persistent script + execute → inspect → revise pattern and exact entity introspection helpers where portable.

### ADAI SketchUp Skill + Managed MCP — CPAL-1.0

Study only the public workflow concepts relevant to this milestone:

- source-first reconstruction;
- method/task cards;
- guided vs autonomous execution;
- visual evidence/review;
- experience-pack idea.

**Do not copy ADAI covered source into this repository without a separate license/compliance decision.** The repo-owned reconstruction Skill must remain independently authored.

### PylonLab demonstration

Use only as a visible quality target inferred from the user's screenshots. No public source has been established, so there is nothing to copy.

---

# TRACK C — real one-image benchmark with Sol

Do this only after Tracks A/B tests pass.

## C0 — user/local source image

Use one local architectural exterior/facade reference image that the user supplies or explicitly chooses. Keep it in ignored project `inputs/reference/`; do not commit it.

Prefer a source with medium complexity similar to the Pylon example:

- 3–5 storeys;
- repeated glazing bays;
- balconies/rails;
- a distinctive roof/canopy/pergola;
- at least one special ground-floor zone;
- visible material/color changes.

## C1 — start clean

Create a new project and a brand-new verified `blank-disposable-*.skp`.

Set:

- workflow: `image_reconstruction`;
- tier: Economy;
- product model: Sol;
- reasoning: **low** for the first run.

Do not provide a taskbook or site. The point is pure image → model.

## C2 — first user instruction

Use a short natural instruction, not a giant benchmark prompt, for example:

> 按这张参考图尽可能还原成可编辑的 SketchUp 建筑模型。先分析比例、层数、开间、阳台/开口、屋顶和材质分区，再建模；完成后对照参考图看截图并自己修正明显差异。

The strength must come from the Skill/MCP/workflow, not from a one-off giant prompt.

## C3 — required modeling passes

The same Agent turn/session may use many tools. Evidence must show:

### Pass 1

- global envelope;
- storey levels;
- bay rhythm;
- major recess/projection;
- main balcony/terrace masses;
- main roof/canopy;
- largest openings/voids.

### Pass 2

- repeated glazing/door modules;
- frames/mullions;
- balcony railings;
- louvers/pergola/fins where visible;
- ground-floor special treatment;
- major material/color zones.

### Pass 3

- source-matched screenshot;
- oblique/isometric screenshot;
- Agent states concrete visual mismatches;
- Agent modifies the **same model / same persistent script(s)**;
- final screenshots captured again.

## C4 — acceptance

PASS only if the model is visibly a developed reconstruction, not merely a working tool demo.

Required where visible in the source:

- approximate floor count correct;
- major bay count/rhythm correct;
- recognizable overall proportions/silhouette;
- balconies/recesses/projections represented with depth;
- repeated windows/doors as editable systems;
- roof/canopy/pergola logic represented;
- at least two facade depth layers;
- basic material/color zoning;
- editable named groups/components;
- source-matched screenshot QA;
- at least one self-correction after visual inspection.

**Automatic FAIL:** primarily a few white boxes, flat facade without source-defining depth, no visual comparison, or tool-success claims without resemblance.

## C5 — cost evidence

Record:

- model and reasoning effort;
- total latency;
- input/output tokens when available;
- tool call count and failures;
- number of modeling/revision passes;
- whether Sol Low passed.

If Sol Low fails after the workflow/toolchain is clearly functioning, one Sol Medium retry is allowed using a new blank model and the same source/instruction. Do not call Astra.

---

# Tests to add/fix

At minimum cover:

- `ConversationRequest.workflow_mode`;
- reconstruction Skill context bound and required quality gates;
- reconstruction card seeding + preservation;
- reference-image label no longer forces anti-copy behavior;
- conversation routing selects image reconstruction context when requested;
- UI sends `workflow_mode`;
- architecture-design path remains backward compatible;
- generated screenshots are not treated as source references.

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

---

# Handoff requirements

Update `docs/HANDOFF.md` with:

- starting repo SHA;
- code changes made locally;
- test count/result;
- exact SketchUp version;
- exact Sol model + reasoning used for the benchmark;
- proof actual source image reached the model;
- reconstruction-card path and summary;
- tool surface used (SAIE/Kongxing/workspace Ruby counts or relevant calls);
- screenshot/evidence paths under ignored runtime;
- whether the Agent performed a visual self-correction;
- quality checklist PASS/FAIL item by item;
- cost/time/token evidence;
- blockers and next step.

Commit repo-owned files, push `origin/main`, verify remote SHA, then **stop**. Do not automatically move on to taskbook/site/new-design generation.

## Milestone acceptance

Image → SketchUp v1 is accepted only when a **cost-efficient Sol run** can take one real image and produce a recognizably similar, developed, editable SketchUp model through the product workflow. Connection/tool smoke success alone is not acceptance.
