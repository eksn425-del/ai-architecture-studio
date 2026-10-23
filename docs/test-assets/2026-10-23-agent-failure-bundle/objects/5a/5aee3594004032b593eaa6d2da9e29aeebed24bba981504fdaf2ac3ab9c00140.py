import json
from pathlib import Path

def read(name):
    return json.loads(Path(name).read_text(encoding='utf-8-sig'))

def save(name, data):
    Path(name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

paths = [['ENVIRONMENT','CURBS',n] for n in ['BUILDING_SIDEWALK','FAR_CORNER_PAVEMENT','FOREGROUND_PAVEMENT','CURB_FRONT']]
paths += [['ENVIRONMENT','TRACKS'],['ENVIRONMENT','CONTACT_WIRES']]
keep = [['BUILDING'],['CONTEXT'],['MODULE_FRONT_WALL'],['VEGETATION'],['ENVIRONMENT','INTERSECTION']]
note = Path('notes/street_execution.md').read_text(encoding='utf-8')
Path('notes/reconstruction_card.md').write_text(note, encoding='utf-8')
e = read('notes/reconstruction_evidence.json')
e['sources'] = [
    {'path':'inputs/reference/4e52d9a057-source-target.png','kind':'exterior_image','role':'SOURCE TARGET','provenance':'observed','notes':['唯一原始建筑目标，单张街角透视。左前路缘和前景铺装圆鼻可见，轨道接地；圆角尺寸和全场地边界未知。']},
    {'path':'inputs/reference/3b597b9df4-06-round1-orbit-balcony-defects.png','kind':'exterior_image','role':'ISSUE LOCATION','provenance':'observed','notes':['历史r6阳台缺陷，不能复制为目标；已修阳台全部保留。']},
    {'path':'inputs/reference/53116483e2-09-round2-orbit-street-defects.png','kind':'exterior_image','role':'ISSUE LOCATION','provenance':'observed','notes':['历史r8街道缺陷定位；界面内小截图只辅助定位，不替代原建筑目标。']}
]
e['hard_constraints'] = ['仅修改街角路缘、轨道及接触线。','全部建筑、阳台及绿化保持原位原形。','保持同一自有根PID19和当前独立模型；不重建。','完成后复核并停止供用户检查。']
e['street_correction'] = {'provenance':'user_confirmed','source_ref':e['primary_source'],'target_paths':paths,'preserve_paths':keep,'observed':['原图路缘有圆弧转角；轨道位于地表。'],'inferred':['路缘半径4500/5000mm；线端按既有场地边界内收1800mm。'],'native_before':{'revision':8,'road_top_mm':-180,'rail_top_mm':75,'site_x_min_mm':-66000,'site_x_max_mm':60000}}
save('notes/reconstruction_evidence.json', e)
f=read('notes/facade_schedule.json')
f['current_local_request']={'scope':'street_only','building_facades':'KEEP','balconies':'KEEP','roofs':'KEEP','vegetation':'KEEP','target_paths':paths}
save('notes/facade_schedule.json',f)
s=read('notes/construction_strategy.json')
s['shared_parameters']['scope']={'value':'街角路缘圆弧、轨道贴地与线端内收；建筑阳台绿化全部保留','units':'text','provenance':'user_confirmed','source':'最新用户直接执行请求'}
s['shared_parameters']['environment_scope']={'value':'仅六个指定街道组；完成后停止','units':'text','provenance':'user_confirmed','source':'最新用户直接执行请求'}
for name,value in [('curb_radius',4500),('foreground_radius',5000),('endpoint_inset',1800),('rail_vertical_delta',-255)]:
    s['shared_parameters'][name]={'value':value,'units':'mm','provenance':'estimated' if name!='rail_vertical_delta' else 'observed','source':'原图圆弧形态结合现模读回；标高差由原生边界计算'}
s['systems'].append({'id':'street_corner_tracks_endpoints','stage':'finish','role':'site','method':'custom_owned_ruby','method_id':'kstudio.custom_owned_ruby','selection_reason':'SAIE installed adapters support straight walls and rectangular openings, not horizontal arc paving or rail/wire transforms. ADAI is disabled. Use guarded unique owned groups.','status':'pending','depends_on':['curb_radius','foreground_radius','endpoint_inset','rail_vertical_delta'],'target_paths':paths,'verification_views':['roof','front','left','right','oblique'],'notes':['先检查临楼代表圆弧，再完成同类转角。','保持全部建筑/阳台/绿化和原路面标线。','轨顶贴路面；线端全部在旧场地边界内。','当前六面及原图视角独立审查后停。']})
s['execution_binding']['notes']=['Verified live r8 root PID19 in same disposable model; current native GUID 48188fe4-229d-4418-876a-05f872913007.','Latest human street correction supersedes previous environment KEEP; all buildings/balconies/plants remain KEEP.']
save('notes/construction_strategy.json',s)
with Path('notes/volume_inventory.md').open('a',encoding='utf-8') as out:
    out.write('\n\n## 街道局部修正 r8 起点\n原图路缘弧线可见；三个附件角色与六个精确修改组详见 street_execution.md。当前建筑/阳台/绿化的包络、虚实、屋顶及连接全部 KEEP，不执行原立面待修项。主路顶 -180mm，旧轨顶 +75mm；改为同标高。轨/线端在原场地 X-66000..60000 内收1800mm。圆角4500/5000mm仅估算。\n')
print('Saved UTF-8 card, evidence, schedule, strategy and inventory; parsed JSON successfully.')
