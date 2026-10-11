# K Studio 托管 Responses 本机开发入口

本轮实现 `app/responses_runtime.py`，复用原来的项目、重建 Skill、AgentToolSurface、Kongxing 单写者、ProjectRuby/KEEP、六视图质量门与独立只读 Critic。没有新网站，没有第二个 SketchUp 写入连接。普通用户不能通过配置窗替换托管运营供应商或提交运营 Key。

## 真实状态

- 图片 → Responses function_call → 工具结果 → 后续 Responses、多轮项目恢复、独立 Critic、取消和错误/预算门：**免费假传输回归已验证**。
- B.AI / 官方 Sol 实际请求、返回身份、图片能力、原生建模质量、账单：**NOT_RUN**。Astra仅可配置，未验收。
- Codex Luna Max是开发对照，不能冒充独立 API 服务，也不会自动回退到 Codex。
- 当前只适合受信任运营人员的 localhost 开发环境；**不是已上线的托管多用户或收费产品**。

## 运营端配置（不要将值提交 Git）

在受信任服务端环境设置 `ARCH_STUDIO_ECONOMY_PROVIDER=responses`。固定允许的端点 profile 是 `K_STUDIO_OPERATOR_PROVIDER=bai` 或 `official`；默认请求型号 `K_STUDIO_OPERATOR_MODEL=gpt-6.1-sol`。主渠道改变必须明确记录，不能悄悄切换。

Key仅由运营人员设置 `K_STUDIO_OPERATOR_API_KEY`，不进入静态网页、分发安装包或 Git。当前实现是进程环境中的服务端秘密注入，不是多用户密码保险箱；不要把平台总Key分发给终端用户。

**只有在真实条款/隐私/转售许可审核和用户明确授权预算完成后**，运营人员才能设置 `K_STUDIO_OPERATOR_TERMS_APPROVED=1` 与 `K_STUDIO_OPERATOR_LIVE_CONSENT=1`。这些配置是代码前置条件，不是取得商业许可的证明。本轮不设置、不付费。

同时必须提供有限正值 `K_STUDIO_OPERATOR_MAX_USD`、每百万Token最贵档单价 `K_STUDIO_OPERATOR_INPUT_RATE_UPPER`、`K_STUDIO_OPERATOR_OUTPUT_RATE_UPPER`。可设置 `MAX_INPUT_TOKENS`、`MAX_OUTPUT_TOKENS`、`MAX_REQUESTS`（都使用 `K_STUDIO_OPERATOR_` 前缀），默认200000/12000/12。

每次请求前按整个输入上限和输出上限保守预留；消息、图片base64、工具schema全计入UTF-8字节门。它不是模型tokenizer，默认大图可能被安全拒绝；不能为了测试通过无限放宽。修改上限需重新核算预算与供应商上下文限制。缓存输入按最贵档估算，费用是运营估计而非发票。

收到型号不符、非法工具参数、未完成输出、拒绝、缺usage或未知输出类型时停止；HTTP错误/超时不自动重试，无隐藏provider/model fallback。未知usage使当前回合熔断。POST `/api/managed-agent/cancel` 可取消后续请求/工具，**无法撤销已经发送的上游费用或已提交几何**。

实际Responses输出（含不透明推理项）保留在忽略的本机项目历史，完整回传后续调用；中断时每个已完成工具结果立即落盘。费用/型号/request ID/耗时回执保存在该项目忽略的runtime中，不能将私人源图/原始请求/Key上传公共证据。公开报告必须脱敏。

## 发布前仍缺的边界

当前预算锁为**单实例每回合**，不是持久账户钱包、跨进程原子预留或每日总额。cancel/loopback/global lock不是用户身份认证。现有项目JSON不是租户数据库。

真正多用户前需要：身份+租户RBAC、Postgres项目与持久预算预留/结算、项目worker租约、供应商速率/并发/重试幂等账务、签名配对的本地连接、运营秘密管理和最小权限、不可变源/工件存储、失败回滚与退款政策。只允许租户拥有的项目/工件上下文；每个SU会话一个写者。必须以并发/跨租户/账务故障测试和真实供应商建模证据验收，当前一律NOT_READY。

## 本次真实证据

[两次严格重放、原生编辑和协议回归](test-results/windows/2026-10-11-managed-agent-beta-offline/README.md)。专业构件诊断仅检查命名组、PID及尺寸，状态仍PARTIAL；不会把分组通过标为屋面/墙/楼梯连接质量通过。
