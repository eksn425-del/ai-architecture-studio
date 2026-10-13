# External independent review brief — K Studio / Claude Code

Date of commission: 2026-10-13. **Review-only, no production action.** This brief exists to invite an *independent* judgment, not to ask another model to affirm or repeat previous GPT/Codex decisions. No personal memory or user/private building references are needed for this PUBLIC-repository task. All current development decisions remain governed by the latest owner handoff, not by this historical review brief.

## Assignment

Act jointly as (1) architectural software product lead, (2) senior AI Agent/Harness engineer, (3) SketchUp/native 3D systems architect, and (4) skeptical external reviewer. The owner sees prolonged iteration, competitor research and upstream Codex study, yet source-faithful native building quality remains unacceptable. Ask **whether the current product thesis and implementation approach can genuinely achieve the intended result**, not just which new Prompt or GitHub dependency to add. You may recommend keeping, narrowing, restructuring, pausing or pivoting the product with explicit evidence and disconfirming tests.

**Critical opening step:** query current `main` HEAD and read root `AGENTS.md`, `docs/CURRENT_TASK.md` and `docs/HANDOFF.md` TOPS, then the newest authoritative linked next-task file. Record their SHA and time. If future instructions supersede any example or reference in this brief, use the newer instructions. Read enough actual code and real failures to independently substantiate each technical judgment; do not judge on README assertions alone.

## First reading order (follow relevant links; don't read thousands of files indiscriminately)

1. Current authority: `AGENTS.md` → `docs/CURRENT_TASK.md` → `docs/HANDOFF.md` → latest linked single task (at commissioning: `docs/NEXT_P0_DELIVERY_AND_CONDITIONAL_CODEX_PARITY_2026-10-13.md`).
2. Product: `docs/PRODUCT_VISION.md`, `docs/PRODUCT_REVIEW_AND_AGENT_ITERATION_2026-10-12.md`, `docs/PRODUCT_DIRECTION_REFERENCE_TO_NATIVE_SKETCHUP_2026-10-09.md`, `docs/K_STUDIO_MANAGED_AGENT_BUSINESS_AND_OSS_2026-10-11.md`. Be aware README has older historical/conflicting "next task" sections; top CURRENT_TASK/HANDOFF take precedence.
3. Recent real native cases (especially the failure, not only green CI): `docs/test-results/windows/2026-10-13-native-harness-new-building/README.md` and its `browser/`, `first-pass/review/`, `model/native-reopen.json`, `errors.json`, `metrics.json`; `docs/test-results/windows/2026-10-13-owner-review-reuse/README.md`; `docs/test-results/windows/2026-10-12-owner-medium-continuation/README.md`; `docs/test-results/windows/2026-10-12-fresh-screen-sol-low/README.md`. Sources may be private and absent: say SOURCE_UNAVAILABLE instead of reconstructing them from public screenshot claims.
4. Agent architecture/code: `app/native_agent.py`, `app/agent_tools.py`, `app/workflow_context.py`, `app/main.py`, `app/project_ruby.py`, `app/codex_parity.py`, `app/modeling_quality.py`, `app/native_delivery.py`, `app/harness_parity_policy.py`, `app/static/studio.js`; inspect related Skills/tool contracts and tests by following actual imports/call sites. Check exact repo tree first: do not hallucinate filenames.
5. Known upstream studies: `docs/CODEX_HARNESS_PARITY_AUDIT_2026-10-13.md` and `docs/CODEX_NATIVE_HARNESS_PILOT_2026-10-13.md`; compare with the **official publicly licensed** current `openai/codex` and documented App Server protocol if needed. State pinned source SHA/license and what is already reused. Upstream agent source does not grant commercial model inference, nor guarantee parity by changing thread mode.
6. Native integrity: `scripts/audit_native_delivery_stages.py`, `scripts/compare_native_replay.py` if present, source construction script in the documented evidence, and the saved/download/reopen path. Trace host writer → native document/definition+instance transforms → saved bound SKP → download bytes → clean native reopen. Differentiate bytes SHA from deep semantic geometry.
7. Where evidence is inadequate, list the exact missing tests or host-only observations, not an invented result. Current private original photos and SKP should stay on authorized local Windows host; no demand to publish them.

## Examine these six hypotheses, including evidence *against* each

