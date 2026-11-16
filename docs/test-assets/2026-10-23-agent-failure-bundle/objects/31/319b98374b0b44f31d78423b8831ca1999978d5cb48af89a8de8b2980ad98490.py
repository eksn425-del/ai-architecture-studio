from pathlib import Path
import json

def load(name):
    return json.loads(Path(name).read_text(encoding='utf-8-sig'))

def save(name, value):
    Path(name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

scope=load('notes/facade_scope_current.json')
e=load('notes/reconstruction_evidence.json')
e['hard_constraints']=['保留现有18层、正面6跨/侧面5跨、总体位置和相连左翼的形体。','仅修正下部格架配色及塔楼原图可见的凹口/实墙位置。','不添加道路、邻楼或其他外部环境。','屋顶、退台和左侧口袋绿化保留；五组既有阳台植物随对应凹口调整。','完成本轮要求后停止供用户检查。']
e['local_facade_correction']={
 'baseline_revision':13,'root_pid':19,
 'source':'inputs/reference/4e52d9a057-source-target.png',
 'all_three_attachments_directly_inspected':True,
 'source_target_count':1,'historical_issue_images_count':2,
 'source_observed':['米色突出梁柱围绕凹入玻璃和浅色实墙；下部局部阴影不应解释成连续黑色格架。','低位转角种植凹口、较高转角凹口以及右端多处透空/阴影凹口可辨。','各凹口由相邻梁柱的同层斜线对应，不能只按图中像素高度横向平移。','屋顶平、退台向左降低，左翼相连；本轮均保持。','未见可确定的外部楼梯，原图无法证明背面和内部节点。'],
 'confidence':{'pale_grid':'high','lower_corner_pocket':'high','front_side_registration':'medium','exact_depth':'inferred','rear':'unseen'},
 'level_mapping_note':'层/跨编号按保留模型的0起始索引登记；单透视向现有18层框架配准为估算，不宣称原图有测量标注。',
 'common_coordinates_mm':{'front_finish_y':0,'right_finish_x':18000,'rear_finish_y':14400,'front_frame_y':-300,'right_frame_x':18300,'front_glass_y':100,'right_glass_x':17900,'wall_thickness':200,'slab_front_y':50,'slab_right_x':17950,'slab_rear_y':14350,'slab_thickness':220},
 'native_sample':'r13 L06 faces and slab corners reused from actual current native readback; new local recesses terminate under next 220mm slab at z+2880; ordinary floors remain 50mm inside exterior finish.',
 'corner_pocket':'Connected shared corner enclosure/ceiling/floor inside existing front infill leaf; matching right infill cleared to avoid a blocking perpendicular wall. Extent about2.7m is inferred for whole corner bay.',
 'qa_required':['six current host-certified views','source-direction overall','source-direction tower detail','side/rear inspection','independent review']}
save('notes/reconstruction_evidence.json',e)
f=load('notes/facade_schedule.json')
f['local_correction_current']={'baseline_revision':13,'front_bays':6,'side_bays':5,'storeys':18,'front_ops':scope['front_ops'],'side_ops':scope['side_ops'],'band':'only existing beam/column faces recolored; geometry unchanged','opening_dimensions_mm':{'ordinary_front_width':2670,'ordinary_side_width':2550,'typical_front_depth':1980,'typical_side_depth':1950,'corner_width':2785,'corner_depth':2665,'return':200,'guard':1100},'registration_confidence':'medium; source has one view only; concealed facades untouched'}
save('notes/facade_schedule.json',f)
s=load('notes/construction_strategy.json')
s['current_stage']='variants'
s['local_current']={'baseline_revision':13,'method_id':'kstudio.custom_owned_ruby','selection_reason':'SAIE wall/opening helpers create root-owned straight walls; they cannot recolor retained nested frame faces, reconcile existing exact infill leaves, or build a connected corner void in these protected existing containers. ADAI explicitly disabled. Custom Ruby edits only the supplied semantic leaves. No wrapped OSS call is claimed.','script':'scripts/facade_pattern_correction.rb','stages':['retain verified primary form and 6/5 sample from r13','native L06 wall/slab coordinate verification','no uniform facade replication: individual source-registered variants','recolor existing lower frame faces','current six/source/rear views plus independent review; stop when request complete'],'scope_file':'notes/facade_scope_current.json','preserve':'all massing, floors, roofs, left terrace joints and planting outside five named balcony instances; unaffected leaves protected by host'}
save('notes/construction_strategy.json',s)
Path('notes/reconstruction_card.md').write_text('''# 本轮立面局部修正（用户已直接授权执行）

同一独立模型 blank-disposable-20261022-173456，terraced_apartment，根PID19，基线r13。三张附件已直接检查；仅第一张是目标图，后两张是历史缺陷定位。

只将下部既有梁柱格架恢复米色，修正塔楼明显不对应的凹阳台及其相邻实墙格。保持18层、正面6跨/侧面5跨、楼板标高、总体位置和左侧连楼形体，不添加外部环境。原图低位种植转角凹口和较高转角凹口优先；侧面远端若干格应有全高凹入，原模型不应有大块浅色上封板堵住凹口。

单图的逐层配准为中等把握；具体见 facade_schedule.json 的 local_correction_current。深度、真实厚度和遮挡部分为估算，背面保持既有推定设计。屋顶/退台/左翼口袋植物均保持；仅五组阳台植物随凹口移位，且须检查实际建筑净空。原图没有可核对的外部楼梯，本轮不增建。

普通围护在Y0/X18000，楼板边Y50/X17950，背部楼板Y14350，厚220；格架外沿Y-300/X18300，墙厚200。已有r13模块和楼板侧后角实测不变；新凹口顶板接至下一楼板底z+2880。角部用一个相连凹空间，避免两组垂直侧墙互相封堵。

方法 kstudio.custom_owned_ruby：修改已存在的精确叶组，不重建楼体。现有SAIE直墙/开洞适配器不能在这些嵌套叶组内完成格架调色和转角组合凹口；ADAI禁用。不宣称OSS产品使用。

提交后取得当前六面、原图方向整体及细部、侧后观察和独立复核。只处理本轮要求，完成即停并报告仍有的视觉差异。未取得保存/重开回执前不宣称保存成功。
''',encoding='utf-8')
with Path('notes/volume_inventory.md').open('a',encoding='utf-8') as out:
    out.write('\n\n## Current r13 local facade correction\nAll primary volumes, 18 tower levels, 6/5 tower grid, left-wing pockets, roof silhouette and their positions are retained. Only existing lower beam/column face materials and identified tower infill leaves change. Low planted corner and upper corner voids are source-visible; exact level registration and corner depth remain estimates. No external stairs are source-observed. All off-site context stays absent by user request.\n')
print('Saved UTF-8 reconstruction card, evidence, facade schedule, strategy and volume inventory.')
