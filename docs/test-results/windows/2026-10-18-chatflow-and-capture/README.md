# Conversation flow and owner live recording — 2026-10-18

Owner found that the fixed activity panel and expanded plans consumed the chat viewport, and requested ordinary conversation instead of an image-purpose selector. Based on the actual local desktop implementation `987a30b`, isolated branch `codex/chatflow-recording-20261018` fixes those product behaviors. The owner's separate project **剧院设计 / architecture-project-dce61** and its current model are preserved; this work does not resume the closed eight-source r20 case.

## Final behavior

- Messages, live execution, plan/details and submitted image history share one scroll container. Updating progress follows the bottom only when the reader is already there; reading earlier messages preserves scroll position. The existing input remains available below the conversation.
- Removed image-purpose selectors and per-image classification controls. Uploads carry the actual draft and image order with automatic interpretation. Submitted images remain available as original files, with their historical model revision when known.
- Existing native contextual interpretation now receives the fresh image pixels alongside the exact user text and host-owned attachment identities. It remains a read-only, tool-free interpretation. Unresolved intent becomes a normal clarification exchange with no model writer, including for a ready session; it no longer requires changing a label or choosing a category. Historical image identities, defect versions, unchanged source bytes, approvals and KEEP boundaries remain enforced.
- This reuses the already integrated actual Codex App Server, rather than introducing a separate agent or provider. No model inference was issued to demonstrate the patch.

## Upstream inspected

Official [App Server documentation](https://developers.openai.com/codex/app-server/) describes ordered user input and public turn/item notifications. The public [openai/codex repository](https://github.com/openai/codex) was read at pinned commit `8c076942cb70fba8e5c4732c23f1faabc4aed484`: `LICENSE`, `NOTICE`, `codex-rs/protocol/src/user_input.rs`, and the App Server README. `UserInput` carries text and image/local-image data; intended architectural use is not an input-category form. The product behavior here is K Studio's interpretation of that interface, not a claim about undocumented Codex desktop internals. License: Apache-2.0. Upstream source was inspected locally, not vendored into production. An initially requested obsolete `protocol/v2.rs` source path returned 404 and is retained in the local source receipt.

## Verification

JavaScript syntax and **89 existing frontend checks passed** after updating obsolete selector expectations. Actual headless Edge loaded the new production HTML/CSS/JS with read-only GET responses from the existing project; progress/messages were controlled layout fixtures, not model activity. At 1600×1080 and 390×844: card and plan are inside the scroll viewport, scrolling 120px remains 120px after both message and progress rendering, no classification selector or horizontal overflow, no page errors or non-GET requests. Conversation viewport heights are 696/978px and 476/734px of their respective chat columns.

Backend contextual/reference checks: **67 passed, 2 failed**. Both remaining failures are pre-existing Windows inability to create test symlinks (`WinError1314`), before exercising the guard; no security configuration changed or fixture bypass was used. An additional **107 approval/reference/progress/reconstruction checks passed**, and the final focused attachment/host rerun passed **43/43** after the fallback no-write adjustment. Tests verify natural clarification, exact image ordering, unchanged historical defect versions, image-byte races, and approval isolation; they are not native modeling-quality acceptance.

Initial failures remain locally: one malformed unsafe-filename fixture, a locale-dependent test JSON read fixed with explicit UTF-8, a fixture assuming a live Blender session replaced with the actual tool-free conversation setup, and a fixture that returned a plan without saving its card corrected to model the plan-file contract. The original two obsolete HTTP409 expectations were updated to require HTTP200 clarification and `geometry_committed:false`. An attempted broader check listed a nonexistent test file, so it ran no tests; the corrected existing 107-check selection is recorded separately.

## Live capture and current model

Owner authorized recording K Studio operations and actual SketchUp output together. Two exact application windows are captured locally with `PrintWindow(PW_RENDERFULLCONTENT)`; there is no microphone or full-desktop recording. The first GDI test returned an empty Chromium surface and a contaminated OpenGL surface; those rejected test images are never used as promotional footage. Actual successful window captures were visually inspected before recording.

Recording began **17:27:19 Asia/Shanghai**, after the supplied screenshots. Earlier activity cannot be retroactively claimed as video. Source videos, separate app tracks, synchronized pairs, elapsed wall times, public progress telemetry and original files are local under the prior UI checkout's ignored `runtime/promo-capture-20261018/`. The 6fps requested encoder rate exceeded the actual capture throughput; raw tracks therefore have a shorter encoded duration than wall time. Timing and any speed adjustment are explicitly recorded when preparing clips. No synthetic UI test screenshot is used as actual product-operation footage.

At capture/inspection, the genuine project is **theatre_reconstruction r3/root19**, with two target photos and one historical defect screenshot. It is **planned, awaiting owner approval** for back facade, site and inferred roof work; every project on service8803 reports `running:false`. The recorder does not approve that plan, send a modeling request, or fabricate new model commits. Actual r3 native window and prior authentic stage images are available as material; browsing or a historical image montage is not described as newly generated geometry. The saved reply explicitly labels back/roof/site inference and says the plan itself did not modify the model. This is development material, not a finished-quality or native-reopen PASS.

Local project snapshot copies inputs, state, outputs and event records with per-file SHA256. It is explicitly non-atomic and does not certify native delivery. API keys, authentication containers and cookies are excluded. The local recording/owner assets have not been uploaded to GitHub or published; no main merge or deployment is part of this change.

## Local rollout

Only after a fresh read-only check shows every current service8803 project idle may the local desktop load this revision. Keep the existing shared runtime and provider/model configuration, preserve the original pending plan, images and model files, and verify current SKP hashes before/after the service change. Do not bind or reopen a native model for this UI fix. If a new owner turn is running, defer the reload and continue recording it.

Private engineering artifacts: `runtime/chatflow-validation/` in this worktree. Current/handoff entries link this report. No public upload is implied by local recording authorization.
