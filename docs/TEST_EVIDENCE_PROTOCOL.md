# K AI Studio — 每轮真实测试的 GitHub 证据交接协议

**从 2026-10-09 起适用于所有 Windows / SketchUp / Agent 真实测试。** 目的不是制造漂亮的 PASS，而是使另一端 ChatGPT 不用访问 Codex 本机，也能复查本轮实际模型质量、工程正确性、失败原因及版本变化。

## 永久规则

每一次有实质运行的测试都建立**新的**独立文件夹 `docs/test-results/windows/YYYY-MM-DD-<brief-slug>/`，只提交用户允许公开、脱敏后的真实文件。禁止覆写旧批次、复制上一轮截图当作新结果、在 Markdown 写本机不可访问的绝对路径冒充证据、删除 FAIL/PARTIAL、用 Agent 自审冒充独立 Critic、用缺失统计的 `0` 冒充实际 Token 数。

测试完成（包括 PARTIAL 或 FAIL）后，在该目录写清楚以下材料，并随代码**commit + push origin/main**，提供公开 GitHub 目录链接、结果 SHA 和后续未完成事项。不能上传某个材料时记录具体原因和 `NOT_RUN`，不允许凭空补造。

## 统一内容（推荐目录）

```text
docs/test-results/windows/YYYY-MM-DD-kai-integrated-v1/
  README.md                     # 中文结论与问题：PASS/PARTIAL/FAIL/NOT_RUN、源证据链接、截图索引
  run.json                      # 实际使用的模型与推理档、Git SHA、Windows/SU/bridge、成功/阻塞状态
  metrics.json                  # 每轮/总工具调用、失败数、writer 次数、耗时、input/output token（未提供=null）
  errors.json                   # 清洗的失败工具名称、原因、纠正方式（空列表=[]）
  source-perspective.png        # 实际 SU2024 来源角度（建模完成时）
  views/
    front.png
    front.evidence.json
    rear.png
    rear.evidence.json
    left.png
    left.evidence.json
    right.png
    right.evidence.json
    roof.png
    roof.evidence.json
    oblique.png
    oblique.evidence.json
  planning/
    reconstruction_evidence.json
    facade_schedule.json
    construction_strategy.json
    validation.json             # 含 schema 校验 PASS 或真实错误
  model/
    write-verifications.json    # 实际 committed writer receipts；失败事务要如实列出
    geometry-readback.json      # 数量/脚本 ID/根 persistent ID/尺寸和分页完整度
    keep-results.json           # KEEP ID/count/bounds 与 precommit negative evidence；如未跑写 NOT_RUN
    native-reopen.json          # 导出 SHA256、从下载版原生重开、鼠标/原生编辑+再保存读回
  review/
    critique.json               # actual reviewer.mode, issues, KEEP, source-matched views & revision
    review.md                   # 人看图片的缺陷、哪些源图可以直接对比、未解决问题
  artifacts.json                # 使用校验脚本生成的相对路径/大小/SHA256 清单
```

最小保留标准：每轮必须有 `README.md`, `run.json`, `metrics.json`, `errors.json`, `review/review.md`；如果有真实 geometry commit，必须保留当次最新 revision 的 **六张完整 PNG、各自的 canonical sidecar、source-perspective.png、writer receipts、readback/native-reopen**，不能仅提交 JSON 或报告。额外 Debug 截图和修正前后对照鼓励保留在该目录中。

**允许真实 PARTIAL/FAIL**：连接中断或未提交几何时，保留失败原因/运行日志并在 `run.json` 标记 `geometry_committed=false`、截图为 `NOT_RUN`；不要生成假的空白 PNG。

### run.json 最小字段

```json
{
  "schema_version": 1,
  "test_id": "2026-10-09-kai-integrated-v1",
  "status": "PARTIAL",
  "geometry_committed": true,
  "base_commit": "40-digit-tested-revision",
  "source_case": "test-assets/cloud-villa/villa-six-view-sheet.png",
  "model": {
    "requested": "GPT-6 Luna Max",
    "actual": "record-the-exact-runtime-reported-model",
    "reasoning_effort": "actual-value-or-null",
    "runtime": "codex-native-through-K-AI-Studio"
  },
  "environment": {
    "windows": "Windows release",
    "sketchup": "2024 / actual build",
    "bridge": "Kongxing version",
    "adai": "0.5.39, enabled/blocked/not_run"
  },
  "qa": {
    "reviewer_mode": "dedicated_read_only/agent_supplied/not_run",
    "fidelity_status": "PARTIAL",
    "needs_fix": true
  },
  "blockers": []
}
```

