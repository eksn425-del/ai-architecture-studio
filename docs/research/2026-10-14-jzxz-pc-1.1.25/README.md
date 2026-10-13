# 建筑学长电脑版 1.1.25：合法静态架构检查

检查日期：2026-10-13 至 2026-10-14（北京时间）。本报告是受许可范围限制的研究结果，不能据此认定或排除某个内部 Agent 实现。

## 结论与置信度

| 问题 | 结论 | 证据等级与限制 |
| --- | --- | --- |
| 是否直接集成官方 Codex Harness / App Server？ | **尚未验证**。没有取得能够证明其打包、启动或调用官方 App Server 的证据。 | 未解包桌面安装负载、未反编译、未运行目标程序，不能以未观察到等同不存在。模型名称、OpenAI SDK、类似工具调用界面都不足以证明此项。 |
| 是否用 Microsoft Agent Framework 自行组织 Agent？ | **尚未验证**。没有已获准的桌面依赖清单、组件声明或调用证据。 | 也不能把“没有证实 Codex”转化为“已证实自研 / Microsoft”。两种方式还可能组合使用。 |
| SketchUp MCP、Skills 与通用 Agent 的关系？ | **一般组件关系已证实；建筑学长的具体组合尚未验证**。 | 官方 MCP / Codex 文档可说明协议、指引和执行循环的职责；官网只确认其宣传桌面接管 SU 等软件，没有公开足够信息证明具体 MCP、Skill 名称、版本或作者。 |

**已证实的目标文件事实：** SHA-256 完全匹配用户给定值，270,234,333 字节；Windows VERSIONINFO 产品版本为 1.1.25、产品名称为“建筑学长电脑版”；Authenticode 返回 `NotSigned`。REA 的资源解析识别为 PE32，machine 332 / `0x014c`（i386），资源表完整检查 44 个条目、19 个资源。

