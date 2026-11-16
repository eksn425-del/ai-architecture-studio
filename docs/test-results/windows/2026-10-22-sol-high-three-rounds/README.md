# Real Sol High novice test — three rounds completed, overall PARTIAL

**Later owner correction:** the owner rejected this result, including schematic roads and the occluding detached neighbor. The controller72/76/78 scores below are historical and withdrawn as quality-acceptance evidence. See [owner rejection and current repair](../2026-10-22-owner-rejection/README.md). The original metrics/failures remain unchanged.

本轮已完成真实网站三轮体验，暂评72→76→78分：首版停在r6，阳台局部修正到r8，街角/轨道局部修正到r10。后两轮能理解截图反馈、保护其他构件并正常结束；第一轮仍发生过度细化。最终SKP已真实下载并用SU2024打开，声明精度下的完整几何比较通过，严格逐位比较失败保留。整体源图保真仍需改进，当前属于内测产品，不能称为已成熟发售。

成本结论：本次没有第三方API实际扣费。按本机已观测缓存及官方参考单价估算三轮合计6.312689美元，不能承诺一个建筑5元；18层建筑和街景也不能代替小场景成本样本。旧DeepSeek案例的主要额外开销来自长回合上下文增长、逐视角编排和强制继续细化，原始中断原因是供应商余额不足。网关超时与Agent效率应分别诊断，不能把这两种问题统称为“API不能建模”。

Owner requested a new privately supplied stepped residential tower image, three real Studio rounds (initial build, screenshot feedback, second screenshot feedback), source comparison, native inspection and complete usage evidence. Website model is actual `gpt-6.1-sol / high` through the owner's local Codex App Server. This is a development subscription route, not independent paid API acceptance. Outer Codex settings are unchanged. Video was explicitly deferred by the owner; screenshots and native versions remain local on E.

## Initial observed failure

Real UI created an independent project, uploaded the original image, answered two concise scope questions, displayed a plan, opened a fresh project model and approved the build. Actual thread/start returned the requested model and high effort. No original project was reused for geometry.

The first build reached six native revisions and recognizable tower/stepped wings/neighbor/vegetation/street/rail geometry, but continued refinements past a coherent first version. At approximately 2000 seconds the controller used the product's normal Stop action. Host acknowledged the interruption and saved the committed model. Current source quality remains NEEDS_FIX; neither this interruption nor post-commit identity/bounds receipts establish complete native delivery or visual acceptance.

Frozen initial evidence reports 10,859,219 input, 10,340,096 cached input and 75,370 output tokens across the case's local threads at the freeze. These include planning, read-only intent and independent Critic work. Counter updates are not HTTP-request counts. Applying current standard Sol reference rates gives USD2.825956 with the observed cache, not a bill or a future-cache guarantee. A CNY5 price promise is not established by this case.

## Repairs identified from the actual run

- Browsing old history during execution works, but returning to the running chat appended an optimistic user message after its server-persisted copy. Keep the pending processing indicator while suppressing only a newly persisted matching message; preserve genuinely repeated instructions from earlier turns. The backend had exactly one submission.
- The concise native Harness prompt branch had not inherited the full branch's completion policy. Share an explicit first-version/user-review milestone and scoped-edit completion rule across both. Independent current-source/current-revision review and writer/KEEP protections remain mandatory; an honest NEEDS_FIX does not authorize automatic unrelated polishing.
- Preserve reported cache reads/writes and reasoning-output counters as turn deltas in the native journal. Missing fields stay unknown, resumed-thread historical counters are subtracted, and reasoning remains a subset of output. This telemetry is not billing.

Initial code checks: 36 focused Python tests and 114 UI tests passed. Later feedback rounds used the same project and image with immutable stage snapshots. They are smaller tasks, not a controlled equal-complexity cost A/B against initial construction.

## Second real round and follow-up candidate

