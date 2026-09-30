# Own modeling Agent: implementation and evidence plan

This document applies the observed desktop workflow to the existing product. It does not redefine CURRENT_TASK or authorize new software backends.

## Target

Web workspace -> replaceable multimodal/tool-capable provider -> reconstruction Skill -> persistent coding workspace -> existing MCP execution/readback -> editable SketchUp -> screenshot comparison -> revision.

The desktop packaging decision can follow quality acceptance. A browser workspace still needs a local connector to control a student's installed SketchUp; a cloud website cannot directly reach that application's localhost.

## Reuse map

| Layer | Current implementation / reuse | Immediate work |
| --- | --- | --- |
| Inputs/projects/conversation | Existing FastAPI web workspace | Reference-only reconstruction context |
| Model runtime | Codex App Server; optional LiteLLM | Same workflow/profile for both providers |
| Skill | Repository reconstruction Skill; licensed adopted guidance | Clarify, parameterize, approve, build, inspect, revise |
| Persistent authoring | Ignored project workspace | Keep parameters, notes and Ruby across turns |
| Execution | Kongxing + guarded workspace Ruby | Verify disposable path/GUID; owned-root revisions |
| Helpers | Existing SAIE MIT backend | Selected ordinary semantic operations only |
| Visual QA | Existing screenshot/model readback | Source view + oblique view + concrete correction |

Do not build a new CAD engine, provider framework or generic MCP server.

## Work delivered in this integration

- Host reconstruction policy is connected to the conversation endpoint.
- Idle auto clarifies; clarification answers generate a plan. Planned auto updates the plan; explicit execute is required to cross first approval. Building auto continues edits.
- Clarification/planning withhold SketchUp tools and do not ping, save or capture the active model.
- First execution requires a reference, planned state and a verified disposable session.
- Both providers receive the reconstruction profile and reference-only image scope.
- LiteLLM has bounded project note/Ruby read/write tools and persisted conversation/tool history. Codex retains its native coding workspace.
- API provider configuration uses LiteLLM rather than a new provider abstraction.
- UI exposes waiting-for-information, waiting-for-approval and modeling states, explicit approval and parameter revision.

## Configurable API route

For a provider that LiteLLM supports, configure server-side environment variables:

```text
ARCH_STUDIO_ECONOMY_PROVIDER=litellm
ARCH_STUDIO_API_MODEL=<LiteLLM provider/model identifier>
ARCH_STUDIO_API_KEY_ENV=<name of environment variable containing your key>
ARCH_STUDIO_API_BASE=<optional compatible endpoint>
```

The key stays server-side; do not put it in committed files or browser JavaScript. Existing DashScope configuration remains compatible.

Models must actually support image input and tool calls. “Any API” does not mean any text-only model can reconstruct images or any unsupported provider has been validated. This round's configurable-provider checks are mocked; no paid third-party model request is claimed.

LiteLLM handles provider parameter translation; supported parameters vary by model. Keep unsupported-call failures visible rather than silently substituting a model. See [official LiteLLM input documentation](https://docs.litellm.ai/docs/completion/input).

## Acceptance order

1. Unit/API checks establish state transitions, input scope and tool authorization.
2. A real website clarification/planning run establishes actual image receipt and parameter-card persistence.
3. On an independent generated model, GPT-6.1 Sol Low executes persistent Ruby and revisions using the website's approved plan.
4. Capture source-matched and oblique views, identify actual mismatches and make at least one correction.
5. Compare architectural completeness to the verified same-model/effort Direct Codex reference. Passing tests or saving a model is insufficient.

Do not displace the user's currently active competitor modeling session to run our benchmark. Preserve it and report quality acceptance as pending until an independent generated session is available.

## After quality acceptance, for later planning only

Package the local bridge and session-recovery UX, then expand provider selection based on real per-model evidence. Distribution, accounts, billing and additional modeling applications require a subsequent explicit milestone. Commercial usability depends on reliable deliverables, understandable recovery and cost visibility; no revenue outcome is promised.
