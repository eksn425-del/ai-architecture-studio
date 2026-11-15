# 参数化直跑楼梯 · SketchUp 2024 实测

整体 **PARTIAL**。直跑梯段、上平台、接缝、既有楼板保护和检查点重开 **PASS**。这是直接走 K Studio 宿主工具与已配对连接器的独立构件样板。整栋读图、Agent 自动选择组件、页面下载和商业发布验收 **NOT_RUN**。本轮付费请求为 0。

## 从建筑学长观察到的做法

旧项目记录显示，AI 将建模任务写入参数方案和脚本，由 SketchUp MCP 在指定副本运行 Ruby。样例保存了四批提交、模型身份、前后视口和几何读回，随后记录了平台断接等具体问题与修复计划。最终修复质量缺少独立验收。另查了 1.1.25 安装器元数据和 AI 渲染 SU 插件的安装说明。后者第 3 页明确显示用“模型截图”取 SketchUp 画面，再输出效果图。当前 1.1.29 的云端模型、内部 Agent 实现与同案例成品精度尚未核实。[旧项目观察](../../../COMPETITOR_DESKTOP_ARCHITECTURE_OBSERVATION.md) · [安装器审计](../../../research/2026-10-14-jzxz-pc-1.1.25/README.md) · [官方渲染插件](https://www.jianzhuxuezhang.com/ai/plugin_download)

Tekto 的 MIT 源码把楼层高差、梯段、平台及楼板开口关联。K Studio 本轮自行实现其中直跑梯段和上平台的联动，将其接入现有 `sketchup_apply_parts`、原生事务及 KEEP。只有名字、数值和批准的部件可作用于既有项目。建筑 Skill 要求平台对楼板使用实际接边检测。外部方法账本显示本次无开源组件调用。[Tekto stairs.ts](https://github.com/modellstadt/tekto/blob/00ff5583b2e7461ef6b973cab4761fd9e821dcdc/src/bim/stairs.ts)

## 原生样板

- r1 保存上层楼板。r2 新增可独立编辑的梯段和上平台实心组。上下完成面相差 3,100 毫米，18 个踢面、17 个踏面，每级约 172.22 毫米。
- 原生读回确认梯段和平台之间竖向贴合 57.78 毫米、横跨 1,350 毫米。平台与既有上层楼板在 3,200 毫米的标高全宽平接 1,350 毫米。上层楼板的深层几何及材质指纹一致。
- 同哈希检查点副本在另一 SketchUp 2024 进程重开，层级、几何、材质和显示指纹一致。六角度图均采自同一 r2 检查点。样板依据尺寸，`source-perspective.png` 为原生斜视审查图。
- 首次提交楼板后，连接器一度报告所选实例过期。确认 r1 检查点哈希，重新选择同一进程和副本，沿用 r1 完成 r2。本次保留该次读回失败。

楼板开口、上下净空、栏杆、折返及薄边平台在本轮验证范围之外。本地定向回归 73 项通过。较广桌面回归首次有 26 项失败，其中 12 项通过 UTF-8 环境复验。其余 14 项在同环境的原基线也失败。云端测试收集缺少依赖，保持未验证。

[斜视](views/oblique.png) · [正视](views/front.png) · [构件参数](planning/parameters.json) · [接边和标高测量](model/geometry-readback.json) · [重开凭据](model/native-reopen.json) · [错误记录](errors.json)
