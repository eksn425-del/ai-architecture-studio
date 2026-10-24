# K Studio 最小用量审计修复与离线复核（2026-10-24）

## 独立审阅后的补充修复

在证据提交 `ba77193a89786835807e4d0536c0f3a029f6ed12` 之后，修复审阅发现的两处可信度缺口：账本覆盖按唯一attempt ID配对，重复ID（包括完全相同的重复行）显式标异常、金额未知，不再用行数相等误判A/A覆盖A/B，也不重复累计负债；finished回执对status、model和关键身份及usage的冲突稳定保留为未知，后续相同回执不能抹掉冲突，正常started→finished和延迟重复started仍有效。

本次仅相关离线回归：聚焦48 PASS，相关178 PASS / 1 SKIP；未重跑全量或原生栏杆，以下原始25/155/1353等结果及原生16/16均保留为前版事实。`test-summary.json` 新增 `review_followup` 区分新回归，并纳入实际38项基线失败的逐项配对状态、安全摘要和原始证据哈希（`paired_baseline_failures` / `baseline_comparison`），不是整套全绿声明。预算fail-closed没有改动，无真实请求。

本轮仅在隔离分支 `codex/run-usage-audit-20261024` 工作，基线 `41fee1ba1c13f8d737a99d3733edef276a0a02fd`，实现提交 `43993e1f9ade1b198a98b648399265011f022694`。未推送、合并、部署或启动用户服务；未读 API 密钥，未使用真实 LLM、付费 API/GPU、用户模型或录像。原仓库已有未提交改动，候选 worktree 起始干净。仓库与用户级 `.agents/skills` 未发现适用此代码审计的技能；已读 AGENTS、CURRENT、CURRENT_TASK、执行守则和最新交接，按本轮明确范围覆盖旧推送/建模指令。

## 实际修复

- `app/provider_test_budget.py`：继续使用原 `requests` ledger；新增可选 attempt ID，与对应运行 trace 的派发事件一一关联。异步取消/KeyboardInterrupt 等 BaseException 在派发后也持久标记 `unresolved`，保持原预留负债，不清账、不返回预算。
- `app/litellm_runtime.py`：Builder、Critic、意图理解共同使用的既有 `_invoke_provider` 边界记录派发与结束。记录只包含标识、usage 数字和异常类型，不包含请求、密钥或上游响应全文。先写原账本预留，再记录派发；成功取 usage，未知保留为 null。
- Native/API trace 新增运行来源：HEAD SHA、实际运行 Python 源文件内容摘要、选中 runtime/provider/model、角色与 UTC 时间。Native 继续保留 App Server 实际报告身份与本轮累计差额。安装副本无 Git 时 SHA 为 null；工作区 dirty 状态不猜测，实际源码摘要用于辨别源码变化。
- `app/run_usage_audit.py`、`scripts/audit_run_usage.py`：读取同一 agent_events trace 和显式指定的原 ledger，输出统一只读视图，不建另一个余额账本。普通输入 = 总输入 − 已知缓存子集；输出已含 reasoning，不再次相加。重复 attempt receipt 不累计，冲突回执变未知，Native 累计 run delta 取末值、不求和。无稳定 ID 的旧事件保留事件数，但不声称已去重的用量。
- HTTP 请求数、SDK 内部重试和真实账单没有证据时为 null。`settled_upper_bound` 与未决预留分开，均不是账单。13 条模型响应事件仍是 13 条事件，不能改名为 13 次 HTTP。
- 既有原生 `tool_receipt` 中的几何对象数、模型 SHA、revision、native_reopen 和 quality_status 可在审计中追溯；KEEP/可编辑性/整体验收没有独立证据时仍 NOT_VERIFIED。工具成功、原生重开、源图质量分别报告。
- 复用现有栏杆合成验收；修复其 Windows 脚本化 peer 的 UTF-8 管道及文本读取，不新增几何实现。`.test-runtime/` 现在明确忽略，防止测试模型、日志和合成凭证被意外暂存。

## 已完成验证

| 验证 | 结果 | 说明 |
|---|---|---|
| 审计/预算/Native usage 初始聚焦 | 23 PASS | 早期版本；最终新增两项冲突及原生回执检查 |
| 最终相关 Python 回归 | 155 PASS / 1 SKIP | 含审计、预算、模型路由、B.AI SSE、取消、身份、隔离安全、Responses、loopback HTTP、栏杆合成规格 |
| 完整 Python 回归 | 1353 PASS / 38 FAIL / 19 SKIP | 在最后两项审计测试加入之前执行；不冒充最终完整全绿 |
| 上述 38 失败在未修改基线重跑 | 38 同样 FAIL | 13 项 WinError1314 symlink；8 项默认编码；3 项 Node spawn EPERM；其余14项基线失败，保留清单，不擅自全部归为权限问题 |
| Node UI（直接单进程运行） | 126 PASS | `--test-isolation=none` 避开沙箱禁止 Node 子进程的环境限制；未改系统权限 |
| 原生栏杆受控验收 | 16/16 PASS | 已装 Blender 5.0 alpha，7轮脚本化 App Server、74对象、6修改、68 KEEP、2次原生版本及独立重开；不是 LLM 智能测试 |
| 零付费 usage replay | PASS | 缓存、缺 usage、超时、取消与原 ledger；重复累计/13事件歧义；生成可读 JSON |

