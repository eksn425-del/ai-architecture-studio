# R2 云服务与官网源码交付

本次提供可检查、可迁移启动的**源码候选工件**，不是预制镜像、公网部署或商用上线证明。

- 工件：`outputs/video-storage/jobs/kstudio-r2-20261104/deployment-artifact/KStudio-R2-cloud-website-source.zip`
- 大小：77552 bytes。
- SHA-256：`ab2ee5f61aecb42efe92f412cbfe0d14aa03f21cdecaabb5e21001f7460d0869`。
- 31 个 payload 文件，另含 `MANIFEST.json`、`SHA256SUMS`，总 33 个归档成员；每项 SHA 解压复核通过。
- 来源：本轮隔离 worktree 的 cloud/website 冻结源码，基线 HEAD 与实际成员 SHA 在 manifest；不假称所有未提交文件已在该 HEAD。

`scripts/build_cloud_source.py` 用明确白名单打包：云端 Python 源码、官网 HTML/CSS/JS/SVG、Compose/Dockerfile/Caddy/备份恢复脚本、运维说明、直接依赖固定表、实际验收 Windows 运行依赖完整版本快照及其平台 marker、用户指南和第三方归属说明。无 `.env`（包括模板）、凭据、runtime、数据库、私有 fixture、Python 缓存、SU 模型或本机写入服务。

从 ZIP 解压至独立目录后，使用已有 Windows 验收 Python 环境实际执行两次 `cloud.cli migrate`（幂等 schema2）、`audit`、`recover-stale`，再由归档内源码运行 API/官网/真实反馈落库：PASS。默认认证/支付/下载保持关闭。检查数据库是独立 SQLite fixture，不代替实际 PostgreSQL/生产基础设施。逐步回执见同目录 `verification.json`，打包回执 `receipt.json`。

当前没有 Docker，镜像 `NOT_BUILT`；生产部署 `NOT_RUN`。直接依赖为精确 `==`，完整已测依赖快照明确标注 Windows，不能称 Linux 可复现锁或镜像验收。部署者需在获准 staging 环境解析/锁定目标 Linux 依赖与 Python/PostgreSQL/Caddy digest，再执行实际镜像构建、SBOM、安全与部署验收。没有为此要求用户电脑额外安装 Docker/数据库。

当前仓库缺少根级 `LICENSE`。工件保留 `THIRD_PARTY_NOTICES` 并明确“私人交付不创造公开再分发许可证”；公开前由拥有权利者确认第一方代码/设计的发布条款。归属说明不替代许可。

操作入口：`deploy/ENVIRONMENT.md`（所有精确外部参数、迁移/启动/备份恢复/回退）、`deploy/README.md`（控制平面和服务边界）、`docs/USER_GUIDE_R2.md`（本机/BYOK/账户/SU/RBZ/停止/导出/恢复/更新/卸载保留数据）。历史 USER_GUIDE 顶部已指向 R2，避免旧单模型/旧插件/无账户说明误导新用户。

## 原 K 图标

新增 `scripts/make_desktop_icon.py`，用已安装 Edge/Playwright 将未改动的 `app/static/k-monogram.svg` 渲染在暖白 `#f5f3e9` 背景，Pillow 生成 16/24/32/48/64/128/256 多尺寸 `app/static/kstudio.ico`。只用于构建，不新增产品运行依赖。原 SVG SHA `db77f269e82e123be854311ef3a0838366e11e5e336c77e5c089cd4856443102`；ICO SHA `30120f570386b263155eb2ca2571528d4152391fe41b291904ece603149edecb`；256px 中间图在 `web-evidence/kstudio-icon-256.png`，已视觉核对保持原 K 设计。EXE/快捷方式/任务栏实际图标安装及最终包 SHA 由负责人验证。

Final build04 source refresh: deployment-artifact-04/KStudio-R2-cloud-website-source.zip, 77545 bytes, SHA256 5079dcd0c1fc29bee6192e01209d38412a8d53866730f09478e792fc465b072a. Based on debe2a8 with exact per-file manifest. Independent extraction/hash/migrate-twice/audit/recover/API/website/feedback checks passed again; IMAGE NOT_BUILT and production NOT_RUN remain. Earlier source artifact is retained as history.
