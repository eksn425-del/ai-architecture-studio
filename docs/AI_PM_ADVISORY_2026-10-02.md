# AI PM Advisory — 2026-10-02

> Status: **Advisory only. Not a mandatory implementation plan.**
>
> This note records a product/Agent architecture viewpoint for Codex and the project owner to discuss. It intentionally does **not** replace `CURRENT_TASK.md`, and it should not be interpreted as a hard constraint if real local experiments show a simpler or less constrained path works better.

## Context

The project owner wants a practical product similar in user experience to an AI modeling assistant: users provide reference images / project information in a simple website or desktop UI, the system connects to SketchUp through the local bridge/MCP, and AI creates and revises an editable SU model.

A repeated lesson from earlier milestones is that over-constraining geometry, prompts, workflows, or tool choice can reduce model capability and produce empty boxes or failed runs. Direct/local Codex experiments have sometimes produced better results faster than tightly specified remote plans. Therefore, this document should be treated as a **set of hypotheses and product principles to test**, not as a rigid architecture specification.

## 1. Current Agent architecture: single main Agent, deterministic host orchestration

The current system is best described as:

**single Builder Agent + host state machine + task Skill + coding/tool harness + SketchUp + readback/screenshots**

It is not currently a true multi-Agent system.

Typical path:

```text
User
  -> K Studio / desktop shell
  -> host workflow/state (clarify / plan / approve / execute)
  -> one primary model/Agent
  -> reconstruction Skill
  -> persistent Ruby / MCP / selected SAIE helpers
  -> SketchUp
  -> model readback + screenshots
  -> same Agent continues/revises
```

MCP, Ruby and SAIE are tools/execution layers, not independent Agents.

This architecture is reasonable for now because SketchUp is a stateful shared workspace. Multiple independent writing Agents could easily overwrite each other or reason from stale state.

## 2. Do not rush into many writing Agents

A possible future direction is **Single Writer, Multiple Checkers** rather than many Agents all editing SketchUp.

Possible roles:

- **Builder Agent** — the only role allowed to change SketchUp geometry.
- **Visual Critic** — read-only; compares reference images against SU screenshots and reports concrete mismatches.
- **Deterministic Validator** — non-AI checks for model/root/revision/file/view/output facts.
- **Architecture/Compliance Critic** — later, for taskbook/site/program projects; read-only checks of area, height, function, access, etc.

This is only a hypothesis. If Codex finds a simpler single-Agent method that produces better quality, prefer the working method.

## 3. Hallucination / random modeling should be handled by evidence, not only prompts

There are several different failure modes:

### A. Visual interpretation error

Example: wrong floor count or wrong facade rhythm.

Useful mitigation:
- extract a compact parameter card before building;
- distinguish **KNOWN / ESTIMATED / ASSUMED**;
- let the user correct high-impact assumptions before execution.

Do not turn this into excessive questioning. If the model can infer something safely and the user already supplied enough information, keep the flow fast.

### B. Unseen geometry invention

A single image cannot reveal rear facade, depth, internal circulation, roof backside, etc.

The product should distinguish:
- source-view reconstruction;
- full editable building with reasonable inference.

Inferred geometry should be treated as an assumption, not represented as recovered ground truth.

### C. Agent claims work was done when SketchUp did not change

The Agent's prose should not be treated as the source of truth.

Preferred evidence order:

```text
actual SketchUp model
> tool/model readback
> screenshots
> persistent state/parameter card
> Agent text
```

A successful tool call alone is also not sufficient proof of good architecture.

### D. Builder self-QA is too optimistic

The GLM run demonstrated that an Agent can believe quality is acceptable while independent inspection still finds glass/frame/material/detail defects.

A separate read-only visual critique pass may be valuable. But do not add it merely for architectural purity: test whether it actually improves output quality enough to justify latency and cost.

## 4. AI capability boundary

The product should be strong where AI is naturally useful, and explicit where information is unavailable.

### Suitable Agent work

- interpret reference images and user instructions;
- estimate proportions and dimensions when no exact data exists;
- generate/revise project-specific Ruby;
- create structured editable SketchUp geometry;
- build repeated facade/window/balcony/louver systems;
- inspect screenshots and make targeted revisions;
- infer unseen geometry when the user permits it;
- continue natural-language edits on the same model;
- later, combine taskbook/site/precedent evidence for concept design.

