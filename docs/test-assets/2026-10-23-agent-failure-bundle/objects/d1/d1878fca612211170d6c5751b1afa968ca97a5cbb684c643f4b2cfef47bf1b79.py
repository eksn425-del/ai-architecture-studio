import json
from pathlib import Path

def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

source='inputs/reference/4e52d9a057-source-target.png'
rows=[['BUILDING','TOWER','FACADE',f'TOWER_L{k:02d}'] for k in range(18)]
pockets=[['BUILDING','LEFT_STREET','ROOF','PLANTED_POCKETS',f'POCKET_{i}'] for i in range(2)]
targets=rows+pockets+[['BUILDING','TOWER','MODULE_PROTOTYPE','FRAME'],['BUILDING','TOWER','MODULE_PROTOTYPE','GLAZING'],['MODULE_FRONT_WALL'],['VEGETATION','BALCONY_INSTANCES']]
request={'scope':'tower_bay_rhythm_and_recessed_left_terrace_connections','approval':'latest_user_direct_execute','baseline_revision':11,'target_paths':targets,'notes':['保留18层主塔、各低翼既有层数与总体位置；只保留相连主体及自身绿化。','只原图为目标；另两张已直接检查，为旧模型缺陷定位。','原图顶部正面约6跨、右侧约5跨，可信度中高；位置/进深无实测，未见背面保持现状。']}
e=json.loads(Path('notes/reconstruction_evidence.json').read_text(encoding='utf-8'))
e['current_local_request']=request
e['hard_constraints']=['保留既有层数与总体位置。','本轮只修主塔可见两面分跨与左侧低翼退台凹入、连接。','外部环境维持已移除状态。','保留米色框架材质、深色下部材质和既有凹阳台深度构造。','完成两项后停止供用户检查。']
e['source_rhythm_observation']={'source_ref':source,'tower_front_bays':6,'tower_right_bays':5,'confidence':'medium_high','storeys':'keep existing 18; source reading approximately 18, medium','setback_direction':'lower toward negative X, low-wing outdoor spaces recessed toward positive Y and negative X','ratios':'tower 18 x 14.4 m and 56.9 m high retained; lower connected volumes 7/6/5/4 storey sequence retained; dimensions inferred','terrace':'rooms/side returns partly enclose planted outdoor pockets; no source-visible exterior stairs','unseen':'rear openings and internal circulation unknown; no new stairs inferred'}
e['user_confirmed'].append('最新请求授权修正主体分跨节奏、左侧退台凹入和连接，覆盖上一轮主体立面完全KEEP；层数及总体位置继续KEEP。')
e['source_comparison']['all_attached_images_inspected']=True
write_json('notes/reconstruction_evidence.json',e)
f=json.loads(Path('notes/facade_schedule.json').read_text(encoding='utf-8'))
f['current_local_request']=request
f['tower_bay_correction']={'source_ref':source,'front_bays':6,'right_bays':5,'front_pitch_mm':3000,'right_pitch_mm':2880,'dimensions_provenance':'inferred from retained envelope','storeys':18,'baseline_front_bays':5,'baseline_right_bays':4,'depth':'existing ~2m loggia returns retained as assemblies; width adapted to corrected axes'}
write_json('notes/facade_schedule.json',f)
s=json.loads(Path('notes/construction_strategy.json').read_text(encoding='utf-8'))
s['current_stage']='representative_module'
s['shared_parameters']['bay_width']={'value':3000,'units':'mm','provenance':'inferred','source':'source six front bays within retained 18000mm envelope'}
s['shared_parameters']['side_bay_width']={'value':2880,'units':'mm','provenance':'inferred','source':'source five right bays within retained 14400mm depth'}
s['shared_parameters']['scope']={'value':'tower visible 6/5 grid and recessed low-wing terrace connections','units':'text','provenance':'user_confirmed','source':'latest direct execution request'}
for ident,stage,role,paths in [('tower_rhythm_sample','representative_module','repetition',[rows[16]]),('tower_rhythm_replication','replication','opening_system',targets[:18]+targets[20:]),('left_recess_connections','variants','roof',pockets)]:
    s['systems'].append({'id':ident,'stage':stage,'role':role,'method':'custom_owned_ruby','method_id':'kstudio.custom_owned_ruby','selection_reason':'Verified SAIE straight-wall/opening helpers cannot transform retained multi-plane infill/loggia assemblies or edit nested terrace slab/guard profiles in place; new return walls belong to exact existing pocket leaves, whereas supplied SAIE creates root-level walls. ADAI explicitly disabled. Custom owned Ruby preserves semantic row/pocket PIDs.','status':'pending','depends_on':['bay_width','side_bay_width','storey_height','wall_thickness','slab_thickness'],'target_paths':paths,'verification_views':['front','right','roof','oblique'],'notes':['First verify one row, then replicate only after current independent review.','Keep rear row children untouched; preserve floor/roof/left-wing groups with native checks.']})
