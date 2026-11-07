# K Studio R3 商业 Beta 候选工程证据（2026-11-07）

**本批 PARTIAL；商业公开 BLOCKED；真实建筑建模 NOT_RUN。** 已完成的签名支付、账户凭据、账本、部署容器和本机工程测试不能替代公开商业验收。没有付费模型请求、真实微信付款、充值或生产部署；没有修改本轮原生模型。正确基线为 R2 候选及 R3 实施分支，测试核心提交 `3f6c5c454cd140ce4ca735d1b2234e80a9ea0078`，不是仅凭 main 判断状态。

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

各suite含重叠用例，不能相加为独立测试总量。零费用仅指本轮实际未发生的产品模型请求/支付；CI和已有基础设施账单未取得，不能冒充零基础设施成本。

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

本目录当前尚待父代理补入最终安全重编安装包、安装/GUI首次使用的独立回执，详见 [待补清单](pending-evidence.json)。即使本地安装通过，也不能替代本次网站下载BLOCKED的结果，更不能当作另一台干净Windows验收。

公网域名/DNS/HTTPS及云运维、Authing/短信/微信登录、Native商户与回调、正式售价/退款/运营资料、代码签名和更新信任仍须实际配置和验证。不得用模板的失败关闭检查冒充已发现生产资源，也不得用合成登录/付款通过宣布商业Beta开放。

本批 `geometry_committed=false`；没有新建筑参考、原生六视图、KEEP、下载SKP或重开证据，所以不补造这些文件、不借用旧模型。付费真实模型和原生最终交付保持NOT_RUN。

## 公布边界与续验

只公布脱敏摘要、非秘密工件哈希与已审阅网页截图。不包含数据库、凭据、私有路径、原始日志、用户原图/SKP。JUnit摘要保留用例名/结果与原XML哈希，移除了机器名、堆栈和夹具密钥；原文件留在本机私有job。未来补入新的真实回执后，重新执行仓库证据校验器生成清单并验证。
