# 最新本机交接 — Dream Coffee 新整图 × OSS 实用化（2026-10-10）

[完整公开证据](test-results/windows/2026-10-10-dream-coffee-oss/README.md)。实际 gpt-6-luna/max、SU2024 24.0.484、Kongxing单writer、ADAI0.5.39 opt-in。用户最新五面板图整幅上传，原图私密未公开，未替换旧案例。网站正式主模型PID35529/r3/110对象，SAIE墙洞与ADAI九条檩条真实调用/提交读回，ledger/adoption公开，效果仍非PASS。

**技术通过**：三份计划schema、三笔写后校验、KEEP、六方向同r3、实际OSS方法调用、网站下载原生重开/鼠标移PLANTERS/保存再开（其余109组不变）、同步baseline后第二个新空白110名称/bounds一致、受控SyntaxError回滚。检查324passed/2skipped。

**PARTIAL/FAIL保留**：漏上层平雨棚、木饰面/柱廊与比例不准、canonical留白多、r3室内匹配未补；独立终审NEEDS_FIX:YES。Builder整回合903172ms超时，最终只读审查由操作者另行恢复；规划/Builder输入10.504M，无降本PASS。首次baseline两玻璃组不一致FAIL已保留。初次MCP无回执留下空根，真实历史原因未证实；操作者仅重开专用空白、修回滚，Native重试建模。原生编辑只下载副本；主模型无人手动改几何。

已修 model_session.rb异常回滚+结构测试；持久生成脚本玻璃框尺寸同步，重新空白重放验证。新 evidence含真实PNG/sidecar、前后图、模型/方法账本、KEEP、下载/编辑、源脚本、所有错误、每轮tokens与延时、SHA256清单。私密原图/SKP/个人路径/Key不提交。ADAI separate MCP未调用，不把smoke计成正式产品效果。

**下一轮唯一可执行任务**：继续本次Dream Coffee新图的主附体/雨棚/柱廊/木饰面质量，控制规划和结束阶段工具循环/上下文，改善构图并补当前室内source pair；真实两轮定向修正、KEEP、同步baseline再重放、完整公开证据。不要回旧咖啡店/别墅或新增CAD/PPT。

---

# 当前下一轮唯一执行任务 — 新建筑参考图 × 开源能力实用化（2026-10-10）

**最高优先级（覆盖下方所有旧咖啡店 r5、旧白色别墅、Sol Low 的历史“下一轮”安排）：** 用户下一次将给 Codex **另一栋建筑的参考图片**。Codex 应先同步最新 `main`、检查本轮新增的 capability catalog／guarded SAIE+ADAI method trace／adoption assessment／GitHub 证据校验，然后使用**新图**在同一个 K AI Studio 网站开展真机建模和真实开源方法复用测试。**现在尚未收到新的图片，不得自行选择旧任务素材启动建模。**

**完整下一轮操作书：** [`docs/NEXT_ARCHITECTURE_TEST_WITH_OSS_ADOPTION_2026-10-10.md`](NEXT_ARCHITECTURE_TEST_WITH_OSS_ADOPTION_2026-10-10.md)

**永久双层产品原则：** [`docs/CONTINUOUS_CAPABILITY_ADOPTION_2026-10-10.md`](CONTINUOUS_CAPABILITY_ADOPTION_2026-10-10.md)：主动吸收有价值的稳定实现改进产品底座，同时每次真实任务依据任务条件选择、真实调用并验证效果。这一规则不限于 SketchUp，今后适用于 CAD、Web、视频等产品。

**已在远端 main 实现的第一版代码：** `app/oss_method_catalog.py`（具体 OSS 方法/许可/适用范围），`app/oss_method_runtime.rb`（真实 SAIE／显式启用 ADAI wrapper 调用事件），`app/project_ruby.py`（SKP owned-root 当前 revision 的调用记录和选用/执行评估读回），`app/agent_tools.py`＋`app/image_to_sketchup_skill.py`（真实建模提示），`app/construction_strategy.py`（可记录每个系统具体方法与理由），`scripts/validate_test_evidence.py`（新批次必须有 OSS 实际调用/零调用证据）。现有独立 GitHub Actions 已对 Python/Ruby 方法合约自动回归；**Windows 真实模型新调用链尚未测试，不能算已经验证产品建模效果。**

**这次真机重点**：可用的 GPT-6 Luna Max/Codex 实际型号、全新源图、多种组件按适用性选择或解释未选、真实 SU2024 受守护几何调用记录、单一项目持久 SKP、最多两轮局部修正、KEEP、独立 Critic、六视图+源角度、完整读回/native reopen、每轮 token/错误与新一套 GitHub PNG/JSON 证据。**不得为了让 ADAI 有调用量而强制调用不适用方法；但不得再以单纯安装或 smoke 代替真正产品使用。**

