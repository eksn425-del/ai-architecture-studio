# K Studio product and engineering reset — 2026-10-11

## Owner goal / actual customer

**Do not compete by shipping a generic chat wrapper**. Make K Studio a reliable localized **project-first AI Design Studio** for architecture, landscape, urban/environmental-design students and junior independent designers. Users can connect legitimate APIs without requiring their own Codex installation. Start with **one real editable native SketchUp deliverable**; let project brief, site, precedent research, approved intent, baseline, task board, correction history and output live in the SAME long-lived project. Future pipelines extend the SAME product; no separate first-party sites.

The demonstration of Building-Xuezhang's mass → facade → drawing → render → walkthrough → presentation is **direction**, not an assertion that K Studio presently delivers these modules. Architecture product's existing `docs/PRODUCT_VISION.md` already correctly says "project, not chat, is the core object". Current UI still calls projects "建模会话"; do not overwrite real work while restructuring UI.

### Verified current state and stopping the polishing loop

- 2026-10-11 Dream Coffee r4 official: 116 root groups; scope and KEEP pass; 110 old groups intact; independent Critic rejects oversize canopy/flat timber; source file private.
- Next native continuation: original downloadable SKP edited with mouse, saved and reopened (PASS). A **fresh blank replay** of persistent reconstruction source produces 116 groups but three strict recursive geometry/material hashes differ: `FRONT_SLOPED_GLAZING`, `FRONT_STORE_FRONT_GLAZING`, `UPPER_GLASS_PAVILION` (FAIL), despite same object counts.
- Multi-turn repair cost was 8,032,977 input / 152,170 output / 110 tools / 12 failures for one committed write plus multiple review/interruptions; these are actual historical run totals, not anticipated third-party API bills. A first-rate model cannot offset repeated full-context/repair loops or a non-idempotent baseline.
- Public proof: `docs/test-results/windows/2026-10-11-dream-coffee-protected-repair/`, `docs/test-results/windows/2026-10-11-dream-coffee-native-replay/`. The 2026-10-11 image QA is not PASS.

**Stop doing extra aesthetic retries on this case**. First produce exact reproducibility; create a one-page failure classification and use one controlled edit only when diagnostics point to a concrete fix. Compare hash AND child-level world coordinates, transforms, face front/back materials and deterministic ordering, not only group counts or raw PIDs. Fix queued SketchUp native open/timeouts and save-modal cancellation before anyone else's originals are exposed to that automation.

## Technical P0A: provider-independent native SketchUp artifact

**Current real blocker:** `app/litellm_runtime.py` explicitly rejects GPT-6.1 Sol/Astra for tool use: existing API builder is primarily Chat Completions, whereas the official models need Responses. UI model settings likewise rejects them; local Codex App Server success MUST NOT be presented as independent Sol/Astra API success. The current gateway-readiness endpoint `GET /api/provider-readiness` reports this truth; it deliberately does not enable a fake model route.

### Required next implementation (Codex with proper budget + user-supplied approved key)

1. Add an **independent Responses-based model runtime** (official SDK/compatible protocol) behind the EXISTING `ModelRouter` and shared `AgentToolSurface`; no new SketchUp bridge, no second writer, no direct "Codex login" shortcut.
2. Support actual text+image source input, system/Skill once, tool call IDs/arguments, tool result return, multiple real tool turns, continuation and compact checkpoint, structured planning, independent read-only Critic with source/current images, usage/cached/non-cached tokens, cancellation, timeouts and honest event/error log. Never assume OpenAI Chat Completions tool calling on these models.
3. Don't fake reasoning-state support or model identity through compatibility proxy; persist provider-returned `model`/request IDs and only pass opaque continuation fields in supported form. A status 200 or text answer is NOT an editable-modeling PASS.
4. Local API credentials via existing Windows DPAPI for BYOK; no keys in Git/logs/client source; explicit provider/base/model pinned per project. No automatic silent substitution Astra→Sol, Sol→Luna, official→gateway. Provider failures/unsupported capabilities must be surfaced honestly.
5. Run contract tests with fake SDK transport, then one owner-approved **real official API** builder test on rights-cleared public reference and installed SU2024. Do not spend money with guessed keys. Equal input, same K Studio Skills/tools/replay/KEEP, capture all genuine six views, native edit/reopen, fresh blank baseline replay, independent source-matched Critic and cost ledger. Compare Codex-native gpt-6.1-sol to standalone official gpt-6.1-sol at similar reasoning effort after confirming actual model ID. Evaluate end-user output quality; parity is a GOAL requiring real evidence, not a model guarantee.
6. Optional B.AI/OpenRouter after official baseline, **one gateway at a time**, with user-authorized small top-up and explicit request cap; verify `/responses`, model ID, provider transparency/route policies, mixed multimodal/tool-call cycles, caching/usage correctness, stop/cancel/retry semantics, privacy/retention and platform terms. A catalog listing does NOT establish product API parity.

**Release gate:** New user can choose an actually validated independent Sol API and finish upload → approve → blank SketchUp → saved native SKP → bounded same-model correction → real QA/download; no Codex process running. Quality must be evaluated visually relative to user source and independently; unsupported models visibly marked "未验证/即将支持", not advertised as working.

## Providers and go-to-market: direct API, optional gateway, not "buy any middleman"

