# Product & Architecture Decisions

## 2026-10-02 — user-approved product repair/research, no new inference spend

The user requested novice input coverage (single image, multiple views, text), connection/progress/revision reliability, OSS/commercial research and a low-cost launch proposal. They then explicitly chose **no spending: product fixes and research first**. This extends the old single-image task for free contract/UX checks and research, not for new paid/native model runs or acceptance claims. Taskbook/site design quality remains a later unaccepted capability; do not introduce payments, cloud infrastructure, other modeling software or a new geometry/provider engine.

Keep a single writing Agent with persistent Ruby and existing bridge/helper capabilities. Investigate a separate Visual Critic only with a measured comparison; it is not mandatory. Preserve approval/disposable identity/owned root/checkpoint guards, relax accidental frontend re-planning and image-required wording for text descriptions. SDK compatibility must be proven before marketing a model preset: GPT-6.1 Sol API tools require Responses; current Chat Completions adapter rejects that route before sending a request. Native Codex remains a development path.

See [product review](PRODUCT_RELIABILITY_AND_LAUNCH_REVIEW_2026-10-02.md). Propose Windows local delivery and invited beta first. Three-input free fixture tests do not establish building quality; GLM historical quality remains FAIL/partial and fresh-machine installation remains pending.

## D-001 — Product form

**Status:** Accepted

Use a hybrid architecture:

**Web Workspace + Local Professional-Software Connector**

The web layer will eventually manage project context, chat, files, results, and history. Local connectors/plugins will control professional design software.

## D-002 — First professional software

**Status:** Accepted

Start with **SketchUp**.

Reason: it matches the first benchmark workflow and is widely used by architecture students and junior designers.

## D-003 — First technical milestone

**Status:** Accepted

Do not build the full web product first.

Validate:

Project Context  
→ Agent  
→ SketchUp  
→ Model  
→ Inspect  
→ Modify

## D-004 — Development model routing

**Status:** Historical / superseded in part by D-012

Earlier prototype routing used ChatGPT for planning/review and Codex for implementation. This division of development responsibilities remains useful, but product-level architecture intelligence is now explicitly assigned to a native Astra-class agent path rather than an in-house fixed geometry planner.

## D-005 — Public repository safety

**Status:** Accepted

Do not commit private graduation-design files, copyrighted reference packages that cannot be redistributed, API keys, secrets, proprietary company materials, or private machine paths.

## D-006 — Human-in-the-loop

**Status:** Accepted

Major design-direction changes require user approval. Ordinary recoverable engineering actions should be handled autonomously.

## D-007 — Reuse-first engineering policy

**Status:** Accepted and strengthened by D-013

Before implementing any major subsystem, search for compatible open-source implementations and evaluate license, maturity, safety, and integration cost.

Decision order:

**Adopt → Fork → Compose/Wrap → Minimal Custom Build**

Custom infrastructure is justified only when existing projects cannot meet the requirement or create unacceptable product/technical risk.

Current high-priority reuse candidates:
- ArchFlow Studio — project-state/CAD/output candidate
- SAIE — richer SketchUp execution candidate
- SketchUp Architect Skill — architecture reasoning/precedent workflow candidate
- VBO SkAgent — lightweight live-control fallback
- LiteLLM — provider/model compatibility candidate for multi-model routing

The product's intended differentiation is above the connector layer: architecture workflow UX, context continuity, packaging, ease of use, and delivery for students/junior designers.

## D-008 — Demo v0.1 architecture

**Status:** Accepted as prototype foundation

Build a local end-to-end product demo rather than another research-only spike.

Architecture:

**Web Workspace → BrainAdapter → Local Connector/MCP → SketchUp**

SketchUp remains the real editable modeler. The web app is the product interface, not a replacement CAD engine.

## D-009 — Codex as temporary demo brain

**Status:** Historical prototype decision

For Demo v0.1, Codex performed architectural reasoning and tool orchestration behind a BrainAdapter/job boundary.

This proved the web-to-model chain but is no longer the intended final modeling architecture when it is constrained by the old fixed geometry schema.

## D-010 — Existing MCP first

**Status:** Accepted

The user's already-working Codex → MCP → SketchUp connection is the first integration candidate.

Do not replace it unless it lacks required capabilities.

Fallback order:
1. existing local MCP
2. SAIE
3. VBO SkAgent
4. other compatible OSS
5. minimal custom bridge only as last resort

