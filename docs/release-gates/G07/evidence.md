# G07 实际证据

合成支付验证使用临时 RSA 商户签名、微信签名和 AES-GCM 夹具、真实本机 SQLite 账本及 FastAPI 请求。全量云端工程矩阵在隔离 PostgreSQL 上另行测过共享账本。运行命令和失败原始日志 SHA-256 在 [tests.json](tests.json) 中。独立 QA 还重跑了并发下单、丢失响应后的原单查询和既有退款查询。

微信支付下单、关闭、验签和金额契约参考官方文档。收到未确认的付款码时，产品保持原订单号供查询。 [微信 Native 下单](https://pay.wechatpay.cn/doc/v3/merchant/4012791877) · [微信 Native 错误码](https://pay.wechatpay.cn/doc/v3/merchant/4020770377)
