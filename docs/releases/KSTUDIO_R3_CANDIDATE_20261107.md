# K Studio R3 网站＋桌面商业 Beta 实施候选

2026-11-07。状态：**工程候选，未公开商业上线**。实施 [PR27](https://github.com/eksn425-del/ai-architecture-studio/pull/27)，分支 `codex/kstudio-r3-launch-20261105`。保留原 R2 build07、用户 API/历史项目和原模型，没有切回 main 重做产品。

## 本次落地

- 网站与客户端沿用原 K 品牌和页面布局；账户 API 页提供明确云加密保存同意、元数据导出/删除和指定设备一次性恢复，客户端按账户隔离工作目录，撤销登录后不能继续复用已同步的凭据。
- 云端 AES-GCM 凭据库绑定账户/连接/密钥版本，主密钥独立于数据库备份。浏览器近期登录与桌面刷新严格分开，修复旧刷新接口能错误更新认证时间的问题。
- 微信 Native 请求签名、响应及回调验证、持久回执恢复、订单查询/关单、退款预留与确认入账已实现；实际商户支付尚未配置，合成测试不算真实充值。
- 平台网关有已验证模型白名单、固定推理配置、跨请求/重启保留的单回合预算、并发和超时、未知用量待核账。`provider-default` 不再被解释为 Low；明确选择 Low 仍真实发送 Low，不假称供应商执行了 High。
- 部署、审计、加密备份、独立数据库恢复和镜像回退有可运行命令。真实 PostgreSQL 恢复验证账户/账本/凭据及待处理支付；生产数据卷不自动重建。
- Windows 安装器不要求客户安装 Python、Node 或 Codex，保留合法 SketchUp2024 与 WebView2 前置条件。安装/卸载拒绝活动进程或另一安装器；新版本目录成功后才原子切换启动指针，同版本原地覆盖修复被明确拒绝，旧版本及用户数据保留。资料目录可通过合法 junction 留在 E 盘。beta03 支持审核后的固定程序／资料路径，启动器将进程级 TEMP/TMP 放入资料目录的 temp，不修改系统全局环境。

## 工件与来源

本机工件根目录：项目数据盘 `outputs/video-storage/jobs/kstudio-r3-launch-20261107/`。这些是本机可核对的交付物，不是已公开 COS 下载地址。

| 工件 | 来源／验收范围 |
| --- | --- |
| beta03 E盘固定安装包 `installer-r3-beta03-e/KStudio-2026.11.07-R3-beta03-win-x64-setup.exe` | 版本 `2026.11.07-R3-beta03`，序号10，运行核心 `790d7f099939228b9828a6524eeccf94f374f7be`；311,380,733字节，SHA256 `35af0a8861c842a7773655797ed31a66fb8854ee62986d02fc387ce9354ed3b7`。完整70451文件审计和无推理Harness探针通过；本机E盘真实安装、开始菜单启动、资料保留及运行目录核对通过。此固定路径包供本机使用，未签名，不是公众下载包。 |
| beta02 冻结桌面 `build-r3-beta02/dist/KStudio` | 核心源码 `802c4b2fe98de8bcd966f6c6cf7e99162f566fe7`，70,451 文件；官方 Harness Python 0.2.1rc2 / Node 0.2.1-rc.5 / Node24.22.1；运行探针通过，不含作者 API |
| beta02 安装器 `installer-r3-beta02/KStudio-2026.11.07-R3-beta02-win-x64-setup.exe` | 版本 `2026.11.07-R3-beta02`，序号9；311,386,588字节；SHA256 `b12f33078b298b9796b395c7034064ff52cb680874861c23e3575fd8fac40388`。NSIS3.13，用户级安装；[逐项收据](../test-results/windows/2026-11-07-r3-launch-candidate/receipts/installer-beta02.json) |
| 云端＋网站源码 ZIP `cloud-source-final/KStudio-R3-cloud-website-source.zip` | 核心 `3f6c5c454cd140ce4ca735d1b2234e80a9ea0078`，111,186字节，SHA256 `76eb64417814ad22d3e87111be8f5bfe36d89bc5b597e2896d25d1032ed73ef0`；42成员核对通过，不含预构建镜像、私有环境或凭据 |
| 许可清单 `desktop-sbom-r3-beta02/` | 656组件、1028许可文本；第一方 LICENSE 缺项及9个上游原文本缺项（提供标准条款）尚待清理；`REVIEW_REQUIRED`，不等于已取得公开再分发许可 |

## 验收边界

[完整可公开证据](../test-results/windows/2026-11-07-r3-launch-candidate/README.md)保留初始失败、修复后结果及截图。Windows PostgreSQL 全集203通过；Linux PostgreSQL202通过/1跳过，真实Docker受限文件系统和network-none启动通过。各测试套件存在重叠，不能相加充当独立用例数量。

独立首次使用模拟者从真实候选网站出发，公开下载、登录、支付入口如实关闭，因此公网旅程 BLOCKED。后续本地安装包验收只记本机补充测试，不能改变这个结论。新资料目录也不等于干净 Windows 或第二台电脑。

真实 BAI BYOK 页面测试创建了独立两层展亭：beta01 经8次真实阶段提交到 r8，却因宿主最终截图目的路径不在配对工作区而报错。beta02 修正路径后，在同一项目实际完成门廊/入口平台局部修改到 r9；10组保护构件深层哈希未变，API 配置重启保留、页面预览和文件生成通过。实际页面下载的86,596字节 SKP 与检查点 SHA256 `31b41d386ae5d51426ba73d401688c046e5cd384720f8fdf86d77d7ce988c4bf` 一致，SketchUp2024原生重开12组深层几何/材质哈希一致。

随后栏杆修改失败：供应商流出现 `Connection error`，用量未知后本机预算保护拒绝 SDK 再次请求，旧版本仅显示 `Host tool refused: 400`。模型保持 r9，没有新栏杆提交，未清账或继续付费重试。beta03 保留保护机制，并把这一拒绝转成明确的中文原因；26项Python与7项Node离线回归通过，不冒充栏杆已修好。本次56个有用量结算请求、1个未知用量请求；供应商实际费用未知。栏杆和后墙/楼梯接合仍需改进；本例是文字定义的首用概念模型，不是复杂照片保真或规范/施工图验收。详见 [完整原生证据及保留的失败](../test-results/windows/2026-11-07-r3-native-byok-delivery/README.md)。

真实公网官网、手机/微信登录、付费充值/退款、平台网关真实首次建模仍需外部配置后验收。此候选未购买任何云资源、未充值、未向客户收费。CI/已有基础设施成本没有账单，记未知，不推断为零。

## 恢复与继续

保留原 R2 桌面入口和数据；R3 单独用户资料目录，卸载保留项目/API。安装失败不覆盖旧版本；同版本目录已存在时改用新构建序号，不能强制删除个人资料。云端使用 [备份恢复操作](../execution/KSTUDIO_R3_BACKUP_RESTORE_20261107.md)，应用回退不回写生产数据库。

负责人只需提供 [已核对的外部缺项](../execution/KSTUDIO_R3_EXTERNAL_INPUTS_STATUS_20261107.md)，工程继续同一 PR/源码完成目标主机部署和真实服务联调。代码签名、生产更新信任、许可及干净 Windows 验收未通过时，下载接口不会允许公开发行。

## E盘运行与C副本清理限制

已完整校验140,911个旧程序文件后，在E盘安装beta03并从开始菜单启动成功；实际EXE、资料、TEMP/TMP与WebView缓存均在E。原R2、模型、API配置和旧版本保留，Windows开始菜单及卸载注册已指向E。最后删除已验证的C盘旧程序副本时，自动审批返回 `blocked by policy`，命令没有执行，未改用其他方式删除。C副本仍在，不能宣称已释放其约2.04GiB空间。详见[迁移回执](../test-results/windows/2026-11-07-r3-launch-candidate/receipts/program-migration-final.json)。
