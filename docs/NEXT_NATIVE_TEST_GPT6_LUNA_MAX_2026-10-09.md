# K AI Studio 下一轮真机建模 — Codex 高能力模型 + ADAI（2026-10-09）

## 建筑学长工作流启发（补充；**本轮不扩范围**）

用户新增的“已有 SketchUp 白膜/用地红线 → 上传意向图 → 自动深化 → 截图修改 → 多方案 → CAD/渲染/漫游”演示，已写入 [长期产品路线](PRODUCT_DIRECTION_REFERENCE_TO_NATIVE_SKETCHUP_2026-10-09.md)。本轮 Codex **不需要**导入用户现有白膜、不需要另造商业办公综合体、不需要实现 CAD、动画、PPT，也不要替换 Kongxing 为竞品私有 SU MCP。

直接借鉴以下**已经能在我们产品中实践**的部分，并作为本轮真实性指标：

1. **从稳定主形开始**：多视图 villa 源图 → 经过校验的已知/估算参数 → 一个可编辑的项目持久 SKP。先核验楼层、建筑体块、开间、关键转折与外立面再复制细部；不要刚开始就铺满家具来掩盖比例偏差。
2. **深挖几何细节而非反复重建**：把 ADAI 的已验证 helper 与 SAIE/ProjectRuby 组合。优先选有来源证据的墙真开洞、窗框、幕墙模数、屋顶/女儿墙/墙顶拼缝；始终保留 root/KEEP 及同一项目模型。
3. **模拟演示的“截图发现问题 → 指定局部修复”**：最终真实截图审查至少点出一个实际可见的最高优先级问题，用指定 group/路径执行一轮 targeted correction，重新捕捉**同一真实 SKP 最新 revision**的前后截图。可安排第二轮修正，但总数仍受原任务两轮约束。记录修什么、KEEP 哪些对象、是否真正消除视觉错误，不能把仅改材质却未修几何称为成功。
4. **工程尺寸不靠口头猜测**：如用户/源图明确了层高和形体边界，在读回中验证 mm 数值；若源图只是视觉意向，标注 `ESTIMATED` 而非伪造“约 7500 平方米”的项目红线或车位规范通过。演示中的停车尺寸并不是本次 villa 的输入。
5. **本次报告新增小节**“与建筑学长演示的可复用原则”：指出上述四项实际验证了哪些、哪些仍不支持（白膜起步、模型方案分支、CAD、渲染、漫游和网页汇报）。此节仅为产品迭代洞察，不要求新 A/B 实验。

下面原有 A/B/C/D 实施步骤继续有效；遇到与此节冲突，以“不扩范围、保护既有模型、真实上传证据”为准。


## 任务性质

**直接在现有 K AI Studio `main` 开发并测试**；不是 DeepSeek vs. ADAI 的 A/B 项目，也不创建新的产品仓库。测试必须走 K AI Studio 的真实 Windows 本地网站 + SketchUp 2024 + 已安装的 Kongxing 单写者。Codex 是本机执行者与可用的高能力模型来源。

### 模型选择（用户本轮最新指令，覆盖历史 Sol Low 默认）

用户希望本轮使用 **GPT-6 Luna Max**，并利用他本机 **Codex 原生模型能力**测试。启动前在 Codex/Native 配置中核对实际可选模型 ID：

1. **首选：在 Codex 中选择 GPT-6 Luna Max + 最高适用推理能力**，若该型号确实可选且支持本地 SketchUp 工作流，建模 Builder 使用这条路线。测试期间不要自动改回历史 DeepSeek 或 GPT-6.1 Sol Low。
2. 若此名称在 Codex 实际模型菜单/运行时不存在，**直接使用当前 Codex 可用的最高能力模型**，不要猜 ID、不要伪造 Luna Max 已运行、不要单独调用其它收费 API 代替。报告 `model.requested`、`model.actual`、reasoning effort 和回退原因。
3. 必须记录本次真实调用链：`codex_native`/实际已接入的 Native 产品接口、website/connector/backend，区分“Codex 直接脚本工程烟测”与“正常网站用户端到端建模”。仅工程 smoke 不能被标为产品 E2E PASS。
4. 上次 Sol Low 550.813 秒/45 调用/11 失败只是历史证据；本轮不需要跑旧版本对照。

## 现有基线（执行前必须读取）