### Should not be promised as certain

- exact measurement from an image without an anchor;
- exact recovery of invisible rear/interior geometry;
- construction-ready structure/MEP/detailing from visual reference alone;
- guaranteed compliance with all codes without deterministic rule checks and human review;
- perfect self-verification by the same model that generated the work;
- exact reproduction when source information is contradictory or incomplete.

Suggested product language should emphasize **editable AI-assisted reconstruction and revision**, not “100% restore the real building from a photo.”

## 5. Product focus recommendation

The clearest initial commercial wedge is still:

> **reference image(s) -> editable SketchUp model -> conversational revision**

A simple customer journey:

```text
upload/paste 1-6 images
-> describe target
-> AI asks only important missing questions
-> compact parameter/assumption card
-> user approves
-> SketchUp builds automatically
-> AI inspects key views and corrects obvious mismatches
-> user says “make the second-floor windows narrower”
-> same model is revised
-> download / continue editing in SketchUp
```

This is already a sellable problem if quality/reliability become acceptable. Do not expand into CAD/render/PPT/payment just because those are possible before modeling quality is stable.

## 6. What the product really sells

The product is not selling the foundation model, MCP, Ruby or SAIE individually.

The value proposition is:

> **give architecture students / junior designers a usable AI SketchUp assistant without requiring them to understand Codex, MCP, Ruby, prompt engineering, state recovery or model/tool configuration.**

The durable product layer is roughly:

**Agent Harness x Task Skill x Professional Software Bridge x Product UX**

The model should remain replaceable.

## 7. Suggested next problem to investigate: Modeling Reliability

This is an advisory priority list, not a mandatory backlog.

Potential next work:

1. Test whether a read-only Visual Critic materially improves reconstruction quality.
2. Define a small set of evidence gates so the product does not accept “Agent says done” as completion.
3. Keep source-view-only and full/multi-view reconstruction behavior explicit.
4. Improve semantic/editable model organization enough for reliable later edits, without forcing geometry into a rigid schema.
5. Build a fixed set of real reference benchmarks and track whether users would actually keep/edit the resulting SKP.
6. Reduce repeated context and full-script regeneration where it causes huge token/latency costs.
7. Prefer incremental persistent Ruby revisions over unnecessary full rebuilds when that is demonstrably more reliable.
8. Compare additional low-cost models only after the harness/evaluation method is stable enough to make the comparison fair.

A useful product KPI is not “number of Agents” or “number of supported models”. A better KPI is:

> **For a fixed real benchmark set, what percentage of generated SKP models are good enough that a target user chooses to keep editing them?**

Secondary metrics: number of correction turns, failure recovery rate, time, provider/tool cost, and whether the same model remains editable across follow-up requests.

## 8. Architecture hypothesis for later discussion

One possible target architecture is:

```text
                 User
                  |
             Product Host
       state / approval / versions
                  |
             Builder Agent
          (only SU writer)
                  |
        Skill + coding harness
                  |
          Ruby / SAIE / MCP
                  |
              SketchUp
                  |
        readback + screenshots
           /             \
          v               v
 Visual Critic      Deterministic Validator
    read-only              read-only
          \               /
           -> correction / accept
```

Again: this is **not** a requirement. Codex should compare it with the current working implementation and with direct-Codex behavior. If adding roles creates more coordination overhead than quality gain, keep the simpler architecture.

## 9. Decision principle for the next discussion

When choosing between a neat architecture and a working architecture:

> **prefer the smallest change that measurably improves real SketchUp output.**

Do not reduce model/tool freedom merely to make the system easier to describe. Preserve successful direct-Codex-like behaviors where possible. Add guards at irreversible/high-risk boundaries and use empirical benchmarks to decide the rest.

## Questions for Codex / project owner discussion

- Is the current single-Agent Builder already sufficient if QA/evidence handling improves?
- Would a separate read-only visual critic improve quality, or just duplicate the Builder's reasoning?
- Which current constraints are helping reliability, and which are suppressing useful model/tool freedom?
- What is the smallest change that would have prevented the latest GLM quality failures?
- Which failures should be solved in Skill, which in Agent harness, which in deterministic code, and which are simply model capability limits?
- What benchmark should define “good enough to sell” for image -> SketchUp?

Do not implement changes solely because this note suggests them. Discuss against local evidence first.
