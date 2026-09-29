# CURRENT TASK — finish SAIE repair, then validate Codex Parity v1 foundation

## Status: Ready for Codex / Sol local execution

ChatGPT has already completed the GitHub-side design and implementation work that can be done remotely. **Sol is the local coding/integration executor, not the product architecture model in this milestone.**

Do not rediscover the architecture from scratch. Execute the two local validation tracks below in order.

## Read in this exact order

1. `AGENTS.md`
2. `docs/SAIE_2024_SMOKE_REVIEW.md`
3. `docs/CODEX_PARITY_V1.md`
4. `docs/HANDOFF.md`
5. `THIRD_PARTY_NOTICES.md`
6. relevant code already written by ChatGPT:
   - `app/codex_parity.py`
   - `app/workspace_ruby.py`
   - `app/agent_tools.py`
   - `app/architecture_skill.py`
   - `scripts/saie_2024_smoke.py`
   - `scripts/codex_parity_smoke.py`
   - `tests/test_codex_parity.py`

## Hard budget / scope rules

- **Do not call Astra.**
- Do not run a thesis/Jinshan architecture-quality benchmark.
- Do not use Sol/Luna as the website architecture designer yet.
- Sol may write code, run local tests, install/patch the pinned OSS checkout, execute deterministic SketchUp smoke tests and inspect screenshots.
- Use only disposable/generated models and ignored `.local/` / `runtime/` paths.
- Do not touch the user's thesis/source SKP/DWG.
- Do not add another generic MCP server or a new custom wall/opening/roof engine.

---

# TRACK A — finish SAIE 1.0.0 / SketchUp 2024 compatibility repair

## A0 — baseline

Run:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Confirm the repository includes ChatGPT's latest Codex-parity files and the worktree is clean before local edits.

Pinned SAIE revision remains:

`eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f`

Do not silently change upstream revisions.

## A1 — focused opening diagnostic

Use a brand-new disposable SketchUp model.

The previous live run already proved SAIE loads in SketchUp `2024.0.484`, `saie ping` works and 59 tools are discovered. The remaining failure is localized to opening/metadata/verify.

In ignored `.local/oss/saie`, test the already-identified minimal boolean correction first:

```ruby
# pinned upstream currently
new_wall = cutter.subtract(wall_group)

# diagnostic candidate
new_wall = wall_group.subtract(cutter)
```

Do not redesign the opening engine. Accept the change only if a single wall + door test produces a real visible void and editable native geometry.

## A2 — metadata compatibility repair

The previous live smoke read back:

- `wall_spec: null`
- `openings_spec: [null]`
- `verify_model`: `undefined method '[]' for nil:NilClass`

Implement the smallest compatibility patch in the ignored upstream checkout so wall/opening specs are serialized to a SketchUp-safe representation (JSON text is acceptable) and parsed when read.

Patch only the upstream locations required for:

- wall create/rebuild;
- opening record/find/modify/delete;
- query entity/deep-scan/export/verify.

Requirements:

- tolerate missing/malformed legacy values;
- `verify_model` must never crash because one metadata entry is nil/malformed;
- fresh `inspect_entity(W_SOUTH)` must return reconstructable wall/opening metadata;
- no new home-grown project-state engine.

## A3 — full deterministic SAIE smoke

Restart from a new disposable blank model and run:

```powershell
.\.venv\Scripts\python.exe scripts\saie_2024_smoke.py
```

Full PASS requires, on the same model:

1. four stable-ID walls;
2. visible real door opening in `W_SOUTH`;
3. slab;
4. 25-degree gable roof;
5. successful `verify_model`;
6. usable `inspect_entity(W_SOUTH)` metadata;
7. screenshot/readback;
8. successful `modify_wall` on `W_EAST`;
9. delete + recreate/repair of `W_NORTH`;
10. successful final verify;
11. native editable SketchUp geometry.

If the focused patch succeeds, make it reproducible in our repository without vendoring SAIE wholesale:

- small patch file under `patches/saie/`;
- deterministic apply/install script;
- exact upstream revision guard;
- pin/record the locally working MCP SDK (`mcp 1.30.0` worked in the previous live run);
- update `THIRD_PARTY_NOTICES.md` only as needed.

If a small patch cannot make this reliable and would turn into a large fork, stop Track A and record **REJECT SAIE 2024** with the exact blocker. Do not keep expanding the patch indefinitely.

---

# TRACK B — validate ChatGPT's Codex Parity v1 foundation

Start Track B after Track A reaches either PASS or a documented REJECT decision. Track B itself does not require an architecture model.

## B0 — repository tests for the new parity code