- 当前 GitHub `main` 已有 **Codex 最新真实 Windows 提交 `98c9aec11c283879ab0bc2e9afc587f6729cdec6`**：Windows ADAI ZIP 安全校验修复、v2.8 precommit KEEP 正/负原生烟测，`scripts/check.ps1` 304 passed / 2 skipped。
- [Codex 真实截图、过程、问题、指标和几何验收报告](test-results/windows/2026-10-09-quality-loop-v25-sol/README.md)；不要写成“ADAI 原生测试已通过”。
- 旧六视图屋顶/墙顶水平拼缝、家具/植物方块化、部分比例/场地不贴合源图，视觉整体 PARTIAL。
- Native 独立只读 Critic 尚未完成；v2.4 `reconstruction_evidence.json` 格式曾被 Agent 写错并静默略过，虽已修严格拒绝，但仍需实际 Native 自动生成/有限重试验证；strategy current_stage/status 没有随真实执行更新；主机 canonical 相机整体场地太大、建筑视觉偏小。
- `app/adai_components.py` 已在主线，可下载 ADAI Skill/MCP，`ARCH_STUDIO_ENABLE_ADAI_GEOMETRY=1` 时才在受保护 ProjectRuby 提供 `adai_geometry`；**Windows 真 SU2024 还没验证过此调用**。其它 SketchUp 版本继续 `NOT_RUN`。

## 本轮只做一条完整链路

### A. 环境、代码和 ADAI 原生烟测（开工门槛）

1. 拉取 `origin/main` 并确认干净工作树；阅读 `AGENTS.md`、`docs/CURRENT_TASK.md`、`docs/EXECUTION_GUARDRAILS.md`、`docs/TEST_EVIDENCE_PROTOCOL.md` 和上一轮结果。
2. 在本机执行 `powershell -NoProfile -File scripts/check.ps1`；保留命令输出与失败详情，不为了变绿而跳过已有检查。
3. ADAI 官方 Skill：若未安装，用 `python scripts/install_adai_components.py --install skill`；若已安装，核实其 manifest/hash。原 CPAL LICENSE/NOTICE 不得删除、不得提交复制来源代码。MCP 官方 ZIP 不需要与已有 Kongxing 同时运行；**禁止双写者同控一模型**。
4. 在**新的可丢弃空白 SketchUp 2024 文档**中使用单一 Kongxing writer，给**该测试进程**开启 `ARCH_STUDIO_ENABLE_ADAI_GEOMETRY=1`，实际调用已导入的 `adai_geometry` 做一个 **带多个真开洞的连续墙** 和一个**非平凡截面/屋面轮廓**。用 root-owned 回读、实际 front/oblique 截图、writer receipts 和原生重新打开证明几何存在。若遇 SU Ruby 版本/API 兼容错误，局部修复集成后重跑。
5. 快速复核现有 precommit KEEP 保护仍然正常：故意破坏受保护对象必须 transaction 内 abort、revision 不前进、last-good 脚本保留；不能在测试后留下被破坏的模型。记录 guard-results；不要长期停在工程 smoke 而没有进入完整建筑。

### B. 在**真实网站**用 Codex 高能力模型完成六视图别墅

1. 用仓库已公开整张参考图 `test-assets/cloud-villa/villa-six-view-sheet.png`。**整图上传，不裁剪成六张**；独立新会话、独立空白 SU2024 模型、源图可推断尺寸按图证据区分 KNOWN/ESTIMATED/ASSUMED。不能把上次 Sol 的截图、产出 SKP 或 baseline.rb 冒充本轮建模。
2. 在同一 K AI Studio 网站里经历“上传图→对话/规划→确认一轮关键参数→执行建模→查看真实截图→定向修正→下载 SKP”。`reconstruction_evidence.json`、`facade_schedule.json`、`construction_strategy.json` 要通过真实 schema 校验；Agent 先写错时允许**有界内部修复**，不能静默跳过或频繁反问用户。策略 current_stage/status 应反映真实执行，而非始终 pending。
3. 明确使用已安装的 ADAI **几何 helper**（至少一个墙洞/屋面构造方法），按需要与原 SAIE/ProjectRuby 组合；Kongxing 单写者及主机事务继续掌控几何。记录 ADAI 方法名、调用位置、返回状态、模型读回和是否真正改善缺陷；光“装上 ZIP”不算完成。
4. 一个主建模 pass，最多两轮 targeted correction。先主体/开洞/屋顶→重复模块→细节，保留已正确 group；修墙顶线、窗口/阳台比例、必要场地和家具，**不允许为了漂亮的 QA 而删原图约束或退化成白盒**。
5. 每次写入后校验 writer receipt、root/project ID、原有 KEEP 指纹；最终六个主机认证角度 **front/rear/left/right/roof/oblique** 来自最新 revision，同一建筑不同视图一致，必要时额外 capture 近景屋顶/门窗。保留原始 `canonical_view` sidecar，不允许假改名。
6. 用**独立只读 Critic**检查源图所示形态、开洞位置、屋顶、拼缝、构件复制、场地材质等，并通过可信后审更新 `qa/repair_history.json`；如果原生运行路径仍不支持真正独立 Critic，明确 `reviewer_mode=agent_supplied` 与 PARTIAL，不可造一个独立 PASS。缺陷仍在两轮后如实保留。
7. 最终从网站下载 SKP → SketchUp 原生打开 → 对测试副本使用鼠标移动/修改一个明确的命名对象 → 保存 → 再次重开/完整 readback，证明 editable；绝不能修改用户原 SKP。记录已下载文件与 artifact SHA256、对象数量与尺寸核对，保留不可上传的 SKP 在本机，不推 GitHub。

