# 最新 R3 商业化内部候选 — 2026-11-14

[发布关卡索引](release-gates/index.md) 固定 PR27 审计基线 `6a8001c`，商业候选在 `codex/kstudio-r3-commercial-candidate-20261114`。桌面 **beta10 / sequence17**，原常用桌面 **beta03**。本机实际安装、更新回滚、未知写入恢复、SKP 下载重开已取得独立技术证据。受控样件之外的图片建模和商业服务仍需实际验收。 [裁决](release-gates/FINAL_RELEASE_VERDICT.md) · [恢复交付](test-results/windows/2026-11-14-r3-beta10-pre-report/README.md)

# 最新本机候选：窗开间学习、单窗口和真实交付 — 2026-11-14

[PR27 实测证据](test-results/windows/2026-11-14-r3-release-training/README.md) 对应新候选源码 `3b9ecabc3ce1b7e55825b7baecf4cacc5fa797dd`。实际客户端使用 BAI DeepSeek Flash Responses，High 请求，完成砖木工坊 r1–r12。同一个 SketchUp 24.0.484 进程完成连接和下载文件重开。原生四个窗开间共用定义，真实开孔、玻璃深度和分阶段提交均已读回。局部改到右侧外梯，r12 逐级修正梯身，15 个其他直接部件和 17 个踏步均保留。r12 交付 PASS、模型保真 PARTIAL。原照片对应的砖木质感、窗框细分和栏杆语言仍有差距，平台与楼板重叠及 60 毫米门槛框有待处理。

E 盘本机候选 `2026.11.14-R3-beta07` 序号 14 已打包，SHA-256 `63d6e8c80f0123e71ca7c65bd4a516191e5e8ab983e2e3740032c1eeb8a83d43`。打包客户端可在本机空白 Profile 启动，桌面安装仍 beta03。公开商业发布 BLOCKED，需干净 Windows + SU2024 首装验收、发行许可与签名以及生产云资源。工作台关闭后的真实在线账号/收费没有在本轮操作。[外部配置续跑](execution/KSTUDIO_R3_EXTERNAL_INPUTS_STATUS_20261107.md)。

# 开源采纳：参数化窗开间 — 2026-11-14

PR27 源码 `a532096ce0d95d1f00d8d9cb789a8f9134b4da16`。将 Local MCP for SketchUp 的带孔边界构造方法接进 K Harness，参考 ADAI 参数化开间与 agentcad 的规格验收。默认建筑 Skills 指导使用 `window_bay` 先做一个直墙矩形窗样板，再阵列原生组件。继续用已有 ProjectRuby、批准范围、接边和深层保护。未知提交时，受控参数化写入与工作区 Ruby 写入都停止继续调用供应商。

[实机样板、失败及源码出处](test-results/windows/2026-11-14-oss-window-bay/README.md)。SketchUp 2024 将五个开间读回为两个共享定义，保留墙、框、玻璃闭合实体，保存检查点在另一实例重开一致。原生工具 PARTIAL 验收已完成，真实客户端看图选用、浏览器下载和整栋效果待测。本轮零外部模型请求。原始素材与 SKP 置于 E 盘 `outputs/video-storage/jobs/kstudio-oss-window-bay-20261114`。桌面仍为 R3 beta03。

# 当前候选：模型质量、原生交付与持续建模 — 2026-11-14

PR27 继续使用 `codex/kstudio-r3-launch-20261105`。起点为 `1ca90f4815a550b4ac1f03d2d5ccf196f5240105`。已有两个原项目和历史账本逐项核对保留；所有测试工程、原图、SKP、原始检查点和详细日志在项目 E 盘 `outputs/video-storage/jobs/kstudio-quality-training-20261114`。

