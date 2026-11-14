# K Studio R3 商业发布验收

执行依据为 2026-11-14 总执行书。固定审计基线 [PR #27](https://github.com/eksn425-del/ai-architecture-studio/pull/27) / `6a8001c5369c323666efa099472ea62f4fbf1c51`。当前桌面核心 `d097b1a5a1e1a45dfc0b5fe5a9301490f164b536`，安装器输入 `32c970bc31b13fc9bc226cf935432dfd6e56ca28`，云端实测逻辑 `e470797bd888c871eaac1ce89276395213f493b8`，统一交付 SHA `d097b1a5a1e1a45dfc0b5fe5a9301490f164b536`。

当前商业发布 **BLOCKED_EXTERNAL**。内部技术候选可供本机受控验收。各关卡保留独立核查、失败与复验。

| 关卡 | 结果 | 当前范围 |
| --- | --- | --- |
| [G00](G00/verdict.json) 基线、隐私和工作区 | PASS | 固定基线，核对原文件和安装，隔离试验 |
| [G01](G01/verdict.json) 首发产品范围 | PASS | Windows x64 与 SketchUp 2024 概念建模边界 |
| [G02](G02/verdict.json) Agent 和质量 | PARTIAL | 原生简单样件与 KEEP 已验证，真实供应商闭环与复杂保真未通过 |
| [G03](G03/verdict.json) 原生连接与恢复 | PARTIAL | 新包实机未知写入恢复、续改再下载已通过，完整故障矩阵待补 |
| [G04](G04/verdict.json) 安装与升级 | BLOCKED_EXTERNAL | E 盘隔离安装和本地更新复验，待合法依赖、签名与独立干净机 |
| [G05](G05/verdict.json) 官网和账号 | BLOCKED_EXTERNAL | 本机浏览器及协议边界已验收，需公网和真实 Authing |
| [G06](G06/verdict.json) 平台 API 和额度 | BLOCKED_EXTERNAL | 本机数据库和发送边界已验，需真实服务授权与成本回执 |
| [G07](G07/verdict.json) 支付退款 | BLOCKED_EXTERNAL | 验签、幂等与退款协议已验，需真实微信商户小额闭环 |
| [G08](G08/verdict.json) 部署与恢复 | BLOCKED_EXTERNAL | 源工件和本机 PostgreSQL 恢复已验，需实际 staging 与回退告警 |
| [G09](G09/verdict.json) 安全、许可、经营资质 | PARTIAL | 冻结工件已核对，许可及签名、合规和实际主机仍需确认 |
| [G10](G10/verdict.json) 首次真实用户 | BLOCKED_EXTERNAL | 真实新用户 0/3，正式完整流程 0/5 |
| [G11](G11/verdict.json) 放行和灰度 | NOT_RUN | 前置关卡未全部通过 |

[最终裁决](FINAL_RELEASE_VERDICT.md) · [外部输入](OWNER_ACTIONS.md) · [版本说明](RELEASE_NOTES.md) · [机器可读状态](release-state.json) · [普通用户验收](USER_FIRST_USE_REPORT.md)

[原生样件](../test-results/windows/2026-11-14-r3-commercial-native/README.md) · [beta10 报告缺失恢复与下载](../test-results/windows/2026-11-14-r3-beta10-pre-report/README.md) · [beta09 续改恢复](../test-results/windows/2026-11-14-r3-beta09-recovery/README.md) · [成本](COST_AND_BILLING_REPORT.md) · [安全许可](SECURITY_AND_LICENSE_AUDIT.md) · [运维](OPERATIONS_RUNBOOK.md)