**相关缺陷**：[Issue #3](https://github.com/eksn425-del/ai-architecture-studio/issues/3)。在下一轮 Codex 真机与图像质量证据完整之前 Issue 保持开放。

---

# 新发现的 P0 产品级缺陷 — 开源方法未进入真实 Agent 建模（2026-10-10）

**用户审计结论：**我们过去把外部开源项目“研究、下载、引入、通过烟测”当作集成成果，却没有确保它在**下一次真实 K AI Studio 工作流**中被明确选择和调用。这是 Agent 执行策略/可观测性/验收的缺陷，不是证明 ADAI 无法工作。新的工程问题：[Issue #3 — OSS method selection + runtime invocation receipts](https://github.com/eksn425-del/ai-architecture-studio/issues/3)。

**已验证的现状：**本仓库 `app/adopted_sketchup_helpers.rb` 真正使用 MIT SAIE/Stultus 源；ADAI 0.5.39 的 `profile_with_holes`/非平屋面**独立真 SU2024 smoke** 已通过，但正式咖啡店实际 `adai_actual_calls=0`。原因可在代码核对：`app/adai_components.py` 只在 `ARCH_STUDIO_ENABLE_ADAI_GEOMETRY=1` 时加载；`app/agent_tools.py` 仅追加可选 ADAI 说明并继续提示优先 SAIE；`app/construction_strategy.py` 只记录抽象方法类别而不记录实际 OSS provider；当前没有 writer-revision 级的真实方法调用归因。最新咖啡店仍存在叠层屋顶、3组 baseline bounds 不符、10.53M input tokens / 1800s timeout；不能把调用次数当作模型质量。

**下次本地 Codex 开始前优先阅读 Issue #3** 并实现最小可验证的 **OSS 方法候选 → 按适用性路由 → 有来源的选择理由 → 原有单 writer 事务内真实调用记录 → 关联 writer receipt/效果/失败原因**。与下方当前两图咖啡店修正任务合并完成，不要额外开一个纯工程 demo 来冒充产品落地。采用合法、兼容且适用的成熟方法；若本次构件并不适用 ADAI，应记录具体原因/失败，保留旧 SAIE/Ruby fallback，而不是强制所有外部工具各调用一次。**严禁本次只再写一份“要重视开源”政策文档而不修改实际路由/遥测与测试**。

**本条为下一轮 P0 任务补充**；下方咖啡店屋顶原位修正、baseline replay、完整真实截图/指标/新 SHA 上传要求继续有效。**目前 Issue #3 只是已经登记，代码层的路由与调用凭据尚未实现，不能说缺陷已修复。**

---

# 最新交接：咖啡店体量修复 r5（2026-10-09）

[完整公开证据与错误](test-results/windows/2026-10-09-cafe-massing-repair/README.md)。实际 gpt-6-luna / max、SU2024 24.0.484，网站同模型两笔定向修正，根 PID51007、34组。写入/KEEP、六方向同r5、三次独立只读 Critic、下载副本原生重开鼠标改菜单保存再读回 PASS。自动检查316 passed / 2 skipped。

**仍 PARTIAL/FAIL**：附体比例/石质外缘不准；误用 KEEP 导致新增屋顶叠层，独立 Critic 漏检。Native完整回合30分钟超时FAIL，Builder输入10.53M，不能声称降本；新空白baseline3组bounds不一致FAIL；Agent改后规划JSON出现额外尾部，已保留坏文件。ADAI本轮调用0，修正Ruby，未把安装当使用。

已修代码：体量inventory指导、fresh read-only无writer Critic、token线程本轮增量。补充KEEP材料≠尺寸/禁止叠层指导仅测试覆盖，尚未真机验证。未修改原始模型，鼠标编辑仅专用下载副本。详情与版本、人工介入、所有真实截图见报告。

**下一轮唯一任务**：同两图咖啡店，原位修旧屋顶和附体/石质外缘，合理KEEP；写后校验三份规划；同步持久baseline并新空白重放；约束记录/结束阶段无限工具循环与超时。重新跑真实两轮修正预算，不用第三轮伪装本轮PASS，不扩CAD/PPT或回旧别墅。独立Critic仍须审查叠层并保留诚实结论。

---

# 当前输入更新 — 用户双视角咖啡店 / Luna Max / SU2024（2026-10-09）

## 本轮已完成 / 下一轮入口

当前两图咖啡店已在网站完成真实 `gpt-6-luna` / `max` 建模、两次局部修正和 r3 六方向截图。完整公开证据：[咖啡店报告](test-results/windows/2026-10-09-cafe-two-view-luna-max/README.md)。三笔 write_verification、下载副本 SU2024 原生打开、鼠标移动菜单立牌、保存再次打开、其余30组不变均 PASS。第一次新空白重放因基脚端点差60mm FAIL；同步持久脚本后，另一个新空白重放31组名称/bounds全部一致 PASS。恢复回合第一笔写入故意破坏 KEEP 屋顶被提交前拒绝。最终自动检查 **314 passed / 2 skipped**。

**视觉仍 PARTIAL**：右后低白墙/低屋顶附属体量不足，主屋顶/木饰面比例、桌椅和铁艺/纹理细节不准确；第二次修正添加植物屏遮人物的策略错误，挡住来源特征。独立 Critic NOT_RUN，实际为 Builder 自审且 NEEDS_FIX:YES；Native token null，不能声称降本。已用完本轮两次修正，不以第三次修正或降低标准改成 PASS。

下一轮只继续同产品的图片还原：先落实主/附体量 inventory 与来源角度比对，再改善遗漏附属体量和比例；实现并实测独立只读 Critic 与可靠 Token 计量；验证新 workspace v11 的 QA 指引能阻止遮挡配景式修正。新 AEC 空白模板已实测不带人物。桌面安装包与源码版本一致性仍待确认。不要回到旧别墅代替用户当前咖啡店，也不要扩展 CAD/渲染/PPT。

以下“继续完成”段落记录执行开始状态，已由上述结果更新。

用户本机明确纠正：**当前应该建新发的两张咖啡店图，不继续旧白色别墅。** 这条最新用户输入覆盖下面旧六视图任务的素材选择；保持同一网站、Native 模型、Kongxing 单写者、ADAI opt-in、最多两轮局部修正和 GitHub 证据契约，不扩建 CAD/渲染/PPT。

实际 `gpt-6-luna` / `max` 已由宿主 catalog 和 Native turn 配置确认。新会话“双视角咖啡店 · Luna Max 1009”已在网页上传两张完整原图、明确单层/估算/合理补全/可见全部细节，完成规划三份 JSON 严格校验并代批准，进入 SU2024 独立模型建模。私人两张原图只保留本机 ignored runtime，不提交；公开结果必须记录此限制，提交真实模型 PNG/receipt/readback/QA。

本轮已发生的旧别墅结果不得丢弃：[新证据目录](test-results/windows/2026-10-09-kai-integrated-v1/README.md)。r3，277 对象，六图同 revision，ADAI 两洞墙/非平屋面工程 smoke、KEEP precommit abort、下载 hash 和原生重开通过；视觉 PARTIAL，独立 Critic NOT_RUN，Token null，用户改目标前未进行该别墅鼠标编辑/重放。自动检查 313 passed / 2 skipped。

继续完成当前咖啡店：真实可识别主形与细节 → canonical 六方向及高/低两种来源角度 → 如实 review/最多两次 targeted correction → 下载副本原生打开、鼠标编辑一个命名对象、保存再重开读回 → 新空白 baseline replay → 新证据目录/检查/HANDOFF/commit/push。不要重新改测旧别墅，不用连接成功代替视觉验收。

---

# 历史本轮任务 — K AI Studio / GPT-6 Luna Max × Codex Native × ADAI SU2024 真机建模（2026-10-09）

**本任务覆盖下方所有历史“继续 Sol Low”“旧版 ADAI 尚未合并”等规划段落。** 用户本轮要求以 [Codex 最新提交 `98c9aec`](https://github.com/eksn425-del/ai-architecture-studio/commit/98c9aec11c283879ab0bc2e9afc587f6729cdec6) 和 Sol Low 实测证据为起点，使用 Codex **实际可选的 GPT-6 Luna Max / 最高能力模型**，在**已融合 ADAI 的 K AI Studio 网站**完成新的一次真实建筑建模，并将结果/数据/真实六方向 PNG **全部上传本仓库 GitHub `main`**。此后每一次测试都遵守相同规则。

**执行说明（Codex 首先打开）：** [`docs/NEXT_NATIVE_TEST_GPT6_LUNA_MAX_2026-10-09.md`](NEXT_NATIVE_TEST_GPT6_LUNA_MAX_2026-10-09.md)

**永久证据契约：** [`docs/TEST_EVIDENCE_PROTOCOL.md`](TEST_EVIDENCE_PROTOCOL.md) 和 `scripts/validate_test_evidence.py`，仓库 `AGENTS.md` 已将每轮上传 PNG/metrics/错误/模型读回设为必需。

### Codex 执行顺序（简单工作清单）

1. 先 `git pull --ff-only`、检查 `AGENTS.md`、上次 [SU2024 Sol 实测报告](test-results/windows/2026-10-09-quality-loop-v25-sol/README.md) 与最新 HANDOFF。上轮 304 passed/2 skipped、precommit KEEP abort 真机通过；**建筑 fidelity PARTIAL**、`reviewer.mode=agent_supplied`、Native Token 缺失、ADAI 原生调用 NOT_RUN。这些是必须对齐的事实。
2. 模型首选 **Codex 中真实可用的 GPT-6 Luna Max 和高推理档**；如果不支持则选 Codex 最高可用模型并完整记录 actual model ID。不得因旧任务而静默改用 Sol Low/DeepSeek，不需要旧新版 A/B。
3. 在测试空白 SU2024 实测 ADAI helper（真正建连续墙多洞口和复杂屋面），通过原有 Kongxing 单写者和 KEEP/回滚，别让 ADAI Managed MCP 并发控制同一模型。
4. 使用仓库公开 `test-assets/cloud-villa/villa-six-view-sheet.png` 在**网站中新开一轮真实完整建模**。规划证据/schema 有界修复、六方向来源一致、最多两次定向修正、单独 Critic（若实际上做不到，必须注明自审并保留 PARTIAL）、重新打开下载版 SKP 并测试可编辑。
5. 必须上传 `docs/test-results/windows/2026-10-09-kai-integrated-v1/`：README、run.json、metrics.json、errors.json、六张真实当前 revision PNG 与 sidecar、source-perspective PNG、schema/KEEP/writer/原生重开/审查结果。用 `scripts/validate_test_evidence.py` 生成并验证 SHA256 文件清单。任何材料无法获取应真实记录 FAIL/NOT_RUN，绝不伪造截图、价格、Token 或独立 Critic。
6. 所有关键改动完成后跑 `scripts/check.ps1`，更新 HANDOFF 与本任务的最新状态，commit + push `origin/main` 并确认远端 SHA 和公开结果目录。回报结果/证据链接，让 ChatGPT 下一次直接读真实数据和截图判断下一步迭代。

**本轮不要求 2018–2026 九个版本全部通过，不做 DeepSeek vs ADAI A/B，不扩建独立网站，不改原始私人 SKP。实际视觉匹配优先于 synthetic PASS。**

### 最新产品方向补充 — 建筑学长「体块 → SU 深化 → 多方案 → 全链路输出」案例（2026-10-09）

用户提供建筑学长 GPT-6 Astra 的商业办公综合体工作流视频转写作为**未来 K AI Studio 的战略参考**。已将真实能力与计划中的能力分开写入 [产品路线文档](PRODUCT_DIRECTION_REFERENCE_TO_NATIVE_SKETCHUP_2026-10-09.md)。

**本轮唯一执行优先级不变：**现有 K AI Studio 网站 × Codex 真实可用高能力模型 × ADAI 几何 × SU2024，使用已公开的白色别墅六视图改善**原图比例、连续墙真开洞、屋顶/女儿墙与墙顶拼缝、材料/细部、六视图相机和局部截图修正**；仅编辑可丢弃模型，实际六张截图及证据按协议提交 GitHub。重点借鉴“**清楚的设计约束 → 主模型深化 → 截图指出问题 → 定向修正 → 回到同一真实 SKP**”，不是测试竞品，也不是开始开发 CAD/渲染/漫游/网页 PPT。

**后续 P1** 才在保障项目模型安全的前提下开发“从现有 SU 白膜/地形起步 + 红线/层高硬约束 + 同一基线多方案分支”。当前 `app/project_ruby.py` 只能直接操作属于项目自己的 `blank-disposable-` 模型，不得为演示便利而取消防误写限制或操控用户原始白膜 SKP。**P2/P3** 的 CAD 图件、渲染、动画、交互汇报暂列路线，不属于本轮 Codex 的工作范围；尺寸合规与施工图需独立专业校验。



---

# 当前任务 — 2026-10-09 Windows 实测后继续质量迭代

本机 Codex 已执行下列历史任务的主要真机检查，并修复运行故障。用户最新指定 **GPT-6.1 Sol Low**；不要擅自改回 DeepSeek/Astra 来隐藏流程缺口。阅读 [本轮完整证据与验收报告](test-results/windows/2026-10-09-quality-loop-v25-sol/README.md) 和最新 HANDOFF 后继续。

最新远端 `1389864` 的统一产品/ADAI opt-in、v2.8/v2.9 工作已合并，未替换 Kongxing；最终自动测试 304 passed / 2 skipped。新增真 SU2024 工程 smoke 已证明 v2.8 precommit KEEP 回滚成功（revision/object/script 保留），v2.9 history 能随提交和下一次 review 更新。ADAI helper 原生 smoke、独立 Critic 驱动 repair memory 的建筑质量改善尚未执行，继续按下方 unified product 主线补齐；不要把旧 v2.6 提交后负例与新 v2.8 abort 混淆。

已完成：SAIE 两面连续墙各三个洞口；真实 canonical 六方向与错标拒绝；KEEP 正/负检测；单图咖啡馆、完整六视图别墅真实建模和最多两次定向修正；两项全新空白 baseline replay；网页下载与原生 SKP 打开；咖啡馆测试副本鼠标编辑、保存、再次读回。源码、Skill、transport/receipt 的修复和自动回归已提交。

**未完成整体视觉验收，仍 PARTIAL。** 别墅家具/植物、墙顶拼接线、比例/场地不足；咖啡馆也有家具/植被/材质差异。单图为用户咖啡馆附件，多视图为仓库白色别墅整图；没有咖啡馆完整六视图，未伪造同建筑六面验收。

下一轮只继续当前图像重建质量闭环，优先执行：

1. **Native 规划契约与独立审查**：此次 strategy 修复后 valid，但 evidence JSON 被 Native 直接写坏，旧 loader 静默返回 None。严格 review 拒绝与 schema 文档已修复；验证模型下一次能自动生成合规 evidence/facade/strategy，补齐有界内部修复，不让用户重复确认。实现/验证 Sol Low 独立只读 Critic 后再称完整闭环，不能把 Builder 自审当独立 Critic。
2. **真实源图缺陷**：针对报告截图的墙顶拼缝、门窗/阳台比例、家具/植被方法继续局部改善，保留当前 root/KEEP，最多两次定向修正；不以移除质量约束或白盒模型获取 PASS。没有私人咖啡馆原图时使用仓库公共整图继续；需咖啡馆像素复验时向用户索取原图，不能要求云端读取私人路径。
3. **可计量与策略真实性**：捕获 Native 每轮 token（当前 null 表示集成未记录，非零费用），记录工具/延迟；正确维护 strategy current_stage/status。不要把不同 provider/素材的运行直接比较成降本成果。
4. **构图及恢复**：canonical 当前方向正确但场地放大了 root bounds、建筑偏小；改进 building-focus，同时保留认证。KEEP 负例检测到回归但已提交，不自动 Undo；受控恢复必须另做 throwaway 真机验证。
5. 完成后重做新空白 replay / SKP 原生打开编辑保存，检查桌面安装包与源码服务一致性，更新公开结果/HANDOFF，commit + push main。

没有非私密完整 CAD＋平面＋室内包，full-evidence 仍 `pending_external`。原 DeepSeek 独立 Critic/受控成本 benchmark 因用户切换模型未完成，不可回填 PASS。下方历史定义保留作技术背景，不覆盖以上本轮实测状态。

---

# Current task — K AI Studio unified product mainline (2026-10-09)

**Owner decision:** All future suitable open-source capabilities should improve the **same K AI Studio website** in `eksn425-del/ai-architecture-studio` rather than creating separate first-party product repositories. ADAI 0.5.39 is the first combined capability. Details: [one-product and open-source policy](ONE_PRODUCT_OPEN_SOURCE_POLICY.md).

**Merged baseline (2026-10-09):** [ADAI PR #1](https://github.com/eksn425-del/ai-architecture-studio/pull/1) was merged into `main` as `4a1d027ab4da693388cce0975cd6241181634b9e`. Its official-download/verified geometry helper is present as **opt-in and default-disabled**. This merge does **not** mean ADAI-assisted native SU2024 execution passed or SketchUp 2018–2026 compatibility is certified. Keep Kongxing's verified single writer, model identity, approvals and KEEP protections. Do not auto-install/activate the alternative ADAI MCP against a live K Studio document.

## Next implementation (K AI Studio, not a separate ADAI project)

1. Pull latest `origin/main`; confirm clean worktree and read `AGENTS.md`, `docs/EXECUTION_GUARDRAILS.md`, `docs/ONE_PRODUCT_OPEN_SOURCE_POLICY.md`, and latest `docs/HANDOFF.md`.
2. Fix user-visible image-to-editable-SketchUp reconstruction weaknesses in the **combined K AI Studio codebase**: roof/parapet outlines, clean wall/window openings, reference-based proportions, repeated modules, facade features, and source-matched six-view QA with targeted corrections. Prefer mature imported helpers and small adapters instead of standalone new websites.
3. When real Windows + SketchUp 2024 is available, run a **minimal disposable native integration smoke** with the opt-in ADAI geometry helper: build one opening and nontrivial roof; current-camera evidence; guarded edit/KEEP rollback; SKP save/reopen/edit. Mark actual results PASS/PARTIAL/FAIL; this is ordinary product validation, **not** a mandatory old-K-Studio-vs-ADAI A/B benchmark.
4. Treat SketchUp 2018–2026 as gradual explicit-version compatibility work. Check plugins/available APIs and native reopen on each actually accessible version, otherwise `NOT_RUN`. Never claim nine-version certification based on detection or Python-only tests.
5. Maintain integrity-verified upstream releases and CPAL-1.0 attribution/source obligations. Feature-gate unverified components until product safety is demonstrated. Integrate future user-found upstream code into this same K AI Studio repo if the license and use case permit.
6. Do not hide the seven inherited full-suite failures by suppressing tests. Latest feature CI verified both ADAI release ZIPs, Ruby/PowerShell syntax, 8 ADAI tests, 290 passing branch tests and the **same seven pre-existing failures** on untouched main. Improve those tests independently where relevant.
7. Update the single repository's `docs/HANDOFF.md`, `docs/CURRENT_TASK.md`, actual test evidence, and licenses, then commit/push `main` after normal validation. Do not claim quality without real model evidence.

## Historical quality-loop milestones

# 当前任务 — 2026-10-09 Quality Loop v2.9 / Host Repair Memory

ChatGPT 继续对照 3DCodeBench 的 critique-history / last-known-good 与 SketchUp Agent Harness 的 project-local runtime memory。当前质量循环已经能独立 Critic、KEEP 保护、提交前回滚和上下文压缩，但旧 correction 历史被压缩后，Builder 仍可能忘记“刚才这个修法其实没有解决问题”，从而浪费第二次 correction 和大量 token。

main 候选新增 host-owned `qa/repair_history.json`：只有真实 committed correction 才记录 awaiting_review；下一次可信 visual review 才把它定为 accepted / still_needs_fix。Agent 只能读不能写。active-context compaction 会把最近几条可信 repair memory 带回当前请求，Skill 明确要求 still_needs_fix 的旧修法不能机械重复。它是 advisory memory，不覆盖 source / evidence ledger / facade schedule / 真 SU / 当前 Critic。

下一位 Windows Codex 直接执行 `docs/QUALITY_LOOP_V2_9.md`，并先完成 v2.8 的真 SU2024 pre-commit KEEP negative smoke，再继续 v2.7 staged six-view benchmark。重点观察 repair memory 是否真的减少重复无效修补、writer/tool/token，而不是因为多了一张 JSON 就宣称提升。

完成后更新 HANDOFF/CURRENT_TASK/test-results，commit + push origin/main，再交给 ChatGPT 复审。远端实现本身不等于真机 PASS。

---

# 当前任务 — 2026-10-09 Quality Loop v2.8 / KEEP 提交前回滚门禁

ChatGPT 在 v2.7 构造方法路由之上继续采用 3DCodeBench 的 last-known-good / do-no-harm 思路和 dcc-mcp-sketchup 的 write-contract 思路，把 v2.6 “提交后才发现 KEEP 被破坏”升级为真正的 **SketchUp transaction 内 pre-commit guard**。

现在 post-review correction 使用 preserve_paths 时，host 会先读取 protected path 的 persistent ID / direct child count / mm bounds，并作为不可由模型伪造的 host-only expectation 注入 ProjectRuby。同一 SketchUp operation 内，候选 Ruby 执行后、commit 前重新核对这些指纹；不一致直接 raise，model_session abort_operation，坏 revision 不应提交。失败候选 Ruby 会归档，persistent workspace script 恢复 last-good 版本。原有 post-commit KEEP readback 继续保留为第二道防线。

下一位 Windows Codex 直接执行 `docs/QUALITY_LOOP_V2_8.md`，并连同 v2.7 一起真机验收。最关键的新证据不是“测试通过”，而是 **故意修改 protected KEEP group 的负向 smoke 必须在 commit 前失败，revision 不前进，模型和上次成功脚本保持不变**。然后再做一次真实正向 targeted correction，以及新的六视图 staged-construction benchmark。

完成后更新 HANDOFF/CURRENT_TASK/test-results，commit + push origin/main，再交给 ChatGPT 复审。远端实现本身不等于 SU2024 真机 PASS。

---

# 当前任务 — 2026-10-09 Quality Loop v2.7 / 构造方法路由与分阶段建模

ChatGPT 已审查 ADAI SketchUp Skill + Managed MCP 0.5.39（`laowang-wy/adai-sketchup-skill-mcp@cd1e02e9`）。上游为 CPAL-1.0，本轮**没有复制/内嵌其 CPAL 源码**，而是把对当前 K Studio 最有价值的建模架构独立实现到现有单写者体系：先完整主形，再真实代表模块，再复制、变体、收尾；同时把“该系统应该用什么构造方法、依赖哪些共享参数、用哪些视图验证”外部化为项目内 `notes/construction_strategy.json`。

main 候选新增：结构化 construction strategy、工作区 JSON 校验、规划/执行阶段方法路由、active-context compaction 保留 strategy，以及对应测试。现有 v2.6 KEEP 无损修正、v2.5 主机认证相机、dedicated Critic、writer receipt、evidence ledger、facade schedule 都继续作为更高优先级质量门，不被新策略替代。

下一位 Windows Codex 直接执行 `docs/QUALITY_LOOP_V2_7.md`。重点不是证明“多了一张 JSON”，而是用同一六视图别墅验证：主形是否更完整、墙洞是否少拼缝、屋面是否选择更合适的 profile/mesh/custom Ruby 方法、是否先验证一个重复模块再复制、full-root rebuild/tool/token 是否下降、KEEP 是否保持。若 strategy 只是文书且 Agent 忽略，按真实证据继续改 host/Skill 或删减，不得因为测试通过就宣称建模质量提升。

完成后更新 HANDOFF/CURRENT_TASK/test-results，commit + push origin/main，再交给 ChatGPT 复审。远端改动本身不等于 SU2024 真机 PASS。

---

# 当前任务 — 2026-10-09 Quality Loop v2.6 / KEEP 无损修正门禁

ChatGPT 基于 3DCodeBench 的 last-known-good / do-no-harm 思路和 SketchUp Agent Harness 的“视觉反馈先结构化再修改”边界，继续优化当前建模质量闭环。

main 候选新增 post-review KEEP 保护：视觉审查后再写模型时，host 强制 update_mode=edit，禁止整根 replace/full rebuild；如果 Critic 给出了 KEEP，Builder 必须先把 KEEP 映射到当前 script_id 下的 exact named owned paths，并通过 preserve_paths 交给 writer。host 会在修正前后重新读取这些路径的 persistent ID、对象数和 mm bounds，任何变化都标记为回归，不能把这次修正当作无损成功。

下一位 Windows Codex 直接执行 docs/QUALITY_LOOP_V2_6.md，并同时完成 v2.5 主机认证六视图的真 SU2024 验收。重点验证：实际修一个 roof/wall 高影响问题时，阳台/格栅/已正确门窗等 KEEP 路径保持 ID/数量/bounds 不变；再做一个 throwaway negative smoke，故意动 protected path，确认 host 真会报 regression。完成后继续 fresh six-view critic、blank replay、SKP 原生重开编辑。

完成后更新 HANDOFF/CURRENT_TASK/test-results，commit + push origin/main，再交给 ChatGPT 复审。当前实现只做确定性回归检测，不自动 undo 已提交 revision；若本机证明该门禁有效，下一步才考虑受控 last-good 自动恢复。

---

# 当前任务 — 2026-10-08 Quality Loop v2.5 / 主机认证六视图相机

ChatGPT 复审 v1 真机结果与 v2.1-v2.4 代码后发现新的证据边界：此前六张截图虽然能校验“文件真实、修订最新、路径不同”，但仍然信任 Agent 自己把任意相机命名为 front/rear/left/right/roof/oblique。现在 main 候选改为由 host 的 `sketchup_capture_canonical_view` 根据当前持久 ProjectRuby 根组 bounds 生成固定六视图，并把 view 名、script ID、camera vectors、current revisions 写入 sidecar；六视图质量门只接受这种 host-certified canonical evidence。

本机 Codex 下一步先执行 `docs/QUALITY_LOOP_V2_5.md`，再继续 v2.4 单图/多视图真实 DeepSeek + SU2024 验收。重点不是增加功能，而是验证六个方向确实正确、构图不裁切，并继续使用 source-matched `evidence_pairs` 检查源图视角/室内细节。若 root 内超大场地导致 canonical framing 过远，记录并修 building-focus bounds，不要退回自由命名截图。

完成后更新 HANDOFF/CURRENT_TASK/test-results，commit + push origin/main，再交给 ChatGPT 复审。

---

# 当前任务 — 2026-10-08 Evidence Fidelity v2.4 / 单图可推断、全证据强约束

用户明确了图片还原产品标准：

- **单张建筑图片**：不是只做白模。必须尽量还原该图片可见视角的体量、比例、层数/开间、门窗、颜色/材质分区、玻璃、栏杆、立面构件以及看得到的室内/家具细节；看不到的背面、屋顶和室内允许 AI 按建筑逻辑合理脑补，但必须标为推断、保持结构/交通/风格一致。
- **多视图**：所有看得到的立面都属于同一栋建筑的硬约束，不能为了修一个面把另一个已观察面改错。
- **完整证据包（全外立面/屋顶 + 平面图/CAD + 室内效果图）**：目标升级为“1:1 对齐已提供证据”。CAD/平面控制尺寸与拓扑，外观/室内图片控制可见外形、材质和细节；有证据的区域禁止自由设计，只允许对真正未提供的信息做推断。冲突证据必须显式报告，不能平均后假装 PASS。

GitHub 已实现 `notes/reconstruction_evidence.json`：机器校验 fidelity_mode / source inventory / exterior coverage / CAD / floorplan / interior / scale anchors / hard constraints / inference policy。Planner 必须与 reconstruction_card/facade_schedule 同轮更新。Dedicated Critic 和 context compaction 也会读取这份 evidence ledger，避免长历史压缩后丢失“哪些能脑补、哪些不能改”的边界。

本机 Codex 下一步只执行 `docs/EVIDENCE_FIDELITY_V2_4.md`，同时保留 v2.3 的 dedicated Critic、single-writer、write receipt、六视图 review、最多两轮定向修正、blank replay 和 native SKP edit/reopen 门禁。

完成后更新 HANDOFF/CURRENT_TASK/test-results，commit + push origin/main，再交给 ChatGPT 复审。没有完整非私密 CAD+室内测试包时，不得伪造 full-evidence 真机 PASS；可以把该门禁保留为 pending_external。

---

# 当前任务 — 2026-10-08 Quality Loop v2.3 / 主动上下文压缩 + 结构化约束校验

GitHub 已在 v2.2 的独立 Critic + facade schedule 基础上继续补齐一个直接来自真实 Windows 数据的问题：Builder 历史上下文过大。现在旧的已完成 chat/tool 历史不会无限回灌给 DeepSeek；当 planner 已把关键事实写入 reconstruction card + facade schedule 后，host 会用 durable project checkpoint 取代旧完成历史，只保留当前用户回合和当前 tool loop。完整历史仍留在本地审计文件。

同时 facade_schedule 不再只是“合法 JSON”，host 会校验 schema_version、provenance、opening/door count、dimension 和列表类型。当前源图优先保留，避免因历史去重 + 压缩导致本轮没有 source pixels。

下一位 Windows Codex 直接执行 `docs/QUALITY_LOOP_V2_3.md`，与 v2.2 一起做真实 SU2024 验收：测试 schema、上下文压缩事件、source image 保留、SAIE 连续墙洞口、dedicated Critic、最多两轮定向修正、新空白 replay、SKP 原生重开编辑，并记录 Builder 与 Critic token。完成后 push main，再由 ChatGPT 复审。

---

# 当前任务 — 2026-10-08 Quality Loop v2.2 / 结构化立面约束 + 独立 Critic

在 main 已有 v2.1 独立只读 Critic 基础上，GitHub 继续补齐 ArchFlow / SketchUp Agent Harness 暴露出的下一处差距：高价值源图事实不能一直只埋在长对话和 Markdown 里。现在每个重建项目会维护 `notes/facade_schedule.json`，规划阶段把 front/rear/left/right 开口与特征、roof/parapet/division 以及 observed / user_confirmed / inferred 来源写入结构化状态；v2.1 的 dedicated Critic 在干净 source + current six views 审查时同时读取这份清单。

本轮不改变 single-writer / ProjectRuby / Kongxing / SAIE / writer receipt 架构，也不宣称视觉质量已经提升。Windows Codex 直接执行 `docs/QUALITY_LOOP_V2_2.md`：跑测试，验证 planner 真正自动写 schedule，真 SU2024 smoke `saie_wall_with_openings`，然后做新的 whole-six-view DeepSeek 重建、独立 Critic、最多两轮定向修正、空白 replay 和 SKP 原生重开编辑。完成后 push main，再交给 ChatGPT 复审。

---

# 当前任务 — 2026-10-08 Quality Loop v2.1 / 独立只读 Critic 真机验收

在 v2 单写者 + 六视图门禁基础上，GitHub 又补了一个关键差距：DeepSeek Builder 不再自己决定自己的视觉 PASS。LiteLLM host 现在会对 Builder 提交的六个 CURRENT view 路径先做路径/revision/receipt 校验，再发起一个**独立、无写工具、无长历史**的视觉 Critic 调用；Critic 只看源图 + 当前 front/rear/left/right/roof/oblique，并用自己的 NEEDS_FIX 结果覆盖 Builder 提交的 verdict。review receipt 会记录 `reviewer.mode=host_dedicated_read_only`。

Codex 本机接手时继续同一里程碑，不加新功能：

1. `git pull --ff-only`，确认 main 为最新；读本节、`docs/OSS_GAP_REVIEW_2026-10-08.md`、Quality Loop v1 真机报告和执行护栏。
2. 跑 `tests/test_modeling_quality.py`、相关 reconstruction/quality suites、完整 `scripts/check.ps1`。若 dedicated critic 改动有集成问题直接修，不弱化断言。
3. 真 SketchUp 2024 先 smoke `saie_wall_with_openings`：一个连续 wall、至少3个不同高程真洞口、无异常分段缝；再测反向中心线/侧墙。失败则实现同组连续面/洞 fallback，不能退回多组墙段拼接。
4. 新 whole-six-view DeepSeek 正常用户重建。验证真实链路：
   primary writer → 六个 current captures → Builder 调 `sketchup_submit_visual_review`（真实路径 + fallback critique；LiteLLM 不信任该 verdict） → **host dedicated visual critic provider call** → persisted review → NEEDS_FIX 时 targeted edit → 全新六视图 → dedicated critic。
5. 检查 runtime event 中存在 `visual_critic_started` / `visual_critic_response`；`qa/visual_review.json` 的 reviewer 必须是 `host_dedicated_read_only`，且 verdict 与独立人工看图对照。若 Builder 自己写 NO 而 critic 判 YES，应以 critic 为准。
6. 总 writer commits ≤3；每次 correction 保留 KEEP 的 unrelated IDs。重点仍是墙缝/开洞拓扑、屋顶分格与 parapet/capping、门窗比例位置。
7. 做 baseline replay、web download/native reopen、单对象 edit/save/reopen；记录真实 token/tool/latency，并单独列 dedicated critic token。对比 v1 六视图约4.92M input tokens，但不要把 runtime token 当账单金额。
8. 如果 dedicated critic 仍明显误判，保留 PARTIAL 和证据；下一步才考虑更严格的 machine-checkable facade/roof schedule。若 critic可靠但 Builder 成本仍过高，下一 GitHub 任务优先做 active-context compaction。
9. 更新 HANDOFF/CURRENT_TASK/test-results，commit + push origin/main。

本轮目标仍是同一个：**让一个代表性六视图别墅从“能生成”升级为“写完必须独立看真图、只改最重要问题、最多两轮、最后的质量结论不是 Builder 自评”。**

---

# 当前任务 — 2026-10-08 Quality Loop v2 / 单写者 + 真六视图审查

ChatGPT 已审查 Windows Quality Loop v1 的真实证据：技术链、保存/重开/编辑/重放已明显成熟，但单图与六视图源图还原仍为 PARTIAL。v1 最大差距不是“再写更强 prompt”，而是 3DCodeBench 那种真正由 host 控制的 critique→fix→rerender 闭环没有接上；同时 reconstruction 仍暴露其它可写工具，会绕过 DCC 风格的统一 verification/write budget；墙体开洞仍以分段为主，造成明显接缝。

本轮 GitHub 已实现 Quality Loop v2，详细对照见 `docs/OSS_GAP_REVIEW_2026-10-08.md`：

1. reconstruction 只保留 ProjectRuby 作为几何 writer；直接 SAIE/Kongxing mutator 在该 profile 隐藏。
2. 新增 `sketchup_submit_visual_review`：六张 DISTINCT 当前 revision 的 front/rear/left/right/roof/oblique `agent-view` 截图必须和当前 Ruby revisions 一致；写入 `qa/visual_review.json` / history / `visual_qa.md`。
3. DeepSeek LiteLLM host 已接入真实质量门：writer 后不能直接结束；必须六视图 review。NEEDS_FIX 才允许下一次定向修正；每次写入后 review 失效并重做；仍保持首建+最多两次修正。
4. 采用 SAIE pinned `eff6f41...` 的 batch-opening 源码思路，新增 root-scoped `saie_wall_with_openings`：一个 combined cutter + 一次 subtract，目标是消除当前别墅“窗洞由很多墙段拼出来”的可见接缝。尚未在真 SU2024 验收，不能宣称已修好。

## Codex 下一步（必须本机执行）

先 `git pull --ff-only` 并确认 main 为最新，再阅读：
- `AGENTS.md`
- `docs/OSS_GAP_REVIEW_2026-10-08.md`
- `docs/test-results/windows/2026-10-08-quality-loop-v1/README.md`
- `docs/EXECUTION_GUARDRAILS.md`

然后：

1. 跑新增定向测试和完整 `scripts/check.ps1`。若失败直接修，不要弱化断言。
2. 在专用空白 SketchUp 2024 模型先做 `saie_wall_with_openings` 真机 smoke：直墙至少3个不同高程窗洞；确认一个连续 wall group、洞真实贯穿、无异常墙段接缝、bounds/receipt 正常。再补一个反向中心线或侧墙 smoke。若 SolidTools/subtract 在当前环境不可靠，保留旧 verified 模型并改成同一组内的连续面/洞 fallback，不要回到多组墙段拼接。
3. 做一次新的 whole-six-view DeepSeek 正常用户重建。不要人工改几何；计划阶段只允许用户核对已知输入，不要人工给 Agent 精确修墙指令。
4. 验证真实执行顺序是：primary writer → 六个 current captures → `sketchup_submit_visual_review` → NEEDS_FIX 时 targeted edit → 新六视图 review；第二个 writer 在没有 review 时必须被 host 拒绝。总 writer commits 不得超过3。
5. 每一轮 review 检查 `qa/visual_review.json` 的路径、revision、writer receipt、≤3 issues、KEEP；禁止旧图、虚构文件名或“工具成功=质量通过”。
6. 重点看 v1 的三类真实缺陷：立面墙缝/窗洞拓扑、屋顶分格和 parapet/capping、门窗比例/位置。修正必须尽量只动 affected named groups，记录 KEEP IDs 是否保持。
7. 最终做新空白 baseline replay + web download/native reopen + 单对象编辑/save/reopen；记录 token/tool/latency，与 v1 六视图 4.92M input tokens / 40 tools 做对比。
8. 若 host review 仍明显乐观，记录为证据，不要手工替它改成 PASS。下一步将拆出独立 read-only critic model call。
9. 更新 `docs/HANDOFF.md`、`docs/CURRENT_TASK.md` 和新的 sanitized test-results；commit + push `origin/main`，确认远端 SHA。

本轮验收核心：**不再只证明“能建模”，而是证明“每次写完都必须看当前真图、根据真图定向修、最多修两次，并且不能绕开 writer/verification”。**

---

# 当前任务 — 2026-10-08 Modeling Quality Loop v1 本机验收后继续

最新本机执行从干净 `2a80973` 开始。**单图和完整六视图均真实生成了可编辑别墅，但视觉验收仍 PARTIAL，不可发布为质量通过。** 云端下一位先审查 [本轮公开报告/当前截图/对象ID/回执/重放/原生编辑/费用统计](test-results/windows/2026-10-08-quality-loop-v1/README.md)，然后按下列同一里程碑任务继续。下方旧结果仅历史，不能替代本轮证据。

## 本轮已执行

- 当前 DeepSeek + K Studio + SU2024/Kongxing，Key 多次重启后自动恢复、真实请求成功，无需重复填写。
- 新单图/整张六视图网页上传→讨论/澄清→计划修改→一次批准→自动连接专用空白→真实几何r5→独立当前六视角检查/完整对象分页。六视图窗数有人工识图纠正；两次主执行各五次全root重写，超过提示要求且改变子ID，不称定向KEEP通过。
- 所有写入回执核对；补不可变回执/截图修订与真实路径的模型可读返回、缺字段失败校验、Skill截断修复、跨script ID Ruby写入预算和计划默认不重复确认。
- 新空白完整基线重放171对象匹配；两次局部茶几探针保留其余对象并恢复原位置，后续写入预算被拒绝，只读仍可用。网页下载/原生Ruby控制台守卫单对象编辑/保存/重开171对象一致，非鼠标Move操作证书。工程首次漏保存导致下载空白，补原生保存后重测，已如实记录。
- 修复产品只保存下载文件、未保存会话绑定文档；当前文档用save、导出用save_copy。真实网页茶几+桌腿100mm修改保留171 ID/其他169不动；保存失败修复后的普通中文重试不再移动，绑定/下载文件原生重开均完整匹配。
- 修复Ruby行号401被误报Key失效；未知script ID返回现有ID/修订提示。最终249 passed/2 skipped/2依赖warnings，指定质量测试51 passed，编译/Node实际分类与语法/diff通过；桌面包重建安装、data/Key/快捷方式保留。

## 下一轮可执行任务（不开始新里程碑）

1. 先读公开单图/六视图current真图与独立QA：白墙分段竖缝、屋顶分格缺失/女儿墙过厚、开口比例与陈设材质仍有偏差。不要沿用Agent“无需返工/已完成”自评。只有局部茶几编辑通过身份保持，建筑修正尚未通过。
2. 在同一DeepSeek路线使用最终修复代码新跑首建，验证新Ruby预算和真实截图路径可读。最多两轮**定向**墙体/屋面修复；尽量采用成熟helper/验证过的连续面洞口方法，保留已正确阳台/格栅/家具等KEEP ID。不要靠全root replace或更强模型掩盖方法缺陷。
3. 将现有critic解析契约接成实际只读检查阶段，核对所有当前修订六视图和源图开口/屋顶schedule。当前回执只验证生成事务与实际读回一致，零厚度或错窗同样可能verified=true；不能视为质量合格。当前prompt引导尚未可靠自动完成QA。
4. 修正后整合基线、新空白重放、再次网页下载/原生编辑/保存重开，保持可公开截图/完整ID-mm与人工干预记录。降低上下文/工具错误/耗时并核对实际供应商账单，不能由runtime token估算直接声称真实价格。
5. 最后补全新电脑/冻结EXE付费完整流程、剩余剪贴板/旧计划失效/失败恢复体验门槛；这些仍pending_external/未本轮实测，不把源码成功等同新用户独立成功。更新HANDOFF/CURRENT_TASK并push main、确认远端。

---

# 远端下发任务 — 2026-10-08 Modeling Quality Loop v1

ChatGPT 已完成一轮可在 GitHub 直接实施的质量闭环改造：引入 3DCodeBench 的 bounded visual critique 思路、dcc-mcp-sketchup 的 expected/actual post-write verification 契约，并接入现有 K Studio persistent Ruby 工作流；没有替换 DeepSeek、Kongxing、SAIE，也没有增加多写者 Agent。

下一执行者先阅读 docs/MODELING_QUALITY_LOOP_V1.md。必须在 Windows + 真 SketchUp 上完成新的单图与六视图本机验收；自动测试不能替代视觉验收。每次写模型后检查 write_verification；最终用当前 front/rear/left/right/roof/oblique 真图形成 NEEDS_FIX + 最多3个问题 + KEEP 清单，最多两轮定向修正。随后做新空白基线重放、下载/原生重开/单对象编辑/再读回。

Codex 完成后更新 HANDOFF/CURRENT_TASK、commit 并 push origin/main；然后由 ChatGPT 复审代码、证据和真实建模结果。当前旧的 2026-10-06 结果继续作为历史基线，不自动升级为 PASS。

---

# 最新本机执行结果 — 2026-10-06 单图 / OSS Skill 实测（余额阻断）

从干净 main `0dd0943` 开始。新增两个 MIT 上游 Skill 节选直接接入产品建模上下文，保留持久 Ruby / Kongxing / 已采用 SAIE 和 Stultus：[采用与排除依据](OSS_RUNTIME_SKILLS_2026-10-06.md)。本轮没有换更强模型，没有修改原始模型，也没有重跑或替换六视图素材。

修复前后端带限定词的批准识别、首条明确请求计划的分派、重复澄清指导、处理时再次批准提示，以及恢复后的持久修订记忆。新单图网页实测一次带限定词批准正确进入自动连接、新空白模型和执行：44次工具调用完成至 rev6。普通中文同模型修改到 rev7–10，中途墙体补丁盖住窗洞，随后纠正；最后 DeepSeek 明确 `Insufficient Balance`，未完成最终全部视角 QA。已保存 Key 在服务重启后自动恢复，MCP正常。

免费验证：恢复 rev6 全179件 ID/名称/毫米边界匹配检查点；网页下载 SKP，原生重开，人工守卫探针仅茶几54509沿X+100mm，保存再次重开全179件匹配，其他178件不动。原生保存提示需人工点击，仍是体验缺口。当前项目恢复到 rev6；失败轮脚本/笔记仍保留，恢复事件已明确记录，继续前必须读回核对。

239 passed / 2 skipped / 2依赖warnings；Python编译、Node语法/实际分类、diff检查通过。桌面包重建安装并保留data/Key；付费建模在源码服务进行，全新电脑/冻结EXE完整付费流程仍pending_external。

**还原质量 partial，未通过可售验收。** 白墙缝、材质、阳台陈设和推断有差异，Agent自评过强，历史上下文成本偏高。首条计划修复只有免费测试，尚未再次付费验证；单图成功补丁/六视图revD新空白重放等门槛仍待完成。[完整公开结果、截图、对象ID、失败补丁与重开证据](test-results/windows/2026-10-06-reuse/README.md)。

## 下一轮可执行任务（当前里程碑继续）

1. 账户恢复余额后，继续同一 DeepSeek 当前rev6模型，核对参数卡、真实ID及失败补丁，修白墙/窗洞、阳台陈设、屋顶与材质；来源图对照全部当前视角，不能盲目执行失败基线。
2. 受控适配现有成熟能力；SAIE opening已阅读，但whole-model/AI-ID/Undo依赖尚未接入。保持专用root、单位和生命周期守卫，避免重写弱几何引擎。
3. 将实际通过的补丁整合后新空白重放单图；保留六视图rev22并补revD新空白重放、最终截图与完整对象证据。
4. 补真实首条计划回归、剪贴板/旧计划失效/保存提示恢复体验、上下文和供应商账单核验。未验证项不得升级为PASS。
5. 更新交接并push确认远端；不扩展新软件、支付、账号或云基础设施。

---

# 最新本机执行结果 — 2026-10-06 六视图 rev22 持续优化

用户要求按真实问题持续优化并效仿相似开源项目。从干净 main `7aa4221` 拉取，实施嵌套命名对象回读/分页与局部删除、源图事实/真实QA/项目记忆 Skill、跨历史同图 wire 去重。研究 Stultus/Agent Harness/SAIE/Auto Builder 实现与许可证：[采用判断](OSS_QUALITY_LOOP_2026-10-06.md)。保留现有 Agent/DeepSeek/Kongxing，不扩展引擎或多 Agent。

同一 DeepSeek 网页 Agent 将六视图模型迭代至 **rev22**：左墙每层1窄窗、后墙每层3窄窗、入户底层只门、二层中梃窗；增加70mm内凹、屋面分格，修复重建产生的竖缝及斜视双水平线、木色。完成当前修订七张真图、完整9页回读，六个顶层ID/root保持；249→229个child，154旧ID及毫米边界保持，95被替换/75新建。最新SKP网页下载→原生重开→单桌人工+100mm→保存→再次重开229件完整匹配，其他228件边界未动。安装包缺Ruby helper已修复并重建安装，数据/Key保留，实际安装包helper只读原生SU烟测通过。228 passed/2 skipped/2 warnings。

**仍 partial，不是可售质量通过**：本轮有监督纠正识图和精确执行提示；材质/室内/植物仍示意，窗位/比例有估算差异，屋面3×2比源图粗。基线revD已整合但未在新空白模型重放。长批准草稿被转计划、多余默认确认、Agent自评过强、历史上下文 token 过大仍待改进。单图本轮未重测；剪贴板/旧计划/恢复/干净安装仍不应宣称通过。

[公开真图、ID/mm、生成源码/卡/QA、重开编辑、人工干预、调用与复现报告](test-results/windows/2026-10-06-iteration/README.md)。这是继续迭代的可审查交接，不是里程碑完成。

下一轮仍只做当前图像建模里程碑：

1. 云端先审查rev22真图及生成基线；本机随后用增强工具/Skill在**新单图会话/专用模型**完整复测，记录未辅助 vs 监督纠正，原六视图模型保持。
2. 在新专用空白模型验证整合revD基线重放；不对已有模型盲目replace，不把只写入基线当重放通过。再细化屋面、窗位、材质/可见细节，以原整图为目标，实质参数变化走网页计划批准。
3. 修复“点击开始但带限制的批准草稿又进计划”交互和无必要的反复确认；执行阶段连续完成，真实失败说明确切原因；补网页剪贴板/旧计划/失败恢复实机门槛。
4. 降低长会话上下文成本，保留需求/源图/对象身份/最近真图/原始审计；核对实际计费。新电脑安装与安装EXE完整付费流程仍 pending_external，不能以源码网页成功代替。
5. 每轮更新此文件/HANDOFF并push main、确认远端；不添加收费/认证/多软件云设施或更强模型救场。

---

# 最新本机执行结果 — 2026-10-06 六视图修复与 SKP 重开编辑

从干净 main 拉取 `0589895` 后已通过同一 DeepSeek 网页 Agent 修复现有六视图专用模型，获得新的前/后/左右/屋顶/斜视六张 rev13 真图。真实保存 Key 启动/服务重启后恢复且继续推理成功，无需本轮重填。重建安装最新桌面包。修复明确执行指令被“检查是否”误判为讨论的 bug；重启后网页单构件 +50 mm 修改成功，249 个 child ID 保持，其他 248 件毫米边界未变。最新 rev15 SKP 网页下载→SketchUp 原生重开→单桌子人工 +100 mm 编辑→保存→再次重开完整回读通过。

**源图还原仍 partial，不是 release PASS**：严重单位/墙体错位已改善，但左侧窗数误读、开口比例、材质/屋面细节仍未通过；不能沿用 Agent“一致 ✓”自评。SHELL/OPENINGS/LOUVER 修复时曾替换 ID，后续局部编辑才保持，不混称全程 ID 不变。单图本轮未重测；剪贴板/旧计划失效/失败恢复/干净安装的实机验收仍待完成。

[新截图、完整 ID/mm、重开编辑证据、人工干预和复现说明](test-results/windows/2026-10-06-repair/README.md)。自动测试 214 passed / 2 skipped，不替代视觉质量。

下一轮执行顺序（保持当前里程碑）：先云端审查上述真图/参数误读 → 网页修订批准左侧窗/立面计划 → 同 DeepSeek 修窗数/深度、屋面细节并逐视角 QA → 合并已生成单位/法线补丁到持久基线后实测（不能仅重跑旧坏基线）→ 单图与剩余 UI/恢复实机门槛 → 核查真实 token/账单成本。不要把此轮工程/重开通过扩大为可售质量通过。

---

# 最新执行任务 — 2026-10-06 云端验收后继续实机建模

用户授权云端验收、修复及测试，完成后交回本机。此节优先于下方历史要求。已验收本机 main `2607494`：安装包/凭据虚拟 Key/SAIE 单墙尺寸证据有效；**未完成真实别墅复测，单图部分成功、六视图质量失败结论不变**。云端修复当前截图证据链并加强 Skill，详情：[本轮验收与测试](test-results/cloud/2026-10-06/README.md)。

本机 Codex 从最新 main 接手，不再只跑连接/墙体烟测：

1. 拉取、检查干净状态、读 AGENTS/执行护栏。使用桌面安装版时重建并运行 `scripts/install_desktop.ps1` 更新快捷方式，保留 data；仅拉取源码不能更新旧 EXE。检查本机默认 DeepSeek 是否已配置，不读取/打印 Key。若缺失，只需用户在本地设置填一次；不要停在烟测后宣称建模完成。
2. 使用现有专用六视图项目/模型，先读持久 Ruby、参数卡、当前几何和 IDs。保留六视图整图；按原批准尺度建立统一坐标和逐立面/楼层开口表，标明图中 panel/地标和不确定项。仅调整错误解释；实质更改用户批准参数须走网页重新计划/批准。
3. **通过 K Studio 同一 DeepSeek 路线**修复错位后墙/侧墙，回读这些构件的 XYZ 毫米位置与尺寸，再修开口数量、真实孔洞和屋顶板/女儿墙。可先用一次小的 edit 校验，再逐部位修复；不要绕过网站直接由本机 Codex 完成整栋模型并称为产品效果。若工程调试直接写 Ruby，明确标人工干预并另做网页验证。
4. 每次修改后取得新截图；前/后/两侧/屋顶/斜视分别与原图对应 panel 比较，记录实际 vs 预期及未修缺陷。先纠正最大的错位/实虚/屋顶问题，再加细节。只修改一个命名 child，验证未修改 child persistent IDs 保持且读回未截断；需要整栋重建时显式 opt-in、如实记录 IDs 变化，不称局部编辑。
5. 完成六视图 SKP 下载→重新打开→实际修改一个构件；继续单图缺陷与网页剪贴板/旧计划失效/检查点恢复。不要把自动测试、文件存在或 Agent 自评替代实际验收。
6. 报告放 `docs/test-results/windows/`：新真实截图、可公开参数卡/立面表和 QA 小片段、修复前后 mm/IDs、模型/时长/调用失败/人工纠正及 remaining。这些公开测试素材生成的片段可提交，但必须删密钥、账号、个人路径和私人项目数据。更新 HANDOFF/CURRENT_TASK，commit/push main 并验证远端。若 Key/许可阻塞真实测试，明确记录未执行，别再声称完成。

云端本轮 209 passed / 2 Windows skips；启动 HTTP 检查通过。无新付费推理/真实 SketchUp/SKP 质量证明。沿用当前建模里程碑，不开展 Google Cloud、收费、渲染或多 Agent 重写。

---

# CURRENT TASK — Windows 本机实际测试与 GitHub 交接（2026-10-05）

用户已开始本机 Codex 测试。本阶段从最新 main 接手，检查 Windows 启动器、DeepSeek、SketchUp/Kongxing/MCP，并在专用空白测试模型中完整验证上传→澄清→计划→确认→建模→截图检查→同模型修改→SKP 保存及重新打开。发现问题直接修复、测试并 push main；不要覆盖本机已有工作或修改用户原始模型。

测试输入已随仓库提交：
- `docs/test-assets/cloud-villa/villa-single-view.png`
- `docs/test-assets/cloud-villa/villa-six-view-sheet.png`
- 素材说明及 SHA-256：`docs/test-assets/cloud-villa/README.md`

保留六视图整图，不使用旧 ZIP 中另一栋别墅的独立图片替代。两个独立会话/模型尽量使用相同需求、尺度和配置；记录图片生成不一致、识图错误和人工纠正，不宣称严格控制变量比较。API Key 由用户本机填写，不提交密钥。缺少许可或不可自动完成的登录明确报告，继续独立可做的工作。

交付：更新 HANDOFF 和 CURRENT_TASK，公开可分享的测试报告/截图放入 `docs/test-results/windows/`，区分真实执行、模拟测试、人工干预及 pending_external。私人素材、密钥、账号、私人 SKP 和个人路径不提交。commit/push 后确认 origin/main，云端直接读取 GitHub 验收，无需用户转发报告。

## 本机续测（2026-10-06）

用户最新要求：设置界面仅留 DeepSeek V4.1 Flash，Key 保存后作为默认并重启恢复。已简化界面、说明本机 Windows 用户保存范围与更换/移除方式；不新增账号云同步或将平台密钥内嵌客户端。后续仍需真实 Key 保存恢复及原建模验收。

后续已解决：Git 经本机既有代理拉取/推送恢复；桌面快捷方式曾指向不包含凭据保存模块的旧 EXE，现已重建安装并更新。新增 `scripts/install_desktop.ps1` 保留 data/旧版本且检查打包模块；真实 EXE 隔离虚拟 Key 保存→重启恢复→移除验证通过，无付费调用。全套 204 passed/2 skipped。旧内存真实 Key 无法恢复，待用户在更新后安装版填写一次，再验收真实 Key 重启和下面未完成建模流程。报告保留此前网络阻塞历史，不代表目前仍无法推送。

[助手实机回读与阻塞报告](test-results/windows/2026-10-06/README.md)：SAIE 墙体在专用空白模型实测尺寸/方向与事务 IDs 通过；不能算别墅质量通过。当前本机 DeepSeek 未配置，真实 Key 重启恢复尚待验证。GitHub 拉取两次连接超时，远端最新状态未确认；下一执行者先恢复连接并拉取。原六视图修复、局部 ID 保持、下载重开实际编辑、剪贴板/旧计划/失败恢复任务继续有效，不扩展里程碑。

## 最新追加：开源代码复用（2026-10-05）

用户要求匹配、筛选并直接复用开源代码，不重复造轮子。已搜索/检查 8 个仓库并实际接入 SAIE 墙体几何子集和 Stultus 毫米边界回读子集：[匹配与接入说明](OSS_MATCH_AND_ADOPTION_2026-10-05.md)。保持 Kongxing/现有 Agent，不新增几何引擎或多 Agent 重写。系统 Ruby 替身验证和 204 自动测试通过，2 Windows skips；尚无真实模型质量通过。

本机先在专用空白模型验证注入的 saie_wall.call(params)（所有参数毫米、字符串键）及事务 owned_before/owned_after 中的 XYZ 毫米边界与 child persistent IDs，再用于别墅修复。墙体子集只创建实体段，不自动开洞；不可用封闭实墙假装玻璃开口。按下方原任务继续完成真实几何、全视角对比、同模型局部改动和 SKP 重开编辑；记录是否截断，不把新工具成功当成视觉通过。

## 云端验收后修复与本机复测（2026-10-05）

已基于 ac8f597 的失败截图完成云端迭代，说明：[云端回归与下一步](test-results/cloud/2026-10-05/README.md)。新增已知米/英寸原点错误的执行前检查、已有模型整栋 replace 显式保护、旧长工具输出缩减、质量未验收提示。202 tests passed，2 Windows skips；这不代表真实模型质量已修复。

本机 Codex 拉取最新 main 后，优先修复现有六视图模型：读当前参数卡/源码/模型→统一墙体原点单位→回读四角与各轴尺寸→核对各立面窗数→修复屋顶女儿墙→截图对照。局部修改使用 edit，读回未修改构件 persistent IDs；整栋重建必须显式 allow_full_rebuild=true 并如实记录 ID 变化。完成六视图下载重开和一次真实局部编辑，发布可公开报告/截图、更新 HANDOFF 并 push。不得只依据 Agent 自评通过，不再把有 SKP 等同于还原质量合格。

## 本机实测更新（2026-10-05）

报告与公开截图：[Windows 实测](test-results/windows/2026-10-05/README.md)。实际 DeepSeek、SketchUp/Kongxing 连接、独立空白模型建模已执行。单图部分成功但屋顶/墙体细节未通过；完整六视图发生严重单位/墙体错位，Agent 误报验收成功。因此当前 **不具备发布质量通过结论**。

已完成：Windows 启动器与依赖；整图上传与刷新保持；计划生成/修改/批准；连接错误显示与自动连接续跑；真实几何和截图；单图输出下载及重开分组可编辑性检查；工程安全局部删除接口和真实对象 ID 保持烟测；聊天空间修复；视觉验收/单位提示修正；测试发现范围修复。

用户追加要求已实现：Windows API 配置使用当前用户 DPAPI 加密保存、重启恢复、移除 Key；真实加密测试使用虚拟凭据，不产生模型费用。旧内存 Key 已丢失无法恢复，等待用户在新配置框补填后继续付费验证。

下一轮仍属于本阶段，不扩展里程碑：

1. 配置恢复后，用同一 DeepSeek 和现有六视图项目修正米/英寸原点、窗数、屋顶；检查实际截图，不接受 Agent 自评。
2. 通过网页仅修改一个建筑分组，读回其他分组对象 ID；下载六视图 SKP、重开并做实际局部编辑。
3. 在 Windows 网页完成剪贴板图片上传、旧计划失效、失败检查点恢复验收；区分自动测试与真实桌面结果。
4. 更新报告、推送真实验收结果；持续记录人工干预。干净新电脑安装仍为 pending_external，不以当前已有环境替代。

---

## 云端阶段历史（以下不覆盖当前实机任务）

# CURRENT TASK — 建模前用户体验迭代（2026-10-05）

最新用户指令优先于下方历史方案：暂不要求云端实际 SketchUp/MCP 建模；把上传、自然对话、澄清、参数计划、计划修订、连接引导、状态恢复做到可用，真实测试并提交推送 main，等待用户 Windows 实验。

- 主要使用用户已授权的 DeepSeek API；Key 仅保存在服务内存，不写入仓库。
- 保留完整六视图整图；图片文件数量不等于视角数量。
- 研究建筑学长与 SUAPP 的公开交互，区分页面观察、产品宣称与真实执行；不复制专有实现。
- 新资料、失败的参数更新都不能沿用旧计划授权建模；提问不应修改模型。
- 本轮不声称真实几何、SKP 输出、Windows 干净安装或视觉还原质量通过。
- Windows 用户从 GitHub 下载后可使用根目录 `Start K Studio.cmd`（需 Python 3.11+）；启动器安装依赖并打开本地网页。

---

## 历史任务背景（以下不覆盖最新用户指令）

# CURRENT TASK — Image → SketchUp Direct-Codex Parity v2

## Status: Ready for Codex local integration after ChatGPT remote refactor

The user paused the previous Codex run. Start only from the latest `main`.

## Single product goal

> **one architectural reference image → GPT-6.1 Sol Low + strong task Skill + Direct-Codex-like coding harness + thin SketchUp bridge → developed editable SketchUp model comparable to the known-good direct Codex result**

Do not expand into taskbook/site/new-design/render/PPT in this milestone.

Read first:

1. `AGENTS.md`
2. `docs/EXECUTION_GUARDRAILS.md`
3. `docs/REMOTE_REFACTOR_HANDOFF_2026-09-30.md`
4. `docs/SKILL_FIRST_AGENT_REFACTOR_V1.md`
5. `app/reconstruction_runtime.py`
6. `app/image_to_sketchup_skill.py`
7. `app/codex_parity.py`
8. `app/workflow_context.py`
9. `app/agent_tools.py`
10. `app/reference_assets.py`
11. `app/native_agent.py`
12. `app/litellm_runtime.py`
13. `app/main.py`
14. `app/static/index.html`
15. `app/static/studio.js`
16. `docs/HANDOFF.md`

`docs/REMOTE_REFACTOR_HANDOFF_2026-09-30.md` and this file supersede older HANDOFF wording that treated the standalone workspace-write probe as a blocking acceptance gate.

## Benchmark model lock

For this milestone use **`gpt-6.1-sol` at `low` reasoning** for both the known-good direct Codex path and the website parity path.

Do not silently fall back to `gpt-6-sol`, raise reasoning effort, or route to Astra. If `gpt-6.1-sol` is unavailable in a specific local execution path, record that exact limitation and continue all non-dependent work; do not substitute a different benchmark model and still call the comparison parity.

## What ChatGPT already changed remotely

Do not redesign these from scratch:

- reconstruction session lifecycle now supports `idle -> clarifying -> planned -> building`;
- requests support `agent_action = auto|clarify|plan|execute`;
- default `auto` policy is:
  - idle -> clarify;
  - clarifying -> plan/parameterize;
  - planned/building -> execute/continue;
- explicit execute before an approved plan is rejected;
- Image → SketchUp Skill now follows:
  **inspect -> clarify high-impact unknowns -> parameter card -> approval -> persistent Ruby -> execute -> inspect -> revise**;
- reconstruction card is now a parameter baseline with KNOWN / ESTIMATED / ASSUMED values;
- persistent workspace Ruby remains the primary project-specific geometry path;
- SAIE is a helper library, not the orchestration center;
- reconstruction context must remain reference-only and small;
- GPT-6.1 Sol Low is now the parity baseline;
- external workspace-write probe is non-blocking and must not interrupt the user during ordinary implementation.

These remote changes are not accepted until local tests and real SketchUp execution pass.

---

# TRACK A — validate the remote refactor

Run:

```powershell
git pull --ff-only
git status
.\scripts\check.ps1
```

Fix concrete regressions. Do not roll back the Skill-first / coding-first architecture just to satisfy stale tests.

Expected product invariants:

- legacy architecture-design path still exists;
- image reconstruction is the current product focus;
- original/private SKP/DWG is never modified;
- all live reconstruction uses a generated/disposable model;
- no Astra calls.

Do not pause the user for an internal probe or reversible setup issue. Record non-critical blockers and continue.

---

# TRACK B — wire the full reconstruction lifecycle into `main.py`

For `workflow_mode == "image_reconstruction"`, use `app/reconstruction_runtime.py` as host policy.

## B1. First turn — CLARIFY

- require at least one `inputs/reference` image;
- actual reference image reaches the model as multimodal input;
- no SketchUp geometry tools;
- no taskbook/site/program context;
- ask at most four concise questions covering only high-impact unknowns:
  1. intended use / multi-angle requirement;
  2. model scope;
  3. any known dimension anchor;
  4. unseen-geometry permission / desired visible detail;
- do not ask what the user already supplied;
- successful turn sets `reconstruction_state = clarifying` and increments `clarification_rounds`.

## B2. Second turn — PARAMETERIZE / PLAN

When state is `clarifying`, normal `auto` resolves to `plan`.

- use the image plus user answers;
- update `notes/reconstruction_card.md`;
- clearly label dimensions/assumptions as KNOWN / ESTIMATED / ASSUMED;
- return a compact parameter/construction plan;
- do not edit SketchUp;
- successful turn sets `reconstruction_state = planned`;
- UI must make approval explicit.

## B3. Approval / EXECUTE

Explicit `agent_action="execute"` is valid only after `planned`.

- verify disposable SketchUp model identity;
- enable `reconstruction_coding` tool profile;
- use same Agent thread/workspace;
- use approved parameter card;
- persistent workspace Ruby is primary;
- selected SAIE helpers are secondary;
- after successful first execution set `reconstruction_state = building`;
- later `auto` turns continue modifying the same scripts/model.

Do not route this flow through DesignIR/BuildPlan.

---

# TRACK C — make the execution environment closer to direct Codex

For image reconstruction, the model should see a small coherent workbench, not the historical 80-tool menu.

Preferred surface:

- `sketchup_run_workspace_ruby`;
- actual available scene/entity/model readback;
- camera/view/screenshot;
- selection/transform/undo/lifecycle if actually exposed;
- selected SAIE query/view and ordinary wall/opening/slab/roof helpers.

Hide for this milestone:

- legacy create_mass/create_road flow;
- ArchFlow/CAD tools;
- broad unrelated OSS tools;
- transient inline project Ruby when persistent workspace Ruby is available;
- any invented compatibility tool not present in the live connector.

Codex App Server and LiteLLM must receive the same reconstruction semantics. Provider choice must not change Skill/tool meaning.

---

# TRACK D — UI should behave like a modeling assistant, not a developer console

Image reconstruction UX:

1. **上传参考图 / 描述目标**
2. **AI澄清关键问题**
3. **建模参数与假设**
4. buttons: `修改参数` / `批准并开始建模`
5. **建模/修改中**
6. show source-matched result and allow natural-language follow-up edits.

Display state in user language:

- 待分析
- 等待补充信息
- 等待批准
- 建模/修改中

Do not expose sandbox/workspace/probe/MCP implementation details in normal UX.

---

# TRACK E — competitor desktop observation is optional and non-blocking

If the legitimately installed Building-Xuezhang desktop package / `su_mcp.rbz` is locally available, inspect ordinary accessible behavior/files/processes/runtime schemas and write:

`docs/COMPETITOR_DESKTOP_ARCHITECTURE_OBSERVATION.md`

Separate:

- Observed facts
- Inference
- Implications for our product

Useful questions:

- is the SU plugin a thin bridge or geometry-heavy engine?
- what MCP tools are exposed?
- is execution script-driven or fixed-tool-driven?
- how are plan/approval/continued edits represented?
- do multiple foundation models reuse the same Skill/bridge?
- screenshot/readback/undo/save lifecycle?

Do not bypass DRM/access controls, decompile protected binaries, or copy proprietary Skill/source.

If the package is unavailable, write `pending_external` in HANDOFF and continue. Do not stop or ask the user solely for this track.

---

# TRACK F — workspace-write probe is no longer a blocking prerequisite

Do not pause the user to request normal PowerShell execution.

If you can run the standalone probe from a normal shell context yourself, do it. Otherwise record:

`workspace_write_probe: pending_external`

and continue all non-dependent implementation/testing.

Only surface this to the user later if the real website reconstruction is actually blocked because persistent workspace files cannot be written.

---

# TRACK G — real parity benchmark

Only after the website lifecycle/tool wiring is functioning.

Use the same reference image that already produced a good result in direct Codex.

A = direct Codex + **GPT-6.1 Sol Low**.

B = website + **GPT-6.1 Sol Low** + latest reconstruction Skill + latest Agent harness.

Do not use Astra.

User instruction should stay short; do not hide weak orchestration behind a giant benchmark prompt.

Required evidence for B:

- real source image reaches model;
- clarify turn occurred;
- parameter card exists and includes explicit estimates/assumptions;
- approval gate occurred;
- persistent `.rb` file(s) authored;
- same scripts/model revised rather than restarted;
- source-matched screenshot;
- oblique screenshot;
- concrete mismatch statement;
- at least one visual self-correction;
- organized/editable geometry;
- model/effort/time/token/tool-call/failure evidence.

PASS requires the final SketchUp result to be recognizably comparable to the direct-Codex reference in developed architectural detail.

Automatic FAIL:

- only rough white boxes;
- visible facade/roof systems omitted;
- no screenshot comparison;
- no persistent coding evidence;
- no same-model correction;
- silent model or reasoning-effort substitution;
- declaring success based only on tool/test connectivity.

---

# End-of-task

Run:

```powershell
.\scripts\check.ps1
git diff --check
git status
```

Update `docs/HANDOFF.md` with:

- exact code changes;
- local tests;
- real SketchUp evidence;
- remaining blockers;
- any `pending_external` items;
- parity benchmark result if reached.

Then commit, push `origin/main`, verify remote SHA, and stop. Do not start rendering/PPT/full-design work automatically.

