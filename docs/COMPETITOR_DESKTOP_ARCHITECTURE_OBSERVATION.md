# Building-Xuezhang desktop architecture observation

Date: 2026-09-30. Read-only inspection of a legitimately installed package and the user's own session. No protected binaries were decompiled, no credentials read, and no proprietary implementation copied into this repository. Private histories, scripts, screenshots and model files remain local.

## Observed facts

### Live UI observation — 2026-10-01

Inspected the running desktop's AI task-assistant and SU automatic-modeling pages through ordinary window interaction, including an existing user conversation. No message was submitted, model tool invoked or proprietary source copied.

- Narrow left sidebar groups capabilities and lists conversation history below them. SU modeling is selected under AI modeling.
- Main workspace has a centered page title, spacious conversation area, and an empty-state introduction with small suggestion chips.
- Input composer is fixed near the bottom. Attachment entry, model dropdown, dialogue mode, Skill entry and send arrow share its toolbar.
- Existing conversation places user messages on the right; history selection changes the central conversation rather than opening a separate project form.
- The visible SU page selected GPT-6.1 Sol. This is UI evidence only, not provider-request verification.
- Product implication: our current scope adopts the sidebar/history/chat/composer arrangement, keeps only AI modeling, and reveals parameter approval and outputs contextually. Our visual assets, styling and implementation are original. Unavailable competitor capabilities are not shown as working features.

### Installation and reuse boundaries

- The desktop installation contains .NET runtime/WPF/WebView2 libraries, a WebUI, isolated Python and Node runtimes, Skills, system prompts, settings and local history storage.
- Library filenames include Microsoft.Agents.AI, Microsoft.Extensions.AI, OpenAI and ModelContextProtocol. These establish bundled dependencies, not which execution path actually uses each library.
- SketchUpMCP includes readable Skill/reference Markdown, `stdio_bridge.py`, a protocol probe and validation helpers. No compatible redistribution license for the competitor's own SketchUp Skill/bridge was established.
- Other bundled packages have explicit licenses: FastMCP 3.4.2 has Apache-2.0; a 3ds Max runtime has MIT; a Revit runtime has MIT with upstream attribution; Illustrator MCP package 1.6.2 declares MIT and identifies `ie3jp/illustrator-mcp-server`; an office runtime has Apache-2.0 and notices. These licenses apply to their packages, not to the enclosing desktop product.
- Python/Node runtimes have their own license files. Copying an entire installed environment would also copy caches, configuration and potentially proprietary or user data; acquire reusable packages from their upstream distributions instead.

### Conversation and execution evidence

- One local history JSON contained 82 records at inspection: 14 user, 30 AI, 22 Process and 16 System records.
- Process content is structured JSON with turn IDs and steps. Steps include start/end phases, tool name/title, parameter summary, success flag, result and duration. Some tool results are truncated; this is not a complete network-level trace.
- Visible execution includes Skill lookup, MCP status/connect, todos, file reading/writing, command execution and image viewing.
- The current visible model selector showed `gpt-6.1-sol`. Backend provider requests/model identity were not independently captured.
- The connected SketchUp window was the user's optimization experiment copy. It was not modified or queried through our bridge during this observation.
- The user's plugin-status screenshot reports running server, port 9986, version 0.1.0, 8 registered tools and 0 active connections at that instant. This alone does not prove the desktop was connected at that instant.
- The assistant's displayed connection result reports `sketchup-9986` connected with 8 tools: `get_model_info`, `get_selection`, `create_geometry`, `transform_entities`, `set_material`, `get_entity_info`, `delete_entities`, `execute_ruby`.

### Persistent coding and feedback

