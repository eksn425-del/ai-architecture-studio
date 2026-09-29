# CURRENT TASK — OSS Takeover v1.1: repair SAIE opening/metadata path, then finish deterministic smoke

## Status: Ready for Codex / Luna Max local execution

ChatGPT has reviewed the real SketchUp 2024 smoke at commit `192f80e147c04b331c9ebaaea4c8d8bf74a825de` and localized the remaining failure.

**Do not rediscover the problem from scratch.** Read `docs/SAIE_2024_SMOKE_REVIEW.md` first and execute the focused repair below.

## What is already proven

- SketchUp `2024.0.484` can load/connect to upstream SAIE 1.0.0 sufficiently for `saie ping` to return `PONG plugin_v1.0.0`.
- Live SAIE MCP discovery returns 59 tools.
- The website composes 15 Kongxing tools + 59 namespaced `saie__...` tools.
- Deterministic SAIE calls created wall/slab/gable-roof geometry in a disposable SketchUp model.
- The smoke stopped specifically in the opening / metadata / verify path.
- No architecture LLM is needed for this repair.

## Hard scope and budget rules

- **No Astra calls.**
- No Luna/Sol architecture-generation benchmark.
- Luna Max is coding/local-integration only.
- No thesis/Jinshan building test.
- No new generic MCP server.
- No custom replacement wall/opening/slab/roof engine.
- Use only disposable models and ignored `.local/` / `runtime/` files.

## Read in this order

1. `AGENTS.md`
2. `docs/SAIE_2024_SMOKE_REVIEW.md`
3. `docs/HANDOFF.md`
4. `THIRD_PARTY_NOTICES.md`
5. upstream pinned files:
   - `.local/oss/saie/ruby_plugin/su_mcp_bridge/ops/opening.rb`
   - `.local/oss/saie/ruby_plugin/su_mcp_bridge/ops/wall.rb`
   - `.local/oss/saie/ruby_plugin/su_mcp_bridge/ops/query.rb`

Pinned upstream revision remains:

`eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f`

Do not silently change upstream versions during this task.

---

## Phase 0 — baseline

Run:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Confirm the user repository is clean and tests pass before repair work.

Confirm `.local/oss/saie` is still the exact pinned upstream checkout before applying a local experiment patch.

---

## Phase 1 — confirm the already-identified defects with the smallest possible diagnostic

Use a brand-new disposable SketchUp document.

Do not run the entire architecture smoke first. Isolate one 6 m wall and one door opening.

### 1A. Boolean direction

Pinned upstream `opening.rb` currently calls:

```ruby
new_wall = cutter.subtract(wall_group)
```

SketchUp Ruby semantics are receiver minus argument. The intended door cut is wall minus cutter.

In the ignored local SAIE checkout only, test the minimal change:

```ruby
new_wall = wall_group.subtract(cutter)
```

Apply the equivalent change to `batch_cut` only if/when the single-opening test proves it is correct.

Evidence required before accepting the change:

- before/after viewport capture;
- visible real void through the wall;
- resulting object remains normal editable SketchUp geometry;
- no private/source model touched.

If reversing the boolean does not produce a correct opening, revert that local experiment and record exact geometry/readback evidence. Do not invent a new opening engine.

### 1B. Metadata serialization

The live smoke read back:

- `wall_spec: null`
- `openings_spec: [null]`

Pinned SAIE stores raw Hash / Array<Hash> objects with `set_attribute`.

Implement the smallest local upstream compatibility patch that serializes wall/opening specs to JSON strings before writing SketchUp attributes and parses them when reading.

Update only the affected upstream paths needed by:

- wall create/rebuild;
- opening record/find/modify/delete;
- query entity/deep_scan/export/verify.

Requirements:

- preserve backward tolerance for missing or malformed legacy values;
- `query.verify` must skip malformed entries instead of raising `nil["ai_id"]`;
- after a fresh create+cut, `inspect_entity(W_SOUTH)` must return a non-null reconstructable wall spec and real opening metadata;
- do not create a separate home-grown project-state engine.

### 1C. Verify implementation

After metadata repair, `verify_model` must return a structured result instead of throwing:

`undefined method '[]' for nil:NilClass`

