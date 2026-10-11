# Dream Coffee r3 → r4 受保护局部修复：PARTIAL

## 实际执行与结论

同一私密五面板整图、K Studio 网站 Native App Server、实际 `gpt-6-luna / max`、SketchUp 2024 24.0.484、Kongxing。参考图未拆分，未公开原图或私人 SKP。本批包含 2026-10-10 至 11 的正式修复运行，旧报告没有覆盖。

正式根 PID35529，r3 的110组 → r4 的116组。只有一笔正式局部几何提交；最后候选未提交。未人工修改正式模型几何，未全局重建。保留原屋顶、门窗、玻璃、楼梯等110组的递归世界坐标几何/面材质指纹均相同。指纹不覆盖全部属性、隐藏状态或继承材质，不能等同于全部语义不变。

| 验收 | 真实结果 |
|---|---|
| 声明编辑范围 + KEEP 正例 | PASS，专用副本真实提交并读回 |
| 越界删 MATERIAL_ZONES | 事务 abort，revision保持4；完整负例后递归指纹未采集，不宣称该层验证通过 |
| 正式 r4 写后验证、范围与 KEEP | PASS，原110组指纹一致，新增6组 |
| 当前六方向 PNG/sidecar | 已采集，同一r4；构图仍有留白 |
| 独立源图+真实修正前后审查 | PARTIAL；雨棚FAIL、木饰面PARTIAL |
| 2.5M Native 输入预算 | 两次真实中断PASS；64次工具上限真机未触发NOT_RUN |
| 建模阶段同步 | 部分直属系统built；嵌套路径pending，仍primary_form，不能报建模完成 |
| SKP网页下载 | 已下载，SHA256与正式导出一致 |
| 原生重开、鼠标修改、保存再开 | 当前BLOCKED：工具仍看到Windows锁屏；没有用Ruby编辑冒充鼠标测试 |
| 新空白 baseline 重放 | 空白已准备；当前BLOCKED，未验证 |
| 全部自动检查 | 334 passed、2 skipped、2 warnings；见[checks](checks.txt) |

## 视觉观察

新增平雨棚把上层露台遮成大块实体板，与遮阳伞、玻璃观察区域在图像上拥挤重叠。独立 Critic 判断它不符合参考图的局部遮阳构件；截图不足以证明精确三维碰撞。右侧木饰面仅有五段较宽分缝，仍是平坦桃色，缺少源图木板密度与材质层次。开放柱廊没有封闭重建，但这不等于源图比例完全正确。室内局部暗面问题仍未解决。

六方向：[front](views/front.png)、[rear](views/rear.png)、[left](views/left.png)、[right](views/right.png)、[roof](views/roof.png)、[oblique](views/oblique.png)；[源角度实际模型](source-perspective.png)。

雨棚：[修正前](before/canopy.png) → [修正后](after/canopy.png)；木饰面：[前](before/timber.png) → [后](after/timber.png)；[独立前后Critic完整结果](model/protected-before-after-critic.json)。源图私密，因此云端只能检查真实模型图及审查记录，无法独立复核原图像素。

## 外部能力吸收结果

| 方法 | 本次适用与实际执行 | 效果/后续 |
|---|---|---|
| SAIE 墙洞 | 原r3已有，KEEP不允许为了计数重新生成墙洞；本次修复0次wrapped调用 | 保留已有墙洞，不把历史调用算新采用 |
| ADAI0.5.39 profile | 尝试用于新雨棚；Ruby `def`无法捕获注入局部变量，NameError，未提交 | 不是证明helper未注入；提示已改为lambda/显式传参 |
| 持久 Ruby | 正式新增雨棚板、梁、柱和木分缝；该笔OSS账本events为空 | 技术提交成立，视觉未通过；不宣称ADAI实用化PASS |

[真实OSS账本](model/oss-method-ledger.json)、[采用读回](model/oss-method-adoption.json)、[全部错误](errors.json)。

## 效率、流程错误与修复

十个正式Native事件合计8,032,977 input /152,170 output、110工具调用、12失败工具、一笔正式写入。四个Builder回合含两次2.5M中断，另有超时。小预算探针单独记录，不混入正式总量。独立Critic与Builder逐轮指标见[metrics](metrics.json)；部分Critic延时不可用为null。成本效率FAIL，不能拿局部修复与上次10.504M完整建模直接声称降本。

修复：Critic无assessment的NO不能被接受；合并全部KEEP块；Native早期中断初始化与真实终止/工具exit_code日志；ADAI局部变量作用域提示；Skill要求只把已提交且写后验证成功的候选合并baseline。相关回归测试全部通过。

实际Builder曾在候选04被执行门挡住前覆盖baseline。操作者已保留该未执行候选，恢复为原r3前缀+准确已提交patch03；尚不能宣称空白重放验证通过。`scripts/dream_coffee_uncommitted_candidate04.rb`及repair04仅审计未提交方案，不是正式r4几何。不能凭文件存在判断执行成功。

## 下一轮可执行项

先恢复可操作Windows桌面，完成下载副本原生鼠标编辑和空白重放。继续同一r4：在白名单范围内把雨棚改为源图位置/尺寸，深化木板；保留其余构件。先修复审查门状态同步与候选baseline推广顺序，避免重复对话和准备脚本却不提交。不得放宽Critic标准或无限增加Native回合。公开证据校验清单由validator生成。
