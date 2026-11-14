# G04 · beta10 安装回归

**本机隔离安装 PASS，公开分发仍为 BLOCKED_EXTERNAL。** 本轮回归对应桌面源码 d097b1a5a1e1a45dfc0b5fe5a9301490f164b536，Windows x64 版本 2026.11.14-R3-beta10，构建序号 17。编译使用同一提交，其三个安装器输入与已复验的 32c970bc31b13fc9bc226cf935432dfd6e56ca28 相同。

| 工件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| 通用安装器 KStudio-2026.11.14-R3-beta10-win-x64-setup.exe | 315,733,774 | f36be32722c6234d560bab20389f0f936a892e2dc48620908dc88b3d866e96b2 |
| 同载荷隔离验收安装器 | 315,733,952 | 785a82d3863d901cae94fcb6fb8b62299010a80cc46538ae85cbe36da60dfa4d |
| 两份安装器共同的载荷清单 | | a3e60d2edb1208b44c17eca35c9cbbddbe645d24e0ab2ca7fddb60a8a5e2f37f |

两份 EXE 均未进行 Authenticode 签名。通用版保存在本轮 E 盘作业的 downloads/installer-beta10-final，隔离版保存在 build/beta10-isolated-setup-verified。隔离版使用单独的注册标识 KStudioR3QA-r3-beta10。

在现有 Windows 上执行隔离版，程序和资料均选择 E 盘的全新中文路径。安装退出 0，注册路径与序号 17、数据模式 1 的版本指针核对一致。逐个读取已安装的 34,428 个载荷文件，所有字节数与 SHA-256 相符。同版重复安装退出 6，持有资料目录运行锁时退出 5，非法盘根退出 2。后两项拒绝后版本指针的原字节保持一致。

实际安装的客户端通过无界面探测启动打包的 DeepSeek Harness 与 Node v24.22.3，退出 0，未调用模型 API。实际卸载退出 0，移除隔离版的载荷与注册表条目。测试资料的 DPAPI 密文和项目标记哈希保持一致，新进程可解密该测试密文。静默卸载保留了轻量归属与高水位记录及自运行的 Uninstall.exe。原 beta03 注册版本与 6 项抽查哈希保持一致，包括原桌面快捷方式。

| 本地回执 | SHA-256 |
| --- | --- |
| audit/g04-beta10-installer-identities.json | 6f3e1896f529b6d3d44f00cde54cabf5121dffa6feb6b3f02bbf6a4cfb7bae2b |
| actual-install-r3-beta10-final/installation-receipt.json | e90b3b6f929c89f7bfbbf7d143253828ea641bab3a1dd2e8b424b6ab05983ef3 |
| actual-install-r3-beta10-final/payload-hash-receipt.json | 08fcfd254f73f92dab97cec6052d3313a4f942421bd3a58467453a3319a5adb5 |
| actual-install-r3-beta10-final/install-guards-receipt.json | 143f7c4e197778a6192761e731f2537c985b5da403155cc522684922f125e1d6 |
| actual-install-r3-beta10-final/installed-harness.json | b8a57057fd3dbaa8b197b85c51602ff59853fc46ae00ee59a9b1912b1bcac31f |
| actual-install-r3-beta10-final/lifecycle-receipt.json | cac773d06acfa6a1b4c547c6617d2b4c2e378e69f355e3633eb5845b08f523ea |

正式发布仍需发布者签名、依赖分发许可、独立干净 Windows＋SketchUp 2024 首用验收和签名更新渠道的真实验收。[早期失败、beta09 安装复验和本机完整更新回滚证据](evidence.md)