## D-011 — Demo vertical slice

**Status:** Historical / superseded for normal product modeling

Demo v0.1 used:

DesignIR → editable SketchUp model → sequential edits → basic DXF → viewport/render artifact → simple A3 presentation.

This remains useful as a regression/legacy demo, but the fixed rectangular BuildPlan is no longer the primary modeling path.

## D-012 — Astra-native architecture intelligence

**Status:** Accepted as quality reference, generalized by D-018

Do not build a weaker in-house architecture brain around a tiny action vocabulary.

The normal product path should preserve the broad reasoning and tool-use ability proven by an Astra-class/native agent.

Target:

**Web Workspace → Native Agent Runtime → existing MCP / reusable OSS tools → SketchUp/CAD → screenshot/model readback → agent continuation**

The thesis modeling workflow remains the quality reference.

## D-013 — Assembly-first startup strategy

**Status:** Accepted

Optimize for speed to usable/sellable product.

Before custom implementation, prefer:

**Adopt → Fork → Wrap/Compose → Minimal Glue**

Do not rebuild a working connector, CAD exporter, architecture skill, agent runtime, provider compatibility layer, or software-control layer merely for architectural cleanliness.

Reuse source only with a clear compatible license and preserve attribution/NOTICE requirements.

## D-014 — DesignIR becomes project memory

**Status:** Accepted

DesignIR may store structured project context such as:

- brief/program
- site constraints
- reference principles
- user-confirmed decisions
- area targets
- important identities
- current design summary

It must not be the mandatory geometry generator or restrict all geometry to axis-aligned rectangles.

Complex geometry may be created directly by the native agent through existing SketchUp tools or safe project scripts.

## D-015 — Product value is packaging and workflow

**Status:** Accepted

The product's value is not inventing a new foundation model or modeling kernel.

The value is packaging strong existing intelligence and professional-software control into a simple architecture-student/junior-designer workflow:

- upload project materials
- discuss design in Chinese
- start/continue an agent session
- generate and edit real SketchUp/CAD outputs
- retain context/history/versions
- hide MCP, scripts, prompts, and setup complexity

Future monetization should build on convenience, workflow integration, packaging, and distribution rather than proprietary low-level geometry infrastructure.

## D-016 — Low reasoning is the default quality baseline

**Status:** Accepted

Do not treat higher reasoning effort as the default solution to architecture-modeling quality.

The premium/reference path should default to the currently configured Astra-class model at **low** reasoning effort unless a specific experiment proves otherwise.

Quality work should first improve:

- architecture workflow context,
- professional tool access,
- task-specific scripting,
- model inspection,
- iteration continuity.

Higher reasoning settings remain optional diagnostics, not the product's normal quality strategy.

## D-017 — Thin architecture skill + task-specific Ruby

**Status:** Accepted

The proven quality stack is:

**strong model at low reasoning + thin architecture skill + existing MCP + safe task-specific Ruby/project scripts + visual/model QA**.

Reuse `Mentat-Uran/sketchup-architect-skill` (MIT) directly or selectively rather than rewriting its architectural workflow from scratch.

Use the existing Kongxing connector first for project-local Ruby/script execution. If it cannot safely provide a required capability, prefer compatible existing OSS such as SAIE or VBO before custom infrastructure.

Do not compensate by adding dozens of bespoke fixed geometry actions.

## D-018 — Architecture capability must be model-independent

**Status:** Accepted

The architecture workflow must not depend on one premium model.

Keep architecture capability in reusable layers:

**project context + thin skill + MCP/Ruby tools + screenshot/model QA + session continuity**

and place model providers behind a small runtime/provider boundary.

The same workflow should be benchmarkable with GPT-6 Luna, Astra, Qwen/GLM-class models, or future compatible providers without duplicating the architecture stack.

## D-019 — Economy + Premium product tiers

**Status:** Accepted

The product should support two practical model modes:

- **Economy / Standard:** low-cost multimodal/tool-capable model handles most ordinary turns.
- **Premium / Refine:** Astra-class model is used for explicitly requested refinement or as a limited rescue path when objective QA/tool execution shows the economy model is stuck.

Do not silently route all work to Premium.

Start with a deterministic router:

- Economy by default
- Premium on explicit user choice
- one Premium rescue turn after repeated Economy QA/tool-loop failure
- return to Economy for routine follow-up when possible

