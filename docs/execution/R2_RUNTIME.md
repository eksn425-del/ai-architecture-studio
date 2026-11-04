# R2 运行配置、图片与空间交接实施记录

2026-11-04。状态：工程及本机离线验证 PASS；真实供应商兼容批次、真实 SketchUp 质量对照 NOT_RUN。本记录不改写旧 PARTIAL/FAIL，不表示已发布或已训练模型权重。

## 已落地

- `app/dsh_configuration.py` 统一端点、模型、协议、effort、窗口/输出上限、视觉/工具/流式声明与证据来源。连接保存、恢复、路由、讨论/计划/执行、意图识别、会话 binding、官方模型描述符、压缩和 spawn/fork 子代理使用同一个配置。未提供服务端回传时 `reported` 为 null。
- 移除连接路由固定 high、执行环境默认 low 的覆盖。产品当前开放经过验证的 provider-default/low/high；medium/max/xhigh 不静默降档。当前官方文档存在其他档位，不代表每个中转端点或本产品组合已经验收。
- **provider-default 实测发现并修正了两个容易误判的边界**：只用 `off:null` 在 Chat Completions 省略字段，但 Responses 仍发 `none`；声明 `reasoningEfforts:false` 后 Python SDK 初始化不能显式传 `off`。最终使用请求专属 `reasoningEfforts:false` 加 Python SDK `reasoning_effort=None`（字段省略）。此处表示客户端不设置推理控制，不能解释为供应商停止思考。
- full profile 保留官方 loop/工具/会话/压缩/子代理实现。只配置相同 provider/model/effort/output；子代理不能自行换模型；原有单写入守卫不变。原生与建筑引导组共享工具、批准、范围、图片、记忆和 effort，仅指导文本不同。与官方直接使用组仍须另行登记实际运行条件，不能把最小引导组叫作无封装官方组。
- 未知端点不再被当作 128k 多模态模型：默认 16k/4k、能力未声明；用户可填写上下文、输出、图像、工具、流式能力，标记 `user_declared_unverified/NOT_RUN`。缺少实际运行所需能力时明确拒绝。精确 BAI/DeepSeek 历史组合只保留历史本机配置标签，不转移真实 PASS；更换端点/模型/协议清空未更新的旧声明。
- PNG/JPEG/WebP/GIF 校验真实内容、扩展名、损坏、文件和解码像素上限。GIF 固定第 0 帧；EXIF 方向规范化派生 PNG，原件不变，记录原始/发送 SHA、方向、格式、尺寸、派生和帧。SDK 请求按界面上传顺序，角色来自 host manifest；不把问题图/输出图提升为来源真值。
- `spatial_handoff.py` 扩展既有设计图与工作区：坐标/尺度、楼层、错层/悬挑/退台/孔洞/楼梯平台、推断、KEEP、计划 hash、来源角色/hash、实际 root/revision、最近视图、脚本 hash、未完成项及中断摘要。新增内容是上下文，不是授权或几何已验收的证明。修改已保存关键空间事实须在新计划说明依据，沿用原批准流程，不增加每个普通工程步骤的点击。
- 有界注入最近最多 16 条/12000 字对话，完整原始记录仍保存在项目，提供归档 hash 和未注入数量；批准图、空间事实与当前状态不靠自由摘要记住。超长当前消息明确拒绝而非截断。阶段 binding 变化保留原会话并从持久项目状态开始；同 binding 使用官方 resume。
- 修复 Windows CRLF 下 Skill catalog 与实际读取回执 hash 不一致，统一对原始 bytes 哈希。只调整 spatial Skill 的交接要求，没有复制竞争对手专有内容。
- `responses_runtime.py` 修复独立 Responses 适配器的真实契约错误：已验证 `status=completed` 的回复转换为共享接口时缺少 finish_reason。现在按有无工具调用映射 tool_calls/stop；保留拒绝截断/过滤/未完成输出的守卫。

## 实际验证

