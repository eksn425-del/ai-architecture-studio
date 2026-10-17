# 2026-10-17 本机 SU 试用候选版：真实主流程完成，保留质量限制

本次是新授权的独立本机产品验收，不继续旧八图r20。隔离分支 `codex/su-trial-candidate-20261017`，以r20/main `564d75c` 为基线，审查并包含 `55b492d`、`a6347ca`。[完整工程结论及启动方式](../../../SU_TRIAL_CANDIDATE_2026-10-17.md)。

**可开始所有者本机个人试用。** 网站/模型入口/SU24真实连接、普通中文建模和一次局部修改、保护、保存、真实网页下载、原生打开和恢复均已执行。源图外观仍 `NEEDS_FIX`；原始双精度比较FAIL，既有声明精度三阶段PASS。没有把离线545测试通过冒充图像建模成功，没有独立商业API或客户交付认证。

本目录仅提交脱敏工程索引及实测汇总。**根据本次新授权，完整原图、日志、截图和SKP保留在本机 `runtime/su-trial-20261017/`，不提交或自动公开。** 这不是可在GitHub独立复核的完整公开原生证据包；没有宣称公开证据协议校验通过。新用户要求覆盖历史自动上传/推main规则。当前分支只做本机提交，不推送、部署或合并main。

本机证据路径均相对仓库根：

| 实测内容 | 原始本地记录 |
| --- | --- |
| 项目/SU/模型身份及原生数据 | `runtime/su-trial-20261017/initial-r3-deep.json`、`actual-r4-writer.json`、`actual-r4-rail-height.json` |
| 16组KEEP和松散几何保护 | `scope-before-edit.json`、`scope-after-edit.json`、`local-edit-protection.json`；保护SHA `cfaaa92e7216ef372d1c39875f8350e288efefa511c6ab5d8805c06331c0af08` |
| 六组真实3/4同机位截图 | `paired-camera-check.json`；原始PNG/侧证在 `r3-record/outputs/renders/` 与 `final-project-record/outputs/renders/` |
| 保存顺序/下载SHA | `edited-r4-before-final-save.json`、`save-ordering-proof.json`、`final-save-receipt.json`、`browser-download-proof.json` |
| 原生两份重开/三阶段比较 | `bound-r4-reopened.json`、`browser-download-r4-reopened.json`、`native-delivery-strict.json`、`native-delivery-declared-precision.json`、`working-r4-restored.json` |
| 网站/刷新/断网/草稿/下载/最终页面 | 本轮 `01`至`08` 截图；最终`08-candidate-ready.png` |
| 真实模型及全部规划/写入/工具/审查 | `r3-record/`、`final-project-record/`，包括原生AppServer事件、四次独立只读Critic和历史失败 |
| 未提交原始模型保护 | `preserved/` 中旧r20/原r4和四份旧状态，末次字节一致核对通过 |
| 全部文件SHA清单 | 本轮本地 `artifacts.json`；没有密钥/账号密码/认证容器副本 |

外部方法：以原生SketchUp面/挤出和组件实例完成，有具体兼容性回退理由；真实OSS ledger为0包装调用，不伪称SAIE/ADAI执行。两项试用分支修复则已进入真实当前网站流程。独立Critic只收原图及当时当前模型截图；前后六配对由宿主另行核对，不冒称Critic收到两版对照。

初建60工具/5失败/424.125s，局部修改28工具/2失败/165.516s，最终只读保存确认4工具/0失败/269.907s。网站五回合合计6,250,695输入/25,390输出，独立Critic四次另计119,942输入/4,271输出；费用未知null、付费供应商调用0，外层控制器Token未知null。延迟与重复读取较重是已知限制，按任务不开展新优化功能。

未验证项目如实保留：硬杀服务时的事务恢复、跨客户端幂等、其他SU版本、独立商业API、严格两次空白程序重放、完整源图保真。普通双击/刷新/网络中断恢复已经真实执行。最后停止推理和几何写入，保留可用页面及工作副本供所有者操作。
