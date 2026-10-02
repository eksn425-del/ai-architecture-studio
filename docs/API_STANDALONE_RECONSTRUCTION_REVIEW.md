# Independent API reconstruction — local integration

Date: 2026-10-02. User-directed extension: discreet removal controls, better inferred backs/materials, independent API delivery and single-view vs six-view villa comparison. The user subsequently selected **GLM-5.3-Flash on the domestic BigModel platform**, replacing DeepSeek as this run's live test target. No Astra or Codex modeling fallback is authorized.

## Implemented

- Reference thumbnails use a small upper-right ×; projects use a right-click delete menu. Existing local trash/restore remains.
- The same reconstruction Skill now requires cross-view evidence reconciliation, explicit inferred rear/side/interior logic, material depth/scale checks and front/rear/left/right/roof/oblique QA. The complete Skill remains within the 8,000-character context budget; these instructions alone do not establish improved building quality.
- Existing LiteLLM handles API models and the same persistent workspace/Ruby/MCP surface. No additional provider framework or geometry engine.
- Domestic preset: `zai/glm-5.3-flash`, API base `https://open.bigmodel.cn/api/paas/v4`, reasoning `low`. `zai/` is LiteLLM's provider prefix; the transmitted model is `glm-5.3-flash`. The international Z.ai option has a separate explicit endpoint.
- DeepSeek remains an optional preset. Thinking content is preserved through tool calls and subsequent turns for both providers. Installed LiteLLM mappings consume/reject some effort parameters; explicit vendor extra-body forwarding preserves Low. ZAI's unsupported parallel-tool flag is omitted; our dispatch remains sequential.
- Per-request local evidence records requested/returned model, effort, token counts, latency and provider failures. Keys remain only in service memory.
- Desktop `--standalone --data-dir <local-profile>` starts an API profile, reads only its explicit bridge.json and refuses Codex preset / Premium. Default standalone provider is domestic GLM; `--api-provider` can explicitly select GLM international or DeepSeek.

## Sources and configuration

[BigModel API](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8) specifies the domestic endpoint, Bearer authentication and GLM-5.3-Flash low/high/max reasoning. Its rendered model dropdown is not a complete Flash availability check. The [developer model card](https://huggingface.co/zai-org/GLM-5.3-Flash) identifies native image capability. Account-specific availability still requires a live response.

Use a domestic platform API key for the domestic option; do not paste it in chat or commit it. Coding-plan, international and ordinary platform keys/endpoints must not be treated as interchangeable. Selecting a preset confirms configuration, not provider reachability or successful building reconstruction.

## Validation boundaries

Real browser actions verify project right-click deletion/restoration and thumbnail × deletion/restoration. No existing user building was deleted. Real installed LiteLLM serializers were exercised through intercepted HTTP transport: actual outgoing image blocks, exact host/model, Low, function messages, screenshot readback and next-turn thinking survived for domestic GLM, international GLM and DeepSeek. These are local contract tests, **not live provider calls**.

Fresh local data/profile testing is distinct from clean-machine installation. The existing locally installed bridge can be selected explicitly without reading Codex config. It is not bundled into the desktop package. No VM/second-machine SketchUp installation is established here; installer/plugin distribution and clean-machine validation remain unresolved release gates.

## Live domestic GLM single-view run — observed, quality not accepted

The user entered a domestic Key locally. Real browser actions used upload → ordinary Chinese chat → floor-count correction → plan → explicit approval → independent blank SketchUp connection → execution → screenshot-driven follow-up → SKP download. Transmitted/returned model was `glm-5.3-flash`, domestic endpoint, Low; no Astra or Codex modeling fallback. Actual local image blocks and tool screenshot readback were observed in private event records.

| Stage | Seconds | Tool calls | Failed calls | Input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| First building execution | 819.032 | 36 | 12 | 1,931,784 | 41,383 |
| Same-model correction | 468.547 | 33 | 1 | 3,632,547 | 15,011 |

Tokens are summed provider-reported usage across repeated requests, not unique input size. No monetary estimate is asserted. Script generation and repeated full context explain part of latency; model price alone does not establish economical reconstruction. Initial GLM floor-count analysis was incorrect and required a user-level correction before approval.

The actual building retained root PID 37853 through revision 8. An earlier empty probe used a separate root, so whole-run single-root purity is not claimed. Side walls were initially missing and repaired after screenshot inspection. Final front still has opaque-looking right glazing, white/heavy frames unlike the source, dangling/poorly placed panels and weak material detail. Rear/interiors/environment are inferred and schematic. Agent-written visual QA claimed success; independent inspection rejects that claim. **Building quality: FAIL / partial output.** Six-view comparison has not run.

Real browser download matched the generated SKP exactly: SHA-256 `d718935189358438e8fe1527a7693564e806cf80f06e48ee7c07f97828279a86`. Private references, generated scripts, event/history logs, renders and model files remain ignored locally.

## Fixes derived from this run

- State the injected model/root contract directly in the Ruby tool and rejection errors. Explain Ruby method scope, host-owned transaction/save and invalidated faces after extrusion.
- Reject roots containing only empty groups/components using recursive geometry inspection. This helper loaded during the correction; an isolated live empty-container rejection test remains pending.
- Keep Skill once in current system context instead of repeated saved user messages. Preserve tool/history evidence; checkpoint completed tool exchanges. Stop after three consecutive failed modeling executions, with error evidence and retained state.
- Fix the narrow-layout result panel crowding the composer and blocking ordinary send. Wrap composer controls and close results when focusing input on narrow screens.

The API-only localhost service was restarted to load these fixes. Restart clears the memory-only Key; the configuration dialog is ready for re-entry. These new runtime changes pass local regressions but have not yet completed a new live building run. The desktop executable was rebuilt successfully. Fresh local profile startup is demonstrated; clean-machine installation and distributable bridge licensing/setup remain pending. No commercial-ready or exact-reconstruction claim.

## Six-view user-session recovery / High (2026-10-02)

The earlier single-view measurement remains historical Low evidence. The GLM preset and standalone launcher now default to High; users can choose Low/High/Max or provider default. High is the middle available GLM tier, not an invented Medium. Same-connection effort changes do not need another Key entry while the process lives.

Actual user session was trapped in clarifying despite an affirmative start. Chat requests were real, but execution tools were intentionally withheld. Corrected the approval transition and explained the gate to the model. Browser approval produced 8 committed revisions in one owned model root, 540.078 seconds, 33 tools / 2 failures, 1,859,915 input and 29,350 output tokens summed across provider calls. Actual High was recorded on each provider event. Six images moved into the historical user message and remain vision evidence, without six fresh duplicate image blocks every turn.

Manual source comparison still rejects quality: excessively pyramidal roof, wrong floor/window composition, simplified glass/materials, and no interior visual verification. The model self-reported QA does not supersede this assessment. Ordinary same-model browser correction is being measured separately; see HANDOFF for its final result. These trials differ in both input count and effort, so they cannot establish a controlled one-view/six-view improvement.

Correction: approximately 742s, 48 tools / 1 failure, 6,185,576 input / 27,824 output tokens; 48-call budget interruption, owned root retained to r16, saved/downloaded checkpoint. Final quality FAIL/partial: wrong street/pool view mapping, roof/facade mismatch, blank side and floating pieces; interior not accepted. Added interruption usage/checkpoint reporting regression, without claiming a live rerun. This context growth and poor self-QA are release blockers despite functioning execution.
