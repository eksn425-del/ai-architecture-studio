# B.AI DeepSeek: real same-image test, incomplete planning

The owner supplied an existing B.AI Key and requested a real K Studio test using the previous narrow residential reference. A separate `deepseek-20261021` project was created through the product UI. No cloud deployment, account purchase, original-model edit or alternative inference provider was used. Raw images, conversation/provider histories, screenshots, balance details and encrypted credential containers remain private on the owner's E drive.

## Actual outcome

| Check | Result |
| --- | --- |
| B.AI credential and exact available model | Authenticated `/models` and `/balance`; catalog ID `deepseek-v4.1-flash` |
| Real image and natural Chinese input | Uploaded through real K Studio; actual provider response identified balcony/grid/roof features |
| Recognition accuracy | Underestimated floor count and proposed an overly wide mass; user-style ten-floor correction recorded, not a fidelity PASS |
| First planning attempt | 240-second nonstream request timeout; no tool/native execution |
| Same-project recovery | SSE transport completed actual workspace read/write cycles, preserving image/history/clarification; later timeouts retained. Low effort and earlier compaction were also tested, with 22 old messages omitted from active requests only |
| Complete approved plan | NOT_COMPLETED: three substantive plan files written; construction-strategy validation failed four times and remained unfinished |
| SU build/edit/KEEP/save/download/native reopen | NOT_RUN; no test SKP or geometry write |
| Existing native files | All 647 baseline SKP hashes unchanged, including all five original acceptance models |
| Paid-provider fallback | Disabled: standalone API-only profile, Codex inference unavailable |

Eighteen real product provider responses plus one isolated small-text diagnostic returned the exact requested model and actual usage: 432,294 input and 39,144 output tokens. Known usage has an undiscounted peak upper estimate of USD0.1766610. Five timed-out calls retain USD0.3538944 each in the durable test ledger; total known-plus-reserved liability is USD1.9461330. Another full reservation would exceed the owner-approved total USD2 ceiling, so no further inference is authorized within this run. The initial USD1 ceiling was raised only after the owner's explicit answer, with all earlier reservations retained. This is a conservative test guard, not an actual bill or cloud credit system. Account-wide balance differences cannot settle individual timed-out calls or prove they were free.

The isolated 36-input/54-output-token diagnostic returned in 7.2 seconds; it is not a modeling or UX PASS. The real product used 21 tools, with four construction-strategy validation failures. Errors included provenance, omitted/misnamed units and an unsupported system role. Invalid files were rejected before native execution. Repeated full rewrites enlarged the active current-turn tool history despite compaction of older turns. This exposed a product recovery weakness as well as provider/network timeouts; do not attribute all failures to the gateway.

## Changes and validation

- Explicit B.AI provider/model/base controls; changing service clears the password and cannot reuse another host's saved Key. DPAPI storage only.
- B.AI SSE assembles fragmented tool arguments and retains reasoning for provider continuity internally. No reasoning is exposed in public activity. Tools wait for a complete terminal stream, matching model and actual provider usage; missing usage is never estimated. Disconnect, truncation, model mismatch and malformed output stop without a retry.
- Failed turns now end with an explicit warning inside the conversation. API stream read timeouts and local budget stops receive actionable Chinese messages rather than a generic local-runtime error.
- Same strategy file failing three times now stops the billable loop, answers all outstanding batch IDs and skips remaining dispatches. Validation errors include the full exact contract and units guidance; rejected files remain unchanged. These fixes are verified offline; they were not used to rewrite or promote the failed live case.
- Clarification/approval/cancellation controls, errors and phase state now live in the scrollable conversation. The fixed composer keeps input and upload/model controls only; duplicate progress text is hidden. Real production-code desktop/mobile fixtures verify a 111px desktop composer in both built and clarification/error states, no horizontal overflow, and no inference/native requests. 99 production JavaScript checks and 25 layout/recovery checks pass.
- Read-only project refresh no longer changes sidebar activity order. Attachment migrations persist only when needed and preserve the prior activity timestamp; repeated reads cannot overtake a newly created project. Two regression cases cover unchanged reads and migration reads.
- Final focused checks: 61 passed. A separate project/reference check has 33 passed/1 platform skip. This includes real transport protocol fixtures, reservation retention, credential-host separation, failure receipt persistence and production-JavaScript error rendering. Fixtures are offline evidence only; they do not establish live provider uptime or native model quality.

The first remote regression also exposed the new Chat SSE branch incorrectly intercepting the separate Responses subclass. Dispatch is now restricted to Chat runtimes; 97 API/context/tool-protocol tests pass after the fix. Original failed CI runs remain visible; no fixture-key rejection was treated as paid owner inference.

SSE, requested Low reasoning and earlier active-history compaction recovered genuine tool execution but did not eliminate provider/network timeouts or deliver a complete plan. The existing five-timeout run is preserved; no native geometry was generated outside Studio to substitute for it. The cause of the remaining idle read timeout is not isolated between the gateway, upstream capacity and the existing local proxy. Direct network access had timed out; successful requests used the already-configured environment proxy. Do not claim mainland direct-network stability, architecture quality, or commercial release readiness from this run.

## Sources

[B.AI API](https://docs.b.ai/llmservice/api/) documents the production base and SSE protocol. [Model capabilities and prices](https://docs.b.ai/llmservice/models/deepseek-v4-1-flash/) document native image input, function calling, default high reasoning, peak input USD0.30/M and output USD1.20/M. Model IDs were verified against the authenticated catalog rather than silently translated from marketing capitalization. Actual settlement depends on platform discounts, caching and metered usage.
