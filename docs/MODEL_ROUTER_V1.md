# Model Router v1 — Cost / Quality Dual Track

## Objective

Keep the architecture workflow quality gained from Skill + Ruby, but stop tying product economics to one expensive model.

Target:

**same architecture skill + same MCP/Ruby tools + same QA loop → interchangeable model providers**

The product should support two practical modes:

- **Economy / Standard:** low-cost multimodal/tool-capable model handles most design discussion, tool calls, screenshot inspection, and revisions.
- **Premium / Refine:** Astra-class model is used only when the user explicitly requests higher quality or when the cheap model fails objective QA / gets stuck.

## Product principle

Do not encode architecture quality inside one provider-specific prompt or runtime.

Architecture capability should live in reusable layers:

1. project context / memory
2. thin architecture skill
3. SketchUp tool surface + project Ruby
4. screenshot / model QA loop
5. provider adapter

This allows Luna, Qwen, GLM, or another compatible model to inherit the same workflow.

## First benchmark candidates

### OpenAI

- `gpt-6-luna` — first low-cost benchmark candidate. Official API docs list text/image reasoning, built-in tools/function calling via Responses API, 1.05M context, and pricing far below Astra.
- `gpt-6-astra` — quality ceiling / premium reference, not the default economy model.

### China / lower-cost candidates

Prioritize models that can satisfy both multimodal inspection and tool/function calling. Candidates include:

- Qwen3-VL Flash / Plus family via Alibaba Cloud Model Studio
- GLM family with tool calling where the selected provider/region supports it
- other OpenAI-compatible providers only if they can reliably round-trip tool calls and images

Do not integrate five providers at once. Add the smallest provider boundary, then benchmark one OpenAI cheap model and one Chinese cheap model.

## Reuse instead of rebuilding provider plumbing

Prefer using the MIT-licensed non-enterprise portion of `BerriAI/litellm` as the provider compatibility layer if it saves time. It already contains provider integrations for DashScope/Qwen and Z.AI/Zhipu-style backends.

Do not copy LiteLLM enterprise-only code. Preserve license attribution if source is vendored; prefer dependency usage over source copying.

## Routing policy v1

Start simple; no ML router.

- normal chat / project parsing / reference synthesis / routine SketchUp edits / screenshot QA → Economy model
- first complex concept generation → Economy model first
- if QA fails twice, tool loop stalls, or user chooses “精修” → Premium model for one turn
- return to Economy for later routine edits when possible

Do not silently escalate every turn.

## Quality gate

A cheap model is acceptable only if it reaches a useful architecture threshold with the same Skill + Ruby environment.

Benchmark identical inputs and tools against Astra Low. Compare:

- program / adjacency coherence
- plan + section / vertical relation
- site + entrance + public-space logic
- facade openings / envelope detail
- successful SketchUp tool/Ruby use
- screenshot inspection and correction
- same-model revision reliability
- semantic model organization / QA defects
- token cost and wall-clock latency

The goal is not “cheap model calls tools.” The goal is “cheap model produces a model a user can continue using.”

## Cost target

Track real per-project tokens and model calls.

Desired outcome:

- Economy mode is cheap enough for repeated student use.
- Premium mode is an optional upsell / rescue path.
- Hybrid routing should spend expensive-model tokens only on the few turns where they materially improve output.

## OSS capability migration continues

Continue adopting proven capabilities when directly useful:

- SketchUp Architect Skill — architecture reasoning / continuity / QA
- SAIE — richer SketchUp tools, snapshots, openings, slabs/roofs, BIM metadata, reports, DXF parsing, batch operations if Kongxing lacks them
- ArchFlow Studio — project state, CAD/output patterns where directly reusable
- VBO SkAgent — fallback bridge / Ruby control if needed

Do not integrate a repo merely because it exists. Move only capabilities that reduce time-to-quality.

## Benchmark output

For each candidate model, record:

- provider + exact model id
- region
- input/output tokens and estimated cost
- tool-call count
- retries/failures
- screenshots from matched views
- objective QA findings
- whether premium fallback was needed

Keep benchmark assets synthetic/sanitized in GitHub; private thesis files remain local.
