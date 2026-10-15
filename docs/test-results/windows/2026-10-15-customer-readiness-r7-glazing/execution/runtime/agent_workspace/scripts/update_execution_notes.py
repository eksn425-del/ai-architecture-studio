from pathlib import Path
import json

base=Path(__file__).resolve().parent.parent
card='''# 已批准的八图还原计划 — 执行记录

用户已确认开始建模，用于课程汇报；主要结构、挑空、楼梯保留，家具简化，周边仅紧邻地面。

KNOWN：八张原图已逐图检查。图1上下为短端外观/模型；图2上下为轴测/模型；图3上下为入口/环廊；图4上下为顶层/双层室内；图5上下为横剖/底层平面；图6四层分解；图7三层平面；图8两张剖面。长条混凝土框架，上加木结构；玻璃外壳与内框架间有深环廊；上部外扩，下部内收；曲面屋顶沿短跨下垂、两边不等高，沿长向延伸。中间层左部大挑空，右部和南侧局部楼板。短端坡道、圆洞旋转楼梯和远端直梯均有来源。

ESTIMATED：内框架50×20米，外皮58×28米，环廊4米；10个5米结构跨。楼层0/3.6/7.2局部/10.8米；外围上层玻璃带7.2—13.5米；低位环廊3.6米。曲面最低约13.8米，边缘约15.5/16.5米。坡道宽2.2米，栏杆高1.1米。按平面约2.5:1与剖面层级估算，无精确测量。

ASSUMED：X长向、Y短向、Z向上；图1短端对应X=0，模型坐标不是真实方位。图5下暂对应L0，图7下/中/上对应L1/L2/L3。未见外观以剖面和平面约束推断。坡道折返连接平台，精确坡度与车道位置待截图核对；不作规范认证。

目标组：STRUCTURE_EXISTING、FLOORS、ROOF_TIMBER、EXTERNAL_ASSEMBLY、ENVELOPE_OUTER、CIRCULATION_INTERNAL、INTERIOR、SITE_GROUND。玻璃、框、栏杆、楼板、洞口、坡道、平台各自可编辑；重复幕墙与柱采用组件。

方法：启用的ADAI profile用于曲面屋顶、坡道和普通楼板；profile_with_holes用于完全内含的圆洞。SAIE wall用于直隔墙。玻璃薄片、框杆、旋转踏步和组件重复采用受保护Ruby：实墙布尔及单一二维型材不能表达它们的组合拓扑。实际调用以写入回执为准。

当前：空白可丢弃模型已读取确认；执行脚本已保存，等待首次提交及独立图像检查。准确曲率、室内圆洞位置、坡道折返细节仍待视觉校正。
'''
(base/'notes/reconstruction_card.md').write_text(card,encoding='utf-8')
strategy_path=base/'notes/construction_strategy.json'
data=json.loads(strategy_path.read_text(encoding='utf-8-sig'))
reasons={
 'frame':'Repeated observed concrete columns and beams require component instances rather than solid-wall helpers.',
 'floors':'Enabled verified ADAI profile_with_holes for interior circular openings; split profiles for boundary-connected atrium.',
 'roof':'Enabled verified ADAI yz profile extruded along X expresses observed asymmetric hanging short-span roof.',
 'ramps':'Enabled verified ADAI yz profiles express individual inclined runs with exact endpoint elevations.',
 'envelope_bounds':'Custom owned faces and frame components express transparent skin and separated deep buffer; solid SAIE wall does not fit.',
 'module':'One dimension-checked glass/frame component is repeated; glass and mullions remain independent.',
 'repeat':'Repeat verified dimensions with unique instance names; structural bays differ from glazing divisions.',
 'stairs_partitions':'Custom radial tread assemblies for spiral stairs; actual saie.wall for ordinary straight partitions.',
 'finish':'Simplified tables and adjacent ground only, as approved.'}
for s in data['systems']:
 s['selection_reason']=reasons.get(s['id'],'Source-constrained owned geometry.')
 s['notes']=['Execution approved. Each sibling has a unique semantic name. Visual verification remains pending.']
 s['status']='pending'
 if s['id']=='ramps': s['target_paths']=[['EXTERNAL_ASSEMBLY']]
for p in data.get('shared_parameters',{}).values():
 if isinstance(p,dict):p['source']='Approved estimates anchored by plan ratio and section storey relationships.'
data['notes']=['Approved first build; mm coordinates X long / Y short / Z up. Current six views and source-angle evidence required after commit.']
strategy_path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(base/'notes/volume_inventory.md').write_text('''# Source to model inventory
| Source | Observed system and proportion anchor | Exact named path | Status |
|---|---|---|---|
| 3,4 lower,5,6,8 | Concrete skeleton, plan 2.5:1, 10 bays | STRUCTURE_EXISTING | pending readback |
| 5,7,8 | Four levels; L2 large boundary-connected atrium | FLOORS | pending readback |
| 1,2,4 upper,5,6,8 | Short-span hanging roof, asymmetric edges, long extrusion | ROOF_TIMBER/CURVED_SHELL | pending readback |
| 1,2,3,5,6 | Deep buffer, upper box, lower inset, flat perimeter canopies | ENVELOPE_OUTER | pending readback |
| 1,2,3 upper,7 | Short-end folded ramp, landings to circulation levels | EXTERNAL_ASSEMBLY | pending readback |
| 4,5,7 | Circular void and spiral stairs, east end stair | CIRCULATION_INTERNAL | pending readback |
| 1,3,5 lower | Adjacent ground only | SITE_GROUND | pending readback |

Source camera pairs: short end (-X); end/long-side oblique (-X,-Y); entrance near short-end corner; long-side gallery underside; top floor interior; lower double-height interior; plan/section-informed unseen sides. No dimensioned CAD supplied. Primary silhouette and ramp connectivity outrank furniture.
''',encoding='utf-8')
print('UTF-8 execution notes saved; approved numeric estimates retained.')
