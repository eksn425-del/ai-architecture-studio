# 文昌灯塔六图测试与 Agent 代码审查交接（2026-11-08）

结论：PARTIAL。真实 K Studio 页面 + BAI deepseek-v4.1-flash / Responses / High，已从骨架 r1 续建至 r11/root19。六张原图按原顺序使用，1017 服务端版本未核实。最新源码 9972d3e；桌面已安装仍为 beta03，不能混为最新源码已发布。

## 实际结果

- r1 骨架；r2 独立窗样板；r3 展开玻璃；随后外罩、楼梯、屋面和场地逐阶段提交至 r11。当前六视图由宿主从同一原生 r11 采集，拍摄前后几何哈希一致。
- 之前两次 r2 写入停在 Face.pushpull，留下 prepared/未知提交，SketchUp 出现 BugSplat。原生底层崩溃原因尚未完全证明；不能说只是 API 或 SketchUp 的错。
- 已实现并实测两次从不可变 r1 检查点恢复到新副本；保留旧未知事务和失败源码。禁止原失败源码原样重放。修复后的独立方杆/薄板路径成功继续，未在这轮再次卡住。
- 自检顺序被误识别为等用户授权，造成多轮只写文字。修正意图提示后，相同中文要求进入执行。中间一次旧进程未退出导致新规则未生效，已如实保留。
- 88 次 settled、2 次 unknown，无 reserved。未知用量不算零，总费用未知。此轮已结束，无无人看管付费循环。

## 尚未通过

建筑质量仍需返工：外罩过于透明且网格感强，原图乳白折面和大开口尚未可靠还原。楼梯平台衔接还需近景与原生测量。周边建筑仅示意。所有尺寸为估计。

本轮 r11 实际下载→原生重开未做；r1 恢复的相等证明不能替代 r11 交付验收。source-perspective.png 是实际斜视图的近似观察方向，未做严格摄影机匹配。六张私人原图及 SKP 不公开，网页版若需逐图审查请由用户另行提供原图。独立模型 Critic 未运行，当前质量观察来自宿主，不能冒充独立 PASS。

## 请网页端重点审代码

1. app/contextual_turn.py：执行意图与 KEEP、样板自检、人类批准之间的边界，避免一再误停或扩大权限。
2. app/native_checkpoint_recovery.py、app/project_ruby.py：未知写入隔离、已退出旧进程、新副本身份与检查点验证；多文件激活的崩溃原子性还需审查。
3. app/dsh_runtime.py、app/dsh_host_tools.mjs、app/dsh_test_budget.py/.mjs：官方 Harness 上下文、子代理调用前的宿主保护、原生不明提交停止后续推理、最多两次网络恢复与未知用量记录。
4. app/k_architecture.py、app/architecture_skills/：六图覆盖、坐标/标高、构件拆分、折面/玻璃/楼梯知识如何转化为原生质量。不能只以读了 Skill、工具成功或测试数作为质量验收。
5. app/connector_deadlines.py、app/public_connector.py、app/sketchup_mcp.py：操作级超时与冻结安装包配置迁移的真实一致性。

## 外部能力吸收

官方 DeepSeek Harness 通过现有 SDK/Node 集成，K Studio 增加建筑 Skills、宿主工具与保护。ADAI 0.5.39 为可选受许可约束的能力，本轮无实际几何调用，见原生 adoption/ledger。不能把研究或安装写成实际使用，也没有进行模型权重微调。

## 版本及下一步

当前分支 codex/kstudio-r3-launch-20261105，PR27。先审本报告及六视图、失败记录，再审以上入口。优先解决源图外罩/开口保真和楼梯局部核验，完成 r11 后续受保护修正、真实下载重开；随后冻结新候选并验安装版。公网商业 Beta 仍受真实身份/支付/域名部署、签名许可、干净第二台 Windows 等条件限制；参考 docs/execution/KSTUDIO_R3_EXTERNAL_INPUTS_STATUS_20261107.md。不要把本次恢复成功改写成已商业上线。
