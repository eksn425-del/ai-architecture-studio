# 安全、隐私与发行许可审查

固定评审基线为 PR27 / 6a8001c。安全结论、具体证据和失败保留规则见 [G09](G09/verdict.json)。

- **运行边界**。发行配置限定模型通过结构化几何工具改指定部件。K Studio 控制项目批准、原生文档、改动范围和未知回执。内部 Ruby 与 Windows 用户同权，文件代理和 Ruby 匹配规则不提供 OS 级隔离。实际用户链路、桌面签名和 staging 出站限制仍需验证。
- **密钥和用户数据**。个人 BYOK 默认保存在 Windows 本机，云同步需主动同意和设备绑定。私有数据清理撤销会话和云端凭据，同时保留账本与必要的身份／安全记录。按实际条款说明留存、导出、销户与服务商传送。新工件排除已公开的旧授权档案，历史不动。公开树扫描范围排除图片元数据、过大压缩成员和已消失的历史对象。
- **依赖版本**。旧 beta07 的 12 组命中仍保留，由官方稳定版替代相关依赖。Python 构建使用 [Windows 锁](../../packaging/desktop-windows-requirements.lock)。将 [npm 清单](../../packaging/harness-package.json) 和 [npm 锁](../../packaging/harness-package-lock.json) 复制进全新 E 盘目录，使用标准名称执行 npm ci --ignore-scripts。保留官方 Node 及 Python SDK 输入与 Windows GUI 适配前后 SHA。 [OSV 查询协议](https://google.github.io/osv.dev/post-v1-querybatch/) · [Pillow 13.0.0](https://pypi.org/project/pillow/13.0.0/) · [certifi 2026.10.18](https://pypi.org/project/certifi/2026.10.18/)。
- **实际 beta08**。655 项组件的 npm/PyPI 元数据与云端直接依赖共 659 项 OSV 查询无命中。实际程序未签名，内置 CPython 3.12.2、OpenSSL 3.0.13、Node 24.22.1 仍有上游安全更新。随后完整冻结的 beta09 已实读 Node 24.22.3、CPython 3.14.10、OpenSSL 3.5.9，官方 Harness 工具目录本机初始化成功。beta09 的 659 项 OSV 查询也无已知命中，范围同前。 [Node 安全公告](https://nodejs.org/en/blog/vulnerability/november-2026-security-releases) · [PSF 3.14.10](https://www.python.org/downloads/release/python-31410/) · [官方 Windows 构建运行时](https://docs.python.org/3.14/using/windows.html#the-nuget-org-packages)。

- **运行时细查**。官方 PSF 3.14.10 的标准库使用 OpenSSL 3.5.9。构建锁 cryptography 50.0.1 静态链接 OpenSSL 4.0.2，上游 50.0.2 已附 OpenSSL 4.0.3。OpenSSL 11 月 10 日新增低危公告的受影响协议/API 单独核对。Linux x86_64/Python 3.12 的临时候选解析 38 项软件依赖，OSV 无已知命中，仍需实际云镜像扫描。 [OpenSSL 公告](https://www.openssl-library.org/news/timeline/) · [cryptography 版本说明](https://cryptography.io/en/50.0.2/changelog/)。

- **beta09 载荷检查**。通用内部候选和隔离 QA 安装器已分别核对身份和签名，两者 SHA-256 不相同、载荷清单相同，均未签名。对 15,963 个冻结文本及 2 个连接器档案成员的有界检查未发现项目密钥或私有文件名。八处疑似字符串均来自官方依赖 wheel 示例或模型标识。PE/PYZ 内部未纳入文本规则。 [检测及安装包 SHA](G09/tests.json)。

- **内嵌 OpenSSL 入口**。beta09 的 cryptography 二进制与核对的 wheel 完全相同，桌面通过该库执行 Ed25519 验证。HTTPS 使用 CPython 标准库或 Node 的 3.5.9。评审范围内未发现 4.0.2 的高危 DTLS 或中危共享 X.509 验证入口，也未发现 11 月公告相关的 QUIC、CMS、AES-GCM-SIV 用法。 [OpenSSL 9 月公告](https://www.openssl-library.org/news/secadv/20260929.txt) · [OpenSSL 11 月公告](https://www.openssl-library.org/news/secadv/20261110.txt)。

- **再分发**。K Studio/第一方连接器发行权利、实际构建里的对应源代码、微软运行库、素材和开源声明仍为 REVIEW_REQUIRED。确认实际出包组件后签核。 [第三方说明](../../THIRD_PARTY_NOTICES.md)。
- **经营适用性**。负责人按实际主体、业务、目标地区和服务形态，确认经营许可或备案、生成式 AI 服务备案或应用登记、实际供应商及提供服务的可核验标识。结合云端及 BYOK 流程核对个人信息和生成标识。SKP 的具体适用范围和元数据格式待适用性核对。 [工信部门《互联网信息服务管理办法》](https://cqca.miit.gov.cn/zwgk/zcwj/flfg/art/2026/art_3aa3d50dbe1648fda74aeab4f39b2db1.html) · [生成式人工智能服务管理暂行办法](https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm) · [生成合成内容标识办法](https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm) · [GB 45438-2025](https://openstd.samr.gov.cn/bzgk/std/std_list?p.p2=GB+45438-2025) · [个人信息保护法](https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm)。
