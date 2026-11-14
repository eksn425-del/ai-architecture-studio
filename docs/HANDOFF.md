# 2026-11-14 R3 商业内部候选交接

[最终发布裁决](release-gates/FINAL_RELEASE_VERDICT.md) 保存 G00–G11、失败和外部条件。桌面与部署源包固定 `d097b1a`，安装器文件沿用 `32c970b` 已验输入。云端逻辑与通过 PostgreSQL 验收的 `e470797` 一致。E 盘隔离试验未覆盖原安装和历史工程。后续本机桌面操作使用已授权的 Windows Computer Use 插件。 [版本与哈希](release-gates/RELEASE_NOTES.md) · [续跑](release-gates/OPERATIONS_RUNBOOK.md)

# 发布前实机交接 — 2026-11-14

实施分支 `codex/kstudio-r3-launch-20261105` / PR27。[训练、开源方法与原生交付证据](test-results/windows/2026-11-14-r3-release-training/README.md)。实测启动连接与多次重开保持一个 SketchUp 2024 窗口。窗样板读取实际孔洞和玻璃退深，再复用到四个开间。r11 纠正梯向并保留其他 13 个部件，r12 只修梯身，17 块踏步原位保留，最多 123 毫米穿出消除到 0，锯齿与踏板底最大间隙 0.5 毫米。r12 下载重开后 1,983 条面记录相同。门槛高差、材料和整体保真为 PARTIAL。

原始作业位于项目 E 盘 `outputs/video-storage/jobs/kstudio-launch-training-20261114`。发布审查目录提供脱敏回执、六视图、对照与用量。保留第一个楼梯回合的输出截断及后来方案反复校验、取消留下的 1 条未知用量。新批次合计 93 条已结算用量，无活动付费回合。beta07 本机包固定 E 盘，已构建、SHA 已验证、打包首次空白 Profile 启动通过。现有 beta03 安装继续使用原有程序路径和 Profile。公开部署和客户干净机验收等待[外部资源和发行门槛](execution/KSTUDIO_R3_EXTERNAL_INPUTS_STATUS_20261107.md)。

# 开源样板采纳交接 — 2026-11-14

PR27 源码 `a532096ce0d95d1f00d8d9cb789a8f9134b4da16`。[参数化窗开间记录与六视图](test-results/windows/2026-11-14-oss-window-bay/README.md)。现有 `sketchup_apply_parts` 增加 `window_bay`，安装器清单校验几何实现及 Apache-2.0 许可文件。E 盘独立样板 `kstudio-oss-window-bay-20261114` 保存 r1–r3、已中止事务、回执和原始模型。最终 r3 节点原生重开通过；没有端到端客户端或 BAI 选用证据。桌面安装版仍为 R3 beta03。以实际新案例测 Agent 何时选用该构造，保留旧模型与账本。

# 当前候选：模型质量、原生交付与持续建模 — 2026-11-14

PR27 继续使用 `codex/kstudio-r3-launch-20261105`。起点为 `1ca90f4815a550b4ac1f03d2d5ccf196f5240105`。已有两个原项目和历史账本逐项核对保留；所有测试工程、原图、SKP、原始检查点和详细日志在项目 E 盘 `outputs/video-storage/jobs/kstudio-quality-training-20261114`。

- [退台高塔 r8/r9](test-results/windows/2026-11-14-stepped-tower-r9/README.md) 实测确认旧副本渲染目录未配对、截图异常会挡住当前交付件。修复后 r8 更新预览和下载通过。BAI 在同一副本提交 r9，调整两块楼板前缘至 4 / 8 米。下载件在 SU2024 原生重开一致；整体源图保真 PARTIAL。
- [文昌灯塔 r11→r13](test-results/windows/2026-11-14-wenchang-r13/README.md) 第四梯段的 600 毫米错台消除，实际全宽接边 1,100 毫米。栏板方向纠正，前面罩开口去掉 35 个面，内层玻璃和另 25 个直接系统的深层签名不变。当前 SKP 已下载和原生重开。折面、边线和乳白质感仍 PARTIAL。
- [新图砖木工坊 r1→r13](test-results/windows/2026-11-14-arts-workshop/README.md) 用同一 BAI DeepSeek Flash 高推理请求走完实际页面计划、原生阶段建模、局部楼梯返工、下载和重开。在 r13 实测踏步与平台板边 1,350 毫米、平台与楼板门宽范围 1,200 毫米。17 个上向踏面位置保留，其余 16 个直接系统通过深层 KEEP 核对。两轮保存的 SKP 都能原生重开。多开窗口后的自动选择仍需一次手动选择。参考图右侧开间读图、砖木材质及首级 250 毫米高差保留为 PARTIAL。
- 源码修复提交 `d97a2a37a61edbdf6f003b05ab56941160c25dbb`。截图配对只关联验证过的项目渲染目录。写入提交和预览分别出回执。建筑 Skills 更新退台世界坐标复核、折面开口优先、各段楼梯的实际标高和连续接边；本次新图调用了 `sketchup_measure_level_joint`。这些是 Skills 和工程编排改进。
- 本批 BAI 账本 121 settled、0 新 unknown，实际扣费金额没有回执。文昌历史 88 settled＋2 unknown 与高塔历史 52 settled 原始行不变。新模型继续使用原有提供商，无切换或充值。评审只发布脱敏数据和原生截图。
- 下一验收继续复核侧立面、楼梯首级和门前几何，按同一输入做 K 增强与原生对照。干净 Windows、安装包、生产登录/支付按现有发布门槛验收。现有桌面已安装版本仍是 R3 beta03 sequence10，源码独立工作台没有替换已安装版本。