| Option | Publicly verified documentation | K Studio decision |
| --- | --- | --- |
| OpenAI official | Sol `gpt-6.1-sol` and Astra `gpt-6-astra` Responses tools; short-context Sol $2/$10 per 1M input/output, Astra $10/$50. | **Primary independent parity baseline**. Access/prices according to actual account. |
| B.AI `https://api.b.ai/v1` | Docs advertise `/responses`, `gpt-6.1-sol`, `gpt-6-astra`, `claude-opus-5.5`; their Sol/Astra standard reference prices currently match official short-context prices. | Only an optional vetted gateway candidate. Not automatically cheaper/faster/equivalent. Small test and contract/terms/privacy check first. |
| OpenRouter | OpenAI-format APIs, model-specific providers, routing, BYOK, credit fees, privacy guards. Standard pay-as-you-go lists 5.5% platform credit fee; verify actual settlement. | Secondary optional candidate to evaluate against official using pinned model/provider, not an undisclosed quality rescue. |
| LiteLLM self-hosted | Open-source proxy supports shared provider integration, cost tracking/virtual keys/budgets (budget enforcement requires appropriate state/database). | **Our gateway layer, not itself an inference reseller**. Extend existing dependency instead of constructing another ad-hoc multi-provider proxy. |
| GLM/DeepSeek official | Current K Studio has independent LiteLLM Chat-completion experiments and real GLM geometry results of PARTIAL/FAIL fidelity. | Secondary budget/provider compatibility baseline, not a claim of equivalent results. |

Official public reference URLs: https://developers.openai.com/api/docs/models/gpt-6.1-sol ; https://developers.openai.com/api/docs/models/gpt-6-astra ; https://docs.b.ai/llmservice/api/ ; https://docs.b.ai/llmservice/pricing-and-usage/ ; https://openrouter.ai/pricing/ ; https://www.litellm.ai/pricing .

**Pilot billing:** Start with user-owned provider keys (BYOK) and/or tiny owner-funded controlled demonstrations; no mandatory gateway. The user pays upstream usage for BYOK; K Studio cannot promise zero cost. For a simpler managed-credit beta, use OUR own legally and securely configured server-side gateway/central billing, authentication, per-tenant quota, credit accounting, rate limits, consent, abuse detection, privacy policy and local software connector. Do not ship platform-wide secret in browser or desktop binary, share someone else's ChatGPT/Codex subscription, silently redirect requests, or assume undocumented resale rights. Official and platform commercial terms, source and upload rights, geography, and plugin redistribution must be reviewed prior to launch.

**Critical physical limit:** A remote web model/API does not itself control a user's locally installed SketchUp/Rhino/Blender/3ds Max. The first beta remains a local Windows app or website WITH a licensed user-approved local connector; a remote web-only SaaS will require separate pairing/auth/permissions and a maintained local agent.

## Product phases: do not build everything next week

**0.0 Engineering stabilisation:** stop replay drift and unfinished native model switch; align stage/critique/source state; reduce repeat massive contexts. Freeze a verified native SKP baseline. Do not endlessly improve Dream Coffee decor.

**0.1 Independent API modeling / internal beta:** Sol official Responses parity goal, optional Astra after measured quality/per-run spend/owner approval. Model/project readiness surfaced honestly; onboarding API key, project, reference images, optional site/brief, approval, native model, source-matched QA, edit/reopen and realistic progress/cost.

**1.0 Student design studio:** project ≠ chat. Main task book, design briefs/site, sourced precedent library, reference-to-design transformation, owner confirmations, safe seed white-mass input/copy, same-baseline variants, named editable model, version history. Target architecture then landscape, interior/environmental design, urban conceptual use cases with distinct quality rubrics; don't claim one generic workflow validates all.

**2.0 Professional adapters:** same shared `DesignIntent / SceneIR / NativeArtifact / QAReceipt` abstraction and each dedicated, legally distributed bridge. SketchUp first; later Rhino/Grasshopper, Blender and 3ds Max in tested slices. No generic unchecked `eval` to arbitrary local applications.

**3.0 Drawing and delivery:** CAD plan/elevation/section/dimension as properly scaled *concept/proposal-grade* editable DWG/DXF, then model-coherent perspective rendering, diagrams/presentation board/interactive web PPT and walkthrough. Geometry-linked updates and human approval. "自动生成施工图/规范达标" must never be promised without multi-discipline professional validation.

## Beta pilot gates

- Rights-cleared public fixed seed test; three different complexity classes (simple mass, multi-view building, safe targeted correction), each with actual official API and reported provider/model/effort/cost.
- Never mark replay PASS until all expected named groups/material/geometry match within explicitly declared tolerances in **two fresh blanks**. Screenshot comparison supplements geometry checks, not substitutes.
- >=8/10 attempts end in native openable editable SKP without developer fixing source; >=7/10 outcomes judged worth retaining by target design users. These are provisional gates, not achieved performance.
- Report failures, human rescue, time-to-deliver, true total spend including failed retries, copyright/asset privacy, install/connector friction.
- Make quality regressions and user time primary, not number of OSS helper calls or 100% green unit tests.

**Non-goals for next Codex cycle:** no CAD production, no whole-studio redesign, no new unrelated provider integrations, no rendering/PPT/video generation, no blanket SU 2018-2026 compatibility claims.