### C. 强制 GitHub 上传（未来**每一次**真实测试都一样）

按照 [证据协议](TEST_EVIDENCE_PROTOCOL.md)，本次目录固定为：

`docs/test-results/windows/2026-10-09-kai-integrated-v1/`

**必须把实际 PNG 拷贝并提交到仓库**，不仅是 Markdown 中写路径：`views/front.png`、`rear.png`、`left.png`、`right.png`、`roof.png`、`oblique.png`，每张附 `.evidence.json`；再附 `source-perspective.png` 和有用的局部近景。确保它们来自本轮最终 revision，不是旧截图。

保留同一目录的：
- `README.md`：中文真实过程、PASS/PARTIAL/FAIL、引用全部 PNG、问题优先级、与上轮已知缺陷的自然进度说明（不要求 A/B）。
- `run.json`：实际模型 ID/推理档、Codex Native/website 路径、git 基线、SU/bridge/ADAI 版本、建模是否真正提交、reviewer.mode。
- `metrics.json`：每轮及合计的输入/输出 token、耗时、调用数/失败数、写入数、全部 root rebuild 数、定向修补次数、人工干预；无法读到 token 就写 **null** 并注明缺失来源，绝不填 0 假装免费。
- `errors.json`、`planning/...` 三项 schema 输出及错误、`model/write-verifications.json`、`geometry-readback.json`、`keep-results.json`、`native-reopen.json`、`review/critique.json`、`review/review.md`。
- 所有数据和截图真实、脱敏；API Key、Token、私有图纸、用户原 SKP、个人本机路径及完整私人聊天严禁提交公开 GitHub。

用 `python scripts/validate_test_evidence.py docs/test-results/windows/2026-10-09-kai-integrated-v1 --write-manifest` 生成证据哈希清单，再无参数校验一次。若模型连接失败没有 geometry，允许提交真实 `FAIL/BLOCKED`、`geometry_committed=false` 的报告/错误记录而不伪造六张 PNG，并写出原因。

### D. 完成定义与交接

- 最小可接受交付：代码可正常检查、ADAI 真 SU2024 方法证据、**一次新的完整别墅网站建模流程**（即使视觉 PARTIAL）、最新六视图、指标/错误/对象读回、下载并原生重开、KEEP 安全，以及真实独立/自审模式披露。
- 整体视觉是否 PASS 取决于可见截图和参考图，不取决于 writer 技术是否成功；如无法完成，真实 FAIL/PARTIAL + 已有证据也要提交。
- 只在本次 K AI Studio `main` 工作；若本地已有用户未提交变更，不覆盖、不强制 reset，先安全协调。真实测试产生合理代码修正时增加必要回归测试，避免顺便大幅重构。
- 更新 `docs/HANDOFF.md`、`docs/CURRENT_TASK.md` 最新状态，提交**代码、Markdown、截图 PNG、脱敏 JSON** 到 `origin/main`，确认 SHA 可在 GitHub 查看。给用户返回：新 commit SHA、GitHub 证据目录链接、截图/指标/结论和剩余障碍。
- SketchUp 2018–2026 仍是长期兼容目标，不要求本轮安装 9 个版本；不可将 SU2024 PASS 推广为全版本支持。

**本轮结束后由 ChatGPT 读取该 GitHub 目录中的真实 PNG/metrics/修正脚本/证据及变更记录，再决定下一次 K AI Studio 产品迭代。**

