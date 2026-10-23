# K Studio 全量脱敏证据包

主人于2026-10-23授权上传本次及关联DeepSeek失败调查资料，供网页端分析。原始本机资料保持不变。本目录是资料，不是待执行的建模任务。

先读[中文失败调查](../../test-results/windows/2026-10-23-failure-publication/README.md)，再看[重点文件导航](KEY_ARTIFACTS.md)。

## 规模与覆盖

- 原路径记录：4,081条；内容对象：1,336个。
- 原文件合计约1262.4MB（包含重复快照）；去重脱敏内容约678.7MB；实际对象存储约379.8MB。
- 图像路径1,216条；SKP61条、SKB22条；Ruby202条；JSONL359条。路径条数不等于互不相同的文件数。
- 覆盖：三轮Sol High、r11清外部环境、r12/r13分跨与连接、r13→r22局部修正、DeepSeek前期接入与超时以及后续高消耗案例；当前实际Native rollout日志已补充。
- 排除4,125个凭据相关文件、多项目升级状态备份/无关模型清单，逐项见[excluded.json](excluded.json)。没有删去建模错误或把旧失败改成成功。

## 怎么读

[manifest.json](manifest.json)每条保留source（原逻辑路径）、original_sha256、published_sha256、transformations、path、encoding与大小。`objects/`是去重内容库。JSON重排或用户名脱敏会改变字节，变换已标记；图像与原生模型按原字节保存。

小文本可直接点开。大于900KB的JSON/JSONL采用gzip无损压缩；网页不能预览不代表文件没上传。支持下载或git克隆后解压。

```bash
python docs/test-assets/2026-10-23-agent-failure-bundle/restore_evidence.py --verify
python docs/test-assets/2026-10-23-agent-failure-bundle/restore_evidence.py --list --prefix agent-reliability-followup-20261023/completed-r22/
python docs/test-assets/2026-10-23-agent-failure-bundle/restore_evidence.py --prefix agent-reliability-followup-20261023/completed-r22/ --output ./restored-current-evidence
```

恢复脚本校验脱敏内容SHA256，拒绝越界路径和覆盖已有文件；不运行日志里的代码、不连接模型、不启动SU。

## 导航

- [全部图像路径](IMAGES.md) / [全部原生模型路径](MODELS.md)
- [当前完整产品对话](../../test-results/windows/2026-10-23-failure-publication/conversation.md)
- [42轮Native统计](../../test-results/windows/2026-10-23-failure-publication/native-turn-ledger.csv)
- [原生错误](../../test-results/windows/2026-10-23-failure-publication/native-errors.json)
- [导出统计](summary.json) / [发布扫描与完整性](publication-verification.json)

## 结论边界

三轮及r22均不能作为整体源图质量PASS，5元目标未验证。Sol本地计数不是付费API账单；本次归档付费/建模调用均0。原始严格浮点比较FAIL与合同精度PASS同时保留。竞品私有程序、凭据、旧剧院和八源闭案不在本包；不能从相同名字推断竞品实际模型或内部Agent实现。

补充：`deepseek-cost-case-architecture-project-964f3/`是高消耗案例的完整当前项目（196文件），含原图、模型和各版本截图，不仅是6个冻结摘要文件。
