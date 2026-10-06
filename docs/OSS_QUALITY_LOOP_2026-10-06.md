# 图像还原迭代：源码检查与采用决定（2026-10-06）

本轮从 main `7aa4221` 的实际六视图缺陷继续：左窗数量误读、后窗过宽、入口面底层多窗、窗框内凹浅、屋面细节不足。保留当前 DeepSeek、Kongxing 和持久 Ruby 工作区，不开展新引擎或多 Agent 重写。

## 实现级检查

| 项目 | 检查版本与文件 | 可采用 | 未采用及原因 |
| --- | --- | --- | --- |
| [Stultus](https://github.com/B-A-community/stultus) | Apache-2.0；`bfb0c012c6a5c669dadb2725aa76980e8481e859`；`server/src/prompt.ts` | 跨模型共享建模上下文、真实毫米场景回读、限定对象修改、截图反馈。此前已采用其边界换算模块。 | 不替换现有已工作的连接器；无需为了形式拆多 Agent。 |
| [SketchUp Agent Harness](https://github.com/marlinBian/sketchup-agent-harness) | MIT；`e431eef6c9a9ee73a611fd68952a6aaa78566b12`；`skills/designer-workflow/SKILL.md`、`skills/project-runtime-memory/SKILL.md` | 项目内保留参数、对象身份、失败及修正经验；产品 Skill 提供方法，项目记录保存本次事实。 | 不搬其特定房间业务 schema 约束整栋建筑。 |
| [SAIE](https://github.com/iamahsanmehmood/saie) | MIT；现有接入版本见 [采用清单](OSS_MATCH_AND_ADOPTION_2026-10-05.md)；另查 `src/su_mcp_bridge/api_agent/architect_prompt.py` | 明确毫米单位与坐标、构件命名；继续复用已接入墙体工具。 | 不搬清空当前模型、通用门窗尺寸及缺少图片证据的默认规则；这些会破坏原图目标和局部修改。 |
| [Auto SketchUp Builder](https://github.com/xilib/Auto-SketchUp-Builder) | MIT；`abec74ba3b7dee7537196ec3156194ccb73e753b`；`ai_service_v2.py` | 逐立面开口清单可用于识图与回读核对。 | 不以狭窄 JSON 体块引擎替代 Ruby coding loop；其单位/屋顶假设需实测，“零遗漏”宣传不是验收证据。 |

本轮为方法适配与现有许可模块的薄封装，没有复制以上新克隆项目的源码。既有 SAIE/Stultus 代码许可证仍在 vendor，NOTICE 不变。专有建筑学长实现未复制。

## 已实现的产品能力

1. `sketchup_inspect_owned`：读已验证专用模型中指定 root/命名 child 路径，返回 persistent IDs、毫米范围、坐标参照和分页；无几何修改、无诊断小体块。
2. `remove_owned_group.call(["顶层组", "child名称"])`：只删除唯一匹配的自有 child；拒绝删除 root、歧义名称、锁定/共享祖先。可保留顶层组及其他构件身份。
3. 紧凑重建 Skill：源图可见事实胜过旧误读记录；逐立面比较预期/实际；成功补丁合并到项目基线；使用真实回读，不接受工具成功或 Agent 打勾替代质量。
4. Provider 上下文只移除跨历史消息重复的同一图片，保留最新整图、不同图片、文本要求及完整本地审计。同一消息内图片不去重，避免破坏多种输入角色。
5. 安装包显式携带 owned-model Ruby helper，安装时检查文件存在，防止源码通过而 EXE 失败。

## 判断

主要问题是识图事实没有可靠沉淀、旧脚本/补丁不一致、回读粒度不足及截图自评过于乐观。单 Agent 能完成这一闭环，但必须得到相同输入和实际工具能力。暂不增加独立 Visual Critic；先让现有 Agent 看当前修订真图，并由独立实机验收记录反驳不准确的自评。多 Agent 的收益需要同输入成本/质量对照，不能凭架构推断。

持续迭代指的是每轮针对可见缺陷修复、重测并保留证据；不承诺单图恢复不可见真实尺寸、无限自动重试或六视图无任何误差。本轮实测结论见 [Windows 迭代记录](test-results/windows/2026-10-06-iteration/README.md)。