- The generated project workspace contains a parameter/optimization plan, trace manifest, persistent `build_model.py`, helper/repair scripts, four batch records, baseline/readback/validation JSON and before/after screenshots.
- The generated script uses a Python RPC client: MCP initialize followed by tools/call of `execute_ruby`. Substantial geometry is composed in Ruby rather than represented as a large set of fixed semantic MCP actions.
- Generated Ruby checks the active model path against the experiment copy; batches use SketchUp start/commit/abort operations and report a persistent owned-root ID.
- Screenshot code creates several cameras, calls viewport image export, and restores the previous camera. Validation reads geometry and saves the designated copy.
- An existing validation artifact records successful save, 42 retained floors, four optimization groups and owned root ID 5226319. These are artifact claims, not independent acceptance of the latest geometry.
- The execution history includes real failures: port mismatch/connection timeout, Python indentation error, Ruby iteration syntax error and validation errors, followed by script edits and retries.
- Image-viewer calls appear after screenshots. The assistant identifies disconnected lift landings and columns intersecting existing curved envelopes; later repair-plan and geometric audit files exist. Final repair execution/quality was not independently verified.
- The readable stdio bridge has a script-presence gate for certain geometry-bearing Ruby calls. The generated project script also directly uses a TCP RPC client; do not assume every execution necessarily passes through the stdio gate.

## Inference

- The observed architecture is consistent with a general coding Agent, lazily loaded Skills, a persistent project workspace and a thin software bridge.
- The package has sufficient components for provider abstraction, but multiple-provider parity and actual model routing remain unverified.
- Conversation instructions appear to govern discussion versus execution. No host-enforced first-build approval state machine was established by this observation.
- Save/undo/image capabilities can be composed through Ruby; the observed eight-tool list does not contain a separate dedicated tool for each lifecycle feature.
- Persistent files and model-root identity explain continuity better than chat text alone. Their existence does not guarantee successful recovery after every interruption.

## Implications for our product

1. Keep the existing Kongxing bridge and verified disposable-model boundary. Do not replace a working connector to imitate branding or packaging.
2. Restore the coding workbench: durable notes/parameters/Ruby, structured tool results, screenshot feedback and same-model revisions.
3. Keep workflow-specific Skill independent of provider. LiteLLM owns provider protocol compatibility; our code owns project state, approval and tool authorization.
4. Preserve an explicit host approval gate. A saved plan is not approval, and an ordinary message modifying parameters must not trigger geometry.
5. Record actual execution failures and recovery evidence. Distinguish scripts authored, scripts executed, model saved, screenshots inspected and quality accepted.
6. Install compatible OSS from upstream with licenses/notices intact. No competitor Skill, bridge source, generated thesis script or private history is a donor for this public repository.
7. Finish image-to-SketchUp quality evidence before adding other modeling applications. The observed Revit/Max/Illustrator packages are later candidates only.

## Unverified items

Full desktop source, protected/compiled internal logic, cloud services, credential handling, provider request routing, token billing, global undo guarantees and final model quality remain unverified. Nothing here claims the entire competitor application has been recovered.


## 2026-10-01 — 再次实际观察新人入口

本轮通过原生鼠标打开用户已安装的建筑学长电脑版，进入 AI 建模 → SU 自动建模。观察到左侧功能/历史、中央聊天、底部输入、附件入口、模型选择、Skills 标识和教程。SU 页的空态直接告诉用户把建模交给助手；输入提示明确先从教程安装 suMCP。教程按钮打开用户可访问的飞书文档。

界面显示 gpt-6.1-sol，但本轮没有向竞品发送请求，也没有测试其模型调用、延迟、收费或最终几何质量；不能从界面推断内部运行模型。既有历史/安装观察见上文，没有新增复制专有 Skill、桥接代码或二进制。

采用的产品行为：聊天优先、统一附件入口、只在建模前教连接、展示明确批准动作、保留历史和继续修改。我们使用自己的布局细节、样式、文案与代码；公开 MIT Markdown parser / BSD pywebview 替代自行造渲染器和桌面壳。

建议先做 Windows 本地工作台：用户建模软件、MCP、项目文件同机，网站界面和替换模型接口继续复用。纯云网页若要控制本机 SU，仍需另一个本地连接组件；桌面形式不能自动提升模型质量。该判断来自本机流程观察和 MCP transport 的 stdio / localhost HTTP 机制，不代表竞品全部架构已经可见。

参考：[MCP stdio transport](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/draft/basic/transports/stdio.mdx)、[MCP Streamable HTTP](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/draft/basic/transports/streamable-http.mdx)、[pywebview](https://pywebview.flowrl.com/)。
