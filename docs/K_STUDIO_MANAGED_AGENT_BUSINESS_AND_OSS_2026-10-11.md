# K Studio — Managed LLM professional Agent service, OSS adoption, 10→100→1000 users
Date: 2026-10-11. Owner decision; replaces the previous mistaken assumption that every public user MUST provide an API key.

## 0. Unambiguous product definition

**K Studio sells the K Studio Agent SERVICE**, not an API-key relay nor an imitation of a login-protected Codex subscription. The operator legitimately buys a supported LLM API from B.AI or another permitted upstream under terms that allow commercial application use, keeps the master key ONLY in secure server-side infrastructure, and bundles intelligence with professional project memory, staged Skill retrieval, SketchUp/other tools, verified native editable deliverables, real QA, retries, user support and a human-usable workspace. Nontechnical students never need Codex/MCP knowledge or self-supplied keys. Optional BYOK is for advanced testers ONLY. Never sell/display upstream keys, assume API redistribution/resale rights, or silently switch model/provider.

**Pilot selection:** B.AI is first gateway candidate (documented `https://api.b.ai/v1/responses` and `gpt-6.1-sol`/`gpt-6-astra`/Opus listings, not product-verified); official OpenAI independent Responses is a parity/reference/fallback candidate; OpenRouter another comparison, not a requirement. Choose on real end-to-end tool/image/continuation/source-match results, provider identity, actual bill, latency, rate limits, refund/failures, privacy and contractual permission. No real upstream spend, wallet connection, keys or account action without owner approval.

**Product promise (first beta):** "Open K Studio, create an architecture project, upload image/site/brief, approve a plan, allow the local professionally installed SketchUp connector, obtain named/editable native SKP with a verified source-aligned preview and safe revisions." Do NOT advertise current Sol/Astra support, other software, project multi-tenancy, complete CAD construction drawings, rendering/video or automatic PPT until demonstrated.

## 1. Business models worth copying: sell completed work, meter cost and support

| Public analog | Observable business mechanism | Adapt in K Studio |
| --- | --- | --- |
| Replit Agent https://replit.com/pricing | Agent workspace with included credit/allowance and model usage-based cost | Project-based plans, hard per-run cap, pay for completed *service*, not just upstream tokens |
| Lovable https://lovable.dev/pricing | Product action/complexity consumption, workspace/month/member credit budgets | Clear balance, confirmation before expensive model/correction, avoid surprising hidden charges |
| Tripo OpenAPI https://docs.tripo3d.ai/get-started/pricing.html | Different generation/segmentation/post-process tasks have separate credit costs and actual consumed_credit | Separate initial model, optional refinement, rendering and output tasks instead of one unbounded "free edit" |
| LiteLLM https://docs.litellm.ai/docs/proxy/users | Virtual keys/user-team-agent budgets + RPM/TPM/concurrency; budgets require persistent PostgreSQL | Use/test a proven proxy rather than writing an ad hoc inference gateway; a database-less global cap is NOT actually enforced |
| OpenRouter https://openrouter.ai/docs/guides/features/guardrails/overview | Provider/model allowlists, key/workspace spend and privacy guardrails | Actual provider/model pinning and per-workspace caps, not silent fallback; verify third-party routing |
| AgentCAD https://github.com/jdilla1277/agentcad | Agent writes build123d; host validates/export/metrics/diff with structured result | Keep native code as source, separate geometry execution/QA; do not claim equal group counts = equal geometry |
| Blender Agent https://github.com/hotspoons/blender-agent | Model-independent LLM endpoint, searchable skills_list/search/read, scene inspection, code/render and context compaction | Reuse patterns: only load relevant professional methods, controlled execution, persistent project/trace, local bridge |
| BlenderMCP https://github.com/ahujasid/mcp-for-blender | Local app bridge with scene readback and material/asset tools, redistribution/telemetry terms apply | Future Blender adapter must implement local permissions, group/material/PID readback and privacy defaults; DO NOT run a second active writer against the same model |