Owner-style defect feedback was submitted with an actual SU Orbit screenshot. The image was correctly classified as `defect_location`, leaving the original target unchanged. After installation of the first repair, real background-history navigation rendered the pending user message exactly once. The balcony correction completed normally at r8 with two targeted bays, current six-view/source-matched independent review and deep KEEP receipts; the global verdict remains NEEDS_FIX. Controller rubric: r6 72/100, r8 76/100. These subjective scores do not certify statutory compliance.

A remaining observed friction was that a defect screenshot reset the conversation into full planning. The repair restores the existing-model lifecycle only when fresh screenshots are all defects of the exact current revision, original targets/camera evidence remain hash-verified, and no new taskbook/site input was added. Independent current-user intent and all native/writer/scope checks still authorize execution. Added current defect screenshots may preserve an existing independent review of unchanged target/model evidence; changed targets, old defect revisions, unknown/supporting roles, altered bytes or missing provenance still invalidate it. Accepted old reviews can prove lifecycle identity without becoming a veto on a new edit. This direct-edit lifecycle passed the real third-round UI test.

Also repair the actual `/E:/...` spelling returned in the second reply into a checked project-relative link, instead of redacting an otherwise valid project screenshot. Foreign files remain outside the allowed project. The follow-up's 142 focused Python tests passed, two Windows symlink privilege cases excluded. No live result is inferred from those checks.

Actual r8 diagnostic also found that a post-Critic `execution_turn` metadata append invalidated the otherwise unchanged review. Source bytes, cameras, model revision and all other evidence facts matched. The loader now tolerates only this non-authoritative receipt field; any other source/design fact or image/sidecar change still invalidates reuse. Its claims never certify saving/reopening or grant an edit. Focused tests and passive validation of the real r8 receipt passed. The third Builder's actual prompt contained the host-verified checkpoint. It nevertheless requested a fresh pre-edit review for the newly targeted street system; the r8/r9/r10 reviews are retained. Do not claim that receipt reuse eliminated all review overhead.

## Final actual stages

| Real UI stage | Native revision | Subjective score | Total tool starts | Native model tools within total | Incremental input/output | Reference USD with observed cache |
|---|---:|---:|---:|---:|---:|---:|
| First version, normal UI Stop after over-refinement | r6 | 72/100 | 118 | 73 | 10,859,219 / 75,370 | 2.825956 |
| Screenshot feedback: two recessed balcony bays, normal completion | r8 | 76/100 | 81 | 45 | 7,339,320 / 36,317 | 1.900498 |
| Screenshot feedback: curved curb, flush rails and contained wire ends, normal completion | r10 | 78/100 | 55 | 37 | 5,691,434 / 28,571 | 1.586235 |

Totals include the case's planning, intent and independent Critic threads. Tool starts include local coding/read tools; 254 starts are not 254 model requests. The 21 native thread runs had200 distinct usage-counter updates, not a verified paid HTTP request count. Actual total input23,889,973, cached22,563,072, output140,258; reasoning50,231 is already part of output. Largest observed individual input240,754, within the reference standard up-to272K tier. Reference totalUSD6.312689 with observed cache; all-input-uncached scenarioUSD49.182526. This is not a subscription invoice, external gateway bill, guaranteed future cache or CNY5 target acceptance.

The third correction kept all building/neighbor/vegetation geometry. r9 changed four existing curb leaves plus tracks/wires; r10 only shortened existing wire groups. Exact owned-path and deep KEEP receipts passed, target containers were retained, and no extra building polish followed the final review. Direct native rail/curb relations and current six-view/source-matched images are retained. Native self-inspection found no newly exposed slab through the facade at the inspected scale; hidden joints are not structurally certified.

Global source fidelity remains NEEDS_FIX: tower front/side bays are5/4 versus approximately6/5 visible in the source, low-wing interlocking planted terraces remain simplified, and neighbor window grouping differs. Rear geometry is inference from one source angle. These limitations remain visible instead of being hidden behind the subjective score. No additional geometry is scheduled after the requested three rounds.

