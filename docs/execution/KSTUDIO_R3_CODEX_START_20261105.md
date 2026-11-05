# K Studio R3：给 Codex 的启动口令

将以下内容完整发给拥有仓库和本地 Windows 环境的 Codex。本轮是实施与部署任务，不是让它再生成一套规划。

---

请执行 K Studio R3 网站＋桌面商业 Beta 上线任务，目标是普通用户能打开公网官网、手机号验证码或微信扫码登录、充值、下载客户端、保存自己的 API 配置，并在 SketchUp 完成真实建模、局部修改、原生保存重开和费用查询。

仓库：https://github.com/eksn425-del/ai-architecture-studio

先同步 `codex/kstudio-r3-launch-handoff-20261105` 分支，读取：

1. `docs/CURRENT_TASK.md` 和 `docs/CURRENT.md`。
2. `docs/execution/KSTUDIO_R3_LAUNCH_EXECUTION_20261105.md` —— 本轮完整执行书。
3. `docs/execution/KSTUDIO_R3_OPERATOR_INPUTS_20261105.md` —— 一次性外部资源与配置表。
4. `docs/releases/KSTUDIO_R2_INSTALLED_20261105.md` 及其真实证据；按需读取已有部署、认证、支付和打包代码。

正确基线是 PR25 的 R2 分支 `codex/kstudio-r2-public-beta-20261104`，核对 SHA `7376f40f678e81618cbd9b470e2f5ba39debeaac`，不是 main。从交接分支创建／复用 `codex/kstudio-r3-launch-20261105` 实施分支，保留用户改动、旧安装、模型、配置和历史失败。不要因旧文档要求而直接推 main 或重启历史建筑研究。

请由主代理扮演产品负责人并统筹，分派 Agent／全栈工程、测试工程和独立首次使用模拟者协作。没有子代理能力时按相同职责执行并如实记录。只有一个执行者写 SketchUp；新手模拟只给官网和任务，不读源码或走内部 API 捷径。

已选路线：腾讯云大陆 CVM＋现有 Docker Compose / FastAPI / PostgreSQL / Caddy，COS 下载；Authing 托管短信＋PC 微信，复用 OIDC 和桌面设备授权；微信支付 Native；平台 BAI 与 BYOK；保留原深绿／暖白／金色及现有 Harness、SketchUp 2024 路线。

请持续完成实际工程、安装程序、账户加密 API 保存、支付和计量、部署、真实验收与交付，不停在计划或 mock PASS。能复用的优先复用；没有新 bug 不重复已经通过的检查，不增加其他软件、模型研究或 UI 大改。参考图保真 PARTIAL 如实披露，不再要求所有研究性基准通过才发布概念建模 Beta。

先读取现有授权与私有配置，能使用就直接继续，不重复索取已给的权限。缺域名、云身份、Authing、微信或商户材料时，完成全部不依赖缺项的工作，然后用配置表一次列清所缺、负责人动作、注入位置和续跑命令。不得要求把真实 Key 放 GitHub／聊天，不伪造备案、身份审核、充值或生产部署。既有 BAI 测试授权按适用范围继续，测试有目的且有界，不自动充值或将其扩写为采购授权。

验收要真实证明：公网官网下载的安装程序在干净 Windows／第二台电脑运行；真实短信和微信登录／绑定；平台 BAI 建模一次并安全修改一次；BYOK 小任务和账户配置恢复；两个账户隔离；原生 SKP 保存重开；一笔授权小额支付、查单和退款；数据库持久化与恢复。自动化模拟、真人、仅新 profile、真实干净系统分别标注；未执行不写 PASS。

条件齐备并通过核心验收后，完成获授权的实际部署和 Beta 开放，不另行用泛泛“是否继续”中断。仅缺负责人才能提供的外部材料时，完成其他全部工件后交接。最终给出真实网站／下载地址、版本与哈希、逐项验收、真实或未知费用、恢复操作和剩余限制，更新 CURRENT／CURRENT_TASK／HANDOFF，提交并推送实施分支、开 PR。不要把本轮文档交接或静态网页预览称为商业产品已上线。

---

这份口令不包含任何生产秘密，也不代表 R2 内部候选已经获得公开发行结论。
