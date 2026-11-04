# R2 公开测试门槛：运营者最少输入与实际执行单

本表只把真正缺少身份、设备、资源或授权的验收列为外部条件。本机工程、源码包、内部候选、测试 IdP、合成支付事件、测试签名均不能冒充真实公网/商户/干净机器验收。最终工件以发布清单记录的版本和 SHA256 为准。

## 运营者需提供的最少条件

| 条件 | 需要提供什么（秘密只进私有配置，不进聊天/Git） | 解除门槛的证据 |
| --- | --- | --- |
| 隔离测试主机和域名 | 批准的地域、DNS/主机权限；真实运营主体、支持联系方式、隐私/保留期/退款条款；大陆节点的实际适用资格/备案 | 真实 HTTPS 域名、服务/数据库健康、外部访问与恢复记录 |
| 成熟身份服务 | OIDC discovery URL、机密 Web client ID/secret；精确回调地址；需要手机号/微信/QQ时在该身份服务开通实际渠道 | 两个真实独立账户的网页登录、设备授权、重启、刷新和撤销/跨账户拒绝 |
| 支付商户和价格规则 | 当前 Stripe 适配需要合资格商户 test-mode Key/webhook secret；币种、整数 credits 单位、套餐、K 服务费与取消/退款规则 | 实际商户官方测试支付、签名回调、重复/乱序/退款、服务端审计；不是SDK合成回调 |
| 平台模型使用权与有限测试授权 | 可用的供应商账户、模型/区域/代理使用条款、服务器 Key；具体有限批次授权见下一节 | 实际供应商与原生建模结果、真实费用记录；运营 Key 不进入桌面 |
| 发布者签名 | 合法证书/硬件签名服务、固定发布者指纹、CA时间戳地址；独立 Ed25519 更新签名 Key 及可信公钥引导渠道 | Authenticode Valid、时间戳和固定发布者匹配，正式签名 manifest；测试 Key 不算 |
| 干净合法 Windows/SU 环境 | 至少一个真正干净 Windows 环境及一个不同于开发机的安装环境；合法SU，优先中文非管理员账户/高DPI | 本文完整首次安装—原生使用—更新—恢复—重装记录。作者暂没有第二台；本机新profile不能算干净机器 |

当前仅实现通用 OIDC 和 Stripe 适配，不能宣称已开通手机号、微信、QQ、微信支付或支付宝。若运营主体不能使用 Stripe，渠道选择后仍要完成对应适配与官方沙箱验证，不能把这部分工程说成已交付。用户可以提供测试同事/服务，不必在作者电脑下载多套大型软件。

## 付费建模批次

以 [R2_FINITE_TEST_BATCH.md](R2_FINITE_TEST_BATCH.md) 和 [批次提案](R2_FINITE_TEST_BATCH_PROPOSAL.json) 为准。六个实际项目ID、资料SHA、生效配置/工具目录先绑定；取得对该具体批次的授权后，才生成执行配置。提案仍为 `awaiting_owner_confirmation`，不能由旧聊天费用表述自动转换为执行授权。模型请求额度是保守预留，不是供应商账户硬封顶；已有零费用SDK/取消/并发测试不替代真实图片建模质量。

## 云端与账户：准确操作和通过条件

仅部署 `cloud.main:create_app`，不要公开本机 `app.main` 或 SketchUp 连接器端口。参数逐项填写 [deploy/ENVIRONMENT.md](../../deploy/ENVIRONMENT.md)；私有 `.env`、账户/商户/供应商秘密不入源码包。以下命令在批准的隔离主机、解压源码根执行；本机没有Docker，容器构建和部署仍为NOT_RUN。

1. 配置真实域名和 `KSTUDIO_CLOUD_ENV=staging`、私网 PostgreSQL、至少32字符随机session secret。开始保持价格未确认、空模型表、充值关闭。只开放80/443，不开放5432或本地建模端口。
2. IdP注册精确回调 `https://实际域名/auth/callback`，支持authorization code、PKCE S256、签名ID token、state/nonce与openid/profile。注册/找回密码使用IdP实际流程，不加测试登录后门。

```sh
cd deploy
docker compose config --quiet
docker compose build app migrate
docker compose up -d db
docker compose --profile maintenance run --rm migrate
docker compose up -d app proxy
docker compose --profile maintenance run --rm migrate python -m cloud.cli audit
```

