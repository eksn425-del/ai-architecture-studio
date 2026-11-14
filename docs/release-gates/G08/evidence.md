# G08 · 工件与证据

最新部署源工件为 E 盘本次作业 `downloads/cloud-beta09/KStudio-R3-cloud-website-source.zip`，119,566 字节。Windows `Get-FileHash` 与构建回执一致，SHA256 为 `3257c79a2556c4604c43b6f6da0f9a3f36a70b982028d705fc8d16e67c1745d5`。含 40 个通过成员哈希验证的业务文件与 2 个清单，匹配冻结源码 `9e295cf1895a4ae62d6bee81ef089d7d5b3fc0aa`。上一版 `downloads/cloud-beta08` 的 SHA 为 `d1beaae95e1e0b5f36245217d6d6ea7c252ba4984f76be7b4d951c721d7058fa`，快照与证据继续保留。

Windows 本机 Uvicorn 真实 HTTP 有 10 个路由及 SQLite 持久化反馈。空库审计通过，账户、会话、订单、钱包、任务和账本均为 0，外部登录、模型、支付和下载均关闭。原始记录 `audit/g08-real-loopback-smoke.log`。商业模板预检在 `audit/g08-commercial-preflight.json` 返回 20 项配置缺失。

审计基线的真实 PostgreSQL17.11/age1.3.2 演练用专用 55461 端口的两个新库。备份耗时 0.547 秒，完整恢复及核对 0.781 秒。17 表摘要相同，独立 Vault 主密钥解密 1 行，已验真收件箱夹具两次维护仅入账一次。快照 SHA256 为 `c6def6bf7c321fa4a1957f7af32bdb63219f1981bb9a0732cd986eb0e3f1d0a0`。真实测试集群停止退出 0，端口已关闭。原始数据、快照和密钥全部留在 `postgres-restore-baseline` 私有目录。

beta08 冻结 SHA 的复验另在 55462 端口全新集群执行，再次匹配 17 个表、恢复 1 条加密 API、维护两轮仅入账一次。备份 0.640 秒、恢复 1.219 秒，完整快照 SHA `2e3db1e208864db4feaeb50eee00aabd1efc41d18ce6deac10547847bd183004`。原始记录 `audit/g08-postgres-final.log`。

针对 beta09 最终源码再次在 55463 端口全新集群复验，17 表、Vault 与模拟已验真收件箱结果均通过。备份 0.719 秒，恢复 1.219 秒。完整快照 SHA `ae6a9104bfdf78c7aca4d8b88fdbcad1f7d513e85ec25d372caebc0ab6880e29`。在已解包的 beta09 源工件上另外完成了 10 路由 HTTP 闭环。对应 `audit/g08-postgres-beta09.log`、`audit/g08-unpacked-beta09-http.log`。本次专用测试均已退出，无遗留监听与明文备份。

当前电脑没有可运行的 Docker/WSL 环境。独立公网 HTTPS、镜像回滚、境内网络和告警收件等待外部资源。操作参见 [运行手册](../OPERATIONS_RUNBOOK.md)。

## 最终云端 SHA 复验

现行部署源包在本轮 E 盘作业 `downloads/cloud-commercial-e470797`，源码提交 `e470797bd888c871eaac1ce89276395213f493b8`，外层 ZIP SHA256 `3bf99dc4b3f9ad97715dfddbc69828be4326ddc7962b07d0ec3091631d34759f`，123,922 字节。独立复核包内 40 项文件哈希与清单，解包后实际本机 HTTP 10 路由通过。此前 beta08/beta09 云包保留。

最终云端 SHA 的 PostgreSQL 17.11／age 独立复验通过，17 表指纹一致，Vault 凭据解密 1 条，已验真通知夹具只入账一次。空库恢复媒体 SHA256 `85198dd3029e93dd45ca873d021d99da4f0d33a9d1385547a58832b4b9293311`。直接使用含中文的现有 PostgreSQL 工具目录时，initdb 以 0xb2 编码错误退出。切换到已存在、指向同一可执行文件的 E 盘兼容路径后复验通过，失败日志保留。云端全量 275 项通过，其中 PostgreSQL 双跑用例 37 项，独立测试服务已退出。实际公网、镜像构建与回滚、试用和告警收件仍需独立环境。


## 统一到 beta10 源码身份

最终交付 ZIP 转到 `downloads/cloud-commercial-d097b1a`，123,921 字节，SHA256 `7af5139cb36d2d24131e12dba93f7c0b1c516723a6d5346e7c27e72c43a54124`。在 `d097b1a5a1e1a45dfc0b5fe5a9301490f164b536` 的干净 checkout 打包，40 个内容成员逐一校验并实际解包 HTTP 通过。与经过本机 PostgreSQL 恢复的 `e470797` 的 cloud、deploy、website 和依赖文件逐字节相同。本机无可运行 Docker，GitHub Actions 执行了现代码 Dockerfile 构建、无外网受限容器运行以及 PostgreSQL 合同，均通过。实际公网 staging、镜像回滚与告警仍未执行。[CI 临时容器和 PostgreSQL 回执](https://github.com/eksn425-del/ai-architecture-studio/actions/runs/43610610668)。
