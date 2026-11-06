# 干净 Windows 只读诊断与验收交付包

没有第二台独立 Windows，因此跨机验收仍 `NOT_RUN`。本次补齐可直接交给测试者的工具和步骤，避免要求普通用户安装开发环境。

工件：`outputs/video-storage/jobs/kstudio-r2-20261104/clean-windows-kit/KStudio-R2-clean-Windows-check-kit.zip`，16366 bytes，SHA-256 `074e53ccd0bac8218534dcb0e13d046db74855ddb92b06556df074fcdeed539d`。六个 payload + manifest，全部成员 SHA 验证通过；无安装包本体、运行时、用户资料或凭据。构建脚本 `scripts/build_clean_windows_kit.py` 仅供开发者重打包，客户运行无需 Python/Codex。

已复用 `Install-KStudioCandidate.ps1`、`Verify-KStudioBundle.ps1` 和 `USER_GUIDE_R2.md`，未另写客户端或修改 build04 源码。新 `Test-KStudioCleanWindows.ps1` 兼容 Windows 自带 PowerShell 5.1，只读取：

- Windows 位数/版本、.NET、WebView2 注册版本；SU 安装注册与第一方插件文件是否存在，不读窗口标题、模型或用户内容。
- 用户明确指定的完整程序包核心文件、EXE SHA/Authenticode；可选清单逐成员大小/SHA，拒绝越界路径、reparse point、私有数据路径和重复条目。不声称未列出文件也已检查。
- 可选明确指定端口的 `127.0.0.1` GET 状态/配置信息；不跟重定向、不用环境代理、不扫描端口、不调用原生 MCP。真实 SU 可达/项目绑定仍 `NOT_RUN`，需要界面只读检查。

只写用户指定的新报告目录，输出白名单字段，不输出用户名、主机名、SID、绝对路径、Key、模型名称或原始响应；不安装、不启动软件、不付费、不改变模型或系统策略。可选安装脚本只有用户另行明确执行时才复制程序并创建快捷方式。

本机实际验证：

| 证据 | 结果与边界 |
| --- | --- |
| `clean-windows-local-core/kstudio-environment.json` | Windows PowerShell 5.1，本机 build03 核心组件/运行依赖检测；未扫描模型 |
| `clean-windows-local-full/kstudio-environment.json` | 同一 build03 清单 **70393/70393 SHA MATCH**，清单 SHA 独立匹配；EXE `NotSigned`，不是可信发布者/跨机 PASS |
| `clean-windows-script-tests05/results.json` | 四个合成场景：正确清单通过；文件篡改、越界路径、清单摘要不匹配均拒绝；未执行假 EXE |
| `clean-windows-status-fixture/fixture-result.json` | 受控 localhost 回复含伪敏感字段，报告没有导出；仅两个 GET、零 POST/原生调用 |

初次合成运行发现从 Python 间接调用 PS5.1 时 inherited PSModulePath 导致 `Get-FileHash` 未加载；诊断程序改为 .NET SHA256 流式计算，避免依赖该 cmdlet。完整清单采用最多8线程 SHA，且只验证清单指定包内文件。测试 harness 另外移除继承的 PowerShell 7 模块目录；实际 PowerShell 5.1 命令复测通过。

客户入口 `docs/CLEAN_WINDOWS_QUICKSTART_R2.md`（打包为 README）：核对包 → 只读报告 → 安装完整候选 → 自己 API 保存/重启 → SU RBZ/只读绑定 → 自有图片正常建模/下载重开 → 同数据目录升级/回退/卸载保留。`CLEAN_WINDOWS_ACCEPTANCE.csv` 默认十项均 NOT_RUN；真实测试者按实际证据填 PASS/FAIL/BLOCKED。脚本成功退出或列出匹配不自动修改这些验收结论。