Run `scripts/check.ps1` after pulling ChatGPT's changes.

Fix only concrete regressions in the newly added parity code. Do not remove the reuse-first architecture merely to satisfy an old assumption.

Confirm tests cover:

- persistent workspace seeding without overwriting agent files;
- workspace Ruby path confinement to `agent_workspace/scripts/`;
- `sketchup_run_workspace_ruby` exposure;
- continued hiding of raw `sketchup_eval_project_file` from the agent surface.

## B1 — inspect the persistent workspace created by the product

For a disposable project, verify this exists:

```text
runtime/projects/<project>/runtime/agent_workspace/
├─ README.md
├─ .architecture-studio.json
├─ notes/design_notes.md
├─ scripts/
└─ qa/
```

Edit `notes/design_notes.md`, re-run the seeding path, and prove the existing note is preserved.

## B2 — deterministic file-based modeling smoke

Prepare/open a verified disposable model whose path is under:

`runtime/projects/codex-parity-smoke/outputs/model/`

and whose filename begins with:

`blank-disposable-`

Then run exactly:

```powershell
.\.venv\Scripts\python.exe scripts\codex_parity_smoke.py
```

This script does **not** call Astra/Luna/Sol for architecture. It validates the direct-Codex-style project coding loop that ChatGPT added:

1. write `agent_workspace/scripts/parity_geometry.rb` revision 1;
2. execute it through the existing guarded `ProjectRubyExecutor`;
3. revise the same file;
4. execute revision 2 on the same owned project root;
5. prove revision progression `[1, 2]` and the same `root_pid`;
6. capture `iso`, `top`, `south`, `east` screenshots;
7. preserve the Ruby file and ignored evidence for inspection.

PASS requires ordinary editable SketchUp geometry and a real source file that remains available for the next turn/revision.

If the deterministic script reveals a small repo-owned bug, fix the glue. Do not replace the workflow with another one-shot inline generator.

## B3 — composed tool surface

With the locally available backends enabled, prove the website tool surface still composes rather than replaces:

- Kongxing named tools;
- namespaced `saie__...` tools if Track A passed;
- `sketchup_run_workspace_ruby`;
- guarded short-inline `sketchup_run_project_ruby` as fallback;
- ArchFlow where configured.

Raw `sketchup_eval_project_file`, imported raw Ruby escape tools and unsafe whole-document lifecycle operations must remain hidden from the model-facing surface.

## B4 — architecture-skill context

Verify `load_architecture_skill_context()`:

- remains within its configured context bound;
- still contains the essential SketchUp Architect sections used by existing tests;
- includes persistent project-coding / execute-inspect-revise guidance;
- includes the vendored selected Supex workflow guidance;
- retains strong-precedent adaptation behavior.

If the extra Supex context pushes required architecture sections out of the bounded context, compact the selected Supex excerpt/context rather than deleting the parity workflow.

## B5 — standalone workspace-write remains user-side acceptance

Do not fight the outer Codex sandbox.

If not already run, leave this exact command for the user to execute later from **ordinary Windows PowerShell outside Codex**:

```powershell
.\.venv\Scripts\python.exe scripts\workspace_write_probe.py
```

Mark it `BLOCKED PENDING USER POWERSHELL RUN` until real evidence exists.

---

# What NOT to do after the deterministic passes

Do not automatically continue into:

- Jinshan thesis benchmark;
- Astra architecture generation;
- Luna/Sol model-quality comparison;
- rendering/productization/auth/billing;
- more custom create_xxx geometry tools.

The next expensive architecture benchmark will be authorized only after ChatGPT reviews this foundation.

---

# Final verification and handoff

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md` with a compact evidence table containing:

- starting repo SHA;
- SketchUp version;
- SAIE Track A outcome: PASS or documented REJECT;
- exact compatibility patch files if any;
- full SAIE deterministic smoke gates;
- Codex parity workspace seed PASS/FAIL;
- persistent Ruby revision `[1,2]` + same-root PASS/FAIL;
- paths of the four parity screenshots/evidence;
- composed tool-surface inventory;
- architecture-skill bounded-context test result;
- `scripts/check.ps1` count/result;
- standalone workspace-write status;
- remaining blockers.

Commit only repo-owned files, push `origin/main`, verify the remote SHA, then **stop** and wait for ChatGPT review.

## Milestone acceptance

This milestone passes when:

- the mature execution stack has a clear SAIE decision;
- persistent file-based project Ruby works end-to-end on a disposable SketchUp model;
- the same source can be revised and re-run on the same owned model root;
- multi-view evidence is produced;
- semantic OSS tools remain composed beside project-specific coding;
- no architecture-quality model quota was spent.
