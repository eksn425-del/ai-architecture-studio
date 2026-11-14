# K Studio R3 运维手册

当前部署包为候选。先用隔离 staging 验证实际服务。[环境变量说明](../../deploy/ENVIRONMENT.md)和[部署契约](../../deploy/README.md)列出配置字段与实现边界。

## 部署与验证

1. 核对独立 staging 主机、域名、私网 Docker 及数据库卷。运营凭据写入受限 runtime.env/秘密挂载，不提交源码。禁用 shell 中其他 Docker 上下文。保护当前卷与备份，首次部署保留注册、平台模型、下载和新充值开关为 0。
2. 从干净 checkout 使用验收记录的完整源码 SHA。以 `kstudio-cloud:<完整源码SHA>` 本机创建镜像，或取得同一源码的已核验镜像 digest。使用 `python3 deploy/ops.py check --env-file PRIVATE` 检查，再依次执行 `deploy`、`health`、`audit`。老 `kstudio-cloud` 项目保留原卷，迁入前独立核对备份和映射。
3. 从获准的外部网络核对 HTTPS、证书、运行版本、静态页、设备登录、长耗时请求、支付回调和身份隔离。先跑关闭开关的真实检查；对外服务逐项独立验收。记录失败现场、来源网络、进程和响应，仅保留脱敏结果。
4. 设置独立告警接收人与值班人，定期收集 HTTPS 成功率和延迟、证书剩余天数、分路由错误率、模型请求耗时、未知用量/账本异常、支付回调以及 PostgreSQL 与备份磁盘空间。用故障工件触发实际通知，记录接收时间。当前没有确认任何已送达的生产告警。

## 数据保护与故障处理

- 在独立存储写入唯一备份文件。用 `python3 deploy/ops.py backup --env-file PRIVATE --output NEW_ARCHIVE.age`，保留 SHA 和独立的 vault 密钥与 age 解密私钥。备份周期、异地保留和恢复目标由运营方配置。
- 用 `python3 deploy/ops.py restore-drill --env-file PRIVATE --archive SNAPSHOT.age --target-db kstudio_restore_NEW` 创建新库，核对全部表、钱包和凭据。回溯实际订单前核对归档时间与增量。应用回滚不写入、清理或替换业务数据库。
- 启用生产开关前核对 G00–G10 完整独立关卡记录、经签名安装摘要、定价/规模、风险、回退和负责人记录。首次开关关闭的生产后台也需要有确认授权，再用 `--permit-closed-production`。开启生产开关另需 `--commercial --gate-state RELEASE_STATE --launch-approval PRIVATE_APPROVAL`。
- 负责人批准应从经验证的内部渠道取证、单独写入私有文件。审批记录包含 `approved`、`owner_reference`、`release_sha`、`signed_installer_sha256`、`gate_sha256`、`origin` 和实际批准的 `switches`；记录通过受控身份验证。门槛 SHA 为键排序、紧凑、UTF-8 JSON 的 SHA256。
- 发生误计费、权限泄露或软件损坏，先收紧关联开关和主机入口，保留已验真回执、已有退款和对账路径。受影响功能恢复前核对封存证据和重复请求。`rollback --previous-image VERIFIED_DIGEST --previous-release-sha VERIFIED_SHA` 先用旧镜像只读验证当前数据，再切换应用和维护镜像。核对旧版 HTTPS、实际运行 SHA 和账本后才能恢复流量。

在真实公网灰度前按 `deploy/ENVIRONMENT.md` 执行 `commercial-policy`，把摘要写入私有门槛和授权回执。G00–G10 各项验收文件以相对路径和原字节 SHA256 入单，运营授权绑定开关、源代码、下载 URL、安装签名与这一政策。灰度的名单和人数上限在 Authing 或获准边缘入口实际验证。生产回滚默认暂停新注册、下载、模型派发和所有新收费；既有回调、查询、退款和对账保持配置信息。重新开放须经实际复验和负责人批准。
