# R3 部署与恢复参数（无凭据，2026-11-07）

当前是工程候选，不代表商业 Beta 已上线。只部署 `cloud.main:create_app` 和官网；本机 `app.main`、SketchUp 写入器及连接器不得暴露公网。模板为 `environment.template`，源码工件排除全部 `.env`。复制模板到运营主机受限私有路径，仅通过 `--env-file` 传入；不要提交或发回密钥。

## 核心配置

| 参数 | 实际值与约束 |
| --- | --- |
| `KSTUDIO_DOMAIN` / `KSTUDIO_CLOUD_PUBLIC_URL` | 实际 DNS 名及匹配 HTTPS origin；不能用占位域名 |
| `KSTUDIO_CLOUD_ENV` | 先 staging；真实验收后才 production |
| `KSTUDIO_IMAGE` / `KSTUDIO_RELEASE_SHA` | 验证的镜像标签或 digest、对应完整40位源码 SHA；ops 拒绝脏工作区或不匹配源码 |
| `KSTUDIO_DATABASE_PASSWORD` | 独立随机数据库密码 |
| `KSTUDIO_CLOUD_DATABASE_URL` | `postgresql+psycopg://kstudio:<URL编码密码>@db:5432/kstudio`；Compose 不发布数据库端口 |
| `KSTUDIO_CLOUD_SESSION_SECRET` | 至少32字符随机服务端密钥，私有备份 |
| `KSTUDIO_SECRET_DIR` | 主机受保护目录，只读挂载到 `/run/secrets/kstudio`；容器 UID10001 需可读指定文件 |
| `KSTUDIO_REGISTRATION_ENABLED` / `KSTUDIO_PLATFORM_ENABLED` / `KSTUDIO_PAYMENT_ENABLED` / `KSTUDIO_DOWNLOAD_ENABLED` | 默认0，各真实验收通过后独立开启 |
| `KSTUDIO_GLOBAL_MAX_CONCURRENCY` | 默认4；单 Uvicorn worker，尚未认证跨进程限流 |

## 登录、个人 API 和平台 API

- `KSTUDIO_OIDC_METADATA_URL`、`KSTUDIO_OIDC_CLIENT_ID`、`KSTUDIO_OIDC_CLIENT_SECRET`：成熟 IdP（执行方案为 Authing）真实机密 Web 客户端，回调精确为 `https://域名/auth/callback`。`KSTUDIO_OIDC_TOKEN_ENDPOINT_AUTH_METHOD=client_secret_post`，scope 默认 `openid profile phone email`。手机短信和微信渠道须在 IdP 完成真实配置与验收，代码适配不等于渠道开通。
- `KSTUDIO_ADMIN_SUBJECTS`：已核对数据库身份的 `issuer|sub` JSON数组，不按昵称授权。
- `KSTUDIO_VAULT_ACTIVE_KEY_VERSION`：例如 `v1`；`KSTUDIO_VAULT_KEYS_FILE=/run/secrets/kstudio/vault-keys.json`。文件结构 `{"v1":"<随机32字节密钥的Base64>"}`；保留每个历史密钥版本直到记录全部轮换。AES-256-GCM AAD绑定用户、记录、版本。数据库只有密文，列表不返回Key。
- 同步个人 Key 必须最近10分钟重新登录，在网页明确选择本人有效设备；120秒一次性凭据绑定用户、设备、连接版本，桌面确认后写入 DPAPI，不自动选择该Key。退出/切换账号隔离工作区与缓存，不删除原模型。
- `KSTUDIO_CLOUD_MODELS`：公开模型ID到已验收上游配置；`enabled` 和 `verified` 都通过才可用。`key_env` 指向私有 `KSTUDIO_BAI_PLATFORM_KEY`。真实地址/model、能力、最大输出、价格版本、预占、日限、`turn_budget_units`、`max_turn_requests` 由服务器配置，客户端不得指定预算或获得平台Key。示例见 README。
- `KSTUDIO_PRICES_CONFIRMED=0`、`KSTUDIO_CLOUD_PRICES={}` 默认关闭。正式整数积分、货币最小单位、服务费、失败/取消/退款规则由运营者确认；未知用量不当0、不自动重复扣费。

## 微信支付与公开信息

R3 已实现微信 Native 支付、签名验真、回调解密、持久已验证事件收件箱、事件幂等、退款核对和维护恢复；真实商户未验收不能宣布收款可用。

