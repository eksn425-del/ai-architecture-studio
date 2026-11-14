# R3 微信 Native v3 实施记录

2026-11-07。代码与离线签名协议测试，不是生产商户开通、真实付款或退款验收。没有使用生产支付凭据或发出真实微信支付请求。

## 实现范围

`cloud/wechat_payments.py` 通过固定微信官方主域发出 RSA-SHA256 商户签名请求，HTTPX 保留 TLS 验证、不跟随重定向。返回及回调按预置微信支付公钥 ID 验签，校验时间戳五分钟窗口；回调先验签再 AES-256-GCM 解密，再核对商户、支付 AppID、订单、金额、币种与付款状态。

验签材料使用明确的**微信支付公钥模式**，不是商户 API 证书，也不自动从不可信响应下载新公钥。服务端私有只读 JSON 文件格式：

```json
{
  "active_key_id": "PUB_KEY_ID_由商户平台取得的实际ID",
  "keys": {
    "PUB_KEY_ID_由商户平台取得的实际ID": "-----BEGIN PUBLIC KEY-----\n由商户平台取得的真实PEM公钥\n-----END PUBLIC KEY-----\n"
  }
}
```

单个公钥可省略 active_key_id；多个轮换公钥必须明确当前请求使用的 ID，旧公钥保留用于已发起交易的验签。所有请求携带 Wechatpay-Serial，使用同商户的公钥 ID 请求对应签名。未知 ID 一律失败。若原商户仍处在平台证书与公钥混合灰度期，本版不能直接用于生产：需要先完成官方公钥切换及真实回调验证，不能关闭验签迎合旧响应。

正式变量沿用执行表：KSTUDIO_PAYMENT_PROVIDER=wechat_native、KSTUDIO_WECHATPAY_MCHID、APPID、MERCHANT_SERIAL、API_V3_KEY_FILE、MERCHANT_PRIVATE_KEY_FILE、VERIFY_MATERIAL_FILE；主密钥文件正文不进入仓库。支付 AppID 必须与 MchID 绑定，不能用网站微信登录 AppID 冒充。KSTUDIO_PAYMENT_ENABLED 和确认价格控制新下单；关闭新付款后保留已有订单查单、验签和退款恢复能力。

## 状态与一致性

- 下单先持久化 wxnative 订单归属再发请求，使用本地稳定订单号；官方 code_url 仅生成本地 SVG 二维码，不使用外部二维码服务，也不将返回页作为成功依据。有效付款窗口30分钟，GET二维码不重新下单。
- 已验证的最小回执进入 verified_payment_inbox，去除 payer/openid 等无关资料；然后调用原有整数账本入账。入账崩溃保留 pending，可重放；重复/并发回调与查单最多入账一次。冲突事件 ID 拒绝。
- 漏回调可查原订单补记；关闭订单后再官方查单确认。未知结果不自动更换订单号重试。
- 全额退款仅支持当前有足额可用额度的订单，管理员近期登录、明确订单与原因才能申请。申请前在同一事务预占待退额度，阻止用户同时消费。管理员 ID 和原因保存在退款记录。
- 退款申请受理不作为完成；随后官方查询或验签回调 SUCCESS 才扣回额度并结束。请求超时/状态未知保留预占，使用原退款号查询，不自动再发新退款。PROCESSING/ABNORMAL 保留预占，CLOSED 释放，SUCCESS 只扣一次。
- 商户侧外部发起退款或部分退款进入 payment_reconciliation 人工核账，不凭金额猜测比例。退款 ABNORMAL 由负责人在商户平台处理，不能声称已退款。
- 官方退款通知省略 currency，按已验证 CNY 原订单绑定；退款查询返回的 currency 必须为 CNY。身份、金额和退款号仍严格核对。

## HTTP 接入

`cloud/payment_routes.py` 注册到现有应用、共用身份与 CSRF 校验：

| 方法及路由 | 作用 |
|---|---|
| GET /api/account/orders/{id}/payment | 当前账户拥有的有效订单二维码 SVG，no-store，无供应商调用 |
| POST /api/account/orders/{id}/query | 所有者主动查单，持久化已验证结果 |
| POST /api/account/orders/{id}/close | 所有者关闭未付订单并查验终态 |
| POST /api/payments/wechat/notify | 验签、持久化和幂等处理后204；失败4xx/5xx，不提前假确认 |
| POST /api/admin/orders/{id}/refund | 管理员、认证时间≤300秒；JSON需 confirm_order_id 与10至200字reason |
| POST /api/admin/refunds/{id}/query | 管理员查询已存在退款号，不发起新退款 |
| POST /api/admin/payments/wechat/recover | 管理员重放已验签的持久化回执，无供应商请求 |

有网络/密钥读取的同步操作均在工作线程执行。前端只能显示数据库/已验证查询结果；不能传入支付金额改变订单、不能用猜测订单ID读别人的付款码。

## 真实验收尚需

本机技术回归已通过：27项签名／通知／账本测试、4项HTTP权限／CSRF／通知应答测试，以及1项真实Edge连接本地uvicorn的订单页测试。订单页实际加载服务器生成的SVG二维码，主动查单后根据数据库状态隐藏二维码，关单后显示关闭；新支付关闭时已有订单仍可恢复。该浏览器测试使用合成已验证支付回执，不向微信发送真实付款或查询，不是生产支付验收。测试文件分别为 `tests/cloud/test_wechat_payments.py`、`tests/cloud/test_payment_routes.py`、`tests/browser/test_r3_wechat_orders.py`；JUnit位于本次私有job的 `wechat-adapter-tests.xml`、`payment-route-tests.xml`、`wechat-browser-tests.xml`。

有效商户 Native 权限、绑定支付 AppID、负责人已确认的价格和退款规则、公网 HTTPS 回调、私有密钥挂载以及授权付款人完成一笔有限金额扫码。测试记录必须分别证明：实际到账一次、主动查单、一次官方退款 SUCCESS、账本一致。离线签名夹具的27项通过不能替代这些条件。

官方资料（2026-11-07核对）：[Native下单](https://pay.wechatpay.cn/doc/v3/merchant/4012791877)、[Native开发指引](https://pay.wechatpay.cn/doc/v3/merchant/4012791891)、[公钥验签](https://pay.wechatpay.cn/doc/v3/merchant/4013053249)、[公钥接入易错点](https://pay.wechatpay.cn/doc/v3/merchant/4054257713)、[退款查询](https://pay.wechatpay.cn/doc/v3/merchant/4012791884)、[退款回调](https://pay.wechatpay.cn/doc/v3/merchant/4012791886)、[退款状态及恢复](https://pay.wechatpay.cn/doc/v3/merchant/4013071031)。