3. 访问实际域名 `/health/ready`、`/api/public/config`、`/api/status`、官网/下载/账户。数据库ready、未授权接口拒绝；没有合格公开工件时下载关闭，没有确认价格/商户时充值关闭。固定单worker；正式部署前锁镜像digest并保留漏洞扫描，不把版本标签当不可变digest。
4. 用真实A/B两个账户验收：桌面正常设备授权由用户在网页明确批准；短期code一次性使用；重启后的DPAPI保存；过期刷新与旧refresh拒绝；撤销设备后不能调用；A的订单/设备/任务不能被B读取或修改。只保留脱敏ID和证据，不发布cookie/token。旧账户文件损坏或运营地址丢失时必须阻止推理，不切成BYOK。
5. 公布版本化收费规则后才启用 `KSTUDIO_PRICES_CONFIRMED=1`。BYOK软件服务费默认0/关闭，不伪造平台上游Token费用；若启用服务费先明确接受对应版本。平台白名单的真实上游model/协议/能力/Key逐项批准，真实验收后才设verified；不静默换模型。
6. 从至少两个真实外部网络记录首页、下载、OIDC、用量及获准平台请求的DNS/TLS、成功率、延迟、时间和样本量；须包含目标大陆网络。CDN或开发机ping不能代替登录和上游API稳定性。平台请求受有限测试授权约束。

## 支付、账本、备份：准确操作和通过条件

商户test mode登记 `https://实际域名/api/payments/stripe/webhook`，事件为 `checkout.session.completed`、`checkout.session.async_payment_succeeded`、`charge.refunded`。从网站创建真实测试订单完成官方测试支付：前端返回页不能加余额，只有服务端核验签名/商户/归属/金额/币种/支付状态后才能入账。用商户控制台重发同一事件、制造乱序/失败支付/退款；错误签名、错误金额/币种/用户归属必须拒绝。审计应显示重复不多加钱、并发预留不透支、未知usage保留待对账，不能写0。记录订单—事件—账本关联；已用额度/部分退款的运营处理限制保留，不宣布完整自动退款UI。

每分钟调度 `python -m cloud.cli recover-stale`、每天 `python -m cloud.cli audit`。接实际告警渠道，验证DB不可达、余额审计不一致、待对账超时、webhook失败、磁盘/备份失败会通知运营者。确定RPO/RTO、保留期、异地位置和恢复联系人；PGPASSFILE、age密钥私有注入。

```sh
sh deploy/backup.sh /approved-backup/kstudio-YYYYMMDD.age
# 先创建空kstudio_restore_YYYYMMDD；PGDATABASE及云数据库URL只指向这个隔离库
sh deploy/restore.sh /approved-backup/kstudio-YYYYMMDD.age
python -m cloud.cli audit
```

比较真实账户/会话/订单/任务/账本行数与样本，验证登录/设备撤销/待对账处理并记录备份时间点、恢复耗时。不得覆盖生产库或丢弃新订单来演练。本机 PostgreSQL17.11/schema2 加密恢复通过是工程证据，不是生产RPO/RTO；本机夹具已优雅停止且数据保留。生产收费和正式公网切换需各自明确授权。

## 正式签名与更新

在受控签名机/CI完成，不要求终端用户安装开发SDK。使用证书存储/硬件服务，不把PFX密码放命令行或把私钥打包。CA时间戳地址来自实际证书服务。先签本公司 KStudio.exe、KStudioConnector.exe、KStudioUpdate.exe，再生成ZIP/hash/SBOM与正式manifest；第三方厂商二进制保留原来源/签名。

```powershell
& $SignTool sign /sha1 $PublisherThumbprint /fd SHA256 /tr $CaTimestampUrl /td SHA256 $FirstPartyExe
& $SignTool verify /pa /all /v $FirstPartyExe
& ./scripts/verify_authenticode.ps1 -Path $FirstPartyExe -Thumbprint $PublisherThumbprint
Get-FileHash -LiteralPath $ApprovedReleaseZip -Algorithm SHA256
```

[Microsoft SignTool官方参数](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool)。变量均由批准的签名/发行环境提供。更新公钥和发布者指纹必须从独立可信渠道固定，不能同时信任下载包提供的新Key。签名服务对 `app.release_channel.canonical(payload)` 字节作Ed25519签名，输出 `{payload,key_id,signature}`，signature为base64。payload使用实际SHA/bytes/HTTPS URL、schema1、windows-x64、唯一递增sequence、version/channel、UTC expires_at、data_schema1和最低兼容字段；稳定渠道还要求真实验收和签名状态。`test-sign`只用于明确内部测试，不能当正式签名服务。

```powershell
& $FrozenUpdater install --manifest $ApprovedSignedManifest --archive $ApprovedReleaseZip --trusted-keys $PinnedPublicTrust --install-root $InstallRoot --data-dir $DataRoot --channel stable
& $FrozenUpdater rollback --install-root $InstallRoot --data-dir $DataRoot
```