| 参数 | 配置 |
| --- | --- |
| `KSTUDIO_PAYMENT_PROVIDER` | 默认 disabled；真实验收后 `wechat_native` |
| `KSTUDIO_WECHATPAY_MCHID` / `KSTUDIO_WECHATPAY_APPID` | 合资格真实商户和关联应用 |
| `KSTUDIO_WECHATPAY_API_V3_KEY_FILE` | 容器内 APIv3 密钥文件路径 |
| `KSTUDIO_WECHATPAY_MERCHANT_PRIVATE_KEY_FILE` / `KSTUDIO_WECHATPAY_MERCHANT_SERIAL` | 商户私钥文件及序列号 |
| `KSTUDIO_WECHATPAY_VERIFY_MATERIAL_FILE` | 容器内可信微信验签材料，按适配器结构配置和轮换 |
| `KSTUDIO_OPERATOR` | JSON字段 `name`、`support_email` 或 `support_url`、`icp`、`privacy_contact`、`data_retention`、`refund_policy`；真实主体及适用备案，不得编造 |
| `KSTUDIO_CLOUD_RELEASE` | version、url、size_bytes、sha256、兼容信息；放开需 verified、public_distribution_authorized、signing_verified、clean_windows_verified 均为 true，license_clearance 必须是字符串 `CLEARED`，`REVIEW_REQUIRED` 不通过 |

原 Stripe 适配仍在，其 Key/签名参数只对另行验收的 Stripe 路线有效。

## 部署、维护与回退

当前 schema **3**：保留 schema1/2 数据，新增认证时间、个人凭据/审计/同步、微信事件与退款、任务预算等能力。先备份再迁移。固定镜像和源码，设置 DNS/TLS/出站限制。命令从仓库根执行：

```sh
python3 deploy/ops.py check --env-file /srv/kstudio-private/runtime.env --commercial
python3 deploy/ops.py deploy --env-file /srv/kstudio-private/runtime.env --commercial
python3 deploy/ops.py health --env-file /srv/kstudio-private/runtime.env
python3 deploy/ops.py audit --env-file /srv/kstudio-private/runtime.env
```

`deploy` 启动私网数据库、迁移，再启动 app/proxy/maintenance。维护进程每60秒执行过期任务恢复、已验真微信收件箱重放及账本审计；PostgreSQL advisory lock 防维护者重叠。未知已派发付费任务进入对账，不自动重发。运营者还需对接告警：审计不一致、长时间待对账、回调失败、磁盘不足、备份失败。

回退：`python3 deploy/ops.py rollback --env-file ... --previous-image 已验证旧镜像`。只切 app/maintenance 镜像，不删卷或订单；先确认旧程序与 schema3 兼容，再验健康与账本。数据库切换另行安排，restore-drill 不自动切生产。

## 加密备份与隔离恢复

主机需要 Python3 与官方 age CLI；pg_dump/pg_restore **在 Compose 的 db 容器内部运行**，不依赖主机 PGHOST、PGPASSFILE 或开放5432。

| 参数 | 配置 |
| --- | --- |
| `KSTUDIO_BACKUP_RECIPIENT` | age 公钥收件人；备份只需公钥 |
| `KSTUDIO_BACKUP_IDENTITY` | 恢复时主机独立受保护的 age 私钥文件绝对路径，不是容器内路径 |
| `KSTUDIO_AGE_EXECUTABLE` | 可选主机 age 路径；默认 age |

```sh
python3 deploy/ops.py backup --env-file /srv/kstudio-private/runtime.env --output /private-backups/new-snapshot.age
python3 deploy/ops.py restore-drill --env-file /srv/kstudio-private/runtime.env --archive /private-backups/new-snapshot.age --target-db kstudio_restore_20261107
```

目标文件与恢复数据库必须不存在。恢复先完整验证 age 密文认证，再创建 `kstudio_restore_*` 新数据库，单事务恢复；不会 DROP、清空或接管原库。随后在应用镜像中只读校验 schema、全部表数量/指纹、每个账本及每条 vault 解密，包括已验真支付收件箱。失败的独立数据库保留供核查，不自动删除。临时明文位于0700私有目录，结束后删除；主机需可信磁盘和访问控制。

**完整恢复还依赖独立密钥保存：** age私钥、vault全部历史主密钥、session及商户/IdP等运营配置须分离受控备份。它们不在数据库快照内；丢失vault主密钥就无法恢复个人API。逻辑数据库快照不包含SKP、录像或WAL/PITR。异地备份、周期、RPO/RTO、保留与恢复联系人须另行配置，目前不自动清理旧备份。

本轮本机 Postgres/age 演练和 Docker/生产分开记录，见 [R3运维证据](../docs/execution/KSTUDIO_R3_BACKUP_RESTORE_20261107.md)。当前本机 Docker 不存在，不能把本机 Postgres PASS 写成 Compose 或生产上线 PASS。CI 的实际结果应以对应提交的工件为准。
