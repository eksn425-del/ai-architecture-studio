# K Studio 托管 Agent 开发与有界严格重放 — PARTIAL

基础main：`0c6f1675505a89670978a0786aa15982165dad8d`。Windows / SketchUp2024 24.0.484 / Kongxing；现有venv启动8787网站，无新网站。正式Dream Coffee r4/PID35529/116组保留不变。

## 验收结果

| 项目 | 真实结果 |
|---|---|
| 自动全检查 | 见 [checks.txt](checks.txt)；协议、生命周期、构件诊断回归，2个既有skip |
| 三玻璃重放根因 | 持久脚本未同步已接受原生构件的尺寸/材质；已做唯一一次源码同步 |
| 新空白A、B | 均初始0实体；各116组递归几何和面材质SHA全部匹配正式r4，严格PASS |
| OSS实际执行 | 每次SAIE wall_with_openings×2、wall×1，ADAI profile×9；原生事务账本读回，不是安装成功 |
| 网页SKP下载 | 下载副本SHA与服务端一致，PASS |
| 原生重开、鼠标编辑、保存再开 | PLANTERS真实Move，115其他组不变；重开全部等于编辑后，PASS |
| 新生命周期修复 | 保存移至桥接事务结束后的UI定时器；切换实际成功；timeout取消/隔离模拟PASS |
| 自有Responses Agent | 真实HTTP代码已实现，图片/多工具回传/历史/只读Critic/预算/取消通过假传输；LIVE_NOT_RUN |
| 建筑视觉/专业接合 | PARTIAL；没有新的独立Critic或美化，不把一致重放算质量PASS |

## 修复过程与证据

先读最新任务，再全检查。真实只读遍历正式r4与旧失败replay的世界坐标、材质、子组变换，发现：入口玻璃边距22→24mm；上层立面竖梃45×55→50×65mm；倾斜下层玻璃肋深85→78mm；山墙木材改为实际使用的深木材。见 [差异诊断](model/managed-glass-differences.json)、[源码参数差异](model/baseline-correction.diff)。**没有修改指纹算法或放宽等价规则**，没有重建正式模型。

只运行两次全新空白重放，[A真实回执](replay-a/result.json)、[B真实回执](replay-b/result.json)。通过产品AgentToolSurface/ProjectRuby guarded writer，启用既有可选ADAI代理。两次真实构件、PID、revision、OSS账本均保存。此为宿主执行之前Luna-authored脚本，**不是新Luna/B.AI自动对话任务**。

六张本批PNG/相机/revision见 [当前B六视图](views/oblique.png) 与 [A六视图](replay-a/views/oblique.png)。所有方向对应独立canonical sidecar；`quality_status=not_accepted`保留。来源整图私密，未公开；[source-perspective](source-perspective.png)为真实近似总体来源角度，不伪装新Critic evidence pair。

原生验证：[下载/编辑/重开回执](model/native-reopen.json)、[重开后真实PNG](model/native-reopened.png)、before/after/reopened指纹JSON。只在下载模型副本修改，操作为SU Ctrl+O、鼠标选PLANTERS、Move、Ctrl+S、再次Ctrl+O，再只读核实。恢复正式主模型后再次确认116指纹全不变。私人SKP不提交。

## 独立 Agent 真正实现的内容

`app/responses_runtime.py`通过POST Responses，复用项目与Skills、Kongxing单写者、质量门和专用只读Critic。tool call ID关联完整结果；不透明推理项保留；每个工具结果及时保存；异常、预算、取消阻止后续写入；供应商/模型不可偷偷替换。运营Key只在服务端进程环境，托管UI不要求用户API Key。详细本机配置和未完成安全边界见 [运营说明](../../../MANAGED_RESPONSES_LOCAL_PILOT.md)。

免费协议测试覆盖 `tests/test_responses_runtime.py`：图片输入、连续工具调用/失败结果回传、项目恢复、7图无工具独立Critic、取消、硬额度、完整schema输入门、缺usage、429/500/超时、拒绝、不完整输出、型号替换、非法参数。假返回身份和Token是**测试fixture**，不计入真实费用或建模质量。见 [模拟轮转记录](api/mock-roundtrip.json)。

本轮没有B.AI或官方付费请求，没有新Luna推理；保留此前实际gpt-6-luna/max baseline记录，不能宣称本次模型生成。实际新LLM Token未知/不适用为null，协议mockToken不混入。宿主全流程总耗时/工具调用未完整计量，也为null；记录缺口明确，不编造零。

## 未完成与下一步

原先独立source-matched Critic的上层平雨棚FAIL、木墙PARTIAL依然有效，见 [历史审查](../2026-10-11-dream-coffee-protected-repair/review/critique.json)。按新任务本轮停止咖啡馆美化。构件组/PID/尺寸诊断通过不代表所有接合关系正确，见 [专业诊断](model/component-assembly-diagnostics.json)。

用户尚未充值B.AI，实时协议、实际账单、独立API原生新建与源图审查全部NOT_RUN。Luna可以继续作为**明确标注的开发对照**；B.AI质量测试必须等合法Key、商业/隐私许可、明确小额硬预算后进行，不能借Luna报告API通过。

尚无认证/跨租户隔离/持久账务/平台Key安全分发方案实装，不能收费上线。先做批准后的运营端真实微测与普通用户无需Key的受控演示，再考虑租户、签名本地配对及持久预算系统。

所有文件见 [SHA256清单](artifacts.json)。旧证据未覆盖；私人源图、账号、Key、机器绝对路径和SKP未提交。
