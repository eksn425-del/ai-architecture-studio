# Visual QA — Quality v1 六视图别墅 1008

## Review contract

- 参考证据：六视图（同一栋建筑，前/背/东/西/屋顶/斜视）；本次为已建模型的局部家具位移，无新增参考图
- 当前模型修订：revision 4（改动前 revision 3）
- 必需视图：前 / 背 / 东 / 西 / 屋顶 / 斜视 — 本次改动为室内家具位移，不改变外轮廓与立面，
  故以斜视总览 + 客厅近景作为本次判定视图
- 工具成功、文件保存、几何非空均不等于视觉验收

## 本次改动核对（茶几 +100 mm X）

- 目标：`FURN_COFFEE_TABLE`、`FURN_COFFEE_TABLE_LEG` 沿 X 正方向平移 100 mm
- 结果：茶几 x 3500..4400 → 3600..4500；台腿 x 3850..4050 → 3950..4150；Y/Z 不变
- 茶几仍位于地毯范围（地毯 x 1100..4900）内，与沙发（x 1250..3300）、餐区（x 5600 起）无碰撞

## Deterministic readback

- 对象总数：171 → 171（未增未删）
- persistent_id 集合：完全一致（37863 … 44003）
- owned root 包围盒：38000 × 38000 × 7360 mm，改动前后一致
- 逐对象比对：仅上述 2 个对象包围盒变化，其余 169 个对象的名称、ID、min/max 全部一致
  （外墙、屋面、女儿墙压顶、门窗、栏板、格栅、雨篷台阶、其他家具均未变）
- 改动前后抽样核对（一致）：WALL_FRONT 0..10000 × 0..300 × 0..6700；
  ROOF_SLAB 50..9950 × 50..7950 × 6400..6700；PARAPET_CAP_FRONT -20..10020 mm；
  DOOR_SLIDER_L2_A 玻璃 2060..4040；WIN_REAR_01..06；FURN_SOFA_SEAT 1250..2350；
  FURN_DINING_TOP 5600..7400；ART_FRAME 5600..6700

## Critic result

NEEDS_FIX: NO（就本次位移要求而言）

### Highest-impact mismatches

1. 无 — 位移方向、距离与隔离性均与要求一致
2. 实体墙分段数量多（前墙 14 段），后续如需编辑洞口需按段处理 — 已知特性，非本次缺陷
3. 室内未划分功能房间，属既定简化范围

### KEEP — already correct, do not disturb

- 全部外轮廓、立面开洞、女儿墙与压顶、阳台栏板、遮阳格栅、入口雨篷台阶、其余家具与摆件

## Correction rounds

- Round 1: 无（本次为单点位移，一次通过；未触发返工）
- Round 2: 未使用

## 保存重试记录（revision 5）

- 触发方式：以只读核对脚本 `scripts/inspect_state.rb` 在同一 script_id（villa_replay）下执行 edit 提交，
  脚本内容不含任何创建 / 变换 / 删除调用，几何保持不动
- 事务回执：expected_revision 4 → script_revision 5，status = committed，
  模型路径 outputs/model/blank-disposable-20261008-153712.skp，时间 2026-10-08T08:20:10Z
- 只读核实：对象总数 171，persistent_id 37863…44003，root 包围盒 38000 × 38000 × 7360 mm（与 revision 4 相同）
- 茶几 `FURN_COFFEE_TABLE` 仍为 x 3600..4500 / y 1850..2700 / z 580..660 mm；
  台腿 `FURN_COFFEE_TABLE_LEG` 仍为 x 3950..4150 mm —— 未被再次移动，符合“不要再移动茶几”
- 抽检未变：ROOF_SLAB 50..9950 / 6400..6700；WALL_FRONT 0..10000 × 0..300 × 0..6700；
  PARAPET_CAP_FRONT -20..10020 / 7200..7260；DOOR_SLIDER_L2_A_GLASS 2060..4040；
  WIN_REAR_01..06；FURN_SOFA_SEAT 1250..2350；FURN_DINING_TOP 5600..7400
- 当前轮截图：outputs/renders/agent-view-a3b261f22f.png（revision 5），
  外轮廓、女儿墙压顶、门窗、阳台栏板、格栅、雨篷台阶与室内家具均与改动前一致
- 判定：NEEDS_FIX: NO（本轮无几何改动，仅重新提交保存）
