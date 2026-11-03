# K Studio / K Harness — 2026-11-03 本机候选更新

状态：**源码候选版，本机 Windows + SketchUp 2024 流程通过；外观还原 PARTIAL；公开下载产品尚未就绪。**

K Studio 是建筑建模工作台；K Harness 是基于官方 DeepSeek Harness、加入建筑指导和受保护原生工具的运行层。可使用用户自己的 API。本次真实推理使用 BAI 的 `deepseek-v4.1-flash`，没有借用 Codex 订阅作为用户推理服务。

## 本次更新

- 接入官方 DSH SDK、会话/上下文压缩、指令与Skill加载、原生工具调用和交互回传。完整能力配置复用上游实现；受保护模式仍可选。插件注册、可配置能力与逐项原生验收是不同状态，不声称所有上游工具已实测。
- 六组建筑指导：参考图分析、空间/标高、立面、原生构件、局部编辑、交付。入口为 `app/k_architecture.py`、`app/architecture_skills/`、`app/dsh_architecture_surface.py`。保留项目设计记录、审批绑定、版本视图核对与局部修改保护。
- 桌面程序区分程序目录和用户数据；新用户默认无Key，个人连接使用Windows DPAPI。支持连接管理；协议、图片、工具及流式能力仍取决于服务商，未验证“任意API”。
- 桌面单实例唤回；修复任务运行时关闭窗口引起的WinForms死锁。空闲关闭退出自身服务。安装文件校验、候选快捷方式及回退脚本保留旧数据和版本。
- 自动连接SU时保留原文档副本并打开会话自己的独立模型；从下载副本继续修改可恢复绑定并继续原请求。
- 请求层使用官方有限重试：瞬时限流、服务器、超时、传输错误最多2次；永久认证/额度/无效请求不盲重试。不重放已完成的整轮几何操作。失败请求用量单独计入，缺失用量保持未知。
- 调整128k网关上下文压缩预留，保留官方压缩器；本轮未再观察到之前的重复压缩循环，但不代表所有长任务已验证。

## 实测结果

实测对象是用户提供的外部折返楼梯商业楼。使用真实桌面界面、普通中文输入和SketchUp 2024，不用后台脚本伪装用户操作。

| 流程 | 结果 |
|---|---|
| 上传、讨论方案、批准、自动连接SU | 通过 |
| 主建模 | r4出现TRANSPORT连接错误，保存原错误与检查点；用户界面继续后完成r7 |
| 局部编辑 | r7→r8，仅屋顶前沿加深300mm；7次工具、0失败 |
| 其他构件保护 | 12个直属构件组深层几何/材质指纹保持一致 |
| 保存、真实界面下载、SU2024重新打开 | r7和r8均通过；保存后绑定模型与下载重开模型深层指纹一致 |
| 最终桌面程序正常退出、桌面再启动 | 通过；API配置与会话保留 |
| 发布前候选回归 | 42项通过，无付费调用 |

最终模型原生采集访问48021个实体、13个直属构件组。下载SKP文件SHA256：`2c14ac633f4fa6572b50bbf73777e34350297904b5f7b0754bc8b4cac32ad9e2`；保存后/重开几何材质SHA256：`b6bbd86ad42aa10a3e93dc12d1dd7fa4ce3387fdcd9a1542a566aed0623743c0`。这不是历史保存前证明、严格空白重放或外观质量证明。私有参考图、模型和原始运行日志未随源码公开。

完整Python回归另有 **1523通过、50失败、19跳过**，并非全绿；详见[失败清单](KSTUDIO_REGRESSION_20261103.md)。因此本次作为待审阅源码候选公开。

## 失败记录和限制

1. 早期候选任务中关闭触发UI死锁，后台仍完成。改为异步提示后，真实忙时/空闲关闭复测通过。失败没有删去。
2. BAI连接在r4中断；仅凭现有日志无法定位到远端服务器、代理或本机网络。真实“继续”成功。修复后的自动重试通过官方插件离线集成，未做真实付费断网故障注入。
3. 缺工具参数和越出变更范围的调用曾被拒绝，Agent自行纠正，没有放松几何保护。
4. **外观仍PARTIAL**：悬挑玻璃盒子、错层露台和大面积木色底面被过度规则化。方案将统一标高理解为取消半层错落，是偏差来源之一。没有独立外观Critic通过、结构/消防/规范审查或权重训练。
5. 实测原生基线仅这台机器的SU2024。其他电脑、其他SU版本、多家API工具循环、缺失WebView2补装、可分发SU桥接、签名、完整安装向导和许可证发布审核仍待完成。扩展SU版本识别不等于兼容验收。

## 开发者接续

源码在本次候选分支/PR。主入口 `scripts/desktop.py`；SDK与工具桥为 `app/dsh_runtime.py`、`app/dsh_full_profile.py`、`app/dsh_host_tools.mjs`；桌面生命周期在 `app/desktop_instance.py`、`app/desktop_lifecycle.py`；建模工具在 `app/su_harness_tools.py`。

构建参数见 `scripts/build_desktop.ps1`。构建需要调用者提供Python、Node、官方DSH及SDK目录；当前候选固定DSH `0.2.1-rc.5`、Python SDK `0.2.1rc2`、Node `24.22.1`。公开源码不包含这些依赖的大型安装树或私人SU插件。Python SDK复制件仅加Windows隐藏控制台启动补丁，前后SHA由 `scripts/prepare_desktop_sdk.py` 记录；未重写官方Agent循环。其他机器不能只克隆源码就声称已经完成MCP安装。

```powershell
python -m pip install -r requirements.txt -r requirements-model-providers.txt
python -m pytest -q tests/test_desktop_bootstrap.py tests/test_desktop_instance.py tests/test_desktop_lifecycle.py tests/test_desktop_distribution.py tests/test_dsh_full_profile.py tests/test_dsh_architecture_surface.py tests/test_k_architecture.py tests/test_su_harness_tools.py tests/test_deepseek_studio.py
```

SDK/Node和SU仍应按各自官方安装说明配置。个人Key不应写入源码或公共安装包；未来运营者预设Key需要服务端保管。

## 上游与许可证

官方DSH/SDK通过依赖使用，保留其许可证；相关第三方说明见仓库 `THIRD_PARTY_NOTICES.md`。ADAI为可选的公开Skill/方法来源，构建可从另行准备的官方分发物附带Skill及LICENSE/NOTICE；本次源码没有新增ADAI Covered Code。不得把CPAL依赖当作无条件可闭源分发。本轮没有ADAI几何包装调用证据。保持上游版本固定，更新经回归后再采用，不自动替换生产依赖。

后续顺序：补可分发桥接和安装诊断 → 干净Windows/SU版本矩阵 → 多协议API真实循环 → 签名、许可证及更新回滚核验 → 小范围试用。本更新用于公开接续与审阅，不是已完成跨机器验收的安装发行版。