`model.actual` 必须是 **真实被调用的模型**，不能把用户请求的 Luna Max 名称直接抄作真实执行结果。如果 Codex 不支持此型号，选实际可用的最高能力型号，写清回退。

### metrics.json 最小字段

```json
{
  "schema_version": 1,
  "elapsed_ms": 550813,
  "tool_call_count": 45,
  "failed_tool_calls": 11,
  "committed_writes": 3,
  "full_root_rebuilds": 1,
  "targeted_corrections": 2,
  "input_tokens": null,
  "output_tokens": null,
  "critic_input_tokens": null,
  "critic_output_tokens": null,
  "human_geometry_edits": 0,
  "token_source": "not_available_from_runtime"
}
```

以上数字是**字段示例，不是新一轮成绩**；执行时必须全部替换为真实结果。Token 来源如果不提供，就写 `null` 并注明为什么；不要反推计费金额。需要记录阶段/每轮指标时可新增 `turns` 数组。

## 六视图真凭据

- 用当前运行的 host-certified `sketchup_capture_canonical_view` 捕捉全部 front/rear/left/right/roof/oblique。不能重命名任意相机伪装，也不能把旧 revision PNG 填进去。
- sidecar 至少包括 `canonical_view`、`model_revisions` 和真实 `camera`。同轮六张图都应对应**同一最新脚本版本**；如果不是，就截新图并说明。
- 有六视图源图时，逐面对照相同真实来源；源图存在自相矛盾时明确冲突，不能通过删证据宣称 1:1。
- `review/critique.json` 必须直接从真实质量门/独立只读 Critic 导出；若实际仅 Builder 自审，`reviewer_mode=agent_supplied`，视觉结论不能写独立 PASS。
- `KEEP` 至少校验 persistent ID/count/bounds；若只是工程负例，不把它等同于模型完成度。
- 真机可编辑性须从 **下载后的 SKP** 原生重开并完成实际编辑/再保存/再读回；不能仅靠 write receipt 宣称通过。

## 公共仓库安全边界

仓库为公开库。**严禁上传**：API keys、access/refresh tokens、浏览器/登录缓存、个人机器路径、用户私人图纸与未获许可参考图、私人 SKP/DWG、真实账户/通信信息、完整未脱敏模型对话；不要直接上传完整 runtime/ 或 .local/。公开测试可使用仓库已有的合成白色别墅图 `test-assets/cloud-villa/villa-six-view-sheet.png`。

每次上传前人工/自动检查敏感材料，并从真实运行导出仅必要脱敏结构化证据。GitHub 图片尺寸清晰可读，必要时附每个关键问题的 close-up，不要把本地 `.png` 链接只写在 Markdown 而不提交文件。

## 校验和交接

```powershell
python scripts/validate_test_evidence.py docs/test-results/windows/YYYY-MM-DD-kai-integrated-v1 --write-manifest
python scripts/validate_test_evidence.py docs/test-results/windows/YYYY-MM-DD-kai-integrated-v1
git status
git add app docs tests scripts
git commit -m "Record K AI Studio native modeling evidence and fixes"
git push origin main
git rev-parse HEAD
```

`--write-manifest` 生成/更新非机密证据文件的 SHA256 清单；第二次命令查漏、核对 PNG 类型/sidecar 对齐与清单哈希。缺少/损坏数据必须补采，不可为了验证通过复制空文件。如果确实无法完成，报告 `FAIL/BLOCKED` 和具体缺口，别凭空建文件。

ChatGPT 下一回合先读取该目录的报告/数值/真实 PNG、对照对应 commit 的代码，再决定下一次方法/质量改动；不会依赖 Codex 一句“完成测试”。

