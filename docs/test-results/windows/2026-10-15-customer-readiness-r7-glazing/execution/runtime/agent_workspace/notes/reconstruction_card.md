# 八图方向复核卡｜2026-10-14｜待用户确认

本轮仅核对原图、画草图和更新计划。未修改SketchUp；不是全量重建请求。

## KNOWN：图中观察／用户确认
- 八张原图全部面板已对照：1端部外观/实体模型，2场地轴测/斜视模型，3入口/外廊，4顶层/双层高室内，5横剖/底层平面，6四层分解示意，7三张平面，8气候/结构剖面。图片内的实体模型仍是原始参考，不是当前SketchUp。
- 整体是长条柱梁框架，上加木质空间；上部外玻璃扩出，内部围护与外皮之间有深环廊。格栅、横梁和下部退进可见。
- 图1坡道端：屋顶右侧更高、左侧较低、中部下垂；图2与图5/8支持横跨曲面沿长向延伸。外廊平檐是另一系统。
- 图1三段坡道的端部投影都向左上升，图3首段接架空平台；不能画成逐层交替左右爬升的简单之字。
- 图5/8显示四个使用标高，局部中间楼板与大挑空；图7中图给出挑空平面范围，图4显示双层高空间。顶层圆洞与这一大挑空分别定位。
- 用户要求先不改模型；屋顶右高、保留曲面及其他部分的约束持续有效。

## ASSUMED：草图约定与待核实拓扑
观察者站坡道短端，朝建筑长向看：X沿长向，Z向上；左为+Y（Y=20000），右为-Y（Y=0）。不是实际北向，当前模型轴/变换尚未原生核验。
原平面图左端旋转到草图下端；图7上/中/下暂标L3/L2/L1，图5下暂标L0。L2近坡道端左侧留大挑空，右侧及远端保留楼板；顶层较完整，另有圆洞。剖面穿过近端挑空，仅为关系示意。
拟定连续路径：地面右侧→坡道向左上升→L1左侧平台→环廊回到右侧下一段起点→L2、L3。各段坡向有图像依据；环廊到底绕哪条长边及转接净宽尚无完整连续路径证据，草图虚线标示，不当作测绘结论。

## ESTIMATED：仅保留旧估值
内框架约50×20m，外皮约58×28m，层标高约0/3.6/7.2/10.8m。源图无可读尺寸；屋顶曲率、最低点偏位、边高差、坡道长度/坡度与准确洞口位置仍待确定。不把旧roof_edge_a/b名称当成左右依据。

## 后续范围与构造候选
确认方向后仍以同一模型局部核查为目标：先核验原生身份、根和变换，再核对屋顶/支承及接缝；任何修改另按确认范围进行，不自动重建或调整坡道。
主体及楼板、屋顶和交通关系先于重复立面细节。历史候选：ADAI闭合洞口板/截面，组件复用框架和玻璃栏杆，SAIE普通直墙；已有曲面局部修正优先保留现有几何，具体变换待原生读回。每个方法均未在本轮执行。

## 文件与证据边界
草图：notes/direction_sketch.png（平面、横剖、坡道投影）；非实测、不按比例。
四份计划文件本轮重新写入UTF-8并校验。没有新增设计任务书、场地要求、URL或CAD；源建筑复核，不做场地/功能改编。
本轮无SketchUp读写工具；模型身份、当前提交、深层变换、下载/重开差异无法原生确认。历史保存前证据缺失及原生交付诊断标记BLOCKED，不编造修正成功。


## 2026-10-14 roof-only execution
User requests right high / left low from ramp end, retain curve; ramps and other parts untouched. Current native root 20606 advanced r2 to r3 by reflecting ROOF_TIMBER and its roof tension ties in place. Current ramp-end image confirms requested edge relation. 119 KEEP paths and 25 unrelated top-level groups passed host checks. Six certified views plus seven source cameras captured. Roof clearance and old ramp/gallery/interior discrepancies remain outside this edit. Save/download/reopen NOT_RUN in this turn. See qa/roof_edit_receipt.json; independent review completed: whole-model NEEDS_FIX for unchanged ramp handedness, floor/void and gallery. No further geometry edits within this roof-only request.


## Approved clearance edit, 2026-10-14
User now authorizes only connected end glass upper edges and frames to follow roof without gaps. Raise the roof middle about 1000mm using source section proportions, keep both unequal side endpoints and concavity; other assemblies protected. Geometry and joint checks pending.

## Ramp local edit 2026-10-15, r5
Source sheets 1/2 show all three runs rising screen left (+Y) from the matched ramp end. Corrected only run 1/3, their own rails and four existing landing containers. Run 3 shifted -2200mm X to avoid the fixed end gallery deck. This transverse offset and same-level return route are inferred. Second run, gallery slabs and rails, roof, glazing, floor structure and all unrelated systems passed deep scope/KEEP checks. Landing pad elevations meet ramp caps at 0/3600/7200/10800mm. Remaining gallery guards block return access: request to scope only their receiving gate ends was rejected by host authorization. Full route is therefore incomplete, no quality acceptance. CURRENT r5 six canonical and eight source camera pairs submitted for review. No current save/download/reopen tool available. See qa/ramp_edit_status.json.


Upper receiving doors r7: only NORTH_BAY_0 (two) and SOUTH_BAY_00 (one) cut to2200x2400mm clear openings inside existing rail gates. Module extents/mullions and all other assemblies retained. Source dimensions estimated. See upper_glazing_door_edit.md and qa/upper_glazing_door_receipt.json. Independent review pending.
