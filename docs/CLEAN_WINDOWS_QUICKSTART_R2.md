# K Studio：另一台 Windows 的最短安装与验收

此包是**只读诊断脚本 + 操作说明**，不是已经通过另一台电脑验证的证据。无需安装 Codex、Python、Node、Docker 或数据库。需要合法安装本版验收清单覆盖的 SketchUp；WebView2/.NET 检测缺失时由用户或管理员按官方/组织流程处理，诊断脚本不自动安装软件或修改系统策略。

## 1. 核对并安装完整候选包

从可信交付渠道取得完整 KStudio 目录、对应文件清单与独立 SHA；保留 `_internal` 等目录，不能只拿 EXE。本机候选尚未等同可信签名正式公开发行，按内测范围及组织策略运行。使用 Windows 自带 PowerShell，不需要管理员权限或降低系统执行策略。

诊断包中的三个脚本放在同一目录。先运行只读检查（替换实际路径；报告目录必须是新的、位于程序目录外）：

```powershell
.\Test-KStudioCleanWindows.ps1 -Bundle 'D:\下载\KStudio' -OutputDirectory 'D:\KStudio验收\检查01'
```

若交付者提供 `audit_desktop_bundle.py` 格式的逐文件 JSON 清单（`files:[{path,bytes,sha256}]`）及清单独立 SHA，可验证全部列出的文件：

```powershell
.\Test-KStudioCleanWindows.ps1 -Bundle 'D:\下载\KStudio' -OutputDirectory 'D:\KStudio验收\检查02' -Inventory 'D:\下载\bundle-audit.json' -ExpectedInventorySha256 '替换为可信渠道提供的64位清单SHA256'
```

`MATCH` 只代表列出文件与所给清单相符，不认证清单的发布者、不扫描未列出的文件、不证明软件兼容。`MISMATCH/REJECTED` 时停止安装并重取完整包，不跳过失败项。退出码 0 表示报告已完成且没有列出的完整性失败，**不是跨机或建模验收通过**；退出码 2 表示核心组件缺失或清单不匹配。报告只有软件版本、布尔状态和散列，不包含用户名、机器名、绝对路径、Key、模型名称或原始 API 回复；发送支持前仍请查看内容。

安装到新的版本目录，数据单独存放。下面安装脚本会复制和逐文件校验后创建“**K Studio（本机候选版）**”桌面图标，不覆盖旧版本，不自动启动、不调用模型：

```powershell
.\Install-KStudioCandidate.ps1 -Bundle 'D:\下载\KStudio' -Destination 'D:\KStudio\versions\候选日期' -DataDirectory 'D:\KStudio\data'
```

脚本执行受系统策略限制时，按组织允许的方式审阅运行；不要关闭安全软件或擅自修改组织策略。安装/诊断不需要把 API Key 写入命令。

## 2. 首次 API 与 SU 连接

1. 点击桌面图标。确认没有预装他人的 Key；本机 BYOK 不要求云端登录。
2. 输入框“模型设置 → API 连接”：填自己的服务商、HTTPS 根地址、准确模型名和 Key，选择对应协议。保存后退出再打开，检查仍有连接记录且 Key 不回显；**保存本身不会测试供应商，不代表模型能力通过**。
3. 打开合法安装的 SU，保留原件，准备独立副本。K Studio 右下“建模工具 · SketchUp”→连接向导→选择实际版本→配置本机配对→下载 RBZ。
4. SU 扩展程序管理器安装 **K Studio Connector**，重启；自动启动失败时点击 **扩展程序 → K Studio Connector → Start paired local connector**。回 K Studio 做只读连接检查，核对当前文档与项目绑定。不要把“配置已保存”“插件存在”当成“原生连接成功”。
5. 使用自有参考图正常讨论并批准方案后再执行。真实测试会使用自己的 API，先约定测试范围和费用；本诊断脚本不会发起这些调用。结束后下载 SKP，重新打开这个实际下载文件，核对几何、材质和分组。

若已知本机工作台端口，可在运行中做只读配置状态检查：

```powershell
.\Test-KStudioCleanWindows.ps1 -Bundle 'D:\KStudio\versions\候选日期' -OutputDirectory 'D:\KStudio验收\检查03' -RuntimePort 8787
```

把端口替换为当前实例实际端口，脚本不猜测或扫描其他端口。仅 GET `/api/status` 与 `/api/connectors/sketchup/setup`，不会向 SU 发送 MCP 命令；实际原生可达/文档绑定仍由界面的只读检查验证，脚本报告保持 `NOT_RUN`。

## 3. 升级、回退与保留数据

先停止任务、保存模型并正常关闭软件，备份原数据目录。升级时使用新版本目录与**完全相同的 DataDirectory**，重复上面的安装命令；已有自定义 `RuntimeDirectory/ConnectionsDirectory/BridgeConfig/GeneratedDirectory` 的安装必须继续传原值，不要隐式迁移。

若此候选需要回退，使用同一安装脚本，将旧完整版本作为 `-Bundle`，新的回退目录作为 `-Destination`，`-DataDirectory` 仍指原数据目录。旧版本与数据都保留；不要直接双击旧 EXE 导致它采用不同 profile。例如：

```powershell
.\Install-KStudioCandidate.ps1 -Bundle 'D:\KStudio\versions\上一个版本' -Destination 'D:\KStudio\versions\回退日期' -DataDirectory 'D:\KStudio\data'
```

若采用已提供可信清单与独立更新器的发行方式，则按发行说明使用 `KStudioUpdate.exe rollback --install-root ... --data-dir ...`，不要混用两套安装根。回退改变程序，不应回滚或删除新项目/账本。遇到不兼容数据迁移，应停止并保留备份，由发布者处理。

卸载独立候选时先退出程序，删除不再使用的程序版本目录和快捷方式即可；不要删除 `data`、自定义数据路径或用户模型。需要撤销云设备/供应商 Key 时，在相应账户明确操作；删除程序并不自动撤销它们。详细说明见同包 `USER_GUIDE_R2.md`。

## 4. 另一台机器必须实际记录的验收

用 `CLEAN_WINDOWS_ACCEPTANCE.csv` 逐项记录日期、观察和证据。默认均 `NOT_RUN`，只能按实际结果改为 PASS/FAIL/BLOCKED，不把本机测试或脚本输出转换为另一台通过。

| 场景 | 应记录的实际结果 |
| --- | --- |
| 干净环境安装 | 未安装 Codex/Python，完整包可启动；版本/清单一致 |
| 默认无 Key | 无开发者配置继承，保存自己 API 后重启仍保留，Key 不回显 |
| SU 插件与文档 | 合法 SU 实际版本、RBZ 安装/重启、真实只读连接和目标副本绑定 |
| 普通任务 | 自有素材、自然对话、批准、真实建模；API 型号/耗时/费用及失败保留 |
| 停止/异常恢复 | 停止不冒充回滚；断线/重启后确认版本与检查点，不重复执行未知提交 |
| 下载重开 | 浏览器/客户端实际下载的 SKP，在 SU 重新打开且外观/分组/材质相符 |
| 升级与回退 | 同一数据目录、原项目/Key保留、连接器能重新连接，旧版本仍可回退 |
| 隔离与卸载 | 不串用其他 Windows 用户凭据；卸载保留自有数据，无私有资料进入反馈 |

不要在验收 CSV 中填写 Key、令牌、私人文件路径或没有发布授权的图像。完成后仅回传脱敏报告与必要证据；真实模型/API/多版本兼容失败必须如实保留。
