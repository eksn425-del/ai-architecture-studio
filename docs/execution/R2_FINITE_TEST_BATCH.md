# 有限测试批次：执行控制与下一步申请

## 已实施的边界

只有设置 `KSTUDIO_TEST_BATCH_CONFIG` 指向独立 JSON 时才启用。普通 BYOK 不设置此变量，不受测试额度限制。前缀不会被桌面 bootstrap 删除；配置/SQLite/OS lease 保存在测试 job 中，不能打入发行包。配置不保存 Key。

`dsh_test_budget.mjs` 使用官方 `llm/stream` waterfall，在下游 adapter 第一次 dispatch 前调用宿主预留，不替换官方 agent loop。SDK的主请求、重试、子代理及官方压缩摘要共用这个入口。`dsh_test_budget.py` 使用 SQLite 原子事务及持久 batch ID/config SHA，跨会话、并发进程和重启累计。改变同一 batch 上限会被拒绝；预登记项目 allowlist 与各 run 等额上限防止另开项目重置。

请求数是精确的**最多允许 dispatch 次数**；已经预留但未真正发出也计数，因此可能保守少发，不会多发。单个请求预留 `declared_context_window + max_output_tokens`，已知 usage 也不退回这份保守 token 配额。配置必须覆盖有效模型容量及输出；可绑定完整 effective configuration SHA。未知 usage、断流、取消、超声明 usage、崩溃后失去 owner OS lease，都会保留未知预留并阻止本批后续 dispatch。官方 retry 即使被触发，也会先被同一账本审核。

**token 配额是保守预留，不是服务商实际 token/账单的数学保证。** 容量、图像与缓存计价、推理 token、路由实际模型和返回 usage 仍依赖服务商。这里没有把价格登记冒充账户端硬封顶。模型侧提示词和正常用户也不能覆盖测试账本；有本机管理员权限的人仍能修改代码/环境，未宣称防管理员篡改。

## 下一批提案，尚未授权/执行

仅选择已登记的复杂悬挑/外露楼梯整图：`codex-clipboard-33a08989-5a43-4fbb-a7f5-1fb4f9d33941.png`。来源 SHA/自然任务与关键空间事实见 `R2_BENCHMARK_SOURCES.json` 的 `split_level_cantilever_stairs`。不扩大到三类全矩阵，不更改旧模型。

- 三组：相同受控工具面的官方 SDK 基线、K Studio 最小指导、K Studio 建筑指导；每组两个独立新项目，共六次。
- 每个项目最多 **30 个 LLM dispatch**，总共最多 **180**。包括意图判断、计划、Builder、工具后续、压缩、子代理、重试、恢复；不是180次建模工具，也不是180次用户消息。
- 六个实际项目 ID 必须预登记；同一个 run 的 intent/builder/子代理/继续聊天共用30次。相同 source bytes/order、provider/model/effort、工具目录、权限、内存、修正次数和验证条件。只允许指导/skill差别。
- 拟用 BAI `deepseek-v4.1-flash`，High，声明输入容量131072、单次输出最多32768；每请求预留163840 tokens，整批最多29491200个保守 token 额度。真实服务端能力仍待核验。
- 当前官方 B.AI 峰值公开价格参考：input/cache-write $0.30/M，output $1.20/M；按180次全部用尽上述输入/输出计算，参考值 **$14.155776**。来源：[B.AI定价与用量](https://docs.b.ai/zh-Hans/llmservice/pricing-and-usage/)，2026-11-04核查。不是人民币金额、实付保证或充值授权；账单按真实上游计量核实。
- 达到任一总量/单run上限、未知费用、认证/余额错误、原生UNKNOWN提交、取消或KEEP异常就停止。不得自动加额、充值、订阅、换模型或重放整次建模。未完成 run 如实PARTIAL/NOT_RUN，不提高额度凑结果。

`R2_FINITE_TEST_BATCH_PROPOSAL.json` 为不可执行的提案：authorization=awaiting_owner_confirmation，六个项目 ID 已通过 build04 实际界面创建并绑定。六个新项目和整图上传已完成；继续在首次运行前核对统一catalog/config绑定，取得对此具体批次的明确授权，再生成真正配置并持久冻结。配置变更不应覆盖已经启动的 batch 账本。当前付费请求仍为0。

## 零费用验收

- 实际锁定官方 SDK：两协议主请求+工具回执、恢复会话后达到硬上限、SSE半工具参数断流后未知阻断。
- 实际官方 subagent 创建并发子会话，共享请求上限；官方 `BasicCompactionEngine.summarize` 在真实SDK agent上通过本机SSE调用并记录 `purpose=compaction`。该项验证真实摘要入口，不声称整段自动历史压缩性能/质量验收。
- 官方503 retry事件仍存在，但未知预留阻止再次发HTTP；实际SDK流式取消也保留UNKNOWN。
- 七个真实Python进程争抢三次总额度恰好仅三次成功预留；崩溃进程重启不清账；配置变化、未登记项目和单run超额被拒绝。

测试均使用127.0.0.1合成provider和dummy key，不是付费模型质量验收。XML/原始SDK trace在本机R2 job，最终计数见 `R2_RUNTIME.md`。