These are observable product/technical patterns, not claims that upstream vendors grant us source redistribution or that a mesh-generation product already creates editable architectural construction details.

## 2. Pricing and margin rule, not a premature public price promise

Upstream cost = uncached input + generated output (including billed reasoning) + cache read/write + provider fees + metered tool/search/image fees + failed/billed retries + taxes/currency. **K Studio COGS also includes** hosted inference gateway/DB/storage/egress, local connector support, customer acquisition/support, rendering and refunds/abuse. Actual per-model/prompt/context-tier price from current operator invoice, not a timeless literal in code. B.AI Sol docs list baseline $2/$10 per million at <=272K inputs, but >272K has higher *entire-request* pricing; output/reasoning can dominate cost. See https://docs.b.ai/llmservice/models/gpt-6-1-sol/ . Do not infer cheaper bills from promotions without actual settlement.

**Launch suggestion, NOT configured billing:** introductory project credits + 3 task bands (planning/chat, initial native model, bounded source-matched refinement); premium Astra requires prominent up-front approximate estimate and explicit confirmation. Charge for consumption with clear unit definitions; present partial failure and provider-billed costs honestly. Reserve expected max per job before sending a request; reconcile actual provider usage after; idempotency on retries, detect/resolve stale reservations; no unlimited included high-effort retries. Require expected gross margin after real failed-task rates (initial business target to measure, not a false achieved metric).

Current `app/managed_beta_policy.py` is a **pure, no-network readiness and operator cost PRE-FLIGHT**, with no real accounts, payments, atomic wallet, or shared keys. It must never be used to assert that a public paid-user release is ready.

## 3. Future runtime data flow (managed vs BYOK are commercial modes, NOT separate Agent engines)

```text
User K Studio workspace + account/project
    -> K Studio backend Auth / RBAC / tenant-scoped Project/Scene/Skill/asset DB
    -> authenticated budget+concurrency reservation (atomic, auditable)
    -> Model Gateway (managed B.AI/official/OpenRouter approved profile OR optional BYOK)
    -> SAME K Studio Agent Planner -> component method search/Skill -> guarded task/geometry writer
    -> signed approved local connector (SU2024 first), readback/QA/version/replay
    -> reconciled spend + outcome/quality/usable editable native result
```

One user/project must NOT access another's SKP/brief/connection, even by guessing ID; existing `app/main.py` has a global lock and loopback-only middleware and `app/store.py` is project-folder/JSON. This is **single-user local desktop prototype**, not a cloud SaaS. For 10 invited testers: separate local workstations and operator pilot credentials scoped to trusted environment, manual opt-in, no shared key in distributed app. For 100+: authenticated hosted app/gateway, PostgreSQL for users/projects/roles/run IDs/billing/reservations, durable object storage for encrypted uploads/exports, per-project signed local pairing with explicit grants, dedicated task queue/worker leases per SketchUp installation, Redis optional for ephemeral queue/rate limiting but NOT authoritative financial ledger. For 1000+: separated inference and geometry workers, per-tenant concurrency caps, retries/idempotency, monitoring/tracing, backup/restore/retention and disaster-recovery testing, cost anomaly alerts and capacity planning. Do not call this done until deployed load tests prove it.

## 4. Agent moat: editable components, assembly correctness, and real project state

