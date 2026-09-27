# CURRENT TASK — Cost / Quality Router v1

## Status: Complete — Cost / Quality Router v1 delivered; no local Qwen credential was available for a live run.

## Objective

Keep the successful **Architecture Skill + project Ruby + SketchUp QA** environment, but make the model replaceable so product economics do not depend on Astra for every turn.

Target product:

**same project context + same architecture skill + same Kongxing/OSS tool layer + same QA → cheap model by default → premium Astra only when useful**

Read `docs/MODEL_ROUTER_V1.md` before implementation.

## Before starting

1. `git pull --ff-only`
2. Confirm clean worktree.
3. Read:
   - `AGENTS.md`
   - `docs/MODEL_ROUTER_V1.md`
   - `docs/HANDOFF.md`
   - `docs/DECISIONS.md`
   - `docs/OPEN_SOURCE_COMPONENT_MAP.md`
4. Run current tests once.

## Priority 1 — separate model provider from architecture capability

Do not fork the current Skill/Ruby/MCP logic per provider.

Introduce the smallest reusable model runtime/provider boundary so the same agent loop can use different backends.

Keep:

- architecture skill context
- project memory
- Kongxing MCP
- guarded project Ruby
- screenshots/readback
- same-model session/revision
- Chinese UI

Provider-specific code should handle only model API/session/tool-call differences.

## Priority 2 — reuse provider plumbing

Do a short implementation-focused check of `BerriAI/litellm`.

Its non-enterprise code is MIT-licensed and already supports multiple providers including OpenAI, DashScope/Qwen and Z.AI/Zhipu-style backends.

Preferred order:

1. use LiteLLM as a dependency/wrapper if it cleanly preserves multimodal + tool calling,
2. otherwise use the providers' OpenAI-compatible APIs behind one very small adapter,
3. do not build a large custom provider framework.

Do not copy `enterprise/` code.

## Priority 3 — Economy model: GPT-6 Luna first

Add a real Economy path using `gpt-6-luna` with the same architecture Skill + tools + Ruby + QA as Astra.

Do not weaken Luna by giving it a smaller tool set or worse context.

Use the lowest reasoning setting that still supports the required agent/tool loop for the chosen API/runtime.

Track:

- model id
- reasoning setting
- input/output tokens if available
- tool calls
- retries
- latency
- screenshot/model QA

## Priority 4 — one Chinese low-cost candidate

Add **one**, not many, Chinese candidate.

Preferred first choices:

- Qwen3-VL Flash/Plus family where the selected region/provider supports multimodal input and function calling, or
- GLM family where the selected provider supports reliable tool calling and image input.

Use environment/local secrets only. Never commit keys.

If no usable provider credential exists locally, complete the provider adapter/config path and record the missing live credential as the only blocker; do not fake benchmark results.

## Priority 5 — controlled quality/cost benchmark

Use the same sanitized architecture benchmark and the same SketchUp tool environment.

Compare at least:

- **Premium reference:** Astra Low + Skill + Ruby
- **Economy OpenAI:** Luna + same Skill + Ruby
- **Economy China:** one Qwen/GLM candidate + same Skill + Ruby, if a real credential is available

Use matched viewpoints and objective QA.

Compare:

1. program/adjacency coherence
2. plan/section/vertical relation
3. site/entrance/public-space logic
4. facade openings/envelope detail
5. tool/Ruby success
6. screenshot self-check/correction
7. same-model follow-up reliability
8. semantic IDs / audit defects
9. token cost
10. wall-clock latency

Do not judge only by entity count.

## Priority 6 — simple routing, not a new AI router

Implement a deterministic v1 policy only after the benchmark plumbing works:

- default → Economy
- user selects “精修” → Premium for that turn
- Economy QA fails twice / tool loop stalls → allow one Premium rescue turn
- return to Economy for routine follow-ups when possible

Do not silently use Astra every turn.

Expose current mode/model in local status and session state.

## Priority 7 — continue capability migration only when it directly improves quality

Do not stop reusing external work.

If the benchmark exposes a tool gap, prefer adopting the smallest useful capability from existing OSS:

- SAIE: openings, slabs/roofs, snapshots, BIM metadata, reports, DXF parse, batch operations
- ArchFlow Studio: state/CAD/output patterns
- VBO SkAgent: fallback Ruby/control path

Do not integrate everything proactively. Only move capability that fixes an observed benchmark gap.

## Cost target

Record real usage rather than guessing.

We want two sellable tiers:

- **Economy / Standard:** cheap enough for repeated student iterations.
- **Premium / Refine:** higher-cost Astra path for difficult concept/refinement turns.

The long-term goal is that most turns run on the cheap model while expensive-model usage is a minority of turns.

## Acceptance criteria

Mark PASS / PARTIAL / FAIL in `docs/HANDOFF.md`.

1. Architecture Skill/Ruby/MCP/QA are model-independent rather than Astra-specific.
2. A reusable provider/runtime boundary exists without duplicating the architecture loop.
3. Existing Astra Low path still works.
4. GPT-6 Luna runs the same benchmark with the same Skill + Ruby + SketchUp tools.
5. One Chinese provider path exists; if credentials are available, it is live-benchmarked honestly.
6. Model/mode/token/latency/tool-call metadata are persisted for benchmark runs where available.
7. Matched screenshots and QA compare quality, not just completion.
8. Economy vs Premium routing is deterministic and visible.
9. Premium is not silently used for every turn.
10. No new MCP server, CAD engine, or geometry ontology is built.
11. Any reused code/dependency has compatible licensing and attribution.
12. Existing Chinese workspace, disposable-model gate, session continuity and project safety remain working.
13. Tests pass; real SketchUp benchmark evidence is recorded.
14. Work is committed and pushed to `origin/main`.

## What NOT to do

- Do not improve Luna by secretly raising Astra usage.
- Do not compare different tool sets or different briefs and call it a model comparison.
- Do not add five providers at once.
- Do not build a learned model router.
- Do not rebuild LiteLLM/provider SDK functionality unless integration truly requires it.
- Do not add auth/payments/cloud deployment in this milestone.
- Do not commit API keys or private thesis assets.

## Final step

Run tests and real local benchmarks, update `docs/HANDOFF.md`, commit, push to `origin/main`, verify the remote SHA, then stop.
