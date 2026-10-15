# NEXT — 同八图网站 r4：源图—几何诊断与有条件的一次斜撑修复（2026-10-15）

**本文件是下一轮 CodeF 唯一执行入口。** 当前工作不重生成整栋，不换案例，不增加 CAD/渲染/PPT/商业功能，不重跑已完成的原版 Codex CLI 对照。历史 FAIL/PARTIAL/NOT_RUN 不可改写。运行前重新 fetch 最新 main，先读 `AGENTS.md`、`docs/CURRENT.md` 顶部；准备时 HEAD `f7a1ce75cec409dd5450a7d662c69799ebf459a7` 只是当时快照。

## 事实与证据

- 同一网站项目 `architecture-project-4f0e4`，八张原图的原始 SHA/顺序、六个 SKP 版本、完整记录在 [公开审查入口](test-assets/architecture-project-4f0e4/README.md)。公开授权**只涵盖此案例**；API Key、账号、密码、cookies、认证令牌/容器仍须严格排除，其他案例不自动公开。
- 恢复后的网站 r4，SketchUp2024 原生根 PID **20606**，整文档深层几何/材质 SHA **`b3fb8fbde6ae874a78570201b78dbd635072b9204ca9881c8972d189bfd14e10`**（不是 SKP 文件字节 SHA）。10月15日恢复时绑定 SKP 字节 SHA 为 `c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db`；仅对同一原文件按字节比较。GUID/文件路径必须真机重新读取，不硬编码。[恢复证据](test-results/windows/2026-10-15-r4-native-restoration-closeout/README.md)。
- r4 原生保存/网站下载/重开 PASS，整栋八图保真 FAIL/整体 PARTIAL；原 r1 历史保存前 BLOCKED、r4 严格空白 replay NOT_RUN、网站新 instruction-root 边界下的建模复测 NOT_RUN。原版对照已完结，不重复。
- 网站仅在真实可用时使用实际 Codex App Server `gpt-6.1-sol / medium`，须验证返回身份；外层 CodeF 控制模型不改。ProjectRuby/Kongxing 单一受保护写者、用户批准、KEEP/作用域、独立 Critic、原图顺序全部保留。无付费 API 授权，本地 Native Token/tool cap 为0不限但不等于模型账户无限或无限几何修改。

## Gate A — 只读诊断，模型写入数必须为零

1. `git fetch`、检查最新 HEAD/交接；备份 r4 原始 SKP、项目状态、八图及日志，所有检测在安全副本进行，原始 r4 不覆盖。核对源图顺序与原始 SHA。验证实际 SketchUp2024 前台、已打开模型路径、实际 GUID、root PID=20606、无组编辑路径；身份不一致 BLOCKED，不能强行 rebind。切换前台失败绝不向聊天窗口输入路径/Enter；须验证新鲜原生对话框并点击 Open。
2. 逐张看真实八图、已发布 `spatial_spec.json`（状态 `AGENT_REVIEWED_OWNER_DELEGATED`，**不是** OWNER_CONFIRMED）、`reconstruction_card.md`、r4 当前六视图和原 Critic。不得把无法看到的内部联系、尺寸或方向猜成已验证。
3. 新建安全 r4 原生深层读回，使用固定只读命令：`python -m scripts.capture_native_deep_fingerprint --model "ABSOLUTE_ALREADY_OPEN_SAFE_COPY.skp" --guid "ACTUAL_LIVE_GUID" --root-pid 20606 --output "NEW_DIR/native/r4-before.json"`。先检查 collector/根/整文档 SHA 等于上面的 r4 基线，查 `document_groups` 是否有逃逸顶层组，核对真实 `TENSION_BRACING` 是根直系还是嵌套。源文件、当前网站工作模型与读回若非同 revision，立即 BLOCKED。
4. 生成四行**有来源的差异矩阵**：`TENSION_BRACING`（薄拉索 vs 厚三角带）、`RAMPS/landings`（连续路径及平台）、`ENVELOPE_OUTER`（轻型框架及玻璃）、`FLOORS/INTERIOR`（大挑空/中间层）。每行引用实际编号源图、对应源图特征、相同机位 r4 截图、真实 PID/路径/世界坐标/剖面截面/材质、来源/推断/未知区别。状态只可选 `CONFIRMED_GEOMETRY_MISMATCH`、`PRESENTATION_ONLY`、`MATCH`、`UNRESOLVED`、`BLOCKED`。保留模糊之处，不编造数值/视图。源图4/5/7/8可辅助挑空判断，但外观图不能证明内部几何。交付易读的带箭头空间/剖面图、图片成对对照，截图必须实际采集。
5. 对斜撑明确判因：是否真实存在厚实面/实体和截面？还是视角、材质、显隐导致？核对端点、连接、名称、PID、材质、世界位置与源图“细杆/拉索”表达。此诊断是参考图还原任务，不做结构安全认定。独立只读审查，不用 Builder 自评冒充 Critic。若根本原因不明确/作用域不确定，Gate B NOT_RUN 并停，不用猜测修复。

