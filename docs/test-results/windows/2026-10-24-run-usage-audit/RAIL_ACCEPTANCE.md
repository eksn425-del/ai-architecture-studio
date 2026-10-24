# 固定六栏杆局部修改规格

直接复用 `scripts/verify_cloud_blender_contracts.py::fixture_objects` 与 `scripts/verify_unified_codex_blender.py`。这是合成74对象 fixture，没有用户模型/图像；脚本化供应商输出必须明确标注，禁止后台写最终模型再称为 Agent 效果。几何写入仍经过现有 router/runtime/host工具和scope gate。

目标为 `bay_{floor}_{bay}_rail`，floor 为0/1/2，bay 为2/3，共6对象。原尺寸每块1.65×0.07×0.60米；修改为1.65×0.07×0.45米，中心Z减少0.075米，底缘保持不变。目标材质RGBA `[0.12,0.15,0.18,1]`。位置X/Y、宽深、ID不变。其他68对象，包括 `KEEP_neighbor`、背墙、玻璃、板、非目标栏杆，几何、材质和拓扑保持完全一致。

验收包含：无批准不写；越界更新/增加/删除拒绝；修改通过既有工具；6目标尺寸/底缘；68 KEEP 完整geometry相等；保存r1/r2；宿主原生重开和全新Blender进程独立重开数组一致；原r1文件hash不变；inspect-only不修改；原生receipt与发给脚本化peer的projection/原图像一致。r2真实发生再次编辑并保存，是合成原生对象可继续修改的证据，不代表 SketchUp GUI或真实LLM可编辑验收。

入口（使用电脑已有 Blender 可执行文件，将它的目录仅加入此shell的PATH，不安装/升级、不改系统PATH）：

```powershell
$env:PYTHONUTF8='1'
$env:LITELLM_LOCAL_MODEL_COST_MAP='True'
$env:ARCHFLOW_GENERATED_SCRIPT_DIR=Join-Path (Get-Location) '.test-runtime/generated-scripts'
# 先将已核实的现有Blender目录加入本次shell PATH
python scripts/verify_unified_codex_blender.py --output .test-runtime/rail-NEW
```

输出目录必须不存在或为空；不覆盖旧结果。Windows此处须使用进程级UTF-8模式，现有后端的默认GBK日志解码仍是已知本机限制，不更改系统区域或权限来消除。

本轮真实结果见 `rail-summary.json`：16/16检查通过，7脚本化turn、14 transport工具调用、13 runtime工具调用、6失败；这些计数互不改名为HTTP/模型请求。840输入/140输出是 fixture 常量，不是真实tokenizer或账单；付费调用未运行。日志/`.blend`/原生重开JSON/渲染原图保留于本地 `.test-runtime/rail-acceptance-utf8/`。