**较强线索仅限安装器外层：** 元数据中有 `DVCLAL`、`PACKAGEINFO` 资源名，提示外层安装引导器可能使用 Delphi/VCL 相关构建工具。资源名与 [NCC Group 的 Delphi 调查工具说明](https://github.com/nccgroup/pythia)列出的编译器识别线索一致，但本次没有检查这些资源的内容。该线索不能推导安装后的主程序架构，更不能证明或排除 Electron、.NET、Codex 或 Microsoft Agent Framework。PE32 也不能证明安装负载都是 32 位。

文件哈希验证的是本次文件身份；未签名时，不能通过数字签名独立认证官方发布者。安装包的合法取得及官方来源由用户提供，本次未重新下载或对照官方签名发行记录。`NotSigned` 本身也不是恶意软件判断。

## Windows 许可检查与研究边界

从官方公开导航定位到[用户协议](https://www.jianzhuxuezhang.com/introduce/userPolicy)和[隐私政策](https://www.jianzhuxuezhang.com/introduce/privacyPolicy)。这两个入口属于官网公开页面，**尚未确认其条款是否涵盖 Windows 电脑版 1.1.25**。

本次 HTTP 页面只返回 SPA 壳；浏览器页面读取两次超时。仅查看官网公开加载的页面组件，确认协议正文需要动态加载，未取得完整正文。没有调用从组件中推导出的配置接口、隐藏接口或登录接口。也未执行安装器来显示或接受 EULA。

因此：**适用于该 Windows 版本的许可全文及明确静态研究授权未取得**。没有证据支持宣称“许可允许反编译”，也不能宣称“已找到禁止条款”。依用户本次要求，研究停在文件元数据、公开组件资料和公开产品描述；受保护代码分析保持 `NOT_RUN`。REA 的 MIT 许可只授权使用 REA，不会授予分析另一家软件的权利。

若需继续深入，应取得 Windows 1.1.25 的确切 EULA / 第三方组件公告，并确认允许的动作及结果披露范围；必要时取得权利人针对解包、依赖清单和相关调用路径的书面授权。拥有安装包或公开下载入口，不能自动证明这些权限。

## REA 版本、依赖与真实使用

- 官方源码：[`morluto/rea`](https://github.com/morluto/rea)，固定提交 `688defca0f4a3de04eb199f7754f323c68896c3c`，源码 package 版本 6.4.0。
- 使用该提交的 [REA Skill](https://github.com/morluto/rea/blob/688defca0f4a3de04eb199f7754f323c68896c3c/.agents/skills/reverse-engineer-anything/SKILL.md) 和连接指引。Skill 是调查指南，不等于 MCP 已接通。
- 实际 npm 包 `rea-agents@6.4.0`；通过项目内独立工具目录安装，143 个包，使用 `--ignore-scripts --omit=optional`，没有全局注册 MCP 或修改 Codex 配置。
- Node.js **24.19.0**、npm **11.16.0**。Node 满足包声明的 `^22.19.0 || ^24.11.0 || >=26.0.0`。
- 生产依赖包括 MCP client/server 2.3.1、Babel parser/types 8.0.4、Electron ASAR 4.2.0、Playwright Core 1.58.2，以及 ZIP、XML、JSON 等解析库。它们是 **REA 的依赖**，不是建筑学长的依赖。
- Frida 17.23.2 是源码声明的可选依赖，本次省略；没有使用进程注入。未在 PATH 找到 Java、Ghidra、7z、既有 REA 命令；这只说明本次 PATH 检查结果，不证明整台电脑没有这些软件。没有安装或启动 Hopper / IDA / Ghidra。
- 原生深层反编译需要适当分析引擎；本次选用内置 `inspect-pe-resources`，无需这些引擎。成功输出的 provider 是 `rea-pe-resources` / parser version 1。

实际执行方法：

```text
Get-FileHash <用户指定原始安装包> -Algorithm SHA256
Get-AuthenticodeSignature <同一安装包>
Get-Item <同一安装包> → VersionInfo
node <REA官方包launcher> --version
node <REA官方包launcher> inspect-pe-resources <同一安装包> 
  --max-file-bytes 300000000 --format json --full-output
```

提高文件读取上限是因为本文件大于默认 64 MiB。资源 payload 保持不透明；输出只有资源身份、范围、摘要及图标组引用等元数据。没有提取安装负载、还原源码、执行安装器、登录账号、读取用户数据库 / 密钥 / Prompt，或捕获目标进程和网络。

[可公开证据摘要](evidence-summary.json)保留原始安装包摘要、版本、REA Evidence ID、工具版本及限制。原始完整 REA 输出只在本地保留，因为其中包含机器路径。摘要是人工审核后的派生记录，**不是原始完整 REA Evidence 的等价替代或完整安装内容清单**。

## 怎样才足以证明内部实现

官方 [Codex App Server 源码与说明](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)展示其独立服务和线程 / 回合协议。若获得授权，确认建筑学长使用它需要相互支持的证据，例如：可认证的上游二进制或包版本、启动 `codex app-server` 的实际路径，以及对应 `initialize`、`thread/start`、`turn/start` 等协议交换 / 调用关系。单个关键词、同名方法或 SDK 不足以证明实际执行。

[Microsoft Agent Framework](https://github.com/microsoft/agent-framework)是可用于组织 Agent 和工作流的独立框架。即使发现相关包，也还需区分“被打包”“被引用”“实际参与该建模工作流”。Windows UI 使用 .NET 或引用 Microsoft 常见运行库，本身不能证明使用 Agent Framework。

一般关系可表述为：用户请求及图像进入 Agent；Agent 执行循环选择并调用工具，消费结果并继续；Skills 提供任务指引；MCP 提供工具与宿主的标准连接；SketchUp 插件 / 桥接层在真实模型中执行并返回结果。Codex Harness 或其他框架都可以组织这个循环。**MCP / Skills 是接口或能力层，不能单独确定通用 Agent 是谁。** [MCP 官方架构](https://modelcontextprotocol.io/docs/learn/architecture)与 [Codex Skills](https://developers.openai.com/codex/skills)提供一般组件职责依据。

官网[电脑版介绍](https://www.jianzhuxuezhang.com/app)公开描述面向设计师的桌面协同，支持 SU、Rhino、CAD 等软件和文件任务。这是公开产品功能描述，未在本次运行中验证功能效果。公开页面组件版本为网站 `v2.17.80`，不是桌面 1.1.25 的内部版本，不能混为一谈。

## 本次能用于 K Studio 的结论

可以参考公开描述中的自然语言任务、软件内执行和成果反馈关系，设计自己的用户流程。**当前没有证据支持复制其内部实现，或声称它是“Codex 套壳” / “Microsoft 自研 Agent”。** K Studio 的优化仍应依据自己真实模型及用户测试失败记录。

研究已完成到本次允许的边界；三个内部架构问题中，前两个及第三个的目标特定部分仍尚未验证。没有为了得到确定答案扩大研究范围。

参考资料均于本次检查访问；工具实现以固定提交和 npm 版本为准，官网和通用框架页面可能随时间更新。REA 自身适用范围见 [固定版本免责声明](https://github.com/morluto/rea/blob/688defca0f4a3de04eb199f7754f323c68896c3c/DISCLAIMER.md)。
