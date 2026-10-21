# B.AI DeepSeek: real same-image test, incomplete planning

The owner supplied an existing B.AI Key and requested a real K Studio test using the previous narrow residential reference. A separate `deepseek-20261021` project was created through the product UI. No cloud deployment, account purchase, original-model edit or alternative inference provider was used. Raw images, conversation/provider histories, screenshots, balance details and encrypted credential containers remain private on the owner's E drive.

## Actual outcome

| Check | Result |
| --- | --- |
| B.AI credential and exact available model | Authenticated `/models` and `/balance`; catalog ID `deepseek-v4.1-flash` |
| Real image and natural Chinese input | Uploaded through real K Studio; actual provider response identified balcony/grid/roof features |
| Recognition accuracy | Underestimated floor count and proposed an overly wide mass; user-style ten-floor correction recorded, not a fidelity PASS |
| First planning attempt | 240-second nonstream request timeout; no tool/native execution |
| Same-project recovery | SSE transport completed actual workspace read/write cycles, preserving image/history/clarification; subsequent stream read timeout retained |
| Complete approved plan | NOT_COMPLETED: three substantive plan files written; construction strategy remained unfinished |
| SU build/edit/KEEP/save/download/native reopen | NOT_RUN; no test SKP or geometry write |
| Existing native files | All 647 baseline SKP hashes unchanged, including all five original acceptance models |
| Paid-provider fallback | Disabled: standalone API-only profile, Codex inference unavailable |

Eight successful provider responses returned the requested model and actual usage: 123,093 input and 11,540 output tokens. At documented undiscounted peak rates, known usage has an upper estimate of USD0.0507759. Two timed-out calls retain USD0.3538944 each in the durable local test ledger. Total known-plus-reserved liability is USD0.7585647; reserving another full request would exceed the initial USD1 ceiling. This is a conservative test guard, not an actual bill or cloud credit system. Account-wide balance differences cannot settle individual timed-out calls or prove they were free. A higher test ceiling requires the owner's answer; prior reservations are not erased.

## Changes and validation

- Explicit B.AI provider/model/base controls; changing service clears the password and cannot reuse another host's saved Key. DPAPI storage only.
- B.AI SSE assembles fragmented tool arguments and retains reasoning for provider continuity internally. No reasoning is exposed in public activity. Tools wait for a complete terminal stream, matching model and actual provider usage; missing usage is never estimated. Disconnect, truncation, model mismatch and malformed output stop without a retry.
- Failed turns now end with an explicit warning inside the conversation. API stream read timeouts and local budget stops receive actionable Chinese messages rather than a generic local-runtime error.
- Final focused checks: 47 passed. This includes real transport protocol fixtures, reservation retention, credential-host separation, failure receipt persistence and production-JavaScript error rendering. Fixtures are offline evidence only; they do not establish live provider uptime or native model quality.

SSE recovered genuine tool execution but did not eliminate provider/network timeouts. The cause of the remaining idle read timeout is not isolated between the gateway, upstream capacity and the existing local proxy. Direct network access had timed out; successful requests used the already-configured environment proxy. Do not claim mainland direct-network stability, architecture quality, or commercial release readiness from this run.

## Sources

[B.AI API](https://docs.b.ai/llmservice/api/) documents the production base and SSE protocol. [Model capabilities and prices](https://docs.b.ai/llmservice/models/deepseek-v4-1-flash/) document native image input, function calling, default high reasoning, peak input USD0.30/M and output USD1.20/M. Model IDs were verified against the authenticated catalog rather than silently translated from marketing capitalization. Actual settlement depends on platform discounts, caching and metered usage.