- [退台高塔 r8/r9](test-results/windows/2026-11-14-stepped-tower-r9/README.md) 实测确认旧副本渲染目录未配对、截图异常会挡住当前交付件。修复后 r8 更新预览和下载通过。BAI 在同一副本提交 r9，调整两块楼板前缘至 4 / 8 米。下载件在 SU2024 原生重开一致；整体源图保真 PARTIAL。
- [文昌灯塔 r11→r13](test-results/windows/2026-11-14-wenchang-r13/README.md) 第四梯段的 600 毫米错台消除，实际全宽接边 1,100 毫米。栏板方向纠正，前面罩开口去掉 35 个面，内层玻璃和另 25 个直接系统的深层签名不变。当前 SKP 已下载和原生重开。折面、边线和乳白质感仍 PARTIAL。
- [新图砖木工坊 r1→r13](test-results/windows/2026-11-14-arts-workshop/README.md) 用同一 BAI DeepSeek Flash 高推理请求走完实际页面计划、原生阶段建模、局部楼梯返工、下载和重开。在 r13 实测踏步与平台板边 1,350 毫米、平台与楼板门宽范围 1,200 毫米。17 个上向踏面位置保留，其余 16 个直接系统通过深层 KEEP 核对。两轮保存的 SKP 都能原生重开。多开窗口后的自动选择仍需一次手动选择。参考图右侧开间读图、砖木材质及首级 250 毫米高差保留为 PARTIAL。
- 源码修复提交 `d97a2a37a61edbdf6f003b05ab56941160c25dbb`。截图配对只关联验证过的项目渲染目录。写入提交和预览分别出回执。建筑 Skills 更新退台世界坐标复核、折面开口优先、各段楼梯的实际标高和连续接边；本次新图调用了 `sketchup_measure_level_joint`。这些是 Skills 和工程编排改进。
- 本批 BAI 账本 121 settled、0 新 unknown，实际扣费金额没有回执。文昌历史 88 settled＋2 unknown 与高塔历史 52 settled 原始行不变。新模型继续使用原有提供商，无切换或充值。评审只发布脱敏数据和原生截图。
- 下一验收继续复核侧立面、楼梯首级和门前几何，按同一输入做 K 增强与原生对照。干净 Windows、安装包、生产登录/支付按现有发布门槛验收。现有桌面已安装版本仍是 R3 beta03 sequence10，源码独立工作台没有替换已安装版本。

---

# 最新实机预检 — 2026-11-11

用户新给退台高塔参考图，要求打开最新K Studio用BAI测试。[启动、上传与SU连接预检](test-results/windows/2026-11-11-stepped-tower-preflight/README.md)：源码de0ea81独立E盘profile，BAI Flash/HIGH配置已恢复，真实界面上传图片、自动打开SU2024并核验本会话空白副本成功。没有发出模型请求，图像建模/修改/交付NOT_RUN；按上一轮用户要求等待本次明确预算。旧文昌r11/失败/账本保持原样，旧安装beta03未替换。继续使用同一新会话，不重复创建；私有续跑记录在E盘jobs/kstudio-stepped-tower-20261111/resume.json。

# 当前目标：模型质量与真实交付优先的可发布候选 — 2026-11-10

最新用户指令优先：PR27 / codex/kstudio-r3-launch-20261105，不合并 main，不开放生产收费。核对起点 b1855e205304e843fb757757e293ee0ac8bf7b1e。保留文昌 r11/root19、六张私有图、所有原始失败/检查点与 88 settled + 2 unknown。新增付费调用必须先有明确预算和授权；旧无限额度授权不用于本轮。

[P0 r11 真实客户端下载、SU2024 重开与三阶段深层交付证据](test-results/windows/2026-11-10-r3-r11-delivery/README.md)：交付 PASS，原221文件 SHA 未变，0新模型请求/0几何写入。质量仍 FAIL，恢复/基准仍待后续验证，不发布新安装包。安装仍 2026.11.07-R3-beta03 sequence10；源码和安装版不得混称。P0 质量和恢复优先，P1 同配置原生/K增强基准及成本，达到门槛后 P2 打包/干净机，P3 商业服务不得冒充上线。

[P0质量定位](test-results/windows/2026-11-10-r3-r11-quality/README.md)：源图保真FAIL；原生第四梯段顶踏面到顶平台600mm间隙。已确认r7复用24×175mm，而末段实际层间仅3600mm；前三段接触不等于全宽连续。外罩/玻璃分层950mm已量化，但主开口、折面与材质/边线仍未通过。0新建模调用，不修改原r11。

[P0恢复故障证据](test-results/windows/2026-11-10-r3-recovery-faults/README.md)：受控副本拉伸/非共面拒绝/回滚、未知回执后SU退出、恢复状态写入中途终止、完成标记丢失后SU重启均已实测；保留TTL心跳误判FAIL与修复后PASS。恢复改为持久化激活日志并阻止未完成期间写入。原复杂pushpull崩溃根因、真实页面恢复按钮与打包版仍PARTIAL/NOT_RUN；不宣称物理断电认证。定向46项+路由12项通过不替代建筑验收。

