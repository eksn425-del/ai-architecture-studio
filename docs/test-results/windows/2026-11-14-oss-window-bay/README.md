# K Harness 参数化窗开间 · SketchUp 2024 实机样板

**构件、局部保护、原生保存重开 PASS。K Studio 客户端对话和整栋读图效果 NOT_RUN，整体 PARTIAL。**

在独立 E 盘副本上直接走 K Studio 的 `sketchup_apply_parts` 宿主调度、签名连接器和现有 ProjectRuby 事务。r1 先建一个样板。r2 读回发现普通组复制后有五个独立定义。r3 使用 SketchUp 的组件定义构造，正面三开间共享一个定义，旋转 90° 的侧翼两开间共享另一个。两个外墙部件的容器和受保护平台的深层几何保持一致。r3 的方法账本实测记录两次定义构造，五个实例通过独立原生读回。

墙厚 250 毫米，两侧真实洞口均为 2,200 × 1,650 毫米。框向内退 90 毫米（正面）或 75 毫米（侧翼），玻璃厚 12 毫米。墙、框、玻璃可独立编辑，各自为闭合实体。按检查点回执取文件并在 SketchUp 2024 的独立进程重开，核对模型层级、几何及材质哈希、显示状态、洞口体积和组件定义，全部一致。检查点 SHA-256 为 `6d403d703ba702865c01e3b069b0ab10e1be67a5f3aeb64b88e144553faafe3c`。

| 来源 | 本轮决定 |
| --- | --- |
| [Local MCP for SketchUp 开孔代码](https://github.com/dtzhlq/local-mcp-for-sketchup/blob/434f6fe6cf1582dd7311157c1d9ea7e6490baa79/sketchup_plugin/alma_sketchup_mcp/profile_operations.rb) | Apache-2.0。采用两侧带洞口的面与显式侧壁做闭合件的方法，接入现有事务，保留许可与 NOTICE。 |
| [ADAI 参数化开间](https://github.com/laowang-wy/adai-sketchup-skill-mcp/blob/15ddf80806d7cbc293500894d4e6f527aacf5347/mcp/sketchup-managed-mcp/toolkits/parametric-facade-bay/README.md) | CPAL-1.0。沿用少量显式尺寸、样板后复用的思想。核对该版本仍标记 0.5.39，本次未复制源码或加载其运行时。 |
| [Procedura Skill](https://github.com/SpatiaOS/Procedura/blob/2bbbbccb891a4c53a96de24750b7b366eebee574/.agents/skills/procedura/SKILL.md) | MIT。逐部件生成并回看差异可用于以后复杂构件，K Studio 现有分阶段流程已覆盖本轮需求。 |
| [agentcad 参数验收](https://github.com/jdilla1277/agentcad/blob/0a8d603813967fb545d53cc9d58fc5adf2a84e2e/src/agentcad/commands/check_spec.py) | Apache-2.0。工具完成与规格是否通过独立记录的做法用于本轮原生验证，继续使用 SU 原生构件。 |
| [SK Ruby MCP 立面排程](https://github.com/PMajesty/sk_ruby_mcp/blob/9e6c8d82a55e3e9939d13dbf6b14c3c9feea8ffe/README.md) | 公开文档提供按朝向排窗和比对的思路。未核实可重用许可证，代码和插件未引入。 |

样板输入只含自建尺寸，桌面客户流程、BAI 自动选用和浏览器下载待正式案例验收。当前工具适用范围是 SketchUp 2022+ API 上的直墙矩形封闭窗洞。落地门、异形洞和折面需要其他构造。旧模型和付费用量均未参与这次测试。所有原始失败、检查点和 SKP 保存在 E 盘测试工程。

[原生视图](source-perspective.png) · [审查](review/review.md) · [历史失败](errors.json) · [调用账本](model/oss-method-ledger.json) · [检查点重开](model/native-reopen.json)
