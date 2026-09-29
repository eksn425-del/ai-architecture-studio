# SAIE 2024 smoke review — 2026-09-29

## What the latest local run actually proved

Remote commit `192f80e147c04b331c9ebaaea4c8d8bf74a825de` is a meaningful partial success, not a failed integration.

Verified locally on SketchUp `2024.0.484`:

- upstream SAIE 1.0.0 plugin loads far enough to own its bridge port and answer `saie ping`;
- `saie ping` returned `PONG plugin_v1.0.0`;
- the live FastMCP server exposed 59 tools;
- AI Architecture Studio composed 15 Kongxing tools + 59 `saie__...` tools;
- deterministic calls created wall geometry, slab geometry and a gable roof in a disposable SketchUp model;
- screenshots/readback and a saved disposable checkpoint were produced;
- no architecture LLM was used.

Therefore **SketchUp 2024 itself is no longer the main SAIE blocker**. The remaining failure is localized to SAIE's opening/metadata/verification path.

## Concrete upstream defects found during ChatGPT review

The next local iteration should not rediscover these from scratch.

### 1. Opening boolean direction is very likely reversed

At pinned upstream revision:

`eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f`

`ruby_plugin/su_mcp_bridge/ops/opening.rb` performs:

```ruby
new_wall = cutter.subtract(wall_group)
```

for both single and batch opening cuts.

SketchUp's official Ruby API defines `receiver.subtract(argument)` as the boolean difference `receiver - argument`.

For a door/window cut, the intended result is **wall - cutter**, so the operation should be experimentally checked as:

```ruby
new_wall = wall_group.subtract(cutter)
```

This matches the observed symptom: `cut_opening` returned success, but the south elevation showed no visible door opening and the post-cut wall lost normal wall semantics.

Do not blindly accept this patch only from static review. Apply it first only in the ignored local SAIE checkout, rerun the single-wall opening diagnostic, and accept it only if the resulting SketchUp geometry visibly contains the void.

### 2. SAIE persists complex Ruby objects directly into SketchUp attributes

`wall.rb` currently stores:

```ruby
group.set_attribute("su_mcp_bridge", "wall_spec", params)
```

where `params` is a Ruby Hash.

`opening.rb` stores an `Array<Hash>` under `openings_spec`.

The local run then read back:

- `wall_spec: null`
- `openings_spec: [null]`

This is the exact state that later breaks modification and verification.

The minimal compatibility patch should serialize these specs to a stable string representation (prefer JSON) before `set_attribute`, and parse them when reading. Do not invent a new project-state system just to repair this upstream serialization bug.

### 3. `query.verify` crashes on the corrupted opening metadata

Pinned `query.rb` does:

```ruby
ops = ent.get_attribute("su_mcp_bridge", "openings_spec") || []
ops.each do |op|
  op_id = op["ai_id"]
  ...
end
```

The observed `openings_spec == [nil]` therefore produces the exact runtime failure:

`undefined method '[]' for nil:NilClass`

At minimum, repaired metadata parsing must return actual opening hashes. Verification should also tolerate malformed/legacy entries instead of crashing the entire model query.

### 4. Upstream changelog and current implementation are inconsistent

SAIE's changelog says `query.verify` was fixed to recursively recover AI IDs after boolean opening operations, but the pinned `query.rb` currently walks only `model.active_entities` and the actual smoke crashes on opening metadata.

Treat the running code and deterministic evidence as authoritative.

## Reuse policy for the fix

SAIE is MIT licensed. We are allowed to adapt it, but the product should remain upstream-first.

Preferred sequence:

1. patch only the ignored `.local/oss/saie` checkout to prove the minimal fix;
2. rerun deterministic no-LLM opening/verify/edit smoke;
3. if successful, store a tiny reproducible compatibility patch/apply script in this repository with upstream SHA + MIT attribution;
4. do **not** copy the whole SAIE source tree into AI Architecture Studio;
5. do **not** replace SAIE walls/openings/roof tools with a new home-grown geometry engine.

## Next acceptance gate

Before any new Astra/Luna/Sol architecture benchmark, SAIE must complete one disposable same-model cycle:

1. create four walls;
2. create a visible real door opening;
3. create slab + gable roof;
4. verify expected semantic IDs without exception;
5. inspect wall/opening metadata and confirm it is non-null;
6. modify one wall;
7. delete and repair one wall;
8. capture final canonical/viewport evidence;
9. keep geometry editable in SketchUp.

Only after that passes should SAIE be treated as a reliable modeling backend for the website.
