# R2 官网与客户端实施 / 2026-11-04

## 实际交付

官网位于 `website/`，由独立 `cloud/main.py` 控制平面托管。没有把本机建模 FastAPI 暴露成公共站点。使用 R2 原 HTML 的首页结构、建筑示意、配色与衬线字体；沿用提供的 K 标志 SVG。首页示意明确写“空间概念示意 · 非实测结果”，不作为建模验收。

真实前端路由：`/`、`/download`、`/docs/start`、`/docs/connect`、`/pricing`、`/auth/login`、`/auth/register`、`/auth/recover`、`/account/usage`、`/account/orders`、`/account/orders/{id}`、`/account/payment-return`、`/account/devices`、`/status`、`/feedback`、`/privacy`、`/terms`、`/licenses`。

登录通过 `/api/auth/login` 发起真实 OIDC；注册与恢复交给同一身份服务，不在浏览器制造身份。账户 UI 使用实际会话、CSRF Token、余额、预占、待结算、费用明细、订单与设备接口。退出和设备撤销均调用后端。支付返回只读服务端订单，不能增加余额。未知模型费用为“待确认”；退款待对账显示“退款待核对”。订单请求在结果未知时复用同一幂等键，取得确定订单后才结束该请求。

下载来自服务端已验证且获准分发的 release 配置，核对版本、大小与 SHA-256；展示签名、发布者、日期、渠道、兼容限制、系统要求和版本记录。缺少开放条件时禁用下载，不能拿示例 URL 或未授权候选替代。正式身份、价格、商户与公开工件未配置时对应功能关闭，页面说明实际原因。反馈真实写入控制平面数据库并显示回执。

客户端保留原 K 标志、244 px 宽屏侧栏（原 CSS 规则）、深绿/暖白/金色、居中欢迎与三建议卡、所有既有 ID/事件、底部输入、右栏默认收起。局部改动：

- 空项目的欢迎区不再占满 100% 后将连接提示挤到输入框下；改为在同一个会话滚动区域内分配剩余空间。输入工具行可换行，长错误/提示完整折行。
- 顶栏“输入已就绪”改为“可输入需求 · 尚未绑定模型”，不把可编辑误写成桥接/项目已连接。
- 侧栏底部增加账户入口，真实读取 `/api/cloud-account`；设备验证码 → HTTPS 官网登录 → 明确批准这台电脑 → 客户端轮询授权。短期/刷新令牌仅由原生 DPAPI 保存，不返回 JS。显示真实身份、余额与平台/BYOK 模式；付费 BYOK 须勾选当前公布服务费，平台模型从后端开放列表选择。运行中不能切换；未配置/错误不显示假余额，关闭弹窗恢复焦点。
- API 连接支持后端实际档位列表，高级项显示上下文/输出上限、图片/工具/流式自报能力、生效配置、来源和 `NOT_RUN`。自报能力不提升为建模已验证；不回显 Key。
- 修复真实错误：普通聊天带有当前方案 hash 时，发送失败原先不恢复草稿；现在按“是否真正的批准按钮动作”判断。自然语言仍原样恢复，失败的空批准不会生成伪草稿。

## 验证与证据

基础提交 `ef52a76f7bda15d59939369da200b3e55778f0a6`，本次修改未独立提交；最终代码散列由总验收记录确定。

本地证据目录：`outputs/video-storage/jobs/kstudio-r2-20261104/web-evidence/`。这些是执行后的真实页面截图，不是 R2 设计输入：

