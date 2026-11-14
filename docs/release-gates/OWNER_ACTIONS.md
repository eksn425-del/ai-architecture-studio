# 商业发布所需的外部输入

本机候选、工件与隔离回归由工程侧处理。按下表集中提供可复用的授权，密钥应通过受控的云秘密管理或私有文件授权，聊天和仓库只记录变量名或引用。

| 你需要提供或确认 | 安全配置位置 | 续跑和产出 |
| --- | --- | --- |
| 经营主体、经营和备案的实际情况、客服与隐私联系方式、正式条款、开票与退款政策，及第一方 K Studio 和第三方分发权确认。 | `KSTUDIO_OPERATOR` 和经营主体私有合规材料，涉及 ICP 和 AI 服务适用性由责任人核对。 | 工程核对软件包许可证和对应源码，QA 检查正式网页、AI 标识与退款入口。 |
| 一个获批独立 staging、域名、DNS/TLS、私有 PostgreSQL、下载存储与告警收件人。录像、主库和发布资源按实际授权隔离。 | `deploy/environment.template` 的私有实例，例如 `/srv/kstudio-private/runtime.env`。域名、数据库与备份配置使用 `KSTUDIO_DOMAIN`、`KSTUDIO_CLOUD_PUBLIC_URL`、`KSTUDIO_CLOUD_DATABASE_URL`、`KSTUDIO_BACKUP_RECIPIENT`、`KSTUDIO_BACKUP_IDENTITY`。 | 工程完成 SHA 固定的 Docker 构建、HTTPS、签名下载、独立备份恢复、镜像回滚、境内网络和实际告警回执。 |
| 有手机号与 PC 微信渠道的 Authing 应用，完成实名、短信资料和微信登录主体配置，提供两个获准测试身份。 | `KSTUDIO_OIDC_METADATA_URL`、`KSTUDIO_OIDC_CLIENT_ID`、`KSTUDIO_OIDC_CLIENT_SECRET` 与私有 Vault key files。 | 工程用测试设备检查注册、登录、同步同意、撤销、跨账户隔离及已有账号复登。 |
| B.AI 商业集成/转售资格，独立平台账户和本批真实测试的有限金额授权，运营套餐、费率、模型限额、灰度规模。 | `KSTUDIO_BAI_PLATFORM_KEY`、`KSTUDIO_CLOUD_MODELS`、`KSTUDIO_CLOUD_PRICES`、`KSTUDIO_GLOBAL_MAX_CONCURRENCY`。私有费用记录及供应商回执单独保管。 | 工程以一条获准路由用真实中文和参考图跑简单案例、同条件 Harness 对照和平台用量，逐项核对金额、失败退款与限制。 |
| 绑定支付 AppID 的微信 Native 商户、APIv3 材料，并明确同意一次真实小额支付和原路退款。 | `KSTUDIO_WECHATPAY_MCHID`、`KSTUDIO_WECHATPAY_APPID`、`KSTUDIO_WECHATPAY_MERCHANT_SERIAL` 和三个 `KSTUDIO_WECHATPAY_*_FILE` 挂载。 | 工程跑创建订单、回调、查询、退款、余额、对账和关闭新充值后已有订单处理。 |
| 可信 Windows 发行签名及一台独立干净 Windows x64＋合法 SketchUp 2024，以及至少三个目标用户。 | 经营方签名工位或经授权受管签名服务。受控试用地址和设备。 | 工程准备内测脚本，逐次记录真实首次安装、连接、建模、局改、SKP下载/重开、更新、失败恢复与卸载。最低 5 次完整流程。 |
| 最终商业审批。当前等待上面关卡实测后的正式请求。 | 私有审批记录绑定发布源码、安装签名、价格、模型限额、退款、灰度策略和开关。 | 达到全部条件后提交 `READY_FOR_OWNER_LAUNCH_APPROVAL`。审批后才启动实际生产灰度。 |

模板预检标出 20 个缺项。密码、会话签名、Vault/备份密钥和镜像 SHA 可由工程在真实授权环境生成或验证。用户只需提供主体、权限、独立资源和限量实测授权。[配置字段](../../deploy/ENVIRONMENT.md) · [运维续跑](OPERATIONS_RUNBOOK.md)
