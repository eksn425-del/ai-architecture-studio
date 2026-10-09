# Windows / SketchUp 2024 验收 — 2026-10-09

## 结论

**技术通路大部分 PASS；建筑高保真、完整独立 Critic 闭环仍 PARTIAL。** 没有把成功的 writer receipt、非空模型或保存成功当作视觉验收通过。

用户在本轮明确改用 **GPT-6.1 Sol / Low**。最终两项建筑执行均使用此路线，没有调用 Astra。原 DeepSeek 验收不能因此标为完成；本轮早期 DeepSeek 失败也保留在报告中。

| 验收项 | 结果 | 可公开证据 |
| --- | --- | --- |
| 全部自动测试 / compileall | PASS：289 passed、2 skipped、2 warnings | 下述命令、代码中的回归测试 |
| SU2024 + 现有 Kongxing 连接、独立空白模型 | PASS | writer receipts、原生重开 readback |
| 两面连续 SAIE 墙、各三个真洞口 | PASS 技术 smoke；不代表建筑质量 | [六方向墙洞截图](wall-smoke/oblique.png) |
| canonical 六方向、实际相机、无模型裁切 | PASS 方向/来源；构图有改进空间 | [相机 sidecars](wall-smoke/roof.evidence.json)、[建筑六视图](six/visual-review.json) |
| 故意互换 front/rear 标签 | PASS：质量门拒绝 | [mislabel rejection](wall-smoke/mislabel-rejection.json) |
| KEEP 正向局部修正 / 故意移动保护对象 | PASS 检测；负例已提交，不自动 Undo | [正例](keep-smoke/positive.json)、[负例](keep-smoke/negative.json) |
| 咖啡馆单图还原 | PARTIAL：完整可辨认三层建筑；家具、植被、比例/材质细节仍简化 | [源角度模型图](single/source-perspective.png)、[审查](single/visual-review.json) |
| 白色别墅完整六视图还原 | PARTIAL：主体、门窗、阳台、木格栅、屋顶；家具、场地、墙顶拼接线仍不足 | [源角度模型图](six/source-perspective.png)、[审查](six/visual_qa.md) |
| v2.7 方法路由 | PARTIAL：实际采用连续墙洞、轮廓女儿墙、代表模块；strategy 阶段状态没有随执行更新 | [strategy](six/construction_strategy.json)、[验证记录](six/planning-validation.json) |
| v2.4 六视图证据契约 | FAIL 本轮：Native 输出格式错误被旧加载器静默忽略；已修复严格拒绝，需新一轮验证规划输出 | [真实拒绝结果](six/planning-validation.json) |
| dedicated Critic | 未完成：Native 路线为 Builder 自审，未实现独立只读 Critic | review.reviewer.mode=agent_supplied |
| 咖啡馆 / 别墅新空白完整 baseline replay | PASS 执行与 readback；继承原视觉 PARTIAL | [咖啡馆 replay](replay/oblique.png)、[别墅 replay](six-replay/oblique.png)、[receipt](six-replay/write-verification.json) |
| 网页下载 SKP / 原生重新打开 | PASS：两项下载文件 hash 与 host artifact 相同，SU2024 能读取编辑对象 | [咖啡馆下载](single/download-proof.json)、[别墅下载](six/download-proof.json)、[别墅对象 ID](six/native-reopened-readback.json) |
| 鼠标修改对象、保存、原生再次打开 | PASS 咖啡馆测试副本：MENU_BOARD0 的变更读回，711 个对象仍存在 | [重开全部对象](single/native-reopened-all.json) |
| 与旧 4.92M input token 对照 | PARTIAL：现集成未记录 Native 每轮 token，且模型/素材/运行路线不同，不能算受控降本对比 | [metrics](metrics.json)、[DeepSeek 压缩事件](deepseek-compaction-events.json) |

## 环境与复现

