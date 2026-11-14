# R3 外部配置核对与续跑入口（2026-11-07）

实施分支 `codex/kstudio-r3-launch-20261105`，审查 [PR27](https://github.com/eksn425-del/ai-architecture-studio/pull/27)。本表是实际资源核对后的交接，不是要求负责人承担代码排错。工程、数据库恢复、网站、安装候选及自动化测试继续独立推进。公众商业 Beta 尚未开放。

在获授权检查的项目私有环境文件、当前环境变量名称、SSH/tccli 常用配置位置中，没有发现可复用的腾讯云运维、正式域名、Authing 或微信商户配置。该结论不表示用户没有这些账户，也没有搜索无关私人文件。现有本机加密 BAI 测试配置可保留使用；没有把它放进分发包或公开仓库。

| 缺项 | 负责人最少动作 | 配置位置与后续由工程完成的工作 |
| --- | --- | --- |
| 腾讯云上海主机、域名/DNS/备案、COS | 提供已有资源的受控运维授权及非秘密资源标识；没有资源时确认采购预算后本人完成账户/实名手续 | 私有 `deploy/.env`，从 `deploy/environment.template` 复制；配置 domain/public URL/image/source SHA/database/session/secret directory。随后工程部署、HTTPS/Caddy 流式验证、COS 上传及健康/恢复验收 |
| Authing 手机与 PC 微信登录 | 提供已开通的 OIDC 应用、短信通道及微信网站登录权限，完成平台要求的主体/扫码步骤 | `KSTUDIO_OIDC_*` 私有变量；回调 `/auth/callback`。工程完成两种登录、身份关联、设备授权、撤销及重登验收 |
| 微信 Native 充值/退款 | 开通商户和正确支付 AppID，给出安全密钥文件引用、套餐与一次真实付款/退款授权 | `KSTUDIO_WECHATPAY_*`、`KSTUDIO_PAYMENT_PROVIDER`；真实回调验签/入账/退款后才打开支付开关。登录 AppID 与支付 AppID 不能混用 |
| 正式价格与平台服务 | 确认对客套餐、模型/软件费、退款条款和可对外提供的 BAI 账号权限 | `KSTUDIO_CLOUD_PRICES/MODELS`、`KSTUDIO_BAI_PLATFORM_KEY`、`KSTUDIO_PRICES_CONFIRMED`。现有余额测试授权不代表已经确认正式收费规则 |
| 经营与发行信任 | 确认真实经营主体、支持联系、隐私/退款条款、第一方再分发许可；准备生产代码签名和更新信任 | `KSTUDIO_OPERATOR` 与发布元数据；当前第三方许可清单仍 REVIEW_REQUIRED，不虚构第一方 LICENSE 或签名。普通干净 Windows/SU2024 安装仍需对应环境验收 |

不需要把账号密码或 Key 发到聊天。使用受控 SSH、秘密文件或最小权限运维身份即可。注册登录、平台模型、充值和公开下载开关默认关闭；已存在订单的查询和可信回调恢复不依赖新充值开关。

资源齐备后的实际命令入口（在配置完成的部署主机执行）：

```bash
python deploy/ops.py check --env-file deploy/.env --commercial
python deploy/ops.py deploy --env-file deploy/.env
python deploy/ops.py health --env-file deploy/.env
python deploy/ops.py audit --env-file deploy/.env
```

`check` 只输出缺失名称和错误代码，不输出秘密。`deploy` 要求固定源码 SHA 与干净工作树；不会购买主机或重建数据卷。备份、独立空库恢复、应用镜像回退的实际参数见 [恢复操作](KSTUDIO_R3_BACKUP_RESTORE_20261107.md) 与 `deploy/ops.py --help`。恢复应用镜像不等于回退数据库。

真实官网和公众下载地址目前 **未分配、未部署**；本机预览及本地安装工件不能替代它们。外部资料补齐后，从 PR27 的最新已核对提交继续同一实施任务，不需要重做已通过的确定性测试。