| 项目 | 结果 | 证据边界 |
|---|---|---|
| 本轮相关 Python 集合 | 219 PASS | `runtime-final.xml`；包含历史失败归因及新边界测试，无真实建模 |
| 官方 serializer → localhost HTTP | 6 PASS | 两种协议 × 默认/Low/High；实际请求模型、effort 字段、输出上限、工具 schema、4 种输入格式派生后的字节和顺序、SSE usage/终止 |
| 官方 Python SDK 完整 loop | 2 PASS | 两协议，真实调用本地 read probe 一次→503→官方请求级重试→完成→进程重新初始化→同官方 session resume；工具未重放、工具结果保留 |
| 官方 SDK full 初始化 | 2 PASS | provider-default/high；各 25 个实际原生工具，零推理请求；子代理配置成功加载 |
| 真 BAI/其他供应商新验收 | NOT_RUN | 未发生付费调用，本地 HTTP 不能证明供应商能力/计费 |
| 真实 SU 几何、源图保真、KEEP、保存/下载重开、外部机 | NOT_RUN | 不从 Python/SDK 成功推导原生质量 |

私人机读记录位于项目 E 盘 `outputs/video-storage/jobs/kstudio-r2-20261104/`：`runtime-final.xml`、`official-sdk-loop.xml`、`pytest-sdk-loop/*/trace-*.jsonl`、`sdk-init2/*/events.jsonl`。初始错误保留在第一次运行输出；SDK 完整测试由已安装 Python SDK **0.2.1rc2** 和 Node/插件 **0.2.1-rc.5** 组成，没有声称两者版本相同或升级了上游。

历史 fixture 修正：预算仍阻止未核费用，只更新断言到实际准确文案；连接错误阶段改为可观测 `awaiting_headers`，不从异常名猜已建立连接；虚拟 LiteLLM 成功回复显式提供终止原因；规划工具集补上已有只读 `workspace_read_many`。没有删除测试或放松写入/预算守卫。

## 复跑（零付费）

使用已安装项目 Python，`PYTHONUTF8=1`，所有临时目录指向项目 E 盘。设置 `KSTUDIO_TEST_DSH_SDK_SITE`、`KSTUDIO_TEST_DSH_BIN`、`KSTUDIO_TEST_DSH_NODE_MODULES` 为实际锁定依赖目录。

```powershell
python -m tests.prepare_dsh_wire_fixture <项目输出目录>/wire-fixtures
$env:KSTUDIO_TEST_EFFECTIVE_CONFIG = '<项目输出目录>/wire-fixtures/configuration.json'
$env:KSTUDIO_TEST_RETRY_POLICY = '<项目输出目录>/wire-fixtures/retry-policy.json'
node --test tests/test_official_dsh_configuration.mjs tests/test_official_dsh_retry.mjs
python -m pytest tests/test_r2_runtime.py tests/test_official_dsh_local.py --basetemp <项目输出目录>/pytest-r2
```

官方 SDK 测试无依赖路径时显示明确 skip，不算 PASS。测试中的端点只有回环服务，Key 是固定虚拟字符串，不读取真实账户。

## 真实对照的下一步

`R2_MODELING_BENCHMARK_TEMPLATE.json` 明确三类：立面层次、错层/悬挑/楼梯、多视角空间关系。当前每类来源 `NOT_SELECTED`、运行 `NOT_RUN`；不能把一张照片包装成多视角样本。

`app.modeling_benchmark.register` 需要准确来源 hash/顺序/角色、自然中文任务、尺度、关键特征与误差、实际配置/DSH/工具 fingerprint、有限授权预算、重复次数和预先冻结的评审标准，采用独占新文件写入防止事后改标准。`assert_equal_conditions` 拒绝条件缺失/不一致。登记本身不授权花费。来源和授权齐备后，真实客户端依次运行官方基线、K 最小引导、K 建筑引导，保留失败，依据既定规则评审原生模型。小样本不得推出整体优越性。

## 官方依据与剩余边界

