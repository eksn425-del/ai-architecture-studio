# K Studio R3 商业 Beta 候选工程证据（2026-11-07）

**工程候选 PARTIAL；商业公开 BLOCKED。** 本目录记录云端工程、安装器及独立首用验收。真实 BAI 建模单独记录在 [原生 BYOK 交付证据](../2026-11-07-r3-native-byok-delivery/README.md)，不能把本目录工程夹具的零模型请求推广为整个 R3 任务零调用。没有真实微信付款、充值或生产部署。正确基线为 R2 候选及 R3 实施分支，云端已验收核心 `3f6c5c454cd140ce4ca735d1b2234e80a9ea0078`，原生r9已验收桌面核心 `802c4b2fe98de8bcd966f6c6cf7e99162f566fe7`；含错误诊断修复的beta03核心 `790d7f099939228b9828a6524eeccf94f374f7be` 已完成真实E盘安装、开始菜单启动及进程路径验收。C盘旧副本的删除被工具策略拒绝，尚未清理。

## 已观察的结果

| 项目 | 实际结果 | 证据 |
|---|---|---|
| 最终本机完整 PostgreSQL suite | 203通过，0失败/错误/跳过，45.563秒；临时数据库已由负责代理正常停止 | [用例清单与原XML哈希](tests/junit-summary.json) |
| GitHub PostgreSQL17 suite | 202通过、1跳过，25.68秒；参数化 PostgreSQL 项实际执行 | [真实CI摘要](receipts/ci-summary.json) |
| GitHub Docker | 实际构建并运行 restricted filesystem / network-none 容器成功；不曾部署生产 | [真实CI摘要](receipts/ci-summary.json) |
| 数据恢复演练 | PostgreSQL17.11，表记录相等、账本一致、1个夹具凭据可解密、待处理支付回执恢复一次，2次维护周期 | [脱敏回执](receipts/postgres-restore.json) |
| 微信适配器及页面 | 27项底层、4项HTTP权限/CSRF、1项真实Edge页面夹具通过；合成支付回执，不是真实扫码支付 | [测试明细](tests/junit-summary.json)、[页面截图](website/wechat-qr-fixture.png) |
| 桌面回归 | 首次15通过/1编码失败，指定UTF-8后16通过；初始失败保留 | [错误记录](errors.json) |
| 打包内核探针 | 实际捆绑Node v24.22.1、SDK import与工具枚举成功；没有调用模型 | [探针](receipts/bundle-runtime-probe.json) |
| 捆绑文件清单 | 70,451文件，清单检查通过；未签名、非公开就绪 | [清单摘要](receipts/bundle-inventory-summary.json) |
| 云端源码工件 | 111,186字节，40载荷/42归档成员，所有成员哈希核对通过；不含预构建镜像 | [工件回执](receipts/cloud-source.json) |
| 独立首次使用网页 | AGENT_SIMULATED沿可见页面操作；下载被真实disabled入口阻塞，账户及平台服务未开放 | [完整独立报告](review/first-user-web.md) |
| beta01 实际安装与首启 | 安装、开始菜单启动、新资料目录空 API 通过；不是干净 Windows 验收，未由首次使用代理执行建模 | [首用报告](review/first-user-desktop.md)、[包与安装回执](receipts/installer.json) |
| beta02 构建 | 修复配对工作区外截图导致原生建模最终报错；冻结包、全工具探针、安装器编译、独立 SHA 核对通过 | [beta02 回执](receipts/installer-beta02.json) |
| beta02 实际UI恢复与门廊修改 | API加密配置哈希保持、未重新填Key，待批准方案恢复；实际UI批准后r9完成且截图/下载链接正常，10个无关组KEEP相同 | [原生补充验收](../2026-11-07-r3-native-byok-delivery/README.md) |
| 宿主400诊断修复 | 26项Python及7项Node离线通过；保留未知用量停止保护，错误细节可透传；不等于真实栏杆纠正复测通过 | [脱敏回执](receipts/host-refusal-diagnostics-fix.json) |
| 自选安装盘/启动器回归 | 35通过、2个明确opt-in夹具跳过；PowerShell启动器使用观察者替代启动应用，不伪称真实安装 | [脱敏回执](receipts/install-roots-regression.json) |
| beta03 E盘安装与启动 | 实际GUI安装/StartMenu启动通过；空API/账户未配置如实展示；201小文件SHA保持 | [包回执](receipts/installer-beta03.json)、[独立首用](review/first-user-beta03.md) |
| 实际运行目录 | EXE/资料/TEMP/TMP及6个WebView进程资料路径均E；未改全局环境 | [运行核对](receipts/runtime-on-e.json) |
| C副本最终清理 | 自动审批拒绝删除，原C目录保留；未绕过，未宣称释放C盘空间 | [最终迁移状态](receipts/program-migration-final.json) |
| C→E程序副本核对 | 140,911文件、2,190,840,011字节，完整文件集及所有SHA匹配；C原件尚未删除，原R2未动 | [复制阶段回执](receipts/program-copy-to-e-checkpoint.json) |

