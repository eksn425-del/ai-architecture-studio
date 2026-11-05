# K Studio R2 build05c — 已安装的本机候选

2026-11-05。**本机候选已更新，公开发行尚未全部通过。** 本次真实 BAI 测试已经执行，不能继续沿用昨日“未付费测试”的结论。旧程序、模型、历史失败和版本槽保留。

实际程序源码 `9c0ef028d127da44389296c4de913c16b5372dfe`；后续提交仅补充测试证据与交接。官方 DeepSeek Harness Node `0.2.1-rc.5` / Python SDK `0.2.1rc2` / Node `24.22.1`。K 品牌、深绿/暖白/金色、衬线和既有布局保留。

## 交付物

项目 E 盘 `outputs/video-storage/jobs/kstudio-r2-live-20261105/`：

| 工件 | 实际信息 |
|---|---|
| `KStudio-2026.11.05-R2-build05c-internal-win-x64.zip` | 433,346,498 字节；70,449 文件 |
| ZIP SHA256 | `d06bd94671baaeaa1d4759a49fcc3b12e140ce5b1f72ac6b3e5a1762b64e42ca` |
| 已安装 EXE SHA256 | `52b594eba2a95b9ff19ad99cd0c54bb3efe45d90c6d748441792ff10aa553498` |
| 桌面入口 | **K Studio R2（内部候选）**，沿用 launcher，图标已更新 |
| 已安装版本槽 | `r2-internal-05c-seq5`，旧槽保留 |
| 私有对照页 | `owner-review/index.html`，原图/r5/r8，含模型链接 |
| 最终原生模型 | `13-final-download-rerun/downloaded.skp`，root21/r8；原图和 SKP 不公开 |

安装使用内部测试更新签名，不是 Authenticode 或生产更新信任。ZIP 内不含作者 API、项目或 Codex 订阅；SketchUp 不在包内。原用户加密 BAI 配置仍可用；独立新 profile 实际为空 API。

## 本轮解决和验证

- 修复 Windows GUI 启动 Node 未采用已启用 HTTP 代理导致 BAI 超时。只使用已有静态代理设置，保持 localhost 绕过；不关闭 TLS 校验、不改系统代理。无 Key `/models` 对照：直连超时，按新设置返回预期 401；真正完成付费建模续写是另一个独立证据。
- 实际页面同一 BAI 模型讨论、规划、批准、生成 r5，再局部修改到 r8。最后一次编辑 561.97 秒，三个成功写入，实际五次上下文裁剪。83 个观察请求事件包括首轮和后续失败，6 次用量未知；没有供应商账单，费用不伪报为零。
- r5 与 r8 均实际浏览器下载及宿主原生重开，深层几何/材质一致。r8 相比 r5 仅木饰面组改变，14 个其他部件深层哈希不变。
- 新版 UI 能明确选择当前会话的 SU 窗口。实际两个 SU2024 进程、两个会话分别绑定；前台切换不串线；关闭一窗后其会话失联，不改连另一窗。
- 实际冻结更新器 build04→05c，207 个受保护 profile 文件保持原字节。历史 bridge 指向外部 build 目录，未冒称自动迁移：宿主备份后明确修复其 command/cwd。
- 包内实际 SDK/Node 初始化通过，13 个原生工具可加载；无推理探针不能替代建模结果。网络改动定向 41 项通过；已有其他工程和云端证据保留。Windows 全量检查仍有 14 项缺 Blender 的失败，不能声称全量本机绿灯；远端完整回归是另一环境。

完整真实证据：[首次建模](../test-results/windows/2026-11-05-bai-stair-building-first-pass/README.md)、[已安装版局部编辑与连接](../test-results/windows/2026-11-05-installed-bai-edit-and-connections/README.md)、[网络修复](../execution/R2_PROVIDER_NETWORK_20261105.md)。

## 不能省略的限制

外观仍为 **PARTIAL**：楼梯过宽、玻璃盒体错落不足、木面平直且缺板缝；建筑规范/结构安全没有独立认证。规划仍有四次失败修正，编辑有两次暂时过期心跳拒绝后恢复；一次完整链路不能证明任意 API 或无限规模稳定。

仅当前 SU2024/Windows 已有真实证据；其他版本和真正干净第二台电脑未验收。正式签名、公开更新渠道、对应源码/重分发条件尚未闭合，许可证仍 `REVIEW_REQUIRED`。新源材料已补入包，但取得源码不等于完成发行义务。

本机 BYOK 试用不需要登录或支付。若上线平台账户/充值，则还需要真实域名、部署主机、IdP 和商户；手机号/微信/QQ、微信支付/支付宝没有被本轮悄悄开通。见[最少外部步骤](../execution/PUBLIC_BETA_BLOCKERS.md)。未生产收费、未部署公网、未合并 main。