- Windows 11 Home 10.0.22000；SketchUp **2024 / 24.0.484**。
- Kongxing AI 0.1.0，复用已安装的本机桥；未替换连接器。现有第三方扩展启动提示由人工关闭，未改其代码。
- Python 3.12.2；FastAPI 0.141.1；Pydantic 2.13.5；LiteLLM 1.102.1；pytest 8.4.2。
- 最初拉取 `b6bfbb9945077345ca10f28db2ba72bc15686d73`；执行中合并远端 `8c6f315`，保留本机修复，没有覆盖远端 v2.6/v2.7。
- 通过现有本机网页完整执行上传、对话、计划修改、批准、自动连接、写入、截图、修正、下载。专用模型均为 ignored runtime 下的空白/测试副本，没有修改用户原始模型。

```powershell
git pull --ff-only
powershell -NoProfile -File scripts/check.ps1
.venv/Scripts/python.exe -m pytest tests/test_construction_strategy.py tests/test_codex_parity.py tests/test_context_compaction.py tests/test_image_to_sketchup.py
```

重新跑建筑：从网页创建专用新会话，使用 GPT-6.1 Sol Low；上传单图或整张六视图，确认估算/范围后批准一次，让 Agent 内部连续执行。每次 writer 后检查当前 `write_verification`、canonical sidecars、source-matched pair、reviewer 类型及 KEEP receipt。最大两轮修正后仍不匹配则报告 PARTIAL，不为 PASS 降低标准。

本次咖啡馆只有用户提供的一张图片，不能伪造它的完整六视图。多视图测试使用仓库原有的 [白色别墅六视图整图](../../../test-assets/cloud-villa/villa-six-view-sheet.png)，从始至终未拆图、未用旧 ZIP。该合成整图各面存在不完全一致的视觉信息，冲突须报告，不能当作精确尺寸控制包。

## 实际执行与干预

### 单图咖啡馆

最初 DeepSeek planner 花费 492.531 秒、33 次动态工具调用（23 次失败），输入 1,667,474 / 输出 106,776 token，主要是结构化证据格式猜错。其首次执行只生成三个工程探针对象；六张工具图片批量回传插入在 tool replies 中间，触发 DeepSeek HTTP 400。**这不是建筑还原成功。** 后来按用户要求切换 Sol Low，没有继续付费 DeepSeek 建模。

咖啡馆同一 script `forest_cafe` 的 r1 是旧探针；Sol 在 r2 建立 666 个命名对象，r3 修正入口/后窗/楼梯窗，r4 再修正推断侧窗及书架穿墙问题，最终 711 个对象，root PID **37843**。这是一次完整 Sol 建造及两次定向修正，分两次网页执行回合完成；不是全新 Sol 规划的受控基线。人未替 Builder 改几何。

最终三层退台、外楼梯、玻璃空间、Forest Cafe 招牌、叠层屋顶、家具和场地可辨认。仍有方块化家具/植被及源图比例、材质/暖光差异。Builder 的 NEEDS_FIX:NO 仅表示该回合所列两处修正结束，**不等于整体视觉 PASS**。其“698 个旧对象 ID 保留”是 Agent 自述，公开截断 writer snapshot 不能独立证明全部 698 个；不要拿此数字冒充全量 KEEP 证明。

SKP 从网页实际下载。用下载 artifact 的专用副本在 SU2024 原生打开，以鼠标移动 **MENU_BOARD0 / PID 77265**，Ctrl+S，原生再次打开，读回其 bounds min `[6217.7,680,-247]` / max `[6737.7,695,683]`，以及 711 个命名对象。这只是编辑性测试：鼠标位移未约束 Z，不能当作建筑质量优化。下载原 artifact 未被人改几何。之后另一个全新空白模型重放完整最终脚本，仍生成 711 个对象和相同整体 bounds。

### 六视图别墅

新会话 / 新空白模型，由 Sol Low 写参数、证据清单、立面表和 strategy。初次 strategy 使用非法枚举、尺寸数组；补充真实 schema 文档后由模型修复，host 验证 11 个系统 / 47 个共享尺寸参数。

Builder 一次连续执行 **550.813 秒、45 次动态 SketchUp 工具调用、11 次失败**。一次初始完整建造加两次 `update_mode=edit` 修正；无人工几何编辑。root PID **43871**，内部 `villa` PID **43883**，含 11 个系统。使用 SAIE 连续墙多洞口、真实门窗内退、玻璃栏杆、轮廓屋面/女儿墙；先检查栏杆和木格栅代表模块再实例复制。首个栏杆尺寸断言失败后事务 abort，模型自修脚本再执行。见 [错误记录](six/tool-errors.json)。