各suite含重叠用例，不能相加为独立测试总量。本目录离线夹具没有产生付费模型调用；后续真实BYOK批次已有57笔预留请求（56 settled、1 unknown），不能再称整个R3任务零费用。已知输入含缓存1,957,920、输出72,581；总usage/实际金额未知，基础设施账单也未取得。

真实native补充整体PARTIAL：初始r8末尾宿主截图归档失败，beta02修复后门廊r9、10组KEEP及实际下载/原生重开通过；栏杆纠正在供应商TRANSPORT连接错误后触发unknown保护。SDK虽产生重试意图，本机在新预留前拒绝，没有第58次供应商派发。栏杆与后墙阶梯轮廓缺陷保留，后续只有离线诊断修复，没有继续付费或重置账本。

## 真实页面截图

以下截图来自本机候选网站，**不是生产官网**。首页建筑图明确为产品空间示意，不是本轮建模效果。

- [首页](website/00-home.jpg)
- [公开下载关闭及发行元数据](website/01-download-blocked.jpg)
- [身份服务未配置](website/03-login-blocked.jpg)
- [数据库可用、模型/支付未配置](website/08-status.jpg)
- [隔离测试订单二维码](website/wechat-qr-fixture.png)：独立测试账户及假订单，仅测试渲染/查询/关单链路，不能用于支付。

## 失败和修复保留

首次云CI [42329089916](https://github.com/eksn425-del/ai-architecture-studio/actions/runs/42329089916) 因依赖/模块环境失败；第二次 [42329449289](https://github.com/eksn425-del/ai-architecture-studio/actions/runs/42329449289) Docker成功，但PG重启测试把脱敏密码URL当成真实连接URL导致1项失败。修复后 [42330104234](https://github.com/eksn425-del/ai-architecture-studio/actions/runs/42330104234) 两个job成功。详细原因和本机首次编码失败见 [errors.json](errors.json)。历史失败不会因为最新通过而删去。

## 尚未完成的真实验收

beta01安装器及GUI首次使用的独立回执、beta02原生恢复证据已经补入；逐项状态见 [验收清单](pending-evidence.json)。beta03已实际安装和启动，程序、资料、TEMP/TMP与WebView均在E，207个原资料文件保留。C副本删除被自动审批拒绝（仅返回blocked by policy），命令未执行，未尝试其他删除路径；仍需清理已验证的旧副本。本地安装通过不能替代本次网站下载BLOCKED，更不能当作另一台干净Windows验收。

公网域名/DNS/HTTPS及云运维、Authing/短信/微信登录、Native商户与回调、正式售价/退款/运营资料、代码签名和更新信任仍须实际配置和验证。不得用模板的失败关闭检查冒充已发现生产资源，也不得用合成登录/付款通过宣布商业Beta开放。

本目录 `geometry_committed=false` 只描述云端工程及安装批次。真实页面生成的新模型、局部编辑、失败恢复、六视图、KEEP 和原生交付归入上面链接的独立原生证据目录；其结果按实际记录判断，不由工程测试推断。

## 公布边界与续验

只公布脱敏摘要、非秘密工件哈希与已审阅网页截图。不包含数据库、凭据、私有路径、原始日志、用户原图/SKP。JUnit摘要保留用例名/结果与原XML哈希，移除了机器名、堆栈和夹具密钥；原文件留在本机私有job。未来补入新的真实回执后，重新执行仓库证据校验器生成清单并验证。