Also compare actual code to upstream changelog's claim about recovering IDs after booleans. If top-level traversal remains sufficient for our fresh repaired objects, do not over-engineer recursion in this milestone. If the boolean result nests/reparents IDs, make the smallest upstream-compatible traversal fix and prove it with the disposable model.

---

## Phase 2 — rerun the deterministic SAIE smoke completely

After the focused single-wall diagnostic passes, restart from a new disposable blank model and rerun:

```powershell
.\.venv\Scripts\python.exe scripts\saie_2024_smoke.py
```

If the existing smoke stops on the first error before collecting later evidence, improve **our smoke harness only** so it records all required failure evidence while still returning FAIL when a required gate fails. Do not hide upstream failures.

Full acceptance requires all of these on the same disposable model:

1. four walls created with stable IDs;
2. visible door opening actually cut into `W_SOUTH`;
3. slab created;
4. 25-degree gable roof created;
5. `verify_model` completes and finds expected IDs;
6. `inspect_entity(W_SOUTH)` shows usable wall/opening metadata;
7. screenshot/view readback works;
8. `modify_wall` succeeds on `W_EAST`;
9. delete + recreate/repair of `W_NORTH` succeeds;
10. final verify succeeds;
11. resulting geometry remains editable SketchUp entities.

Save ignored evidence under `runtime/saie-compat/`.

---

## Phase 3 — make the successful compatibility patch reproducible

Only if the local upstream patch makes the full smoke pass:

Do **not** vendor the whole SAIE repository.

Instead add a very small repo-owned compatibility mechanism, for example:

- a unified patch file under `patches/saie/`, plus
- a deterministic apply script under `scripts/`,

that targets exactly upstream revision:

`eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f`

Requirements:

- fail closed if the upstream revision/file context does not match;
- document every patched upstream file and why;
- retain MIT attribution in `THIRD_PARTY_NOTICES.md`;
- keep upstream checkout ignored under `.local/oss/saie`;
- do not fork/copy unrelated SAIE source.

Update `scripts/prepare_saie_2024.ps1` only if needed so a future clean machine can reproduce:

prepare pinned upstream -> apply our tiny compatibility patch -> install plugin/package -> smoke.

Also pin/record the locally working MCP SDK range/version (`mcp 1.30.0` was the successful runtime in the previous smoke) rather than allowing an incompatible major version to silently break FastMCP startup.

---

## Phase 4 — website integration regression

With repaired SAIE running:

- prove the product still exposes 15 Kongxing tools plus the live namespaced SAIE tools;
- prove no raw SAIE `execute_ruby` or whole-document lifecycle escape is exposed through the website backend;
- keep Kongxing as the current model identity/lifecycle boundary;
- do not call an architecture model.

Run repository tests and add focused regression tests for any repo-owned compatibility/apply logic added in Phase 3.

---

## Phase 5 — standalone workspace-write remains a separate acceptance item

This is not the cause of the SAIE opening failure.

If the user has not yet run the standalone probe from ordinary Windows PowerShell outside Codex, leave it clearly pending. Do not waste this Codex session trying to defeat the outer host policy.

Command for the user later:

```powershell
.\.venv\Scripts\python.exe scripts\workspace_write_probe.py
```

Expected result path:

`runtime/projects/workspace-write-probe/runtime/workspace-write-result.json`

---

## Final verification

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md` with:

- exact pinned SAIE revision/version;
- exact local compatibility patch files/lines or reason patch was rejected;
- single-wall visible-opening diagnostic result;
- metadata readback result;
- full deterministic smoke PASS/FAIL by gate;
- final live tool count;
- website namespaced-tool result;
- exact ignored evidence directory;
- test count;
- standalone workspace-write status;
- remaining blockers.

Commit only repo-owned changes (patch/apply script/tests/docs, not the ignored upstream checkout), push `origin/main`, verify remote SHA, then **stop**.

## Acceptance decision

The milestone is ready to move forward only when either:

### PASS

SAIE on SketchUp 2024 completes the full deterministic wall/opening/slab/roof/query/view/edit/repair cycle with a reproducible minimal compatibility patch.

### REJECT SAIE 2024

A focused minimal patch cannot make the real opening/metadata path reliable without effectively maintaining a large SAIE fork. In that case record the exact blocker and stop; ChatGPT will choose the next OSS backend/strategy.

Do not run an architecture-quality model benchmark in either outcome.
