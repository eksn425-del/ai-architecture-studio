# K Studio R3 发布裁决

**BLOCKED_EXTERNAL，仍有内部验收项 PARTIAL。** 正式裁决未达到 `READY_FOR_OWNER_LAUNCH_APPROVAL`。可由项目所有者在现有机器的独立 E 盘目录使用内部工程候选，验证 SketchUp 2024 下的概念样件、局改、恢复与本机交付。公网官网、下载 URL、收费、真实批准和独立用户验收均没有已验证结果。

| 清单 | 判定 | 证据或剩余条件 |
| --- | --- | --- |
| Repo | PASS | PR27 锁定 `6a8001c`。商业候选在独立分支。原工作树 18 项、4 份历史 SKP、9 份已索引源图或文字、原快捷方式及版本指针哈希复核一致。见 [G00](G00/evidence.md)。 |
| 核心 Agent | PARTIAL | 冻结 beta09 启动官方 DeepSeek Harness 工具目录并载入建筑增强，真实供应商自然对话建模和对照待验。见 [G02](G02/evidence.md)。 |
| 质量 | PARTIAL | 简单展亭通过独立原生核查。工坊楼梯走向、平台和门槛，文昌折面和楼梯，退台种植和体量依据历史源图仍待修验。见 [G02](G02/evidence.md)。 |
| 局部修改 | PASS | 工程样件只改门廊。底座、框架和屋面全子树一致，续改版为 1,050 毫米。见 [恢复续改](../test-results/windows/2026-11-14-r3-beta09-recovery/model/write-verifications.json)。 |
| 连接 | PARTIAL | Windows 11、SU 24.0.484 单窗口和原生进程恢复通过。多实例、未保存文档、选择变更有源码合同覆盖，完整新包实机组合仍待补。见 [G03](G03/evidence.md)。 |
| 交付 | PARTIAL | 真实 beta09 工作台下载 SKP，在 SU 2024 原生重开，层级、几何、材质和显示一致。下载件上的独立用户再次编辑未验收。见 [交付](../test-results/windows/2026-11-14-r3-beta09-recovery/model/native-reopen.json)。 |
| 失败恢复 | PARTIAL | 故意丢失一个真实原生回执后重启恢复，旧命令阻止重放。阶段中断保护有测试，复杂原生崩溃、物理断电和全部组合未验。见 [G03](G03/evidence.md)。 |
| 安装 | BLOCKED_EXTERNAL | E 盘真实隔离安装 34,428 文件哈希与冻结清单一致。同版本阻止覆盖。离线实际完整载荷更新和回退通过。仍需真实签名、干净机、迁移及线上升级。见 [G04](G04/evidence.md)。 |
| 官网 | BLOCKED_EXTERNAL | 本地真实 Edge，18 个页面、4 种宽度和焦点、反馈验证通过。公网 HTTPS 和真实下载未验。见 [G05](G05/evidence.md)。 |
| 账户 | BLOCKED_EXTERNAL | 本机 OIDC 协议、已存在账号复登、跨账户、DPAPI 与本地 Vault 合同已复验，真实手机号/微信及设备未验。见 [G05](G05/evidence.md)。 |
| API | BLOCKED_EXTERNAL | 服务端密钥读取、协议及额度门槛有数据库证据。本轮 0 个真实供应商请求，费用和实际模型服务须实测。见 [G06](G06/evidence.md)。 |
| 余额 | PARTIAL | SQLite 与真实隔离 PostgreSQL 的预占、并发、终态幂等、未知用量、恢复和补偿验证通过。实际供应商账单仍待闭环。见 [成本和计费](COST_AND_BILLING_REPORT.md)。 |
| 支付 | BLOCKED_EXTERNAL | 合成签名、回调、退款与重试测试通过，真实商户付款、退款、对账 0 次。见 [G07](G07/evidence.md)。 |
| 运维 | BLOCKED_EXTERNAL | 加密备份、空库恢复、17 表数据指纹、Vault 解密、收件箱一次处理通过。真实云镜像、HTTPS、监控、告警和回滚等待 staging。见 [G08](G08/evidence.md)。 |
| 许可与合规 | PARTIAL | 代码、包内容和实际依赖初审完成。经营主体适用性、第一方及第三方再分发、许可文本和可信签名仍需经营者核准。见 [G09](G09/evidence.md)。 |
| 用户体验 | BLOCKED_EXTERNAL | 内部模拟的页面与独立实机夹具已有证据。外部真实目标用户 0/3，真实首发完整流程 0/5。见 [首次使用](USER_FIRST_USE_REPORT.md)。 |
| 运营放行 | NOT_RUN | 先完成 G00–G10，再提交商业放行请求。见 [G11](G11/evidence.md)。 |

## 核验版本

- Windows x64 内部候选为 **2026.11.14-R3-beta09，序号 16**。通用安装文件 315,733,922 字节，SHA-256 `8c52a0f53532ef4de29aeb9b5c0fcffa79fc67c04900a0f13a83cebee62fe5a5`，Authenticode `NotSigned`。原常用桌面安装为 beta03。
- 云端和官网的源码工件为 123,922 字节，SHA-256 `3bf99dc4b3f9ad97715dfddbc69828be4326ddc7962b07d0ec3091631d34759f`，40 个内容文件逐一验证。部署使用实施提交的干净 Git checkout。云镜像和公网运行状态仍待真实验收。
- 本轮实际付费模型请求/支付/退款均为 0。历史供应商扣费未核验，原用量和未知数据已保留。生产开关和生产数据在本轮没有操作。

[关卡索引](index.md) · [最少人工步骤](OWNER_ACTIONS.md) · [安装和原生工件版本说明](RELEASE_NOTES.md)
