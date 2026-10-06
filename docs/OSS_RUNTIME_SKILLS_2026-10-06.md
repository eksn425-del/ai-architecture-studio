# Codex / SketchUp MCP 与 Skill：本轮实际采用

用户要求继续吸收相似项目代码与架构。保留现有 DeepSeek → 持久 Ruby 工作区 → Kongxing → 模型回读/真图 → 修订路径；不重写连接器或将模型限制为体块 JSON。

## 新采用的许可片段

| 来源 | 固定版本 / 许可 | 本轮采用 | 不采用 |
| --- | --- | --- | --- |
| [SketchUp API Skill](https://github.com/euphraetes/sketchup-ai-skill) | `10e1e0fb47abcc30c033e6f2046f3252ca4386d3` / MIT | 几何调用前校验与 `safe_normal` 示例，直接装载进产品建模 Skill | 插件开发整套规范、25行方法硬限制、重复嵌套 Undo；不是建模质量证明 |
| [SketchUp Agent Harness](https://github.com/marlinBian/sketchup-agent-harness) | `e431eef6c9a9ee73a611fd68952a6aaa78566b12` / MIT | 项目记忆 guardrails 原文节选：实际来源/回读优先，不拿手写修正伪装自动识图 | 室内业务 `design_model.json` 作为整栋建模的强制引擎；新增连接器替换 Kongxing |

代码/文档片段：[产品运行时节选](../app/vendor/sketchup_runtime_skills/reconstruction-excerpts.md)。两份许可证同目录随安装包分发，来源登记在 [NOTICE](../THIRD_PARTY_NOTICES.md)。压缩本地重复说明后，完整建模上下文为 9,982 字符，保留末尾安全/记忆规则而非截掉。

上游也需检查：API Skill 的 `safe_offset` 对 `edge.line` 使用 `offset(distance)`；官方说明 [Edge#line](https://ruby.sketchup.com/Sketchup/Edge.html#line-instance_method) 返回点/向量二元数组，[Array#offset](https://ruby.sketchup.com/Array.html#offset-instance_method) 是点按向量偏移，不能直接当作此线偏移示例。该示例未接入。读开源 README 的能力宣称不能替代本机验证。

## 已有可复用代码仍在实际使用

- SAIE MIT 墙体子集：毫米参数的墙段几何。
- Stultus Apache-2.0 回读：真实毫米边界；已扩展到命名嵌套对象分页。
- SketchUp Architect MIT：现有受控 Ruby 生命周期。
- 对接口/工作区/执行约束采用薄封装；已有来源和版本见 [先前采用清单](OSS_MATCH_AND_ADOPTION_2026-10-05.md)。

## 本轮产品修复

1. “批准执行，检查是否错位，不要执行旧基线，不要修改其他部分”识别为执行限制；网页与服务器相同规则，不再因这些限定词转回计划。
2. 真正暂停、问题、尺寸/数量变更仍不能自动批准；明确处于“修改参数”模式仍先更新计划。
3. 首条明确“给我计划/生成计划/整理建模计划”直接走计划，无几何权限；一般“按图建模”仍先澄清。已给尺度/范围/推断许可不应重新出问卷。

自动测试和真实网页测试分别记录；本轮新单图模型结果与未执行门槛见 Windows 交接报告。没有以更强模型替换 DeepSeek。