A learned/AI model router is unnecessary at this stage.

## D-020 — Cost and quality are benchmarked together

**Status:** Accepted

A candidate model is not accepted because it is cheap or because it can call tools.

For the same sanitized architecture task, same Skill, same SketchUp tools, and same QA loop, record:

- architecture quality
- tool success/retries
- same-model revision reliability
- screenshot/model audit defects
- input/output token usage
- estimated model cost
- wall-clock latency

The startup target is at least one commercially viable operating point:

1. a low-cost model that produces useful architecture through the shared Skill/tool stack, or
2. a premium model that produces sufficiently high quality to justify a higher-priced user tier.

The preferred end state is both, with most turns handled by Economy and Premium used only where it materially improves results.

## D-021 — Precedent images are first-class architecture input

**Status:** Accepted

Do not treat a precedent URL's extracted text as equivalent to the original multimodal reference package.

For architecture tasks where the user supplies effect images, plans, diagrams, sections, or technical drawings, those images are first-class model input alongside the taskbook/site/user conversation.

The product should preserve a clear boundary:

**taskbook/site constraints + precedent text + precedent images/drawings + user intent → agent reasoning → SketchUp/CAD**

Generated model screenshots and final thesis outputs are not automatically recycled as precedent evidence. This prevents circular benchmarks and accidental self-conditioning.

The current local runtime should attach safe project-local images from `inputs/reference`, then `inputs/site`, then `inputs/brief`, while excluding generated `outputs/` images.

## D-022 — Historical workflow parity before further model conclusions

**Status:** Accepted

The user's successful direct graduation-design Codex workflow is the current product quality reference. Before concluding that a premium or economy model is intrinsically weaker, reproduce the successful workflow's information conditions as closely as practical:

- same taskbook/site evidence,
- same Jinshan precedent URL and key image/drawing set,
- same meaningful user-prompt sequence,
- same Architecture Skill/Ruby/MCP environment,
- separate disposable SketchUp copies,
- matched review views.

Astra-class Low vs Luna Max is a controlled benchmark configuration, not a permanent product-default decision. Product defaults remain independent from benchmark-only reasoning overrides.

If the website premium path remains materially worse than the historical direct result under equivalent inputs, migrate the missing capability/input/feedback loop before raising reasoning effort or rewriting the architecture engine.

## D-023 — Sol Medium standard tier after Luna Max latency failure

**Status:** Accepted for the local prototype; Sol architectural quality remains unproven.

The reference-rich Luna Max run completed only the site-base turn in 17 minutes, then failed a 30-minute road-refinement wait and was stopped after more than 55 minutes on a recovery attempt without a completed second turn. It never reached the first building prompt. This is a standard-tier usability failure, not evidence about the quality of a completed Luna building.

Per the user's follow-up, set **Economy / Standard** to `gpt-6-sol` at **medium** effort and keep **Premium / Refine** at `gpt-6-astra` at **low** effort. Sol was tested on the same private taskbook, eight reference/site images, historical prompt order, Architecture Skill, Ruby and Kongxing SketchUp tools from a separate blank model. It completed two site turns; the user ended the run before the first building turn returned, so this is a provisional route choice rather than a building-quality pass. Astra is an existing reference only; no further Astra modeling calls are needed in this comparison.

This supersedes the automatic Premium rescue in D-019: repeated Economy failures may recommend Premium, but only an explicit user selection routes a turn to Astra. The model/provider boundary remains replaceable and the benchmark-only Luna Max override remains available for diagnosis.


## 2026-10-01 — user-directed novice workflow and local delivery recommendation

The latest user request explicitly extends this local turn beyond the old image-only milestone: natural conversation, pasted images, uploaded task/site evidence, connection teaching, real progress, SKP download and replaceable API settings. It authorizes preserving explicitly supplied evidence, not inventing taskbook/site content or a new CAD engine. Auto in clarifying now stays conversational; explicit plan requests precede approval and execution.

Recommend Windows local workbench first, keeping the existing web workspace and runtime boundary. Added a BSD pywebview shell and locally built PyInstaller executable. This is a local prototype delivery, not an accepted commercial rollout. No accounts, payment, cloud deployment or new professional-software engine added. A distributable licensed bridge/plugin package, independent API inference/quality validation and clean-machine first-run acceptance remain release gates.