Gate A 输出至 `docs/test-results/windows/<实际日期>-eight-source-r4-quality-diagnosis/`：README、真实八图 SHA/顺序、差异矩阵、`diagnosis.json`（可从 [空模板](EIGHT_SOURCE_R4_DIAGNOSIS_TEMPLATE_2026-10-15.json) 填写，不能把 NOT_RUN 模板当结果）、原图与 r4 同机位对照、深层 read-only JSON、带方向的剖面/拓扑示意、实际错误/Token/耗时/工具记录与局限说明。新产生的日志/图片仍执行认证信息检查。

## Gate B — 仅当斜撑为已证明的几何错误，允许一次有界网站局部修改

- 若 Gate A 证明 `TENSION_BRACING` 是厚实体与原图薄构件之间的**真实几何差异**且实际归属、受影响构件明确，再在备份的同网站 r4 工作副本进行**至多一次受保护几何提交**，保持原八图顺序和真实 gpt-6.1-sol/medium。普通学生用户聊天只发简短中文：

> 原图里的屋顶斜向支撑是比较轻、比较细的杆件或拉索，现在模型里显得太厚，挡住了通道。请只按原图修正这些斜向构件的粗细和连接，保留现有曲面屋顶、左右高低、净空、坡道、幕墙、楼板和其他部分不变。

- 任何新增结构歧义都停止澄清，不能擅自重建。提交后的超时先只读确认 receipt/实际模型 SHA；最多一次**只读**恢复，不重复提交几何。不切到独立CLI/付费 API，不无限重试。
- 新 `scripts.audit_scoped_native_edit` **只支持根下直系命名组 `TENSION_BRACING`**。如果真实斜撑为嵌套路径，不得为了让脚本 PASS 而重命名、移出原父组或扩大 allowed 到 `ROOF_TIMBER`；**暂停写入**，先依据真实证据补充路径级保护及负例测试，再另定写入任务。直系验证可运行：
  `python -m scripts.audit_scoped_native_edit BEFORE.json AFTER.json --expected-before-document-sha b3fb8fbde6ae874a78570201b78dbd635072b9204ca9881c8972d189bfd14e10 --allowed-direct-group TENSION_BRACING --json`
- 此脚本只审核直系保护组/外部顶层组/根变换/呈现状态及目标确实变化；**不是**整文档松散几何免疫证明。须额外实测 root 自身松散实体、host KEEP 与实际目标深层 geometry/material/PID。`scope PASS` 不等于保真、交付、重放 PASS。
- 独立 Critic 用**同一参考原图与匹配机位**对比 r4 BEFORE 和实际 AFTER（近景截面+六视图），分别判定斜撑截面/端部连接改善、屋顶/坡道/玻璃/楼板回归影响。随后网站真实保存、点击下载，**新鲜**绑定副本重开与下载副本原生重开：三阶段深层指纹交由 `scripts.audit_native_delivery_stages`；严格空白 replay 未另测仍 NOT_RUN。不能覆盖原始 r4。

## Gate C — 验收、停止与真实回传

每项独立报告 `DIAGNOSIS`、`SOURCE_FIDELITY`、`SCOPED_EDIT`、`PROTECTED_GEOMETRY`、`DELIVERY_3_STAGE`、`STRICT_BLANK_REPLAY`、`WEBSITE_POST_PATCH` 的 PASS/FAIL/BLOCKED/NOT_RUN。门槛：实证缺陷→同图同机位看得到改善、非目标原生深层/松散几何零意外变化、真实单次写入、三阶段交付一致、自然对话能恢复。容量/身份/权限问题标 BLOCKED；保留初次 FAIL 与恢复后的分开结果。不将 CI 单元测试/脚本数量/代码提交数说成产品 PASS。

如 Gate A 显示斜撑并非最确定几何问题，只输出诊断与下一次单缺陷建议，**不自动改换其它写入目标**。按实际结果提交 README、指标、截图/原生证据、必要最小补丁和负例测试，更新 `docs/CURRENT.md`、`docs/HANDOFF.md` 顶部；不要漏源图/结果的 SHA、运行模型真实身份和 token/耗时的不可得值（未知记 null）。

**本仓库当前提交的是下一轮只读作用域审计脚本/8项本地合成回归/任务说明/空模板；这不是已经执行过的 CodeF/SU2024 真实诊断或修复。**
