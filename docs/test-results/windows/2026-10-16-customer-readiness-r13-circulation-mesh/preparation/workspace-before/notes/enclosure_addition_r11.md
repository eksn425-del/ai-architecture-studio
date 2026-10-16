# 已提交的内层围护补建

用户2026-10-16授权：补顶层两长边玻璃和下部两端围护，真实出入口接原楼板/交通；屋顶、结构、楼板及正确部分保留。原图八张全部面板已对照，直接依据1/2/3/4/5/7/8的内外层关系与平面交通；细分门数、门宽及开启表达为推断，不是源图测量。

## 第11版提交与独立可编辑组

- ENVELOPE_OUTER/HALL_LONG_SOUTH_ADDITION
- ENVELOPE_OUTER/HALL_LONG_NORTH_ADDITION
- ENVELOPE_OUTER/LOWER_END_WEST_ADDITION
- ENVELOPE_OUTER/LOWER_END_EAST_ADDITION

脚本 scripts/complete_inner_enclosures.rb。四个精确新增叶节点允许创建，原有95个围护子组及26个根级兄弟共121处KEEP。保护检查和提交后write_verification通过，根20606不变；完整回执及当前六视图/源图对见 qa/enclosure_addition_r11_receipt.json。OSS ledger committed_readback但events为空：仅受保护自定义几何，没有声称SAIE产品调用。

两侧上厅按2500mm原有木柱节奏各20跨，固定/门口模块为正式组件实例；读取屋顶真实世界坐标，玻璃/顶框接既有180mm边梁下，避免历史镜像的局部坐标混淆。下部端玻璃接原横梁下3180/6780/10380mm，基部接0/3600/7200mm楼板。没有封成新的整栋外盒。

共16处门洞：上厅两侧各3；西端0/3600mm各2，7200mm仅有楼板的北半侧1；东端底层1、3600/7200mm各2。宽2000/2100/2200、高2400mm，门洞没有横封玻璃及抬高门槛，双扇向外90度表达。每处门内侧已有楼板Face实际分类检查通过；此为局部落脚检查，不代表完整路线已通。东端底层Y13500..20000保留已有实心服务核，未在其表面覆盖假玻璃。

近景：outputs/renders/agent-view-147369b1fc.png（上厅门窗）、agent-view-a8e0812642.png（西端L2门洞）、agent-view-4006a02852.png（东端门洞）。屋顶、梁柱、室内板、坡道、平台、外格栅、旧玻璃及圆洞栏均保护。

## 全栋外部继续检查

仍有旧上层平台外伸约2200mm余段、远端直梯支承/扶手/上口与格栅冲突、外廊/坡道/平台缺细白网栏、旧长侧低层门窗缺细分及开启部分、缓冲顶盖缺细薄框格和节点。新增门口的接地不解决这些旧通路问题。主屋顶、主体结构和已建真实透空格栅不应整体重建。

## 持久化状态

提交补丁保留且有精确源哈希、范围、门位和当前证据。未经严格空白重放不提升为替代全量基线；本轮未销毁根、未更换模型、未做空白重建。文档及下载SKP保存由宿主在最终回复后处理。

## Independent review r11 completed
Whole-model NEEDS_FIX. Remaining exterior blockers: upper landing projections; intermediate stepped classroom-front enclosure/entrance returns; entrance concrete header and opaque spandrel bands not adequately expressed. These affect pre-existing long-side enclosure bays and broader interior room fronts, beyond the four missing enclosure leaves added this turn. New doors and glazing do not certify whole-building source fidelity. Old rail mesh, end stair/grid connection and canopy details also remain from direct audit. No speculative global material replacement or protected wall/slab edits made.

## Unapplied local clearance candidate
Post-review closeup identified west L2 north door leaves projecting1100mm into the narrow1650mm inner return. Proposed scripts/clear_west_middle_entry.rb parks these two leaves at72mm projection, retaining aperture/slabs. Both parent-bay and narrowed exact two-leaf guarded writer calls were refused before commit with Declared scope exceeds exact HOST-approved paths; do not widen to an ancestor. No geometry changed after r11. Existing 90-degree leaves remain; approximate550mm behind-leaf return clearance is insufficient. This is an unresolved new-door junction, not a completed circulation route. Candidate not promoted or applied; do not report sliding as built.


## Host clearance recovery now registered
The exact two new west L2 door leaves are now approved in local-edit-scope.json as existing targets; no creation, no broader parent. First rejected writer changed nothing. Re-read policy and retry the saved clear_west_middle_entry.rb with exact two leaf paths and KEEP of all unrelated geometry. Existing source-based opening/frame stays. This is authorized completion of the newly added entry, not a reason to pause.
