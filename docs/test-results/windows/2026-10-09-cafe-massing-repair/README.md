# 双视角咖啡店体量修复：PARTIAL

本轮继续用户两张完整咖啡店图，通过 K AI Studio 网站执行真实 `gpt-6-luna` / `max`，SketchUp 2024 24.0.484，Kongxing 单写者。基于 269826b 的本轮代码修改运行。私人原图未获公开许可，不上传；因此云端无法独立核对全部来源像素。以下均为真实 SU 截图，不是新生成效果图。

## 验收

| 项目 | 结果 | 证据 |
|---|---|---|
| 两次定向修正、写入验证、KEEP | PASS | [writer](model/write-verifications.json)、[KEEP](model/keep-results.json) |
| 同模型 r5 六方向相机与版本 | PASS | [front](views/front.png)、[rear](views/rear.png)、[left](views/left.png)、[right](views/right.png)、[roof](views/roof.png)、[oblique](views/oblique.png)，同名 evidence.json |
| 独立只读 Critic | 技术 PASS，视觉有漏检 | [三次实际审查](review/independent-review-history.json)、[最终审查](review/critique.json) |
| 下载 SKP → 原生打开 → 鼠标修改菜单 → 保存再打开 | PASS | [readback/hash/差异](model/native-reopen.json)、[前](model/repair-native-before.png)、[后](model/repair-native-readback.png) |
| 新 AEC 空白重放 | FAIL | [三个构件差异](model/baseline-replay.json)、[真实重放六图](replay/oblique.png) |
| Native 完整流程正常结束 | FAIL | [错误](errors.json)：1802640 ms 后超时，几何与截图已保留 |
| 建筑还原质量 | PARTIAL | [人工审查](review/review.md) |

## 修正前后与实际对象

[上轮 r3 高角度](before/prior-r3-source-high.png) → [本轮 r5 高角度](source-perspective.png)；[上轮低角度](before/prior-r3-source-low.png) → [本轮低角度](source-perspective-low.png)。before 明确是历史批次，不冒充本轮结果。

本轮共两笔 committed writes：r4/r5，同根 persistent ID 51007，最终34个直接命名组，完整读回见 [geometry](model/geometry-readback.json)。增加低白墙/低屋顶附属体块，删除错误巨大植物屏。没有人工修改 Builder 主模型。鼠标移动只在下载后的专用副本进行，菜单 PID 59243 改变，其余33组保持不变。私人 SKP 不上传。

## 代码修复与仍未解决

新增体量 inventory 指引；Native 宿主启动 fresh read-only Critic，真实来源整图 + 当前六图 + 两个来源角度，不接收 Builder 的拟定 PASS；记录线程 token 增量。测试 316 passed / 2 skipped。增加 KEEP 材料风格与待改尺寸的区分，禁止新增叠层绕过 KEEP；该最后指引是几何运行后补充，仅单元测试覆盖，尚未真机证明。

Builder 把 KEEP 屋顶误读为不准修改旧屋顶，于是加新层，仍有重复檐边；附体投影与石质外缘比例仍不准。独立 Critic 没可靠识别叠层。生成的持久 baseline 与实模3组 bounds 不一致。规划文件在 Agent 修改后出现 JSON 尾部多余内容，原始脱敏坏文档保留 planning/*.invalid.txt；这是新发现的失败，不伪造 schema PASS。后续需要写后再次严格校验。

## 指标与介入

[metrics](metrics.json)：Builder input 10,528,462 / output 116,074；三次 Critic input 114,994 / output 18,796；116次 Builder tool calls，4次失败；Critic无工具调用。Builder总延迟包含宿主审查，不重复相加计时。与历史约4.92M输入流程不可直接等条件比较，但本轮没有降本 PASS。token 是观测线程本轮增量，非账单金额。

人工：一次网页修复指令；工程 readback/截图/下载/原生副本编辑/新空白重放及证据采集。两个原生副本边界错误被护栏拒绝后纠正；未对主模型手工修形。ADAI 可用但本轮实际调用0次；修正使用 Ruby，原有 SAIE墙洞保留。安装/启用不等于参与建模。

## 下一轮复现入口

保持当前两张私人整图和同产品。r5 两次修正额度已用完，本轮不加第三次追 PASS。下轮先把旧屋顶原位修正并选择合理 KEEP、调整附体和石质外缘；同步 baseline 后用全新空白重放；限制重复记录与结束阶段耗时，验证新 Critic 仍只读且不降低视觉标准。不得用旧别墅替代咖啡店。

代码/指标/截图清单由 artifacts.json 提供 SHA256；事件是脱敏必要结构，源图、凭证、个人路径与私人模型均不提交。
