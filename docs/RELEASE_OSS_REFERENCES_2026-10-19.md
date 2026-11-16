# 发售基础设施的开源参考与集成判断

2026-10-19检查；本次为同一K Studio选取可组合组件，不创建另一套产品、不下载不明许可源码、不用安装数量代替上线能力。以下HEAD只用于固定研究时点，不是推荐直接使用未发布版本。实际集成时选稳定版本、锁依赖并再核对许可、安全公告及功能边界。

| 项目与研究时HEAD | 能借鉴什么 | K Studio接入点 | 当前决定/实际执行 |
| --- | --- | --- | --- |
| [FastAPI full-stack template](https://github.com/fastapi/full-stack-fastapi-template)，`b1125d8839482cb7bbae603ddc6d0081bf87532e` | PostgreSQL、认证、邮件找回、数据库迁移、Docker、CI与浏览器测试 | 云端账号与项目API；保留K Studio现有前端与原生工具保护 | MIT；研究其组织方式，后续选择性接入，未把模板认证宣称为本产品已上线 |
| [LiteLLM](https://github.com/BerriAI/litellm)，`6762d65eb866a670e0b8c93d5e6135c06857a2e9` | 模型网关、限流、冷却、重试、回执与监控 | 现有model_router与Responses运输外侧，运营服务端 | 项目已有部分LiteLLM集成；本轮未升级或发起收费请求。MIT核心与enterprise目录各自核对许可；不假定网关已经正确支持目标模型全工具链 |
| [Celery](https://github.com/celery/celery)，`0731c053b0e09f231363ec62988fded6c9846878` | Linux worker、持久队列、失败与重复投递 | 云端任务调度；Windows连接器通过独立认证通道接收受控指令 | BSD-3-Clause；计划组合，尚未安装/接入。核心验收是重复投递不重复写模型或扣费 |
| [Locust](https://github.com/locustio/locust)，`3a1d0caa5bde59494ede55f513fcb4becbf406a0` | 用Python定义用户负载和故障场景 | staging认证/项目/额度/排队API；模型请求走模拟服务 | MIT；计划采用。此次实际小型只读HTTP检查使用现有httpx，不能写作Locust或云并发已验收 |
| [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector)，`ebfdf90d82abe991c69554b31f2efc4a96622803` | 收集与转发trace/metrics/logs | run_id/request_id贯穿浏览器、API、worker、供应商、连接器 | Apache-2.0；计划接入。先过滤密钥和用户源资料，再接云监控；本轮没有部署Collector |

## 从研究变成有效能力的验收

1. 确定解决的真实问题与许可证/平台约束，只引入必要部分。
2. 接到现有产品入口和状态系统，不能留一个从未调用的助手文件就称已完成。
3. 留下实际调用、故障和用量记录；模拟与真实供应商分开标注。
4. 验证用户效果：登录恢复、项目隔离、断线不重复改模、付费不重复扣款、真实SKP可交付。

当前已经落到产品的本轮改进是：历史执行摘要接入实际conversation/progress与前端、收尾存储故障释放写锁、应用lifespan持有本机目录锁、只读发售状态端点。云端数据库、队列、网关重试和监控仍按发售方案逐项实施。

不得把Redis兼容托管服务一概称MIT开源；具体产品、版本和部署合同单独核对。不得把Celery的重试机制当“exactly once”，也不得在网络超时后重新运行原生写指令来伪造恢复成功。

参考原始文档：[FastAPI模板](https://github.com/fastapi/full-stack-fastapi-template)、[LiteLLM可靠性](https://docs.litellm.ai/docs/proxy/reliability)、[Celery任务](https://docs.celeryq.dev/en/stable/userguide/tasks.html)、[Locust](https://github.com/locustio/locust)、[OTel Collector](https://opentelemetry.io/docs/collector/)。完整实施顺序见[大陆发售准备](RELEASE_PREPARATION_CN_2026-10-19.md)。