**本轮收尾**：[发布边界、冻结对照输入、成本与最少外部动作](test-results/windows/2026-11-10-r3-candidate-boundaries/README.md)。新增源码真实页面恢复按钮已在无API独立副本PASS，打包版仍NOT_RUN。58项定向工程回归；视觉仍FAIL，不能用数量替代验收。88 settled＋2 unknown逐行未变，0新增推理。桌面旧R2指针已备份并纠正到E盘现有R3 beta03 seq10；本轮源码未安装。P1对照等待明确预算/授权，P2等待质量与干净机，P3等待既有外部资源，无main合并/生产收费。

---

# 最新网页审查交接 — 2026-11-08

用户现在要求将最新 Agent 全部代码与测试现状交给网页端审查。[本轮报告、六视图、失败及回归证据](test-results/windows/2026-11-08-wenchang-agent-review/README.md) 为最新入口，优先于下方历史快照。分支 `codex/kstudio-r3-launch-20261105` / PR27，实际测试代码 `9972d3ed8b9640335c0721213930a5dae784246f`。

文昌灯塔六张私人参考原图，真实 K Studio 页面 + 官方 DeepSeek Harness + BAI Flash Responses / High，1017 未核实。模型已续建到 r11/root19，状态 PARTIAL：样板/玻璃/外罩/楼梯/场地已提交；外罩源图保真与楼梯局部质量尚未通过，r11 下载和原生重开 NOT_RUN。两次原生卡死/崩溃、未知提交、误判澄清和旧进程复用均保留。已核验的 r1 恢复不能冒充 r11 交付通过。

本轮结束：88 settled + 2 unknown，无 reserved，总费用未知，不留下自动付费循环。先供网页审代码和实际视图，再续同一案例；不重建、不丢弃原模型与失败。安装桌面仍 beta03 seq10；最新源码未重新打包安装，商业 Beta 未上线。原图/SKP/密钥/原始对话保留在 E 盘私有目录。

---

# R3 implementation checkpoint — 2026-11-07

