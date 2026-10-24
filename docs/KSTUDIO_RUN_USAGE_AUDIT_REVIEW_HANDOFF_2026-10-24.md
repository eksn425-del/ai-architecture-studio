# K Studio 用量审计 review branch 交接

本次获准仅发布 `codex/run-usage-audit-20261024`，供独立审阅和后续 Codex 获取。该分支不是 main 或桌面安装更新，不代表生产安全认证、真实供应商质量/账单验收或上线许可。本文件在实际推送前提交；是否发布成功以远端分支精确 SHA 回读及独立发布回执为准。

## 代码与审阅范围

- 本轮代码基线：`41fee1ba1c13f8d737a99d3733edef276a0a02fd`。
- 首轮实现：`43993e1f9ade1b198a98b648399265011f022694`；首轮证据：`ba77193a89786835807e4d0536c0f3a029f6ed12`。
- 独立审阅修复：`6b5287b9e1c0a42fe030c91887edd39af0798423`。账本按唯一 attempt ID 覆盖，重复/冲突行显式未知；finished 回执的状态、模型及关键身份冲突持续保留，不由后续重复抹除；正常 started→finished 生命周期不误判。
- 该 review branch 还包含基线之前4个已检查的本地 Windows/Blender 修复，不能把 GitHub 新增范围误称为仅两个审计提交。

## 测试证据分层

最新审阅修复的聚焦离线测试为 **48 PASS**，相关回归为 **178 PASS / 1 SKIP**，零付费回放 PASS。没有在这次修复后再跑整套全量或原生建模。

此前完整回归 **1353 PASS / 38 FAIL / 19 SKIP**，同一38项失败均在未修改基线实际复现；它不是全绿结果。此前合成栏杆原生验收 **16/16 PASS** 使用脚本化 App Server 与实际本机 Blender，不能等同真实 LLM 推理或 SketchUp 验收。旧25/155项测试与旧原生结果属于此前版本事实，不借用为本次新全量验收。

[中文详细报告](test-results/windows/2026-10-24-run-usage-audit/README.md)、[可复核测试汇总及38项基线配对](test-results/windows/2026-10-24-run-usage-audit/test-summary.json)、[固定合成栏杆规格](test-results/windows/2026-10-24-run-usage-audit/RAIL_ACCEPTANCE.md)。原始用户日志、凭证、用户模型、录像、申请材料与私人路径清单不在此次新增公开范围。

## 使用与仍有阻塞

读取原 agent_events 与显式指定的原 ledger：`python scripts/audit_run_usage.py <trace.jsonl> --ledger <budget.json>`。零付费回放：`python scripts/replay_run_usage_audit.py --output <新的本地输出目录>`。回放费率和usage仅为合成常量。

真实账单未知保持null，HTTP数及内部重试未知不改成模型事件数。Codex Responses金额上限仍 **fail-closed**：尚无已验证的逐请求保守预留边界，不因分支发布关闭保护或沿用旧预算。本轮没有真实付费API/GPU请求、代理实施或原模型写入。

后续真实测试仍须另有具体 provider/model/account、新单次及总预算与可执行预留边界。main、桌面版本和用户服务不由本次分支发布改变；没有部署或自动合并。