## Real native delivery inspection

The final model was downloaded by clicking the real product link; its bytes matched the host checkpoint SHA. SU2024 then opened the current bound model and the clean downloaded copy through its native Open dialog. A fixed host-only read-only definition-graph collector verified root19,4103 definitions and119,067 unique physical entities at all three stages. It does not write model geometry or call an LLM.

All three complete comparisons passed the pre-existing `KStudioNativeStableGeometry/1` contract: coordinates/translations in mm, topology, materials and other fields stay exact; only dimensionless face normals and affine linear coefficients use12 decimal places. Raw full-double pre-save→reopen remains FAIL, while bound-reopened→download-reopened raw comparison is PASS. The raw failure is not overridden. This establishes consistency for these inspected native files under that explicit contract, not strict program replay, source fidelity, building-code compliance or commercial readiness.

The initial capture was after the product's automatic checkpoint and before an explicit native Ctrl+S/reopen test. Historical evidence before the product's own checkpoint was not captured and remains NOT_RUN. Do not present this as retroactive proof of every earlier save. Strict blank program replay was not run. Final K Studio reconnection restored the original project model without another Builder call. The frozen r6/r8/r10 versions and downloaded copy remain separate.

## Final UI cleanup, preservation and validation

The actual direct-edit run temporarily retained planning-only shortcut text while execution was underway and displayed a nonpending working note as an unverified new plan after completion. Hide those shortcuts while busy and hide an existing-model working card when no matching pending plan exists; new pending-plan hash/approval checks remain fail closed. Remove the remaining Economy/precision tier captions from transient UI text, keeping the actual selected model/effort. This is presentation cleanup, not a new model route or effort change.

Latest focused Python run64/64 and production Node114/114 passed; earlier follow-up backend suite142 passed with two Windows symlink privilege cases excluded. Actual browser feedback round and native reopen evidence are separate from unit tests. Final verified source activation/reload receipts remain local. All649 pre-test SKP files are byte-identical, and the API credential container hash is unchanged. No paid provider calls were made. New private journals, full per-round audits, actual prompts, images, native fingerprints and source/model SHA manifests are on E; public [metrics](metrics.json) contain only sanitized counters and verdicts.

## Public source review

Pinned upstream Codex HEAD on 2026-10-22: `07316174c6f62deb20278c53add2dbd9dcf6da70`, Apache-2.0. Reviewed public `context_manager/history.rs`, `compact.rs`, `tools/router.rs`, and supported App Server documentation. K Studio already uses the actual upstream App Server; it does not need a second imitation Harness. Retain durable project facts and authoritative model identity separately from the bounded active model window, pair tool calls/results, and measure cache/latency/output rather than treating raw total tokens as invoice cost. No upstream implementation was copied by these repairs.

Sources: [Codex](https://github.com/openai/codex/tree/07316174c6f62deb20278c53add2dbd9dcf6da70), [App Server](https://learn.chatgpt.com/docs/app-server), [Sol reference pricing](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [compaction](https://developers.openai.com/api/docs/guides/compaction).

Building Xuezhang's public app/tutorial pages were opened but returned no readable page body. Existing ordinary UI observations are documented separately; their selected model label does not verify served model or internal orchestration. No license for its private agent implementation has been established. This run does not decompile the installed app, copy private prompts, inspect hidden endpoints or spend its credits. Public workflow observations cannot explain its architectural quality causally without a comparable authorized test.

## Scope and limitations

Architecture and bounded scene context are the current domain. Future mechanical/game workflows need their own units, topology/mesh, constraints, export and quality criteria; architectural facade checks cannot certify them. This test does not implement those domains or cloud deployment.

New source images, SKP, raw event journals, owner session data and native screenshots stay private. Only sanitized engineering records/code belong on the isolated development branch. Credentials, API liabilities, earlier failures and all old native models are preserved. No paid gateway call, public media publication, main merge or deployment is part of this test.