Professional native deliverable contract (future formal `NativeArtifact` / `ComponentAssemblyQA`):
1. **Semantic named hierarchy:** site, storeys, wall/openings, slabs, columns/beams, roof sublayers, glazing/fenestration, stairs/railings, repetitive modules; every user-facing element has a stable semantic path/type and owner, sensible component reuse and editable native material. No enormous anonymous welded mesh as primary SketchUp deliverable.
2. **Real geometry, not image imitation:** dimensions and user-confirmed levels, correct openings, non-overlapping or explicitly intentional intersections, roof/wall junctions, aligned mullions/frame/glass, doors-to-wall clearance, load-path plausible concept support, site/grade logical, no floating/disconnected facade parts. Declare geometric tolerance in mm per joint/type; do not invent a blanket zero-gap rule (construction joints/shadow gaps may be intended).
3. **Hierarchical source evidence:** facts marked user-confirmed/observed/estimated; source camera/visibility, approved IR; use a human-accepted named assembly as baseline, not a new reconstruction for every revision.
4. **Workflow selection:** prioritize a verified specific upstream helper for its matching task; use guarded custom Ruby if unavailable/incompatible. Keep OSS provenance and host-issued invocation ledger, but quality depends on actual per-component fidelity, NOT call counts.
5. **Version/replay:** keep owner original immutable; all writes project-specific single writer; accepted candidate promotes persistent source ONLY AFTER visual acceptance, native re-open and two independent source replays with strict geometry/material canonical fingerprints.
6. **User corrections:** explicit allowlisted target/KEEP, before-vs-after matching angle and independent read-only Critic, rollback if already-approved regions degrade, honest PARTIAL if source cannot be matched.
7. **Skill library:** CORE always loaded (safe write, project intent, source evidence, model inspection, QA); optional categories search/load on demand (wall/opening/roof/glazing/stair/landscape/render/CAD per validated adapter). Never dump dozens of external repo docs into context. Candidate → licensed hash-verified adapter → real method route → executed current-run receipt → effect review → retain/replace/reject.

Near-term test: use the existing public villa fixture plus actual Dream Coffee FAIL evidence to compare one Sol/B.AI/official model with same K Studio tools. Minimum first product acceptance = correctly grouped and individually editable roof, wall, glazing, stairs and site, source camera conformity, native save/reopen and strict blank replay; don't aim to handcraft a perfect one-off café scene forever.

## 5. Priorities and explicit no-scope-creep

**Now P0: (i) existing strict 3 glazing replay issue #6 in bounded native diagnosis; (ii) independent Responses-based K Studio Agent through an operator-configurable validated provider, preferably B.AI as user's first candidate after legal/technical screening, official Sol used as neutral control, not mandatory user-facing BYOK; (iii) one fixed public architecture native SKP build/edit/QA comparative run.** Fix only measured Agent/Skill/MCP/geometry failures.

**P1: ten invited studio users**, project cards, uploads/brief, named element browser, clear model/usage/credits, consent/local pairing. Study pricing from actual quality+cost and support. No public signups/sharing keys before hosted auth+atomic quota+tenant isolation.

**P2: 100→1000 readiness**: Postgres, account/tenant security, background job queue and worker, gateway budgets, S3 compatible signed file storage, observability/support/backup and terms; verify load tests before rollout. Optional official/BYOK fallback.

**P3: same-project deliverables**: controlled safe cloned user seed SketchUp site/mass + redline, independent qualified Rhino/Blender/3dsMax adapter, proposal-grade CAD plans/elevations/sections, linked rendering/diagrams/board/web presentation/walkthrough. No construction compliance claim without independent professional verification and review.

## 6. External implementation rules

Copy *legally licensed and inspected useful source*, not a protected third-party commercial product. Record source URL, version/commit, actual LICENSE obligations, required attribution/notices, deps/telemetry/licensing constraints, exact user outcome to improve, real call receipts; never unconditionally start another software writer. For external Blender plugins, review and disable data telemetry in private-client workflows before trials. CPAL ADAI attribution and upstream license remain intact. Every accepted external component must change LIVE Agent execution behavior and pass task-specific native evidence. If it sits only in vendor/, README or a smoke folder, status is `installed/smoke_verified`, not product improvement.

This is one product + one codebase; next Codex full instructions: [NEXT_CODEX_MANAGED_AGENT_BETA_2026-10-11.md](NEXT_CODEX_MANAGED_AGENT_BETA_2026-10-11.md).
