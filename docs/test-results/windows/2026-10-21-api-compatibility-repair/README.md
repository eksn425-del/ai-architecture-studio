# Third-party API diagnosis and compatibility repair — 2026-10-21

The owner's request is to explain the gap between successful local Codex modeling and the failed B.AI DeepSeek test, repair product-side faults, and assess launch maturity. This follow-up is offline engineering plus local installation/UI inspection. It does not add paid inference, change the USD2 ceiling, repair historical liabilities, or modify native models.

## Findings from the actual failed case

The [original live test](../2026-10-21-bai-deepseek/README.md) has 18 successful product responses, image recognition and real workspace tool exchanges. The gateway was not completely unavailable. It still failed to complete the plan and never reached SketchUp modeling.

Four actual strategy writes, each 8,425–8,492 characters, were rejected in sequence for invalid provenance, an array used as a text parameter, a numeric dimension without the required units, and an unsupported system role. Active context eventually grew to 132,141 characters / 42,360 input tokens. Prior-history compaction cannot remove the complete current-turn tool journal without risking reasoning/tool continuation; no history was erased to make the metric look better.

Local Codex and the independent API share guarded modeling tools but previously did not have equal orchestration. Codex had native contextual intent interpretation/coding tools. Other providers fell back to the legacy explicit workflow and a generic text-file writer. In particular, “continue completing the plan; do not build yet” could enter clarification rather than the formal plan stage. This was a product-side difference, not proof that third-party inference cannot model.

Five real requests timed out. Direct B.AI access also timed out in the original diagnostic; the existing environment proxy sometimes worked. The old records cannot attribute each stall to the local proxy, gateway or upstream inference. Increasing timeout or blaming one vendor is not a demonstrated fix.

## Product changes

- Selected-API read-only intent interpretation now uses the same host snapshot, reference/model/plan identity and approval validation as native intent. There are no writer tools in this call. Negations, stale plans and conditional approval remain blocked. The explicit approval button needs no additional inference. API intent usage is recorded separately and uses the same durable budget guard as Builder/Critic, with no Codex fallback.
- `workspace_update_strategy` exposes actual parameter units/provenance and system roles/methods as a typed function schema. It updates entries by stable name/ID using the SHA from a prior read, retains unspecified entries, validates the entire update before writing, and returns a small receipt. It does not guess units, turn dimensions into strings, change provenance, approve plans or write geometry. Existing raw JSON tools remain available; repeated failures of either tool share the same three-failure limit for this file.
- Workspace writes now replace files atomically after validation. A rejected or stale update preserves the old file. Nonfinite numeric values and malformed enum types are rejected.
- B.AI transport records header arrival/status, safe request ID, first chunk and connection/response-wait/stream failure phase. Text/reasoning, keys and headers are not included in this telemetry. Full tool exchanges and reasoning state remain intact for continuation. No partial stream output runs tools; no automatic paid retry was added.
- Advanced local API settings now expose an additional OpenAI-compatible Chat Completions connection, with editable model/Base URL, HTTPS/base-address validation and host-bound credential reuse. Saving settings makes no inference request and does not certify modeling. B.AI and official DeepSeek retain fixed addresses. Other protocols still require their own adapter.
- The product readiness matrix explicitly records this exact B.AI DeepSeek route as live planning failed / native not run, alongside the existing historical independent-API partial modeling evidence.

## Verification and limits

Offline tests exercise the actual SSE parser, complete tool batches, private reasoning continuation, workspace dispatcher, typed plan update and durable journal together through mock HTTP. They also cover false execution proposals, stale plan identity, no-writer intent, no hidden provider, pre-dispatch budget rejection, invalid units/provenance/arrays, atomic rejection and stale versions. Mock success is not native/model quality acceptance.

Latest grouped checks: 344 Python passes, one platform skip; 102 production JavaScript passes. Two existing Windows symlink tests first failed with WinError 1314 and are excluded from the subsequent focused intent run; they are not counted as passes. A separate run without Python UTF-8 mode initially hit an existing locale-dependent test read, then passed under the CI-configured UTF-8 mode. All raw failures remain local. GitHub workflow results are checked separately for the actual final commit.

The first GitHub broad baseline comparison on `db171a8` detected an outdated integration-test allowlist that still expected exactly the previous three workspace tools. It is updated to require the new fourth typed tool and its version precondition. The initial failed CI run remains visible; it is not rewritten as a pass. Existing main Ruby/MCP test-environment failures are separate from this additional contract mismatch.

The same 41-file failed API project, its 24-row budget ledger and native SKP files are preserved. No fresh external inference, native build, edit, save, download, reopen, original-program replay or cloud deployment is claimed for this follow-up. Further paid acceptance needs a new explicit ceiling decision or attributable settlement of the five unknown requests; aggregate account balance is insufficient to erase them.

## Product judgment and next acceptance

The local workflow is an internal beta: conversation scrolling, inline plans, compact composer, project recency and approval controls have engineering/UX evidence. External-provider end-to-end reliability and fidelity remain unqualified. Public cloud tenant authentication, isolated storage, atomic credits, durable jobs, paired devices and load/restore testing are still separate unfinished release gates. Deploying the existing loopback JSON service does not deliver them.

The compatibility target is qualified models/endpoints with image input, reliable function calling, sufficient context/code generation and attributable completion/usage. OpenAI-compatible Chat Completions and the separately configured operator Responses adapter are different routes. Arbitrary chat-only APIs, incompatible protocols and unsupported models cannot honestly inherit modeling certification. Even identical API protocols do not guarantee equal architecture fidelity.

Next real acceptance stays on the owner's same source/separate API case: complete a valid plan; approve through real K Studio; first native build; one bounded natural-language edit with KEEP; actual save/download/reopen; inspect original and modified/protected geometry and source-matched views. Keep failed attempts, actual provider/model, latency and costs. No model substitution, manual plan fabrication or direct Ruby may be presented as successful user flow.

Provider contracts checked against [B.AI DeepSeek model documentation](https://docs.b.ai/llmservice/models/deepseek-v4-1-flash/) and [LiteLLM function-calling documentation](https://docs.litellm.ai/docs/completion/function_call). Provider claims are not independent proof of served model weights or K Studio quality.
