# K Studio R3 开源方法落地与发布前实测

**实际客户端保存下载和 SketchUp 2024 重开 PASS，建筑视觉 PARTIAL，公开发布 BLOCKED。**

K Studio 通过已配置的 BAI DeepSeek Flash（Responses，High 请求）走了图片上传、自然对话、批准、分段建模、两轮有范围的局部修正与真实下载。实际使用单个 SketchUp 窗口，复用同一进程连接和重开。r2 读回二层窗样板，r3 重复，最终 r12 四樘共用一个定义，两个实测洞口环均为 2900 × 3150 毫米，框离外墙 120 毫米，玻璃前缘离外墙 161 毫米，玻璃厚 8 毫米。原始窗高估算 3300 毫米，建模后实测调为 3150 毫米。

| 上游 | 实际进入 K Harness |
| --- | --- |
| [Local MCP for SketchUp 几何读回](https://github.com/dtzhlq/local-mcp-for-sketchup/blob/434f6fe6cf1582dd7311157c1d9ea7e6490baa79/sketchup_plugin/alma_sketchup_mcp/geometry_regions.rb) | Apache-2.0。保留开孔构造的许可与 NOTICE，用原生洞口环、玻璃退距、闭合状态和共享定义验收样板。 |
| [ADAI 立面审查](https://github.com/laowang-wy/adai-sketchup-skill-mcp/blob/15ddf80806d7cbc293500894d4e6f527aacf5347/skill/professional-sketchup-modeling/references/facade-skin-review.md) | 学习按立面和层段拆开核查、先样板后复制的方法。K Studio 独立编写建筑指导。 |
| [agentcad 规格检查](https://github.com/jdilla1277/agentcad/blob/0a8d603813967fb545d53cc9d58fc5adf2a84e2e/src/agentcad/commands/check_spec.py) | 将验收拉回实际世界坐标，用剖面、接边和深层哈希校对计划。 |
| [Procedura Skill](https://github.com/SpatiaOS/Procedura/blob/2bbbbccb891a4c53a96de24750b7b366eebee574/.agents/skills/procedura/SKILL.md) | 参考逐系统验证并保留局部结果，现有原生事务按实际提交修订显示阶段。 |

[源图方向实拍](source-perspective.png) · [视觉与剖面](review/review.md) · [窗口检查](review/single-window-guard.json) · [原生重开](model/native-reopen.json) · [保护核对](model/keep-results.json) · [失败](errors.json) · [用量](metrics.json)。

安装候选 2026.11.14-R3-beta07（序号 14）已编译，SHA-256 `63d6e8c80f0123e71ca7c65bd4a516191e5e8ab983e2e3740032c1eeb8a83d43`。用本机独立空白 profile 打开了打包客户端，确认新会话要求配置 API。打包 SDK 初始化也通过。此包固定到用户 E 盘目录，供当前机器验证。桌面已安装版仍为 beta03。干净 Windows、签名和发行许可尚待验收，正式云、登录、收费与公开下载地址尚未部署。[安装证据](release/installer.json) · [生产预检](release/production-preflight.json)。