完整失败名、类别和基线对照见 `test-summary.json`。原始本机日志和 JUnit 在隔离工作区 `.test-runtime/` 保留。没有为了制造 PASS 开启 symlink 权限、关闭沙箱或改代理/系统网络设置。

保留的过程失败：首次 pytest 指定的 basetemp 父目录未创建，导致23项选择中11个 setup error和128项选择中101个 setup error；建立任务 scratch 后重跑。初版 provenance 调用 git 子进程与已有 FakeProcess 协议测试冲突，产生27个回归失败；改为只读 Git 元数据及源码摘要后151项通过。栏杆入口第一次在 peer 的 UTF-8/GBK 解码失败，第二次在 Blender 后端默认 GBK 解码失败；第三次以仅进程级 `PYTHONUTF8=1` 运行16/16通过。前两次目录和日志完整保留，不伪装成一次全绿。

## 如何复核

在此分支、现有 Python 3.12 环境中运行，不安装软件：

```powershell
$env:PYTHONUTF8='1'
$env:LITELLM_LOCAL_MODEL_COST_MAP='True'
$env:ARCHFLOW_GENERATED_SCRIPT_DIR=Join-Path (Get-Location) '.test-runtime/generated-scripts'
New-Item -ItemType Directory -Force $env:ARCHFLOW_GENERATED_SCRIPT_DIR | Out-Null
python -m pytest -q tests/test_run_usage_audit.py tests/test_provider_test_budget.py tests/test_native_usage_breakdown.py -p no:cacheprovider
python scripts/replay_run_usage_audit.py --output .test-runtime/replay-NEW
python scripts/audit_run_usage.py .test-runtime/replay-NEW/cache/events.jsonl --ledger .test-runtime/replay-NEW/cache/budget.json
node --test --test-isolation=none tests/test_ui_*.js
```

replay 必须用新目录，拒绝覆盖旧证据；其中 endpoint、model、usage、费率全部是测试常量，没有真实请求。审计实际运行时将 trace 与其原 ledger 作为参数，不能给一个无关联 ledger 就声称覆盖全部费用。Native 示例无该账本覆盖，费用应继续未知。原生栏杆详细入口见 [固定规格](RAIL_ACCEPTANCE.md)。

## 金额硬上限：保留关闭保护

App Server 的可控入口是 `turn/start`，不是其内部每次 Responses HTTP 派发；一个 turn 可包含多次模型请求/重连。当前没有宿主可在每次真实请求之前原子预留金额的 hook。因此没有改 `_check_api_budget`，配置金额上限仍拒绝 `codex-responses`，不能拿事后 usage/估算充当支出上限。本轮也没有新建代理、凭证或调整网络安全设置。

现有 LiteLLM 路线有 `_invoke_provider` + 原 ledger 的预派发边界，本次只补其可核对性和取消保留。它是本机单进程锁、按事先声明的最坏费率和输入/输出上界预留，仍需要验证供应商实际计费规则、输入边界、SDK重试行为。没有把它宣布为跨进程或托管 SaaS 的精确支付系统。

将来若要为 App Server 支持硬上限，必须先获得受控的逐 HTTP 派发 hook 或经过认证的供应商预算端点：持久写入唯一请求/模型/预算授权 → 以完整文本、图像、工具 schema、reasoning 的保守上界预留 → 才派发 → 已知usage仅结算为上界 → timeout/取消/崩溃仍保留负债；并发必须原子争用同一总账。缺价格或最大输入/输出/重试边界则拒绝派发。这是设计及阻塞，尚未实现。

## 仍不能保证与下一次真实测试

本轮没有真实第三方质量、端点实际服务模型证明、准确账单、真实成本节省、SketchUp真机可编辑性或商业验收结果。离线证明的是审计和保护契约，不是源图建模能力。先前 schema重写、超时与上下文膨胀的历史失败仍有效；本轮没有新证据把质量差归因于某一个模型或网关。

下一次候选规格（**未批准，不能执行**）：B.AI 网关、`deepseek-v4.1-flash`、原 LiteLLM/B.AI SSE 路线，仅合成六栏杆局部改动；新一轮上限建议 USD1，总新增测试额度建议 USD2，先由用户明确同意具体账户/模型/单轮及总额。不得继承旧USD2授权，也不能清除旧ledger的未决负债来获得额度。实际费率、模型输入输出上界和每次预留须重新核验并写明；额度不足或账本无法保守预留就停止。若选择 `codex-responses`，即便同意预算，仍须先解决逐请求边界，保持关闭保护。

下一次验收至少记录准确代码来源、选中/报告身份、完整用量/缓存来源、原ledger、失败与未决、6目标尺寸/68 KEEP、保存重开和继续编辑。只有独立原生几何检查通过才算栏杆任务通过；真实模型及支出未知项不能借用本次 fixture PASS。
