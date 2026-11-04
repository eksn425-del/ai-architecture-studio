# R2 部署参数清单（此文件无凭据）

云服务/官网与本机 SU 工作台分离。仅部署 `cloud.main:create_app`；不要将 `app.main` 或连接器端口暴露公网。源码工件不包含任何 `.env`，包括示例文件。运营者通过受保护的主机配置或 secret store 提供下列值；Compose 使用本机私有 `deploy/.env`，不得回传聊天或提交 Git。

| 参数 | 必须提供的实际值 / 默认行为 |
| --- | --- |
| `KSTUDIO_DOMAIN` | 实际 DNS 主机名，不含协议；仅代理使用 |
| `KSTUDIO_CLOUD_PUBLIC_URL` | 与域名匹配的 HTTPS origin，无路径；桌面运营配置也使用同一 origin |
| `KSTUDIO_CLOUD_ENV` | 先 `staging`，验收及明确批准后才 `production` |
| `KSTUDIO_DATABASE_PASSWORD` | PostgreSQL 唯一随机密码；Compose 创建数据库使用 |
| `KSTUDIO_CLOUD_DATABASE_URL` | `postgresql+psycopg://kstudio:<URL编码密码>@db:5432/kstudio`；原生部署填写实际私网主机 |
| `KSTUDIO_CLOUD_SESSION_SECRET` | 至少32字符随机服务端密钥；备份且受控保存，轮换会影响浏览器会话 |
| `KSTUDIO_OIDC_METADATA_URL` | 成熟身份服务实际 discovery URL，如其 `/.well-known/openid-configuration`，不能用示例域名 |
| `KSTUDIO_OIDC_CLIENT_ID` / `KSTUDIO_OIDC_CLIENT_SECRET` | 正式注册的机密 Web 客户端；精确回调 `https://实际域名/auth/callback`；支持 code + PKCE S256、签名 ID token、nonce/state、`openid profile` |
| `KSTUDIO_ADMIN_SUBJECTS` | JSON 数组；实际身份 `issuer|sub` 格式按数据库 identity 记录核验后配置，不按昵称授权；默认 `[]` 无人工对账管理权限 |
| `KSTUDIO_PRICES_CONFIRMED` | 默认 `0`；正式单位、兑换率、价格版本、服务费方式、取消/失败/退款规则由运营者确认后才为 `1` |
| `KSTUDIO_CLOUD_PRICES` | 默认 `{}`；版本、套餐金额（最小货币单位）、币种、整数 credits、BYOK 服务费开关/金额。结构见 README；示例数值不是售价 |
| `KSTUDIO_STRIPE_KEY` | 有资格的商户测试密钥；非 production 仅允许 `sk_test_…`。缺失则充值关闭 |
| `KSTUDIO_STRIPE_WEBHOOK_SECRET` | 同一商户/模式/端点的签名密钥。端点 `/api/payments/stripe/webhook`；事件 `checkout.session.completed`、`checkout.session.async_payment_succeeded`、`charge.refunded` |
| `KSTUDIO_CLOUD_MODELS` | 默认 `{}`；模型公开 ID → 已确认服务端 endpoint、真实 upstream_model、协议、Key 的环境变量名、能力、输出/预占/日限与价格。模型 Key 只放服务端；不打包入桌面 |
| 每个模型的 `key_env` 所指变量 | 对应运营者自己的供应商密钥及使用条款；缺失不能宣布平台模型可用 |
| `KSTUDIO_CLOUD_RELEASE` | 默认 `{}`；公开下载需 version、url、size_bytes、sha256、verified=true、public_distribution_authorized=true，同时公布兼容/签名/发布者/日期/限制。不得填工程夹具或私人链接 |
| `KSTUDIO_WEBSITE_DIR` | 原生部署时官网绝对目录；容器默认为工作目录下 `website` |

**仍需外部完成：** 实际运营主体/支持邮箱/隐私与保留期/退款条款、域名 DNS、合资格主机地域与相关手续、OIDC 客户端注册及其短信/微信/QQ 等渠道配置、合资格商户沙箱、确认价格与 API 合同、可信桌面签名及获准公开的安装包。当前只有通用 OIDC 和 Stripe 适配；不能宣称手机号、微信、QQ、微信支付或支付宝已直接接入。