Implementation continues on codex/kstudio-r3-launch-20261105, [PR27](https://github.com/eksn425-del/ai-architecture-studio/pull/27), preserving the R2 baseline, original installations/configurations/models and failed tests. Cloud account encryption/device restore, recent-auth, WeChat Native signing/ledger recovery, gateway budgets, website gates and deployment/backup operations are implemented. [Engineering evidence](test-results/windows/2026-11-07-r3-launch-candidate/README.md): local PostgreSQL 203 passed / 0 skipped; CI PostgreSQL 202 passed / 1 skipped and actual restricted Docker service passed. These are engineering results, not live Authing/customer payment/public deployment.

**Real local BYOK modeling is now PARTIAL, not NOT_RUN.** [Native evidence](test-results/windows/2026-11-07-r3-native-byok-delivery/README.md): actual K Studio UI and BAI DeepSeek Responses/Low built the text-only 12×8m two-storey pavilion to r8; beta01 failed its final host screenshot destination check after preserving geometry. beta02 core 802c4b2fe98de8bcd966f6c6cf7e99162f566fe7 fixed capture, resumed the pending plan with unchanged encrypted API settings, and completed the porch-only r9 edit. Ten protected groups retained identical deep geometry/material hashes. Actual UI download and SketchUp 2024 reopen passed byte/deep-hash equality. Railing detail and rear-wall/stair visual defects remain; no building-quality or regulatory PASS.

The paid test is stopped with **56 settled + 1 unknown provider attempts**. A provider stream first returned TRANSPORT Connection error with synthetic zero usage; the official SDK retry was refused by the host unknown-liability guard before another reservation. There was **no 58th provider dispatch**. Total usage/cost remain unknown, not zero; do not reset/replay the batch or continue paid work automatically. The subsequent diagnostics fix retains refusal details and the stop guard; offline regressions 26 Python + 7 Node passed without new paid/native calls. This fix is not a successful rail rerun.

beta03 core `790d7f099939228b9828a6524eeccf94f374f7be`, version **2026.11.07-R3-beta03 / sequence10**, is installed on E. Actual GUI installation, Start-menu startup and initial empty-API/account-state checks passed; all207 existing profile files remained present and201 small-file hashes were unchanged before startup. Host readback confirmed executable/data-dir/TEMP/TMP and six WebView profile paths on E. Program copy C→E verified140,911 files /2,190,840,011 bytes with complete SHA equality; old version slots and original R2 remain preserved. **Deleting the verified C program copy was rejected by automatic tool policy (`blocked by policy`); no deletion ran, and the C copy remains.** See [installer](test-results/windows/2026-11-07-r3-launch-candidate/receipts/installer-beta03.json), [runtime paths](test-results/windows/2026-11-07-r3-launch-candidate/receipts/runtime-on-e.json), and [migration result](test-results/windows/2026-11-07-r3-launch-candidate/receipts/program-migration-final.json). This is existing-PC acceptance, not clean-Windows certification.

**Public commercial Beta remains BLOCKED_EXTERNAL.** [Exact external inputs/resumption](execution/KSTUDIO_R3_EXTERNAL_INPUTS_STATUS_20261107.md). No real public URL/download, production identity/SMS/payment or customer charge is claimed. Local installation/verification is complete; C-copy removal is blocked by policy and production needs the listed external inputs; do not revive closed private building cases or promote local/fixture acceptance to production.

Historical material below retains its original scope.

---
# R3 launch task accepted — 2026-11-05

**Current task:** turn the R2 internal candidate into a real website + desktop commercial Beta. Read the [R3 execution book](execution/KSTUDIO_R3_LAUNCH_EXECUTION_20261105.md), [owner inputs](execution/KSTUDIO_R3_OPERATOR_INPUTS_20261105.md), and [Codex start](execution/KSTUDIO_R3_CODEX_START_20261105.md).

The owner now explicitly authorizes deployment, phone/WeChat login, account-owned encrypted API settings, BAI platform service, domestic payments, packaging and a complete first-use acceptance. Reuse the existing Harness, UI style and cloud/OIDC foundation. This supersedes older stage restrictions against cloud/auth/payment work and research-only next steps; original-model, credential and evidence protections remain. Do not revive closed private building cases or perform endless quality experiments.

**This handoff is documentation only.** R2 PR25 source baseline is `7376f40f678e81618cbd9b470e2f5ba39debeaac`; installed build05c source remains `9c0ef028d127da44389296c4de913c16b5372dfe`. No R3 deployment, live identity/payment acceptance, new installer or native first-use test is claimed by this commit. Public release remains unproven until the execution gates actually pass. Handoff branch: `codex/kstudio-r3-launch-handoff-20261105`; implement on an isolated R3 branch, not main by default.

Everything below is preserved historical evidence and authorization context. The R3 execution book controls the new task; applicable existing test authorization is retained and is not expanded into cloud purchases, automatic recharge or charging third parties.


**Implementation started 2026-11-07:** preserving the latest R2 build07 fixes and evidence below; R3 production remains NOT_DEPLOYED pending implementation and verified external inputs. Raw videos from the Nov7 simple-house test were subsequently deleted at the owner's request; historical hashes/screenshots/models remain, and that geometry case is closed.

---

# Latest checkpoint — progressive construction, installed build07 — 2026-11-07

Desktop K Studio R2（内部候选）now uses installed build07 seq7, source `6f3fbf273c32dd9993daa0dbf413d8f0236ae01d`. [Candidate/artifacts](releases/KSTUDIO_R2_INSTALLED_20261107.md), [actual evidence](test-results/windows/2026-11-07-progressive-building-and-recovery/README.md). New independent project `architecture-project-7d1b1`, root19/r7: six actual construction stages, same-root stop/resume, one natural scoped correction, actual browser download and host native deep equality PASS; six protected parts unchanged. Existing earlier r8 project preserved. 78 focused tests pass. 20 raw videos indexed on E. Architectural fidelity remains PARTIAL, public release NOT READY. BAI configuration persisted. No unattended paid run remains; this one-time batch is complete.

Below is preserved history; earlier build05c is no longer the newest installed version.

---

# R2 installed build05c and real BAI continuation — 2026-11-05

**Current final checkpoint:** [installed candidate and exact artifacts](releases/KSTUDIO_R2_INSTALLED_20261105.md). Desktop **K Studio R2（内部候选）** now launches installed `r2-internal-05c-seq5`, source `9c0ef028d127da44389296c4de913c16b5372dfe`. Actual BAI same-image first model reached r5, protected wood-soffit edit reached r8; browser download/native deep equality and 14 protected parts passed. Actual two SU2024 windows were selected independently in the UI, foreground changes did not reroute, and closing one did not fall back to the other. New empty API profile and existing encrypted owner BAI persistence passed. Public release remains **PARTIAL / NOT READY**: visual fidelity, clean second PC/more SU versions, signing/licensing and actual production services are not fully accepted. No automatic paid continuation is left running.

Read [first model evidence](test-results/windows/2026-11-05-bai-stair-building-first-pass/README.md) and [installed edit/connection evidence](test-results/windows/2026-11-05-installed-bai-edit-and-connections/README.md). Subsequent owner testing should use the original `architecture-project` r8, preserve its r5/r8/checkpoints, and select its existing safe model in the bottom-right modeling tools. The temporary empty dual-window test project remains in history; its SU window was intentionally closed. Do not confuse that expected disconnected project with the connected original model.

Below is preserved historical checkpoint text; its build04/in-progress/no-paid statements are superseded by the dated final checkpoint above.

**Latest owner continuation, 2026-11-05:** owner now explicitly authorizes BAI real-model testing without a monetary ceiling, until available balance is exhausted, and asks for a more complete release candidate. This supersedes the paid-test defer below. Use purposeful bounded experiments, record actual/unknown usage, stop on authentication/balance failures or unresolved native commits, never recharge or silently switch provider/model. Continue the actual K Studio user workflow and preserve all previous failures. No production merchant charging/public deployment is implied. First current build04 real BAI image discussion completed and stored a plan; geometry/build/edit/delivery acceptance is in progress. New independent engineering improves API error/state UX, explicit SU instance selection and distribution-source evidence.

**Subsequent owner self-test diagnosis:** the empty candidate API configuration was restored from the owner's existing encrypted BAI connection through the actual UI, without inference or changing the old vault. A selected Studio session differed from the session owning the open SU model; current reconnect entry identified, no geometry changed. Arbitrary SU window selection is not implemented. [Actual diagnosis and limits](test-results/windows/2026-11-05-candidate-api-and-session-diagnosis/README.md). One prepared benchmark project now contains a user-attempted unavailable-provider failure; preserve that history, do not treat all six as untouched.

**Earlier owner decision, superseded by the continuation above:** preserve the current candidate; do not perform paid testing for now. The six-run proposal is DEFERRED_BY_OWNER, not awaiting an immediate answer. Keep prepared projects/images and historical evidence unchanged. No automated paid continuation or repeat authorization request; resume paid work only after a new explicit owner instruction. This decision supersedes the pending-authorization wording in earlier checkpoint records below.

Current task is the owner's adopted R2 execution book, on isolated branch `codex/kstudio-r2-public-beta-20261104`, based on PR24 `ef52a76f7bda15d59939369da200b3e55778f0a6`. Original workspaces and historical models remain preserved. This entry supersedes older next-step instructions without changing their results.

Read [execution](execution/PUBLIC_BETA_EXECUTION.md), [acceptance](execution/PUBLIC_BETA_ACCEPTANCE.md), and [external conditions](execution/PUBLIC_BETA_BLOCKERS.md). Current core regression: **1653 passed, 20 skipped**; source interface/cloud/offline SDK checks and six native connector fault cases passed. Actual browser-downloaded engineering SKP reopened with deep equality, then an owned copy accepted a scoped edit with KEEP unchanged. These are engineering fixtures, **not new image-modeling quality PASS**.

The [internal candidate and artifact hashes](releases/KSTUDIO_R2_INTERNAL_CANDIDATE_20261104.md) are ready. Final installed build04 seq4 is running from a separate desktop shortcut; real upgrade/rollback/reissue preserved 37 protected files. API restore/removal, six prepared source projects, single instance and read-only SU2024 connector checks passed. Actual Docker image build/restricted-container HTTP smoke passed in GitHub run41871824820; no image was pushed or deployed. Clean-Windows check kit and deployable cloud source are packaged.

Public beta is **NOT ready**: new live-provider/source-quality benchmark, clean second Windows, production identity/payment/hosting/signing and licensing decisions remain external gates. At the earlier build04 checkpoint, no new paid inference, production deployment, customer charge or main merge had occurred. The latest continuation now authorizes real BAI tests; the prepared [finite six-run proposal](execution/R2_FINITE_TEST_BATCH.md) remains historical and is not claimed executed. Do not transfer engineering PASS to building quality. Original private sources/models and old shortcuts remain preserved.

---

# Historical public update — 2026-11-03

Latest source candidate: **K Studio / K Harness local desktop candidate**.

Read [release notes and continuation entry](releases/KSTUDIO_LOCAL_CANDIDATE_20261103.md) for implementation, source entry points, dependency versions, actual test evidence and limits.

Local Windows / SketchUp 2024 workflow passed: BYOK persistence, real UI modeling, interruption continuation, scoped edit, SKP download/native reopen and desktop restart. Source fidelity remains PARTIAL; clean-machine/multi-SU/multi-provider/public-installer acceptance is NOT complete.

The release notes deliberately omit personal connection settings, credentials, private source images, native models and raw session logs. Older case documents retain their historical scope and verdicts.
