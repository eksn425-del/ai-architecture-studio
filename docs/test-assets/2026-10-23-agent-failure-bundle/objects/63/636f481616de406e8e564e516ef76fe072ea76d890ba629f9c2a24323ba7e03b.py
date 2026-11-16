import json
from pathlib import Path

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(p,d):
    Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

targets=[['CONTEXT'],['ENVIRONMENT'],['VEGETATION','STREET_INSTANCES']]
keep=[['BUILDING'],['MODULE_FRONT_WALL']]+[['VEGETATION',n] for n in ['ROOF_INSTANCES','TERRACE_INSTANCES','BALCONY_INSTANCES','LEFT_POCKET_INSTANCES']]
Path('notes/reconstruction_card.md').write_text(Path('notes/cleanup_execution.md').read_text(encoding='utf-8'),encoding='utf-8')
e=read('notes/reconstruction_evidence.json')
e['hard_constraints']=['仅清理独立邻楼和全部外部环境。','保留主体四段相连建筑、原形体、层数、格架及全部立面和阳台。','保留全部建筑自身阳台、露台、屋顶及低翼种植。','只在同一模型同根精确路径清空几何，不以隐藏代替移除。','完成后独立复核并停给用户检查，不处理既有建筑差异。']
e['user_confirmed'].append('最新请求覆盖历史环境保留：移除邻楼、道路、轨道、架空线、街树等，仅保留相连主体及建筑自身绿化，主体形体立面保持现状。')
e['environment_scope']={'provenance':'user_confirmed','state':'remove_external_geometry','target_paths':targets,'preserve_paths':keep,'notes':['本轮为主体展示范围调整；源图环境仍属源图事实，但不再属于交付范围。']}
e['current_local_request']={'scope':'extract_connected_building','target_paths':targets,'preserve_paths':keep,'approval':'latest_user_direct_execute','baseline_revision':10}
e['source_comparison'].update(source_target_view_count=1,issue_location_view_count=2,all_attached_images_inspected=True)
e['plan_turn']={'geometry_written_this_turn':False,'scope_approval':'latest_user_direct_execute','native_readback_this_turn':True}
write('notes/reconstruction_evidence.json',e)
f=read('notes/facade_schedule.json')
f['current_local_request']={'scope':'extract_connected_building','building_facades':'KEEP','balconies':'KEEP','roofs':'KEEP','building_vegetation':'KEEP','street_vegetation':'REMOVE','neighbor':'REMOVE','environment':'REMOVE','target_paths':targets,'preserve_paths':keep}
f['user_confirmed'].append('最新请求：主体形体和立面保持，外部环境与邻楼移除，保留建筑自身绿化。')
write('notes/facade_schedule.json',f)
s=read('notes/construction_strategy.json')
s['current_stage']='finish'
s['shared_parameters']['scope']={'value':'清理邻楼和外部环境；主体形体/立面/阳台及建筑绿化保持','units':'text','provenance':'user_confirmed','source':'最新用户直接执行请求'}
s['shared_parameters']['environment_scope']={'value':'CONTEXT、ENVIRONMENT、VEGETATION/STREET_INSTANCES仅清空几何','units':'text','provenance':'user_confirmed','source':'原生命名组核对与最新请求'}
s['systems']=[x for x in s['systems'] if x['id']!='extract_connected_building']
s['systems'].append({'id':'extract_connected_building','stage':'finish','role':'site','method':'custom_owned_ruby','method_id':'kstudio.custom_owned_ruby','selection_reason':'Remove existing native owned context only; installed SAIE straight wall/opening geometry helpers do not fit removal, and ADAI is disabled. No new roof/wall/opening/profile geometry.','status':'pending','depends_on':['scope','environment_scope'],'target_paths':targets,'verification_views':['front','rear','left','right','roof','oblique'],'notes':['Keep building, actual sample wall and all four attached planting domains with native deep fingerprints.','Clear only three exact existing groups, preserve target container PIDs.','Current independent source/canonical review required after write, then stop.']})
s['notes'].append('Latest execute request supersedes prior environment KEEP. Extract existing connected building without editing its geometry. See cleanup_execution.md.')
write('notes/construction_strategy.json',s)
with Path('notes/volume_inventory.md').open('a',encoding='utf-8') as out:
    out.write('\n\n## 最新主体提取任务｜r10基线\n四段主体BUILDING/TOWER、STEPPED_WING、LEFT_UPPER、LEFT_STREET及MODULE_FRONT_WALL全部保持；原阳台和屋面不改。保留VEGETATION下ROOF/TERRACE/BALCONY/LEFT_POCKET四个INSTANCES域。清理CONTEXT、ENVIRONMENT、VEGETATION/STREET_INSTANCES三组的全部几何。邻楼/街景源图存在，但按最新要求排除交付。详见cleanup_execution.md。\n')
print('Saved UTF-8 cleanup card, evidence, facade schedule, strategy and inventory; JSON parsed.')