| 证据 | 结果与范围 |
| --- | --- |
| `results.json`、`home-1440.png`、`home-900.png`、`home-390.png` | 真实 Edge headless + 独立 cloud/SQLite；16 路由 × 3 宽度无横向溢出；JS 错误 0；手机菜单/Escape；真实反馈落库 |
| `account-usage-fixture.png`、订单/设备/回跳 fixture 截图 | 明确标注“本地验收 fixture（非真实用户）”；真实 cookie/服务端账本读取和退出撤销；不代表真实 OIDC 商户验收 |
| `client-results.json`、`client-1440-dpr1.png`、`client-800-dpr2.png`、`client-390-dpr1.png`、`client-api-dialog.png` | 1440×960、1280×900、1024×720、800×600、390×844；发送在屏内，无 body 横向/纵向溢出，右栏默认关闭，账户弹窗状态/焦点/API 禁用档位通过 |
| `client-api-persistence.json` | 真实客户端添加 `example.invalid` 离线虚构配置→刷新保留→Key 不回显→能力仍 NOT_RUN→删除；无供应商请求 |
| `client-api-persistence-missing-sdk.json` | 缺少 DSH SDK 环境时同样完成配置持久化流程；运行时缺失不再导致连接管理 500 |
| `../client-before.png` | 负责人保存的旧 build07 原生桌面截图，2560×1600；连接提示被 composer 截断。原生同条件 after 由负责人统一记录 |
| `../web-browser-junit.xml` | 仓库可重复浏览器测试 1 PASS，含设备撤销、真实反馈、48 路由/宽度组合、未开放下载/认证禁用、实际退出 |

`tests/test_ui_contextual_composer.js` 37 PASS。先修 fixture 缺少 `refreshHarnessInteractions` 引用，随后复现真实草稿恢复缺陷并修复；既有失败用例仍在，加了空批准失败不伪造草稿的回归。

首次离线 API UI 保存发现另一真实缺陷：缺少 `KSTUDIO_DSH_SDK_SITE` 导致 `model_router.status` 抛 KeyError，保存后的连接列表 500。原始错误保留在 `client-ui-missing-sdk-first-failure.err`；运行时负责人修复为 available=false / blocked_missing_deepseek_dependency，另起无 SDK 隔离进程的真实 UI 复测通过。另一次脚本等待已有“已保存 1”过早结束属于测试同步错误，改为等待保存结束、Key 清空及按钮解锁后通过。

可重复命令（已有 Edge，不自动下载浏览器）：

```powershell
$env:KSTUDIO_RUN_BROWSER_TESTS='1'
python -m pytest tests/browser/test_r2_website.py -q
node --test tests/test_ui_contextual_composer.js
```

`playwright` 仅用于验收环境，不是产品运行依赖。测试需 cloud requirements 和已安装 Edge；SQLite 是显式本地 fixture，生产控制平面需 PostgreSQL。所有生成截图/日志/数据库在项目 E 盘目录，未读取开发者 Key 或用户模型。

## 尚未证明的范围

浏览器 DPR 1.25/1.5/2 是设备像素比模拟，不等于 Windows 原生 125%/150%/200% 完整验收。真实身份提供方注册/恢复/登录、真实支付、生产域名与主体/规则、公开安装包授权、另一台 Windows 电脑及多版本 SketchUp 仍需对应外部条件。前端本地通过不等于建模质量或商业发布全通过；不将这些项改写为 PASS。

## 追加：公开连接器与真实设备授权 UI

连接向导继续沿用原布局与 ID，读取 schema2 `kstudio-public` 的实际候选年份、插件种类和本版验证记录。配对配置、插件文件存在、原生可达、项目绑定、建模质量分别显示；配置完成不能写成插件已安装或原生验收通过。网页指南使用 K Studio Connector 的真实菜单，不宣传旧私有桥接可公开分发。

真实点击复现 `start-agent-session` / `start-blender-session` 缺少 `type="button"`，位于聊天表单时会同时提交消息，导致连接向导被 busy 状态挡住。已修复并添加回归；`public-connector-ui.json` 记录实际 schema2 页面、选择候选 2027 和真实 RBZ 下载 SHA 一致，且没有 POST 聊天、安装或模型请求。原生连接由负责人独立验证，不能由下载成功推导。

