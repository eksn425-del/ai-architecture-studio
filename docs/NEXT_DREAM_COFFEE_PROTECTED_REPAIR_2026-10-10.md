# Codex 下一轮唯一真机任务：Dream Coffee 保真局部修正 / GitHub 全证据（2026-10-10）

## 任务边界与起点

用户已要求 ChatGPT 根据上一轮证据**修改 K AI Studio 的实际代码**，现在已完成首版修改。本轮你（Codex）直接用最新 `origin/main` + 自己的 Windows / SketchUp 2024 真机接力；**继续现有 Dream Coffee 新五面板建筑，不要回旧别墅/旧咖啡店，也不要凭空用别的图代替。** 原私人五面板源图只在用户现有本地会话/授权资产中读取，未经同意绝不上传 GitHub。找不到原图就先告诉用户需要重新发送，不得猜测。

- 最后完整真实旧证据：[2026-10-10 Dream Coffee r3](test-results/windows/2026-10-10-dream-coffee-oss/README.md)
- 最新产品代码：`app/edit_scope_guard.rb`, `app/project_ruby.py`, `app/workspace_ruby.py`, `app/agent_tools.py`, `app/strategy_progress.py`, `app/native_agent.py`。
- 关联：[GitHub Issue #4：修复局部退化](https://github.com/eksn425-del/ai-architecture-studio/issues/4)，[Issue #3：OSS 方法真实使用](https://github.com/eksn425-del/ai-architecture-studio/issues/3)。
- **运行前先** `git pull --ff-only`、清理前置运行状态（不能 `reset --hard` 丢用户改动）、重启 K AI Studio 源码服务，保证本次测试确实载入新的 Python/Ruby 文件。读取 `AGENTS.md`、本任务和 `docs/TEST_EVIDENCE_PROTOCOL.md`。运行 `powershell -NoProfile -File scripts/check.ps1`，记录全量结果。
- 测试路径：现有 K AI Studio 网站 → Codex Native 实际可选 GPT-6 Luna Max（报告真实 model/effort）→ Kongxing 单 writer → SketchUp 2024 的**项目专属可丢弃/重放副本**。ADAI opt-in + SAIE 按实际任务需要选择，不能开双 MCP、不能为了凑调用而乱用。

## A. 新代码实机先验：修正必须有边界

**A1 正例：**从真实 r3 的**测试副本**或可重放 baseline 起步，挑 `FRONT_ENTRY_OPENING_HOST` 这样的单一子组进行不改变参考主形的小改动，调用 `sketchup_run_workspace_ruby`：
- `update_mode=edit`，传 `allowed_mutation_paths` 为允许更改、删除或新增的**所有直接顶层名字/所属顶层路径**。其余原有顶层对象要由 `KStudioEditScopeGuard` 自动保护；如果新增组未在白名单也应拒绝。
- 同时使用 `preserve_paths` 明确 KEEP 已知正确的山墙/屋面/其他局部对象，确认 precommit KEEP 与 `edit_scope_receipt.status=passed`，外部 PIDs/child counts/bounds 没变化。
- 当前保护是**顶层未修改对象的拓扑与边界约束**；它不能证明白名单内部视觉效果没有恶化。因此还要修正前后来源匹配图。

**A2 负例（必须用可丢弃独立副本）：**白名单只允许前入口子组，却故意删改木饰面或屋顶顶层。宿主应在**事务提交前**阻止越界，旧 root revision/ID/persistent script 与非白名单对象保持不变，保留真实 abort receipt。未通过时先修运行时代码，不能用提示词说“以后注意”。

**A3 真实阶段状态：**确认 `construction_progress.json` 的 `script_id/revision/root_pid` 与最新提交一致，`construction_strategy.json` 中**经直接 root readback 证实**的目标才从 `pending` 更新为 `built`；包含嵌套路径但尚未经过真实 nested readback 的系统保持待验证，需通过修正错误路径或扩展安全只读路径验证（不改为虚假 built），视觉 `verified` 仅来自后审。历史 Dream Coffee 的 13 个状态均 pending 是本轮待修。

## B. Dream Coffee 保真修正：先解决两个清楚的视觉错误

从保存的 Dream Coffee 模型 r3 作为当前视觉起点；**本次最多两轮 targeted correction，不得偷换成重新全局建模**。

1. **优先修 P1：**上层露台缺少的水平外伸雨棚及支撑，确保连接在玻璃屋顶旁合适位置，但不重复/遮挡原有双坡玻璃温室；检查露台轮廓和室外通行。
2. **优先修 P2：**恢复右侧墙的真实木饰面层次，观察历史 `before-r1` 与现 r3。r1 原有二十条木装饰线被简化成三块平板，导致视觉退化。选择源图中可见的正确分格频率、厚度和材料；不能只往整墙贴纯色。
3. 检查首层柱廊是否保持开放、入口玻璃与斜玻璃附体比例正确，屋架不叠层；不要随意移动前景树木遮挡错误，也不要损伤准确的门窗/双坡屋顶。
4. 每次局部修正明确：`repair_intent`（原图问题、目标组、允许修改的路径、预期变化、受保护路径、源角度），实际适用的 SAIE / ADAI 方法或自写 Ruby 理由，commit/writer receipt、`edit_scope_receipt`、KEEP 前后指纹。**视觉成功的标准是建筑源码约束和真正的局部前后图，不是对象数增加。**
5. 每轮修正前后都用真实同方向、同尺度的特写比对：露台雨棚、右侧木饰面、主入口。每轮后复拍当前模型六方向 front/rear/left/right/roof/oblique，当前 revision 一致，另拍源图对应角度/室内视角以核对右中室内面板。源图不能公开时只上传模型生成的图，并通过 private source hash 引用原图。
6. **独立只读 Critic** 在最终当前 revision 上执行，要求能发现“木饰面退化/雨棚缺失/玻璃被遮挡/重复屋顶/尺度错误”，带 `KEEP` 和修正建议。没有真实 source-match 或 Critic 仍 NEEDS_FIX，则整体视觉只能 PARTIAL。

## C. 降低失败调用和 Token 消耗

- 新版 `app/native_agent.py` 默认每个 Native Builder turn **64 次可观测工具调用、2,500,000 输入 token**的主动限制；若 Codex 不提供实时 usage，无法凭空实时计算，要记录 `unavailable`。这属于**每个 turn 的熔断器，不是整轮自动降本证明**。
- 按“先规划一次 → 一个主修改方案 → 最多两次有限局部修正 → 总结”进行。绝不无限重复构思、反复查看相同主图、重建整栋楼或在 token 失控时不断启动新的大上下文 turn。
- 对 budget_exhausted 真实中断：应保留已提交 SKP 和可恢复源，不把 INTERRUPTED 改写为 PASS。分开记录总 input/output token、失败工具原因、有效/无效调用比例、每阶段时长。对照旧 10,504,446 input／160 次工具／26 失败，只判断是否真实降低，不做不同条件下的夸大性加速。
- 记录 `planning/adai_geometry_contract.md` **作为旧历史证据，不要回写改造历史原始档案**；本次另生成与真实 ADAI 开关一致的运行环境说明，避免“disabled”旧说明误导执行。

## D. 持久源与证据（每次真机必须推 GitHub）

- 每次针对当前对象的局部修改都同步到项目持久 Ruby baseline，最后在**另一个全新空白的项目副本**重放当前最终源，检查全部命名对象/PID 无需跨副本一致，但**名称、数量、尺寸和关键材料/拓扑**应与主模型的当前最终 revision 对应。上次首次重放失败的历史记录不抹掉。
- 浏览器下载本轮 SKP → SketchUp 原生打开副本 → 鼠标修改一个非 KEEP 子组 → 保存并原生重开读回；确认原正式模型没被误改。
- 新建事实目录：`docs/test-results/windows/2026-10-10-dream-coffee-protected-repair/`（若实际执行日期变化，目录日期改为当天）。保留 `run.json`、`metrics.json`、`errors.json`、六方向真实 PNG + sidecar、source-perspective、before/after closeup、独立 Critic、修正计划和 `edit_scope_receipt`、本轮 updated construction_strategy 和 construction_progress、OSS actual ledger/adoption、所有 writer/KEEP/baseline/native reopen 凭据。即使失败也上传真实 FAIL/BLOCKED 资料。
- 禁止上传原私人来源图、SKP、Keys、token 或原始隐私日志。当前参考图原件未公开，因此 GitHub 图片无法独立完成像素级比对，需如实披露。
- 运行 `python scripts/validate_test_evidence.py <folder> --write-manifest` 和无参数校验；**确保新证据 GitHub Actions 也通过**。前一轮 GitHub evidence manifest 已由 ChatGPT 修复跨 Windows/Linux 排序逻辑，不许复制旧 JSON 伪装本轮。
- 再运行 `scripts/check.ps1`，所有修复代码/新测试/实图/JSON 更新 `docs/CURRENT_TASK.md` 和 `docs/HANDOFF.md` 后 commit/push `origin/main`；确认远端 SHA、报告目录、CI 结果，并总结每项 P0 原因/改动/效果（PASS / PARTIAL / FAIL）。

## 验收限制与现状

ChatGPT 仅完成 GitHub 源码改动、CI 中 Python/Ruby 离线测试；**尚未通过真 Windows SketchUp 2024 验证新版运行时的 edit-scope / construction-progress / native budget**。第一条 Codex Windows 操作就必须现场验证，无法通过时不要跳过继续声称“能力已落地”。

本轮不启用 CAD 施工图、效果图、漫游/动画、网页 PPT、多版本 SketchUp 2018–26 兼容性攻坚，也不增加新开源仓库；只守住“从现有证据修出更正确的同一建筑且不会破坏别处”。
