# Public local connector — R2

The candidate now includes first-party `connectors/sketchup/` and the console MCP
adapter `app/public_connector.py`, packaged as RBZ + KStudioConnector.exe. No
Kongxing plugin/server/node wrapper is included by the normal build. The private
trial build switch remains explicitly non-public, not a license grant.

Upstream evaluated: `zinin/sketchup-mcp2`, revision
`b8cdda790315fa6304c10b2e415c0aab8ea331b4`, MIT, inspected 2026-11-04. Its poll-on-
SketchUp-main-thread and nonblocking transport are useful reference patterns,
but its unrestricted eval/TCP listener without authentication is unsuitable as
the public protected writer. No source was copied. This small local-file IPC
adapter uses official SketchupExtension/UI.start_timer interfaces and leaves all
geometry implementation in the existing ProjectRuby/native helpers.

Pairing uses user/SYSTEM ACL, random HMAC secret, signed expiring requests and
signed receipts. It opens no network listener. Invalid queue entries are
quarantined, a process lock serializes native dispatch, and operation IDs retain
the initial request digest and document identity. RETURNED means transport
returned, not commit/save success. ProjectRuby's durable unresolved-write gate
blocks a different script ID too. Camera/export requests carry document path
and GUID; the wrong instance does not consume them.

This is not an OS Ruby sandbox. SketchUp Ruby runs as the user's SketchUp
process. A compromised same-user application can access its own pairing data;
filesystem ACL/HMAC do not prevent that. Agent write permission, source guards,
owned root/revision/KEEP and post-commit checkpoint remain mandatory.

Native health: actual SketchUp 24.0.484 / Ruby 3.2.2 / main thread / unique saved
test document verified. First failure was Windows backslashes in ROOT making
Dir.glob see no request files. Fixed by normalizing separators. A Chinese account
also exposed UTF-8 decoding of whoami output; the installer now decodes Windows
ANSI explicitly. Original failures remain in local evidence.

Six real native fixture cases passed after a fixture-only invalid project-ID
correction: before dispatch, transaction abort, lost reply after actual commit,
capture failure, disconnect after scheduled save, normal edit and disk reopen.
Each used a distinct disposable model, real ProjectRuby, two named groups,
deep geometry/material KEEP checks and durable host state. Unknown outcomes
blocked a different operation; no geometry was replayed. These are transport/
recovery tests, not image modeling quality or real end-user UX acceptance.
Private evidence: R2 job `native-faults-01` (fixture ID failures),
`native-faults-02/receipt.json`, per-case native fingerprints and model artifacts.

Candidate API range 2019–2027 is an evaluation range, not supported-version PASS.
Only SU2024 has the above native evidence. Installation on a clean different
computer and other SketchUp versions remains NOT_RUN. Initial plugin installation
requires SketchUp Extension Manager/restart; opening a model alone does not
install a missing extension. Existing plugins/settings are preserved.

本轮实际运行限定一个活动 SketchUp 2024 实例。相机/截图消息有显式文档路由；生成 Ruby 的内置文档守卫遇到不符实例会拒绝写入。多个 SU 进程同时消费同一配对队列的端到端自动选择没有验收，不宣传已支持无感多实例切换。

补充实际证据：`packaged-connector-paired.json` 是构建 EXE 的真实界面配对；`packaged-connector-check.json` 是更新程序版本后仍读取原配置的真实只读检查。冻结程序会为明确第一方配对解析当前安装槽旁的连接器 EXE，不改写原配对/凭据。`native-browser-download-reopen-02/receipt.json` 验证真实浏览器下载字节重开一致，并在导入的 owned copy 上继续 scoped edit，KEEP 保持一致。直接编辑下载目录的首次请求被正确拒绝，失败记录保留。
## Actual RBZ installation and restart, 2026-11-04

The controller installed the build04 RBZ through SketchUp 2024's actual Extension Manager, verified both installed Ruby files byte-for-byte against the RBZ, closed SketchUp normally and reopened the owned engineering fixture. The newly started SketchUp process answered the packaged connector's health request automatically, without a Ruby console reload. Receipt: local R2 job `native-rbz-manager-install.json`; RBZ SHA256 `abab443b198cb89da39eee78a4c7dd1aba43bf3cd02c4a57cc025c7e6c22ef5a`.

This is an existing-install update on the owner's machine, not clean-machine acceptance. Existing unrelated TT_Lib2/InstantRoadPro/SketchUcation startup warnings were dismissed without changing their configuration. SketchUp 2024 is the only version with this native evidence.
