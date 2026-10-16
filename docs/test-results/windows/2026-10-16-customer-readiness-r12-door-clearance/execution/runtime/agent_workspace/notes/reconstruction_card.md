# 当前执行：修正新建西端中层两扇门的回廊避让

同八图原项目/root20606当前r11。上一次围护已保存、实际下载并SU2024重开验证，原r4不变。本次只改local-edit-scope.json批准的两扇新门：ENVELOPE_OUTER/LOWER_END_WEST_ADDITION/LEVEL_7200_BAY_6/DOOR_LEFT_OPEN_90及DOOR_RIGHT_OPEN_90，均已原生核实唯一且未锁定。旧四组新增授权已被当前两扇既有门的精确范围取代。允许合理推断滑开方式，保留2200x2400洞口/门框/门槛和其余所有正确部分。

继续已保存scripts/clear_west_middle_entry.rb，检查滑开后实际侧向回廊净宽、门洞和板支承。两次旧scope拒绝没有提交新几何，当前仍r11；不要重建或再添加四组围护。当前批准及原生目标证明见west-entry-clearance-recovery.json。r11独立八图12对审查可复用；本轮修改后再做真实当前视角审查。

随后继续外部交通/端梯/格栅洞口、细网栏杆及立面实墙玻璃/进退关系，不在这两扇门修好后停止整个任务。

---
历史建筑状态仅供已建事实参考，旧执行范围不适用于本轮：
# 当前建筑执行卡｜2026-10-16｜外部连续补建

当前任务：所有者要求完成同八图建筑的可见外部，并允许依据相邻部分和原平剖关系推断未见处。不是停留在局部补丁、等待旧草图确认或重建整栋。最新外部巡查：exterior_completion_audit_r10.md。历史卡已完整保存在history/before-exterior-20261016-reconstruction_card.md，历史只读/屋顶单项限制不再是当前范围。

## 实际已建状态
原项目architecture-project-4f0e4，root20606，当前r10，原r4不可覆盖。原八图SHA/顺序不变，网站Sol6.1Medium、外层不变。原生已核查旧框架、五块楼板、曲面木屋顶、外层缓冲玻璃、三坡道、13块透空格栅、三处外层入口及两小洞护栏。built仅表示几何存在，全部源图保真尚未通过。完整MCP清单由host保留，实际屋顶/组变换以新读回为准。

## 当前有界补建
允许新增四个已原生核实缺失的准确叶组：ENVELOPE_OUTER/HALL_LONG_SOUTH_ADDITION、HALL_LONG_NORTH_ADDITION、LOWER_END_WEST_ADDITION、LOWER_END_EAST_ADDITION，详见local-edit-scope.json和exterior-enclosure-registration.json。补上顶层大厅两长边内层玻璃/细框（10800以上到实际屋顶边下缘），以及下部内退两短端分层围护/真实出入口。现有ROOF_SUPPORTS有端玻璃、木柱及边梁，没有两长侧上厅玻璃；不能把外围缓冲玻璃当作内层已完成。下部INNER_GLAZING只含两长边，无两短端。

根据实际屋顶高低边、木柱、楼板、原图与端部交通定位，禁止使用旧roof_low13800硬编码。源图没有可读尺寸：分格、框截面及未拍到的门窗分区都是一致估计。门洞必须落在真实楼板上，L2西端仅y11000..20000有板；远端现有核心区和直梯要避让，不能把入口封死或在既有实墙上重叠玻璃。保留敞开下外廊。

## 观察与推断
原图1/2外观、3入口/格栅、4室内侧窗、5/8剖面、6构造拆解、7三平面共同约束围护边界、退进和层级。原图内模型是参考物，不是当前SU。未见的反侧细分允许合理推断并记录，不能反复向所有者索取选择。原生现有坐标X长向、Z上；几何高低与方向从实际矩阵核对，不靠旧组名猜测。

## 当前保护与接续
本轮保留现有屋顶及端玻璃/木柱、旧框架、全部楼板/洞、既有内外玻璃和拉索、坡道/平台/格栅及内部。保护这批是为了安全完成围护；接续任务将另行精确授权上层平台、端梯/梯口、细网护栏、长侧门窗和轻框节点，不把未完成外部永久冻结。新叶组一次有界提交，修改后真实六视图/八图独立审查、原生间隙/门洞检查、保存下载重开。不能把有限目标改善当作整栋完成。


## Authorized enclosure additions, 2026-10-16
KNOWN: root20606/r10, body X0..50000/Y0..20000, levels0/3600/7200/10800, L2 west floor only Y11000..20000. Read existing world roof edges, never infer handedness from child-local bounds. Protect all existing geometry including opaque east core X47000..50000,Y13500..20000,Z0..3600. USER_CONFIRMED: add upper hall two long glass sides and missing lower-end enclosure with actual entries; roof/frame/floors and accepted assemblies stay. ESTIMATED: 2500mm matching side rhythm, 40mm new framing, 2400mm doorway height, 2000/2100/2200mm portal widths. ASSUMED: three access portals per upper long side; west end two portals at0/3600 and north-only at7200; east ground south portal only, upper two per level. Open door leaves show operability and leave empty passage; no threshold across portal. Reference panels1/2/3/4/5/7/8 constrain layers and entries, exact counts are inferred. See notes/enclosure_addition_scope.json and scripts/complete_inner_enclosures.rb.

## Current local correction result, r12
West intermediate entry two-leaf sliding correction committed in the SAME root20606. Exact target leaf PIDs169319/169458 retained; all non-target geometry protected by deep exact scope. Aperture2200x2400mm retained, leaf projection72mm, estimated local gallery clearance1578mm. All14 explicit KEEP paths verified. Current six canonical and15 source/detail pairs submitted to independent review. Existing upper landing projections, remote stairs/guards and facade material/partition differences remain outside this request. This result supersedes historical statements that the sliding correction was blocked. See notes/west_entry_sliding_current.md and qa/west_entry_sliding_r12.json.
