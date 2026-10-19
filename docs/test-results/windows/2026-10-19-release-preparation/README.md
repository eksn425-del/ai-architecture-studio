# 2026-10-19 K Studio 发售准备与统一候选回归

**结果：本机候选更新已验证；付费公网发布仍为BLOCKED。** 这是代码、合成界面与本机只读HTTP检查，没有生成新建筑、重试已停止副本、调用原生建模/付费供应商或操作现用服务。素材与其他聊天的原生结论不移植成本轮PASS。

基线`89d54d03efec48b6913664a1de01483b58fc16bd`；独立分支`codex/release-prep-20261019`。主目录、现用聊天工作树及宣传片工作树均未修改。

## 改动

- 纳入已存在的显式副本归属迁移与拒绝评审证据诊断；原保护和源/目标SHA、原生指纹不放宽。
- 对话中的公开执行摘要持久保存、按真实消息锚定、按时间排序；刷新可回看；重绘保留阅读位置；含糊图片通过语境询问，保持用途表单移除。
- 回执存储失败也释放应用任务/写锁，原请求仍为待核对，重复请求拒绝。
- 应用lifespan持有本机目录OS锁；另一个采用同一保护的服务不能占用相同runtime；多worker和误设云部署模式会拒绝启动。非分布式锁，旧服务不自动参与。
- 新增只读`/api/release-readiness`和离线检查，明确无云认证、PostgreSQL额度、持久队列、远程设备配对、私有对象存储或支付闭环。
- 排除本机outputs/视频素材扫描；修正测试工具schema和旧UI预期，使预算/取消等测试重新走到目标行为。没有放宽生产协议校验。
- 增加Linux/Windows候选契约CI。公网架构、开源许可证选择及验收顺序见[大陆发售准备](../../../RELEASE_PREPARATION_CN_2026-10-19.md)。

## 实际验证

| 检查 | 结果 | 边界 |
| --- | --- | --- |
| 最终候选重点Python | **155PASS、1SKIP、0FAIL** | 副本保护、回执故障、运行锁（含自建子进程异常退出释放）、预算、取消、参考图/评审与界面契约；不是实际新SU建模 |
| Node界面契约 | **98PASS、0FAIL** | 实际生产JS、受控I/O |
| 最终Windows全量 | **1005PASS、22FAIL、27SKIP** | 14项缺少此测试进程可用的Blender、8项WinError1314符号链接权限；未跳过或放宽这22项 |
| 基线对照 | 单独运行未修改89d54d0代码与同一环境，对照结果另存JSON | 首次基线导出缺两份历史fixture已纠正，不把它们算作本轮修复 |
| Playwright真实浏览器、合成项目 | **PASS** | 1920×1080/390×844；14条执行摘要刷新留存，scrollTop200→200，无横向溢出、无JS异常；供应商执行被禁用，原生适配器禁止访问 |
| 本机只读HTTP | **1000请求、20并发、0错误** | 500合成虚拟客户端，无注册/认证/云数据库/公网/模型负载；p95约211ms，仅为本次机器观察 |
| 发售状态检查 | 正确返回`paid_multi_user_release_ready=false`，CLI退出2 | 不以配置声明或离线测试假冒商用PASS |

早期原始GBK测试运行49FAIL、975PASS、27SKIP，随后使用明确的PYTHONUTF8=1验证；原始日志均保留在本机`runtime/release-audit/`。初次UTF8候选46FAIL、978PASS、27SKIP，随后修复测试fixture与新增功能断言，再取得最终结果。旧schema测试曾在注册阶段失败，未实际覆盖取消/预算，因此本轮修正fixture而不降低真实注册要求。

最后一次全量结果发生在所有功能修复之后。测试、浏览器、HTTP结果均不证明实际商用供应商、所有SU年份、源保真、全部扶手完成或原生交付重开通过。

## 可复核文件

- [summary.json](summary.json)：实际结果与仍失败的测试ID，无用户目录或凭据。
- [browser-and-http-results.json](browser-and-http-results.json)：界面滚动、移动端与HTTP观察。
- [release-readiness.json](release-readiness.json)：本机/云端能力的真实边界。
- [oss-source-pins.json](oss-source-pins.json)：2026-10-19研究时实际读取的上游HEAD。
- [桌面](ui-desktop.png)、[手机](ui-mobile.png)、[运行卡片](ui-live.png)：全部为明确标注的合成回归项目；不是用户原图或模型截图。

复现重点检查：

```text
python -m pytest -q tests/test_copy_ownership.py tests/test_runtime_safety.py tests/test_progress_activity.py tests/test_conversation_receipts.py tests/test_reference_roles.py tests/test_requirement_lifecycle.py tests/test_native_turn_control.py tests/test_native_turn_budget.py tests/test_project_turn_budget.py tests/test_ui_project_recovery.py tests/test_novice_flow.py tests/test_su_relation_audit.py
python -m scripts.release_readiness --json
python -m scripts.verify_release_workspace
```

最后一个脚本需要已安装Playwright及其Chromium；只启动独立loopback合成服务，结束后正常退出，不连接SU。不同机器的HTTP延迟不应当作同一测量结果。
