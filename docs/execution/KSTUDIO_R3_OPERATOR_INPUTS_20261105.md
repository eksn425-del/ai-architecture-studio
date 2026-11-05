# K Studio R3：负责人一次性配置表

日期：2026-11-05。配合[上线执行书](KSTUDIO_R3_LAUNCH_EXECUTION_20261105.md)使用。本文件只记录配置名称、状态和秘密的安全引用，**不填写真实 Key、验证码、证书私钥、完整手机号或密码**。

Codex 先检查已获授权的现有配置，能复用就复用；不要让 Alan 重复注册已有资源。未提供的商业主体、签约材料和预算不能猜。所有不依赖缺项的开发、测试、打包与部署工件继续完成。

## 1. Alan 只需集中准备这些资源

| 资源 | 最少需要什么 | 由谁／在哪里完成 | 缺少时 Codex 继续做什么 |
| --- | --- | --- | --- |
| 云主机和域名 | 腾讯云已有实例或采购预算；获授权的运维连接；正式域名、DNS 权限和备案／接入状态 | Alan 在[腾讯云控制台](https://console.cloud.tencent.com/)完成账户、采购及备案主体操作，安全授权 Codex 运维 | 完成容器、配置校验、迁移、恢复演练和部署脚本 |
| 手机号／微信登录 | Authing 租户与 OIDC 应用；有效短信服务／额度；具备微信登录权限的网站应用 | [Authing](https://console.authing.cn/)与[微信开放平台](https://open.weixin.qq.com/)；按真实控制台指引，不冒用资质 | 完成 OIDC 兼容、设备授权、页面与确定性测试 |
| 微信充值 | 正式商户号、Native 权限、获准绑定的支付 AppID、支付凭据 | [微信支付商户平台](https://pay.weixin.qq.com/)；登录 AppID 与支付 AppID 分开核实 | 完成 adapter、回调验签／幂等、查单、退款和联调说明，收费开关关闭 |
| 平台 BAI 与价格 | 正式服务配置；允许平台提供的模型；已有授权测试账号；对客套餐、服务费和预算 | Alan 的实际 BAI 账户与经营决定；密钥放安全配置，不发到 GitHub | 复用已授权测试路由；完成白名单、计量和费用展示；不擅自定正式售价 |
| Windows 发行与实际使用 | 能测试的合法 Windows＋SU2024、生产签名／更新信任、发布组件的许可材料 | 现有 Windows Codex 环境、代码签名服务／凭据；需要时准备独立 Windows VM 或第二台电脑 | 构建安装程序、保留原 profile、完成静态发行检查；无法真机则明确 NOT_RUN |
| 对外经营资料 | 经营主体名称、支持联系方式、隐私／服务／退款确认信息 | Alan 确认真实资料；Codex 负责落到产品 | 先完善可审阅正文，字段留待填写，不用虚构公司或备案号 |

无需把所有账号密码交给代理。优先最小权限临时身份、受控 SSH、秘密管理或本机私有环境配置。控制台要求本人实名认证、扫码授权或付款时由本人完成。

## 2. 非秘密状态表

在执行环境填写此表的副本。提交仓库时仅保留必要的非秘密标识与状态；手机号、内部地址和敏感账号标识按需脱敏。

| 项目 | 当前填写值／秘密引用 | 状态 |
| --- | --- | --- |
| 正式域名／公开 URL | 待提供或发现现有值 | UNSET |
| 云地区／实例／运维身份引用 | 主选上海；实际待核实 | UNSET |
| 云采购预算／现有资源授权范围 | 待提供；不从测试 BAI 授权推断 | UNSET |
| ICP／接入状态与负责人 | 待核实实际备案 | UNSET |
| 发布 COS／私有备份位置 | 分开权限；实际待配置 | UNSET |
| Authing 租户／Discovery／Client ID | 复制实际控制台，勿拼接 Discovery | UNSET |
| OIDC Secret 引用 | 例如受控环境变量名，不填值 | UNSET |
| 短信通道与正式额度 | Authing 托管或已有获批腾讯云短信 | UNSET |
| 微信网站登录应用／Secret 引用 | 已取得登录权限的应用 | UNSET |
| 支付商户／支付 AppID／Native 权限 | 与网站登录应用分开核对 | UNSET |
| 支付私钥／APIv3／验签材料引用 | 仅引用路径或秘密名称 | UNSET |
| BAI Base URL／模型／协议 | 复核 R2 实测 Responses／Low 路线 | UNSET |
| BAI 平台 Key 引用／账号权限 | 仅服务端读取；不进入安装包 | UNSET |
| 已有测试授权及本轮费用边界 | 保留仍适用的授权，明确不自动充值 | UNSET |
| 生产签名与更新密钥引用 | 两套不同用途；不能用内部测试信任代替 | UNSET |
| 测试 Windows／SU 版本／操作者 | 记录是否真实干净系统或第二台电脑 | UNSET |
| 经营主体／支持联系／文件确认 | 实际值与负责人的确认记录 | UNSET |

可用状态：`READY`、`CONFIGURED_NOT_VERIFIED`、`WAITING_OWNER`、`WAITING_PROVIDER`、`BLOCKED_EXTERNAL`。填写了字段不等于真实登录或支付已验收。

## 3. Authing 控制台实际配置

1. 一个正式用户池、一个 OIDC Web 应用；网站和客户端沿用同一用户身份。
2. 授权码模式、S256、RS256/JWKS；token endpoint 方法与后端一致，主选 `client_secret_post`。
3. Authing 回调白名单：`https://实际正式域名/auth/callback`。不要把示例域名原样填进去。
4. 开启手机号验证码；确认有效发送额度、防滥用配置、正式服务开通与回收号码相关账户恢复规则。
5. 开启 PC 微信扫码；填有登录权限的网站 AppID / AppSecret。微信到 Authing 的授权回调域用该租户官方值；它不是第 3 项的 K 回调地址。
6. 账号身份关联采用询问绑定、手机验证码确认；先手机后微信、先微信后手机都实测同一 `sub`。不自动合并既存的两个钱包。
7. 套餐／品牌化／自定义短信支持按实际控制台核实，不假设所有能力永久免费。若用腾讯云自有短信，确认签名、模板、运营商实名与相应主体授权；托管短信按 Authing 自身准入核实，不能套用未经核实的资格推断。

## 4. 支付与收费必须明确的业务值

| 业务项 | 要填的决定 |
| --- | --- |
| 计价货币 | 首发 CNY；页面显示元，支付／账本按整数最小单位处理 |
| 额度定义 | 明确多少额度对应什么服务价值，不把上游 Token、人民币和软件额度混成同一个数 |
| 充值档位 | 至少一个实际可卖套餐：金额、到账额度、是否赠送、有效期如有 |
| 平台 BAI 费用 | 每个已开放模型的输入／输出计价、服务费、舍入规则、版本生效时间 |
| BYOK 软件费 | 每个可核验服务授权／回合如何收费；用户的模型费另付供应商；失败／取消如何处理 |
| 试用额度 | 有或无；若有，金额、领取次数与防滥用上限明确 |
| 退款规则 | 未使用额度与已消费额度、异常任务、待核账的实际处理方式和支持入口 |
| 测试边界 | 可用模型账号及授权范围；一次真实支付／退款的金额上限与付款人；短信数量上限 |
| 全局保护 | 账号并发、全局并发、单任务／每日平台费用上限与告警负责人 |

不提供建议售价冒充已确认售价。Codex 可以输出基于实际成本的可审阅建议，但在 Alan 确认前不得启用真实对客充值。此前对测试 BAI 的授权继续按适用范围使用，不自动等同于允许付款账户产生新交易。

## 5. 环境变量映射：区分已有与本轮新增

### 5.1 已有源码的变量

这些已在 R2 `cloud/config.py` 或部署文件出现；具体结构按 `deploy/ENVIRONMENT.md` 和当前源码验证：

```text
KSTUDIO_DOMAIN
KSTUDIO_DATABASE_PASSWORD
KSTUDIO_CLOUD_PUBLIC_URL
KSTUDIO_CLOUD_ENV
KSTUDIO_CLOUD_DATABASE_URL
KSTUDIO_CLOUD_SESSION_SECRET
KSTUDIO_OIDC_METADATA_URL
KSTUDIO_OIDC_CLIENT_ID
KSTUDIO_OIDC_CLIENT_SECRET
KSTUDIO_ADMIN_SUBJECTS
KSTUDIO_PRICES_CONFIRMED
KSTUDIO_CLOUD_PRICES
KSTUDIO_CLOUD_MODELS
KSTUDIO_CLOUD_RELEASE
KSTUDIO_WEBSITE_DIR
```

`KSTUDIO_CLOUD_MODELS` 使用 `key_env` 指向服务端 BAI Key 的变量；模型配置不能含 Secret 正文。`KSTUDIO_ADMIN_SUBJECTS` 使用核实的 `issuer|sub`，不能把手机号或微信昵称直接写成管理员主键。已有 Stripe 变量保留，但微信商业首发不要求填写 Stripe。

### 5.2 本轮应新增并实现的变量（当前不能假定已生效）

```text
KSTUDIO_OIDC_TOKEN_ENDPOINT_AUTH_METHOD
KSTUDIO_VAULT_ACTIVE_KEY_VERSION
KSTUDIO_VAULT_KEYS_FILE
KSTUDIO_PAYMENT_PROVIDER
KSTUDIO_WECHATPAY_MCHID
KSTUDIO_WECHATPAY_APPID
KSTUDIO_WECHATPAY_API_V3_KEY_FILE
KSTUDIO_WECHATPAY_MERCHANT_PRIVATE_KEY_FILE
KSTUDIO_WECHATPAY_MERCHANT_SERIAL
KSTUDIO_WECHATPAY_VERIFY_MATERIAL_FILE
KSTUDIO_BAI_PLATFORM_KEY
```

这些是执行接口建议，Codex 可依所采用 SDK 小幅调整，但必须同步代码、校验器、模板和运维文档。文件变量引用服务端私有只读挂载；`VERIFY_MATERIAL_FILE` 的格式须明确选择官方微信支付公钥／平台证书机制，记录 key ID／serial 和轮换，不自己发明加密算法。

Authing 托管短信、微信登录 AppSecret 配置在 Authing，通常无需再复制进 K 云端 `.env`。部署后的正式配置只在受控服务器／秘密管理，提交的模板只含字段名和安全示例。

## 6. 阻塞时的统一交接格式

Codex 完成可独立部分后，只发一次如下表格，不把普通 bug 或终端命令推给 Alan：

| 缺项 | 已完成准备 | Alan 唯一需要的动作 | 安全注入位置 | 补齐后的自动续跑与验证 |
| --- | --- | --- | --- | --- |
| 例如微信登录权限 | OIDC、绑定页与回调已实现并本地验证 | 在本人开放平台完成网站应用审核 | Authing 社会化身份源配置 | 真实扫码 → 同一账户 → 桌面设备授权 |

明确外部阻塞影响哪个入口；其他可验证路径继续运行。只有代码完成却缺真实云资源时，应交付“部署候选完成”，不能写“网站已上线”。

