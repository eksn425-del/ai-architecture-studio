# R2 本机执行边界与基准素材登记

2026-11-04，本轮零付费推理、零 SketchUp GUI/几何调用。以下是工具层工程验收，不是原生建模或操作系统隔离验收。

## 发现与修改

原 full 配置以当前 Windows 用户执行官方 PowerShell 和文件工具，子进程能够读取继承环境、同用户文件并修改仓库；只限制某些工具名不能保护这些入口。测试仅使用临时凭据/仓库 canary，不读取真实凭据。原 hook 只限制部分子代理写工具和 ADAI 命名空间，也没有覆盖第二 MCP。

默认 `production-file-proxy` 现在：

- 保留官方 SDK 的 agent loop、模型协议、会话恢复、压缩、规划、Web、curated skills、子代理及 hook；不修改上游包。
- 取消未隔离的 shell、任意原生文件读写/搜索、插件配置、工作目录切换、依赖安装、代码 workflow 等工具注册；hook 再对未审核新增原生工具 fail closed。不是通过检查 shell 内容来猜安全。
- `workspace_read/read_many/search/write/update_strategy` 承担项目持久 Markdown/JSON/Ruby 文件操作，仍能写复杂构件脚本。路径格式、真实路径、符号链接及 Windows reparse/junction 都受检查；host-owned QA JSON 不可覆盖。
- 生产配置拒绝外部 MCP 配置，阻止其进程启动；所有 `mcp__*` 直接调用也被 hook 阻止。当前原生写入通过产品已有 ProjectRuby/绑定文档检查/事务/KEEP/未知结果恢复入口。已审核辅助库仍由该入口加载。
- 子代理默认只读 allowlist，不可写项目文件、改图、保存计划、再次派生或发送变更指令；它可以读取证据并返回建议。没有 root agent identity 的调用也按只读处理。
- 官方 skill filesystem 禁用默认用户目录/祖先项目扫描，仅加载显式运营配置的目录。产品建筑 skill 仍通过 `kstudio_read_skill`；产品指令由 host 注入。模型不能改插件配置来打开权限。
- `trusted-development` 是单独显式环境配置，可恢复未隔离原生编码工具。不能将该模式当生产安全证据。`native`/`architecture` 指导开关不改变安全策略、文件代理或工具目录；比较三组也必须用相同策略。

## 剩余边界

**没有 Windows OS sandbox。** SDK/宿主进程仍以当前用户运行，SDK 内含本轮模型 credential；恶意同用户本地进程能够访问同用户资源。这次代理限制的是模型公开工具面，不能防御本机管理员、进程注入或竞争修改链接。

**SketchUp 进程内任意 Ruby 仍具有宿主用户能力。** 原生事务和文档归属保护约束正常产品写入，不是恶意 Ruby 的文件、网络或进程隔离；不能证明任意恶意 Ruby 无法另起连接或访问外部文件。生产候选必须明确披露这点，不能把字符串扫描称为沙箱。要消除这个剩余风险，需要独立的受限进程/用户架构或将任意 Ruby 限制为审核过的原生操作，两者都不能在保留同进程任意 Ruby 的同时凭提示词实现。

## 实测证据

`tests/test_r2_execution_boundary.py`：真实同用户子进程 canary 读取/写入；生成 Ruby 写读；路径穿越/Windows ADS 拒绝；真实 Windows junction 的读、写、根目录替换拒绝；生产第二 MCP 配置在启动前拒绝；官方 SDK full 的实际工具 inventory；两协议 `request_retries=0` 对本机503都只发一个真实 HTTP 请求。

`tests/test_r2_tool_boundary.mjs`：通过真实产品 hook 检查子进程 continuation 是否执行；未隔离 shell、第二 MCP、未知工具、子代理写全部拒绝，root 文件代理及子代理读允许。此测试运行真实子进程 continuation，但不是付费模型驱动攻击测试。

首批 28 Python + 5 Node PASS；扩展相关回归 58 Python PASS，另18项产品/连接器/搜索回归 PASS。完整 XML 与 SDK 原始 trace 保存在本机 R2 job，历史失败不删除。最终复核结果见 `R2_RUNTIME.md` 追加记录。

## 三类来源与公平比较

`R2_BENCHMARK_SOURCES.json` 冻结三类来源：1张阳台/斜撑立面、1张错落悬挑楼梯、8张历史同一建筑整图。逐张检查原图，记录 SHA256、顺序、target 角色、自然语言任务、关键空间事实、估计边界与测评容差。私有绝对路径只在本机登记中，原图和旧项目不修改，历史模型与 PASS 不复用。

三组×两次均为 **NOT_RUN**。这是素材/验收规则冻结，不是假装完整实验已经注册或执行：实际 live catalog SHA、实际 provider 身份与明确本次计费绑定仍需冻结。拟用 BAI 配置只标 proposed。原生基线也必须共享项目归属与生产权限，因此它是受相同安全约束的官方 SDK 基线，不是无约束原版 CLI。运行后才能给出建模质量、成功率、token/费用和稳定性结论。