---

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
# R3 launch handoff — 2026-11-05

## Work completed in this handoff

Reviewed PR25 at `7376f40f678e81618cbd9b470e2f5ba39debeaac`, installed build05c documentation and current cloud/auth/device/payment/deploy source. Prepared the [R3 launch execution book](execution/KSTUDIO_R3_LAUNCH_EXECUTION_20261105.md), [owner input sheet](execution/KSTUDIO_R3_OPERATOR_INPUTS_20261105.md), and [Codex startup prompt](execution/KSTUDIO_R3_CODEX_START_20261105.md). Engineering, QA and first-user-perspective reviewers checked the task for feasibility and bounded acceptance. This was source/document review, not a live first-user test.

Chosen route: Tencent mainland CVM + existing Compose/FastAPI/PostgreSQL/Caddy, COS distribution, Authing-hosted phone/PC WeChat via existing OIDC, WeChat Native payments, BAI platform plus account-owned BYOK. Preserve the existing desktop visuals and Agent runtime.

## Next owner: local Codex implementation

Follow the execution book end-to-end on an isolated R3 implementation branch. Finish all available work before presenting one consolidated external-input blocker list. No main merge, live deployment, production SMS/WeChat/payment, clean Windows test, new paid inference, or new installer was performed by this handoff. Actual environment resources and secrets must be supplied through existing authorized private configuration; never publish them.

The owner now authorizes launch implementation and deployment. Historical pause/no-paid/build04 text below is archival, not the active instruction. Applicable prior BAI test permission is preserved within its actual scope; never infer permission for unlimited cloud purchase, auto-recharge or customer charges. Installed R2 build05c remains an internal candidate until new acceptance actually passes.


**Implementation started 2026-11-07:** preserving the latest R2 build07 fixes and evidence below; R3 production remains NOT_DEPLOYED pending implementation and verified external inputs. Raw videos from the Nov7 simple-house test were subsequently deleted at the owner's request; historical hashes/screenshots/models remain, and that geometry case is closed.

---

# Latest 2026-11-07 handoff

Read [CURRENT](CURRENT.md) and [build07 evidence](test-results/windows/2026-11-07-progressive-building-and-recovery/README.md) first. One-time progressive-building batch complete; preserve root19/r7 and earlier r8. No paid loop. Internal candidate, not public-release acceptance. Historical handoff follows unchanged.

---

# Public continuation

**Owner update 2026-11-05:** keep the installed internal candidate and defer paid testing. Six prepared projects remain NOT_RUN; no paid request is authorized. Do not automatically resume the batch or repeatedly request permission. Earlier pending-authorization text below is historical.

Start with [CURRENT](CURRENT.md), [R2 candidate/artifacts](releases/KSTUDIO_R2_INTERNAL_CANDIDATE_20261104.md) and [execution](execution/PUBLIC_BETA_EXECUTION.md). The isolated branch now provides installed internal build04, real updater/data-preservation receipts, deployable cloud source, restricted-container CI and clean-Windows kit. Final public-beta acceptance is not established. Six same-source live-test projects await finite-batch authorization; no new paid inference occurred. Exact external actions are in [blockers](execution/PUBLIC_BETA_BLOCKERS.md). [2026-11-03 release notes](releases/KSTUDIO_LOCAL_CANDIDATE_20261103.md) remain the historical baseline. Preserve prior failures and do not transfer old model success to this revision. Private images/models/credentials/raw logs remain local.