| Hypothesis | Concrete question and falsifiable observation |
| --- | --- |
| H1 multimodal / source representation | Were original images provided in order and truly seen? Are front/top/section/physical-model views reconciled into one coordinate system, proportions, handedness and geometry constraints before writing? |
| H2 model/Agent/Harness | How do stage instructions, thread start/resume/compaction, tool feedback, reviewer continuity, context duplication and actual model/effort influence the first usable geometry? Is an extra host wrapper creating a regression despite already using official Codex App Server? |
| H3 geometry capability | Can the available Ruby/ProjectRuby/ADAI/SAIE operations actually express curved roofs, circulation, facade semantics, reusable definitions and nested transforms reproducibly? Separate planner error from wrong constructor from writer/save error. |
| H4 host/output integrity (P0) | At which *verified* transition does identical revision cease to have identical deep world-space geometry? Is this independent of source interpretation? Never fix by guessing a global transform or re-building a different building. |
| H5 product UX and recovery | Does one natural Chinese approval launch real work? Can one correction target a named region while preserving legitimate KEEP and revealing BLOCKED status? Are native preview/download/edit/reopen/replay candid? |
| H6 product strategy / economics | Why would architects/students choose this service over native Codex+SketchUp or available alternatives? What is the smallest paid/valuable workflow, likely willingness to pay, operator inference/tool cost and realistic go/no-go criteria? Distinguish unverified assumptions from customer evidence. |

## Ground truth at commissioning (historical, refresh against current main)

- Recent eight-whole-private-image case: real site `gpt-6.1-sol / medium` and SU2024, single r1; first-pass source fidelity FAIL, three attempts at roof scoped correction produced **no edit commit**, clean downloaded SKP reopened with visibly wrong/missing roof; overall PARTIAL, native delivery FAIL. Baseline technical tests and read-only KEEP probe are not visual or end-to-end pass.
- `app/native_agent.py` already uses real upstream Codex App Server; "replace our fake harness with Codex" is an incorrect unverified diagnosis. `docs/CODEX_HARNESS_PARITY_AUDIT_2026-10-13.md` states a source-grounded comparison and limitations.
- Current owner P0 = diagnose native delivery in a disposable safe copy first, then actual same-site edit; only if delivery PASSES but fidelity/edit/UX still FAIL, and model is available, run a fair conditional original Codex control. A model capacity outage is BLOCKED, **not** an ability verdict. Do not bypass this dependency in your recommendation.

## Independent decision framework

- Split causal chain: source perception → multi-view spatial specification → plan/approval → code/geometry generation → guarded native mutation → independent source-matched QA → saved/downloaded/reopened/edited native asset → recovery. For each stage cite exact files and tests; label `OBSERVED`, `INFERRED` or `UNKNOWN`.
- Do not claim model-only failure without same-input/model/effort/tool/budget controlled evidence. Compare before/after under consistent original sources and geometry target. A different building is a descriptive case, NOT a causal A/B.
- Identify where current system is over-engineered and which complexity (screenshots, Critic, checks, thread resets, duplicated Skills) actually prevents or assists user success. Quantify from real logs where possible; report missing latency as null. Real acceptance measures: first-pass primary form, correctly joined source systems, one scoped edit and KEEP, semantic native groups, identical post-reopen deep fingerprints, first useful-result time, per-project usage/errors, and normal student UX.
- Propose at least **two competing product/architecture routes** plus a possible stop/pivot: e.g. repair the present agent; narrow to site/massing/structured-constraint editable workflows; or different assistance/review model. Evaluate technical risk, owner effort, defensible moat, deliverable user value and falsifying pilot for each. Do not insist on a specific route before diagnosis.
- Official public competitor product materials may inspire workflow questions; do not access private code, hidden endpoints, encrypted packages, account automation or prohibited reverse engineering. Any protected testing needs rights/terms review and explicit owner approval. Preserve OSS licenses and upstream attributions.

## Deliverable — write your analysis in Chinese to the user first

1. **One-page verdict:** current viability (continue / narrow / pivot / pause), confidence and top three evidence-backed reasons; note what cannot yet be known.
2. Source-of-truth table: HEAD, current authority, real runs, outcome dimension (`PASS/PARTIAL/FAIL/BLOCKED/NOT_RUN`), direct file references.
3. System chain/architecture and ranked root-cause tree (proof vs hypothesis and cheapest discriminator).
4. **Codex source audit:** what's already integrated, what's genuinely missing, what to remove or replace, license/effort and why another harness revision may not improve geometry.
5. Product definition and competitive wedge from the working user's perspective; recommend a narrow real user promise or recommend not pursuing it.
6. Three routes evaluated side-by-side with opportunity cost; identify one preferred route, one reversal criterion and 2-week / 6-week / 3-month milestones for a small team/solo owner.
7. A **single bounded next experiment**: exact same project and evidence needed, input comparability, acceptance thresholds, effort/cost caps and no-go/stop conditions. Respect active P0 dependency and no unapproved spend.
8. Risks/open decisions (at most five) for owner. Include a skeptical self-critique of your own recommendation.

**Mode:** review/read-only initially. Do not silently edit app/code, promote PASS, force-sync, publish private data, operate the local GUI, automatically continue a stopped test, purchase API calls, or merge changes. If asked for later implementation, propose a small isolated branch and await approval. Your findings are advisory, not a new owner override.
