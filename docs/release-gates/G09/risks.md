# G09 剩余风险

- **发行权利**。核对品牌、K Studio 及第一方连接器发行权，逐版本确认对应源码、LibreOffice／图像库／certifi、微软运行模块和实际资产。
- **历史资料**。旧授权八图案例存在可能识别工作站的档案路径片段。负责人需要确认其发布范围和最小化处理。新版工件排除该档案。
- **包内运行时**。当前 beta08 冻结程序实读 CPython 3.12.2／OpenSSL 3.0.13／Node 24.22.1，落后于官方安全版本。beta09 完整冻结包已核对 CPython 3.14.10、OpenSSL 3.5.9、Node 24.22.3 和官方 SDK 工具目录初始化。仍需核对已签名工件及客户链路。 [Python 安全发布](https://www.python.org/downloads/release/python-31216/) · [Node 安全发布](https://nodejs.org/en/blog/vulnerability/november-2026-security-releases) · [OpenSSL 版本说明](https://www.openssl-library.org/news/openssl-3.0-notes/)。

- **真机安全**。签名候选须从其实际启动流程确认受控工具和验证范围、隔离新用户与旧输入、运行依赖检查。内部 Ruby 运行仍属于当前 Windows 用户权限。
- **新版内嵌密码库**。独立构建输入中，标准库 OpenSSL 3.5.9 和 cryptography 50.0.1 内嵌的 OpenSSL 4.0.2 需与公告按入口核对。后者可升级到上游稳定 cryptography 50.0.2 自带的 OpenSSL 4.0.3。本次冻结保留原锁。桌面 cryptography 用于 Ed25519 更新签名验证。已检查 HTTPS 走 Python 标准库或 Node 两套 OpenSSL 3.5.9，PyOpenSSL 扩展未随包使用。未发现包内 4.0.2 的高危 DTLS 或中危共享 X.509 验证入口，也未发现 11 月涉及的 QUIC、CMS 和 AES-GCM-SIV 应用入口。 [OpenSSL 公告](https://www.openssl-library.org/news/timeline/) · [cryptography 版本说明](https://cryptography.io/en/50.0.2/changelog/)。
- **实际服务**。staging 核对身份、权限、管理员退款、跨用户、凭据撤销、出站限制、备份暴露和隐私流程。账户清除功能仍按业务规则保留必要交易和安全记录。
- **经营合规**。确认实际主体和适用 ICP 或经营许可、生成式 AI 备案或应用登记、生成标识、个人信息、账单/退款、发票及支持。