2026-11-04 核对 [官方 Harness](https://www.deepseek.com/harness/en/)、[官方源码](https://github.com/deepseek-ai/deepseek-harness)、[DeepSeek thinking 文档](https://api-docs.deepseek.com/guides/thinking_mode/)、[Responses 协议](https://api-docs.deepseek.com/guides/responses_api/)。实际适配以本机锁定 SDK 的 `llm-pi-ai`、`agent-default-model`、`tool-subagent` 和真实 wire 结果为准；DeepSeek 直连的文档不自动给 BAI 端点背书。

官方请求级有限重试保留。本轮验证一次 503 重试不会重放已完成工具；Retry-After 在具体供应商的实际行为、未知提交后的原生读回、取消中的真实供应商用量、压缩后的真实建筑效果仍需单独验证，不能从此离线结果声称全部完成。所需外部条件只阻塞真实批次，不阻塞本次代码与安装候选准备。


## 后续集成发现与公开连接器复审

- 实际 UI 发现未设置 SDK 目录时连接保存后的 status 抛 KeyError/500；已修为明确 dependency unavailable，保存/查看设置不依赖运行时安装。48 项后续回归 PASS，`runtime-ui-fix.xml`。网页组另行保存真实界面复测证据；原失败保留。
- 公开 Ruby 薄连接器 ROOT 的 Windows 反斜杠被 `Dir.glob` 当转义处理，目录存在但请求扫描为空；规范化为 `/`。无效/损坏请求移到私有 rejected 目录，不再占据前两条阻塞健康请求；writer.lock 打开失败也清除 busy；最终 journal 保留初始文档身份/请求和脚本 hash，RETURNED 仍只表示 transport 返回。
- 相机/图像导出必须携带模型路径/GUID，public 协议 Adapter 先读身份后绑定；不匹配的 SU 实例不消费另一文档请求。旧连接器协议未增加不支持的参数。没有修改任何显示材质/风格设置。
- 跨新 operation 的未知写入门控复核位于既有 ProjectRuby：先持久化 intent，任何 unconfirmed owned revision 都禁止所有后续模型写入，包括不同 script_id，允许只读调查。没有把脚本 hash 去重当作全局提交恢复。
- 连接器/安装/原生提交/深指纹/相机离线回归 54 PASS，`connector-review.xml`。Ruby 在真实 SketchUp 加载、实例路由和 native 结果仍由主执行者单独验收，此离线数字不代替其原生证据。

图片回执边界补充：`dsh_images.sent_sha256` 标识送入 Python SDK 的规范化输入，官方 attachment 层仍可按自己的图像预算缩放/重编码，不是任意大图的最终 HTTP 字节保证。6 组 wire 测试逐字节核对的是小尺寸合成 fixture；真实大图与真实供应商的最后请求边界仍需对应批次留证。

## 2026-11-04 §10.3 production boundary closeout

- Added `dsh_security.py` + `dsh_tool_policy.mjs`. Default full SDK composition now preserves official orchestration while arbitrary shell/filesystem/plugin/config/code-workflow tools are unregistered; unreviewed future tools fail closed. Explicit trusted-development remains unconfined. External MCP launch is rejected in production, and direct second-MCP calls are denied in the hook.
- Attached existing reviewed workspace file proxy to both product guidance arms so persistent Ruby creation/read/search still works; ProjectRuby remains the product write route. Subagents are read-only allowlisted. Windows reparse/junction roots/parents rejected, not only `is_symlink()`.
- Actual same-user child process demonstrated synthetic credential read and repo write before policy; no real credentials touched. Actual official full SDK initialization confirms process/file tools absent while subagents/web/skills remain. This is not an OS sandbox; SketchUp arbitrary Ruby and malicious same-user processes retain host-user permissions. See R2_EXECUTION_BOUNDARY.md for explicit remaining boundary.
- `request_retries` 0..2 flows through effective configuration to official retryPolicy. Both real local HTTP protocols prove 0 causes one request on503. Platform device-token bridge can select0 without hidden SDK retry/rebilling.
- Final freeze verification: **78 Python PASS** (`runtime-security-freeze.xml`, includes both actual official local HTTP checks and inventory), **18 related PASS**, **21 fairness/config PASS** after explicit full/protected parameterization, **5 Node PASS**. Sets overlap; do not add these counts as unique tests. Tests use E job basetemp. An initial command named two nonexistent test files and ran no tests; corrected invocations above ran to completion.
- `R2_BENCHMARK_SOURCES.json`: three classes with1+1+8 owner sources, whole images inspected, exact SHA/order/role and natural tasks/critical geometry frozen. Private absolute paths only E job `benchmark-source-registration/source-criteria.private.json`. All three arms×two repetitions NOT_RUN; no prior model verdict reused. Live catalog and spend binding deliberately unasserted. `scripts/prepare_r2_benchmark_sources.py` regenerates a fresh registration without inference.

## API 流中断补验（2026-11-04）

`tests/test_official_dsh_local.py::test_official_stream_drop_preserves_completed_tool_and_rejects_partial` 在两种协议实际运行官方 SDK：第1个本机HTTP给出完整 `readonly_probe` 调用并真实执行，回执进入第2个请求；第2个SSE返回未完成的工具JSON参数后直接socket FIN，不给finish/response.completed。`request_retries=0`。

结果 **2 PASS**（12.27秒）：运行抛 `NativeAgentUnavailable`，partial状态为failed；唯一已完成只读工具记录保留且执行总数1，半截工具未执行，HTTP总数2，无重试事件，也没有错误completed。仅使用127.0.0.1合成provider与dummy key，付费调用0，SketchUp操作0。原始trace及streamdrop-receipt.json在E-drive R2 job `pytest-streamdrop`，XML `runtime-streamdrop.xml`。未发现需要变更产品源码的问题，候选源码freeze保持。

## 有限测试执行预算最终补齐（2026-11-04，build04源码候选）

此前状态的纠正：旧 `provider_test_budget` 仅在 LiteLLM 路径，DSH 的 benchmark登记不是预算执行。这次新增 `app/dsh_test_budget.py` + `app/dsh_test_budget.mjs`，在官方 `llm/stream` 入口前预留；不改官方loop，也不改变未启用测试配置的生产BYOK。

独立 `KSTUDIO_TEST_BATCH_CONFIG`（桌面bootstrap保留）选择固定batchID/hash/有效配置绑定、总dispatch次数、每run次数、预登记项目ID与保守token额度；SQLite原子事务+OS owner lease持久跨进程/会话/重启。崩溃、取消、断流、未知usage保留unknown并阻止同batch后续。无有效授权记录不启用；仅字面loopback允许local_fixture零付费授权。没有Key写入配置/账本/日志。

最终回归：**47 Python PASS** (`runtime-budget-release.xml`，含七个真实进程争抢三额度、崩溃不重置、未知锁定、配置hash/项目/每run上限、bootstrap保留配置路径、默认BYOK无账本)；**8实际SDK本机HTTP PASS** (`runtime-budget-sdk-freeze.xml`，两协议主请求/工具/跨session恢复上限/断流，以及官方子agent共享额度、真实BasicCompactionEngine摘要入口、503retry再次dispatch被拒、流中取消unknown)；**5 Node hook PASS**。全部0付费/0SU几何，测试集计数存在交集不能当新增独立用例总数。

请求上限精确限制dispatch，固定token是保守预留，不声称上游真实账单硬保证。`R2_FINITE_TEST_BATCH.md` 与 `R2_FINITE_TEST_BATCH_PROPOSAL.json`给出待授权首批：同一复杂楼梯样本、3arms×2独立项目、各30/总180请求，131072输入+32768输出保守预留；按官方峰值价格参考$14.155776，不等于人民币账单或充值授权。六实际项目ID/catalog与授权尚未绑定，proposal不可执行；不自动扩大三类全矩阵。