两次修正改变格栅/门/屋面材质和显线，KEEP 指纹均通过：[write 2](six/keep-preservation-write-2.json)、[write 3](six/keep-preservation-write-3.json)。没有整根重建或自动升级 Astra。最终 r3 的六张 canonical 与额外源角度截图全部来自真实 SU2024。

仍有屋顶/墙顶水平拼接线、家具/植物过于方块、场地简化、部分比例/源图冲突。自审只给三项建议，未独立审查全部源面；因此不宣称所有立面视觉通过。

更严重的是 Native 直接写文件绕过 workspace tool 校验，证据 JSON 使用 `../../inputs/...` 和 `six_panel_exterior_sheet`，旧加载器静默返回 None，review 中 `fidelity_mode=pending`。修复后的严格 gate 已对**这份真实输出**拒绝一次试图 NEEDS_FIX:NO 的审查，没有覆写旧审查或伪造成功。该失败保留，格式说明改进仍需下一次模型规划实测。

完整最终 baseline 在另一个新空白模型重放，root PID **19**，writer 验证成功，紧接六方向 capture 全成功，没有旧 GUID 误报。网页下载 SKP 的 SHA256 与 artifact 一致；原生重开读到 11 个系统、13 组门窗、22 个格栅/衬板对象、59 个室内/植物命名对象。

## 修复与剩余问题

已修复：

1. DeepSeek 多工具回复与视觉图片的顺序：先回传完整 tool batch，再提供用户视觉块；回归测试覆盖一/两次工具。
2. 旧 Skill 文本截断、遗漏护栏，JSON 契约提示不足；提供 host schema 模板给隔离 Native workspace，保留 remote 的 KEEP 指令。
3. context compaction 不再让大 checkpoint 反而扩大请求；真实压缩事件保留，但 Native 降本仍无法计量。
4. Native 隔离登录缓存只同步较新的已授权登录状态，避免旧 refresh token 导致 401；未读取/提交密钥。
5. SketchUp2024 子组移动后 definition bounds 缓存：记录 expected bounds 前 invalidate；重新做正/负 KEEP 真机测试。
6. writer 的截图/zoom 后 GUID 刷新：重新核验同一 disposable path/context，不放松原模型保护；真实六视图 replay 验证。
7. Agent 说“没有保存工具”但 host 已保存：提示 host 保存职责，成功后追加软件确认，失败保留错误。本次旧对话错误文字仍在历史中，不能据此判断磁盘空白。
8. 非法 reconstruction evidence 不再静默绕过视觉 gate；提供 evidence/facade schema 说明。此修复只证明拒绝有效，未证明下次 Native 能自动产出合规格式。

仍待完成：

- Native Sol 的独立只读 Critic、每轮 token 指标与可比较的成本实验。
- Native planner schema 自动校验/有界修复；strategy 的 current_stage/status 未更新。
- 墙顶拼接/门窗比例、曲面家具、植被/场地和材质源图匹配的下一个方法级迭代。
- canonical 以含场地 root bounds 构图，建筑偏小但没有被裁切；需要 building-focus bounds。
- KEEP 指纹仅证明 ID/对象数/bounds，不能证明材质/内部拓扑完全不变；负例不自动撤销。
- 新安装用户的首次一键连接、打包桌面版与本机网页版本一致性未重新验收。
- 完整 CAD/平面/室内证据包缺失：`pending_external`；不能宣称 full-evidence PASS。

## 证据公开边界

本目录包含软件生成的模型截图、脱敏 receipt、对象 ID、验证失败及 metrics。**没有**私人参考原图、私人 SKP、账号、API Key、机器绝对路径或 Codex 登录状态。咖啡馆源图来自本次用户附件，未获原图公开授权，因此不提交；云端可检查模型结果与记录，不能独立重做源图像素比对。需同一源图实测时由用户在软件上传，不要求云端读取本机路径。

SKP 不提交。下载 hash、原生重开对象 readback 与手动编辑记录是公开可核查证据；其二进制原生重开不能在云端重复验证。本报告不把该限制藏在私人本机文件链接中。
