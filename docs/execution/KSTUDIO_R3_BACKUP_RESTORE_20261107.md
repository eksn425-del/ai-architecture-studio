# R3 加密备份、恢复与维护实测 — 2026-11-07

## 范围和结论

本机独立 PostgreSQL17.11 + 官方 age1.3.2 的真实加密备份/新库恢复 **PASS**。
17张表恢复前后数量与规范化 SHA256 全部一致；恢复后的1条个人API密文用分离主密钥解密成功；账本一致。
恢复库中1条已验真微信事件收件箱夹具，在两次维护循环里只入账1次。它是合成的已验真收件箱输入，**不是真实微信签名/支付验收**。

- 加密备份：0.828秒；恢复及只读验证：1.359秒。这是小型本机夹具，不是生产RTO承诺。
- 加密快照SHA256：`897234b9e9056f42856c2663079a9c1c143083077aab311d0eb910c650cf2f5e`。
- 无真实模型API调用、付款或充值；没有生产资源费用。
- 本机未安装Docker，Compose完整执行为 **NOT_RUN**。CI与生产验收必须单列实际证据。
- parent独立复用首个专用集群，以隔离schema完成全量cloud测试：192 passed /0 skipped；该结果由主代理记录。

本地私有工件保存在项目E盘 `outputs/video-storage/jobs/kstudio-r3-launch-20261107/postgres-restore-r3-verified2/`：
receipt.json、snapshot.age、独立vault主密钥和age恢复私钥、两个独立夹具数据库。密钥、数据库目录和加密归档不提交GitHub。
临时明文dump已删除；模型、旧业务数据库和用户配置均未改动。两个本轮集群55448/55449已正常停止，保留数据目录，不留后台测试服务。

## 真实缺陷与修复

旧运维脚本默认主机127.0.0.1:5432，但Compose数据库并未发布该端口，因此不能按文档备份。现在由 `deploy/ops.py` 在私网db容器内调用pg_dump，将输出流直接交给age；主机不再需要PGHOST/PGPASSFILE或开放端口。

恢复必须显式提供一个不存在的 `kstudio_restore_*` 数据库。先完整认证age归档，再createdb并单事务pg_restore；没有DROP/覆盖生产库操作。成功后应用镜像用原密钥挂载只读核对schema、全表、账本及vault。恢复故障保留独立目标供排错，不自动切换生产数据库。

本机演练最初initdb在中文路径遇到Windows ANSI/UTF8 bootstrap冲突；失败目录保留。使用同一E盘项目的ASCII兼容junction后成功，不搬移用户文件。第二次启动中pg_ctl返回后，Windows子进程继承stdout pipe导致Python等待EOF；修复为启动器私有日志文件，新的独立集群完成演练。原集群只供主代理隔离schema测试，随后一起停止。

## 回归与重跑

`tests/cloud/test_deploy_ops.py` 覆盖错误恢复库名、不可覆盖旧备份、age认证失败时零SQL、已有目标不执行restore、缺少/错误vault主密钥不能通过、schema不符拒绝，以及商业预检公开字段和明确许可状态。实际结果见主报告所附ops-tests.xml。

本机演练命令（全新输出目录和未占用端口；最后不带keep-server会自动停止专用集群）：

```sh
python -m deploy.restore_drill --bin OWNED_POSTGRES_BIN --age-bin OWNED_AGE_BIN --output NEW_PRIVATE_DIRECTORY --port 55449
```

生产命令、密钥恢复要求、关闭开关与回退步骤见 [deploy/ENVIRONMENT.md](../../deploy/ENVIRONMENT.md)。备份不包含vault主密钥/age私钥，必须分离私有保管全部所需版本。逻辑快照不等于WAL/PITR，异地备份计划、告警、保留期和实际恢复切换仍需运营部署验收。

工具来源：[PostgreSQL pg_dump官方文档](https://www.postgresql.org/docs/current/app-pgdump.html)、[age v1.3.2官方发布](https://github.com/FiloSottile/age/releases/tag/v1.3.2)。Windows age ZIP SHA256与发布资产digest一致：`f48d8f8f9ebe903ab5027ed067652f2cc1db94bc206976430133b905dcd8e8c7`。工具下载留在E盘，无生产软件全局安装。