验收签名/发布者/哈希有效，篡改、过期、错误渠道、低序号、路径攻击、不兼容schema、正在写模型时更新都被拒绝，旧项目/Key不变。回滚不降低最高序号；恢复新版通过重新签发更高序号，不手改指针。本机冻结EXE的大包演练和损坏归档拒绝均是内部测试签名证据，不能代替Authenticode或正式分发渠道。

## 许可证：已补齐的工程与真正待决定事项

最终 `third-party-notices/` 附组件/版本、公开来源、SHA、SBOM、条款文本和 `binary-license-map.json`。完整私有构建源路径映射留在本机，不公开。早期03的14项已逐项追溯，不再把它们笼统列为未做的外部工作：pi-telemetry精确发布commit、同版本koffi、两个实际父包MIT模板已提供原文/明确父包映射；其余10项在精确发行包/源码中原本缺完整许可证文件，已提供其明确声明许可的官方标准条款及原始声明证据，并永久标记 `UPSTREAM_ORIGINAL_LICENSE_TEXT_ABSENT`。这不表示追回了原始版权通知或法律审查通过。

实际183个原生文件均已分类：25个CPython、75个Python发行组件、1个Node、24个npm文件映射已收集notice；52个Microsoft CRT/UCRT/WebView文件需核对具体重分发条款；4个LGPL/MPL文件需对应源码/义务确认；2个自有EXE待发布者签名。不存在“181个都不知道”的泛化结论。

真正的发行决定包括：

- `@img/sharp-win32-x64` 的Apache-2.0/LGPL-3.0-or-later及 `@deepseek-ai/libreoffice-kit*` 的MPL-2.0：保留原文/NOTICE，核实实际二进制对应源码、修改说明、源码提供/替换条件并选择履行方式；上游首页链接或npm声明不能冒充已履行。
- CRT/UCRT/WebView2及ConPTY分别保留实际来源和适用条款；公司名/签名识别本身不授予任意系统DLL复制权。具体核对[Microsoft的VS2022可分发列表与有效授权条件](https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution)；WebView2依[官方分发说明](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)使用Runtime及实际SDK版本的条款，不能把Edge浏览器本身当生产Runtime。
- 私有fast-uri benchmark模板声明ISC而父包BSD-3-Clause，需明确该示例范围，或在公开包中排除无关示例并重新审计；不能用同名但无关的公共benchmark包许可证替换。
- 运营者决定K Studio自身终端许可、隐私、数据保留/删除、退款和公开案例授权。个人试用Kongxing等不在默认公开包内，作者本机授权不转授客户。没有新的公开授权，不重新发布私人图片/SKP。

判据是每个实际分发组件具有明确合法路径且义务已履行，不是许可证文件数量大于零。整体状态仍为 `REVIEW_REQUIRED`，不自动批准公开商用。

## 干净机器验收操作单

给独立测试者提供获准候选、SHA256、发布者/签名状态、可信manifest与公钥、冻结updater、支持矩阵、安装/卸载/恢复说明。设备不装Codex/Git/开发Python，不继承作者Key/订阅/项目目录；合法SU/WebView2按向导安装。登记Windows build、非管理员/中文账户、DPI、WebView2、SU/Ruby版本。

1. 验包、首次安装到用户可写程序目录；数据目录独立；运行包内诊断并真实打开GUI。验证缺WebView2、断网、端口占用和重复启动，不把命令行诊断当GUI通过。
2. 正常账户设备授权或明确BYOK配置；关闭/重开保存仍有效。错误Key、撤销、未验收模型/协议必须清楚拒绝，不泄露Key、不伪装成功或换模型。
3. SU扩展管理器安装包内第一方RBZ，正常重启SU后按向导配对，打开独立模型并核对路径/GUID；不覆盖原插件/原模型。候选扫描范围2019–2027不是支持证明，目前实际原生证据仅SU2024。
4. 在授权批次内用自然中文完成一次真实图像建模、局部修改/KEEP、保存、下载、SU重开与继续编辑；保存模型SHA/层级/截图、输入与错误。传输夹具不算图像质量PASS。
5. 写入中更新应延后；正常更新、损坏/签名错误/中断拒绝、回滚、重启、卸载再装检查项目及加密连接数据。卸载默认保留数据，删除须测试者明确选择；本机新profile不替代这项测试。
6. 两个环境分别提交版本矩阵、人工帮助次数、过程证据、诊断/安装日志、模型和更新receipt。失败留FAIL/PARTIAL，不由作者电脑的结果覆盖。通过后才讨论公开渠道推广；正式收费/生产切换仍需各自授权。