s['current_local_request']=request
write_json('notes/construction_strategy.json',s)
Path('notes/reconstruction_card.md').write_text('''# 主体分跨及退台局部修正

本轮按用户直接执行请求，在同一 terraced_apartment 根 PID19、r11 基础局部修改。已直接检查三张附件；仅第一张是建筑目标，两张旧模型截图只定位缺陷。无任务书、CAD、平面或其他目标视角。

原图锚点：塔顶约(666,294)，正面左边约(539,379)，右边约(774,341)；最高段可辨正面6跨、右侧5跨，可信度中高。保留现有18层、18×14.4m塔身及56900mm顶标高。分跨因此调整为正面3000、右侧2880mm，尺寸仍为估算。左向逐级降低，低翼保留7/6/5/4层次、原位置；原图低翼上方户外凹空间与房间及侧墙相包合，并非连续玻璃托盘。未见外楼梯，不新增楼梯。

先修TOWER_L16代表行，检查六/五跨、转角及楼板后再复制。既有凹阳台作为完整组件按新轴线缩宽、保持约2m进深及侧墙顶底板。分跨目标逐层为独立行容器；仅改FRONT/RIGHT/SIDE/LOGGIA，后立面原生子组原样。旧测试模块只清空FRAME/GLAZING、保留SLAB，独立样墙随末跨调整。左侧只改现有POCKET_0/1，减少外挑边，补回靠左楼的围护与凹入门窗、侧墙、顶底板和局部栏杆；保持屋面种植，避免树冠进入新增房间。

共同坐标：X向右，Y向后，Z向上；塔正面Y=0，右侧X=18000，后侧Y=14400。现测代表楼板边X50..17950/Y50..14350，厚220；独立样墙厚200；普通楼板比外皮内收50mm；格架外沿Y=-300/X18300，窗面Y100/X17900。修分跨不移动这些平面。保留塔MASSING/ROOF、测试SLAB、阶梯翼、左端楼及低翼主体立面、屋顶/退台绿化；阳台植栽仅随所属凹格移位。

方法 kstudio.custom_owned_ruby：SAIE直墙/开洞不能对既有多面阳台、窗格及露台剖面作嵌套原位变换；SAIE墙适配器创建于根，不能用于现有POCKET叶范围。ADAI已禁用。无OSS调用不计产品使用。

每次提交后获取当前六面、原图方向及局部图并独立复核，再决定必要局部修改。完成本轮两项即停，后部与隐藏连接仍属推断，不宣称整体保真验收。
''',encoding='utf-8')
with Path('notes/volume_inventory.md').open('a',encoding='utf-8') as out:
    out.write('\n\n## 当前分跨/低翼修正 r11 基线\n主塔18层/原轴线及所有主要体量位置不变。目标顶部正面约6跨、右面5跨（中高）；原生当前5/4。代表楼板X50..17950/Y50..14350/Z53580..53800，外皮内收50mm、厚220。低翼POCKET_0/1是本轮退台连接目标；其屋顶分别16600/19700，连接左端7层楼与4层沿街楼。只在既有轮廓内调整凹室、侧返与栏杆。源图背面/隐藏接缝无证据。全部外部场景保持空。\n')
print('Saved UTF-8 card and three JSON notes; local scope anchored at revision 11.')