## 加密备份参数

生产备份/恢复使用主机 PostgreSQL 客户端和 `age`：`PGHOST`、`PGPORT`、`PGUSER`、`PGDATABASE`、受限 `PGPASSFILE`；备份设置 `KSTUDIO_BACKUP_RECIPIENT` 为 age 公钥，恢复设置 `KSTUDIO_BACKUP_IDENTITY` 为隔离受控私钥文件路径。不要把私钥与加密备份存在同一公开工件。SQLite 只用于显式本机验证，`KSTUDIO_BACKUP_KEY` 为独立 Fernet 密钥；它不替代生产 PostgreSQL 运维。

## 初次启动、迁移和回滚

在部署前确认 TCP 80/443、DNS、证书签发、出站 IdP/供应商/支付网络；数据库端口不得公网开放。先备份，再执行迁移；当前 schema2 对 schema1 会话表增列，不删除旧数据。源码包不包含容器镜像；本轮 Docker 不存在，镜像状态 `NOT_BUILT`。

从解压目录根执行（所有凭据已通过私有配置注入；不要把以下命令理解为生产授权）：

```sh
cd deploy
docker compose config --quiet
docker compose build app migrate
docker compose up -d db
docker compose --profile maintenance run --rm migrate
docker compose up -d app proxy
docker compose --profile maintenance run --rm migrate python -m cloud.cli audit
```

验证实际 `https://域名/health/ready`、`/api/public/config`、官网、OIDC 完整登录/设备授权和未授权拒绝。上述 Docker 命令本轮 `NOT_RUN`。上线前锁定实际 Python/PostgreSQL/Caddy 镜像 digest 并记录镜像 SBOM/漏洞扫描；当前 Dockerfile 的版本标签不是不可变 digest。

已有 Python 3.12 与受控 PostgreSQL 的主机也可按下述方式启动，不要求在用户电脑安装 Docker：

```sh
python3.12 -m venv /srv/kstudio/venv
/srv/kstudio/venv/bin/python -m pip install -r requirements-cloud.txt
/srv/kstudio/venv/bin/python -m cloud.cli migrate
/srv/kstudio/venv/bin/python -m cloud.cli audit
/srv/kstudio/venv/bin/python -m uvicorn cloud.main:create_app --factory --host 127.0.0.1 --port 8920 --workers 1 --no-access-log
```

进程工作目录为解压根，环境由服务管理器私有注入；原生部署需将 Caddy 上游从 Compose 的 `app:8920` 明确改为 `127.0.0.1:8920`。不要将 `deploy/Caddyfile` 原样误用于非 Compose 主机。代理信任仅放行实际代理地址，不使用 `*`。单 worker 是当前进程内限流的部署约束。

每分钟调度 `python -m cloud.cli recover-stale`，每天 `python -m cloud.cli audit`；日志应记录退出码和脱敏摘要。未知已派发状态进入待对账，不重发付费请求。出现 DB 不可达、余额审计不一致、长时间待对账、回调失败、磁盘不足、备份失败时通知运营者；候选不附带已开通的告警服务。

```sh
# 所需 PG* 与 age 参数已私有注入；目标文件必须不存在
sh deploy/backup.sh /approved-backup/kstudio-YYYYMMDD.age
# 先创建隔离、空的 kstudio_restore_YYYYMMDD 数据库，再将 PGDATABASE 指向它
sh deploy/restore.sh /approved-backup/kstudio-YYYYMMDD.age
# KSTUDIO_CLOUD_DATABASE_URL 也指向隔离恢复库
python -m cloud.cli audit
```

比较实际行数、订单/任务/账本样本、登录及设备撤销，并记录恢复耗时与备份时间点。恢复演练不能覆盖生产库。程序回退先恢复上版程序/镜像，保留数据与备份；若 schema 不兼容，停止并使用审核后的迁移/切换方案，不能靠还原旧快照静默丢弃新订单。正式 RPO/RTO、保留期、异地备份及恢复联系人须运营者确定。