`tests/browser/test_r2_device_account.py` 使用完整客户端 `create_app` 与真实云端 `create_app`、数据库迁移和 Windows DPAPI。在真实 Edge UI 中依次完成设备发起、官网登录、受控身份服务确认、Authlib PKCE/nonce/state/RS256/JWKS 校验、官网明确批准设备、客户端授权/持久恢复、真实平台 router 切换、付费 BYOK 未勾选拒绝/明确确认、官网撤销和本机失效。另查未配置状态、800×600/390×844 弹窗无横溢出。未发起模型调用或扣费。

**证据边界：** IdP 为签名/协议 fixture；测试的 HTTPS hostname 经浏览器受控转发到本机 HTTP 服务，不是公网 TLS 验收。没有生产登录后门，没有用手工写 cookie 代替此项登录。正式 IdP、真实商户、正式域名仍未验证。

新增证据在同一 `web-evidence`：`device-account-ui.json`、`client-account-authorized-fixture.png`、`website-device-approved-fixture.png`。负责人另保存 `../client-after.png` 与原生 before 对比。首次账户测试失败是 fixture 转发丢失 Host 被真实 TrustedHost 中间件拒绝，已修测试保留合法原 Host；不是放宽产品主机校验。

回归命令另含 `node --test tests/test_ui_connector_setup.js`（16 PASS）与 `python -m pytest tests/browser/test_r2_device_account.py tests/browser/test_r2_website.py -q`。需实际客户端依赖、cloud requirements、Playwright 和已安装 Edge，显式 `KSTUDIO_RUN_BROWSER_TESTS=1`；`KSTUDIO_BROWSER_EVIDENCE_DIR` 与 pytest basetemp 指向 E 项目存储。整个 R2 总验收仍以负责人冻结记录为准。

冻结复测：`web-account-final06-junit.xml` 2 PASS；`web-node-final.log` 53 PASS。平台模式下从 API 面板保存配置会先读取本机账户来源并阻止静默替换，提示明确选择 BYOK；浏览器实测 router 不变、连接库仍为空。最初新增该用例漏点“模型设置”的折叠菜单，属于验收脚本问题，补实际点击后通过。客户端及网站源码已通知负责人冻结，未继续改布局。

build03 前最后追加恢复边界：后端配置恢复失败时来源为 `unavailable`，API 面板也拒绝更改连接，不默认当作 BYOK。账户弹窗在 `account_restore_required` 时提供明确选择入口，标注“尚未重新授权”，避免要求用户恢复却隐藏操作入口；免费 BYOK 可由用户明确确认恢复，平台/收费身份仍由后端验证。`web-account-final07-junit.xml` 1 PASS，重新走完整真实整站授权流程，并验证 unavailable 保存拒绝 → 账户明确 BYOK 恢复 → 未配置关闭状态，0 付费推理。产品前端已再次通知负责人冻结。

## 工程 SKP 真实网页下载（不计建模质量）

负责人提供 `native-faults-02/.../blank-disposable-reopened.skp`。在隔离 ProjectStore 建立显式命名“工程下载夹具 · 非模型生成与建模验收”的项目，复制该 SKP，依据其真实 `reopened-fingerprint.json` 导入两组元数据；不虚构模型调用、连接或原生结果。真实网页点击历史项目 → 模型与文件 → 下载 SKP，浏览器保存为 `web-evidence/engineering-fixture-browser-downloaded.skp`。

原文件、项目副本、浏览器下载三个 SHA-256 均为 `b71054187c43b78069f4e8449bb8ca7c2bff3870a4e9be8ad2d82ceecd1e4914`，245377 bytes。0 POST、0 JS 错误、0 模型/原生调用。截图及 receipt：`engineering-fixture-download-ui.png`、`engineering-fixture-download.json`。首次夹具未导入真实对象元数据，正常被产品“无几何不显示 SKP”规则过滤；补齐来源明确的实际只读元数据后下载通过。后续实际下载文件的原生重开/KEEP 由负责人独立进行；此证据只证明真实下载链路，不计入建模基准通过率。
