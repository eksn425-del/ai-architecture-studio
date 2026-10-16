from pathlib import Path
import json,sys,shutil,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';O=D/'corner-jamb-preparation';notes=P/'runtime/agent_workspace/notes'
assert json.loads((O/'validation.json').read_text(encoding='utf8'))['status']=='valid'
assert json.loads((D/'r17-native-delivery-verification.json').read_text(encoding='utf8'))['status']=='PASS_WITH_DECLARED_PRECISION'
assert any(json.loads(x).get('event')=='project_budget_finished' for x in (P/'runtime/agent_events/221eef97d9ab4ee0959ba0bd72c2cc66.jsonl').read_text(encoding='utf8').splitlines())
assert json.loads((R/'runtime/owned-face-guard-20261016/actual-native-results3.json').read_text(encoding='utf8'))['status']=='PASS_NATIVE_SCOPED_FACE_DELETION'
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((O/'authorization-prepared.json').read_text(encoding='utf8'));assert Path(i['model_path']).resolve()==Path(policy['model_path']).resolve() and not i['active_context']
source='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==17
g=r;rows=[];['ENVELOPE_OUTER','OUTER_EAVE_VENTS'].each{|n|v=g.entities.select{|e|e.respond_to?(:name)&&e.name==n};raise 'Ambiguous parent' unless v.length==1;g=v.first;raise 'Shared/locked parent' unless !g.locked?&&g.definition.instances.length==1;rows<<{name:n,pid:g.persistent_id}}
raise 'New leaf already exists' if g.entities.any?{|e|e.respond_to?(:name)&&e.name=='NORTH_EAST_CORNER_JAMB'}
{geometry_writes:0,revision:17,root_pid:20606,unique_unlocked_parents:rows,new_leaf_absent:true,current_vent_component_count:g.entities.grep(Sketchup::ComponentInstance).length}
'''.replace('GUID',json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-corner-jamb-activation-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only missing corner jamb exact leaf and owned unique ancestors'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;assert v['current_vent_component_count']==38;(O/'native-target-verification-r17.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
backup=O/'workspace-before';assert not backup.exists();shutil.copytree(notes,backup/'notes');shutil.copy2(P/'runtime/active_edit_scope.json',O/'original-active-edit-scope.json')
model=P/'outputs/model/blank-disposable-r17-before-corner-jamb-20261016.skp';assert not model.exists();shutil.copy2(D/'r17-record/models/r17-actual-browser-download.skp',model)
for n in ['design_graph.json','buildplan.json']:shutil.copy2(O/n,notes/n)
reg=json.loads((O/'registration.json').read_text(encoding='utf8'));reg.update(status='ACTIVE_NATIVE_VERIFIED_R17',actual_native_verification=v);(notes/'corner-jamb-registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf8')
policy.update(status='active',model_guid_at_activation=i['model_guid'])
for p in [P/'runtime/active_edit_scope.json',notes/'local-edit-scope.json',O/'authorization-active.json']:p.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
(notes/'reconstruction_card.md').write_text('''# 当前施工：第17版外檐末跨缺失角竖框

原八张整图/原项目/root20606，实际17已网站保存、浏览器下载、SU2024重开3阶段声明精度通过；rawstrictFAIL与严格空白重放NOT_RUN保留，原r4/r17不覆盖。实际网站Sol6.1Medium、外层不变，本地Token/工具/总时间0无限，历史累计不清零。只补一个真实缺失叶，不重建建筑或换案例。

native-target-verification和corner-jamb-registration/local-edit-scope给唯一允许新叶ENVELOPE_OUTER/OUTER_EAVE_VENTS/NORTH_EAST_CORNER_JAMB，现有祖先原生唯一/未锁、叶不存在。全模型其他几何包括38现有玻璃开口、38外翻窗及其五金/屋顶/坡道/内部/旧框架全部深层KEEP，不能修改整个OUTER_EAVE_VENTS父组或把共享BAY做unique。

主机真实17探针228/228开口、152/152保留玻璃、38/38半透明片通过；铰点/撑杆连接151/152通过。唯一错误NORTH_BAY_19的STAY_1，起点53985,24000,12800mm不在任何实际原长/短边竖框内，终点53945,24340,12770已接窗框。原生成器每跨只建左立柱，末跨右边没有下一跨；短端竖框最后Y21200不到北角，确实漏了一根。只在新准确叶补X54000/Y24000、Z7200..13500mm的细白角竖框，约60mm断面按既有框格合理推断，让实际原横框与缺支承撑杆足座都接上。不得移动/重建已有窗扇、玻璃、撑杆或其他框件。原生检查支持实际端部接触，不是仅框框包围盒近似。

新增守卫修复了raw .erase!/clear!正则标点漏判。必要开孔只用erase_owned_faces.call(批准叶的准确路径,[face.persistent_id])，会检查所有面直接属于目标、共享全出现位置获批；先核实Face.area和valid?再删除。真实安全副本共享38叶正例和6负例通过，两个原生fixture误用已存在洞边重加face的失败保留并修复；当前不需删任何面，只加一个新竖框。不要重放旧17开窗脚本，它已经执行；已归档源SHA和原始失败完整保留。

当前全部八源图事实和SHA/顺序不变，notes/reconstruction_evidence.json禁止写施工进度/时间戳。施工记录另放notes/corner_jamb_plan.json/qa。独立Critic最新17本来就可复用同修订证据；不要无理由重拍同修订所有视图再复核，先读当前紧凑卡/准确scope/host_native_vents_r17_diagnosis即可施工。新模型18再做六视角+八原图对应与角竖框近景独立复核。内部天花/材料仍有差异，后续继续，不在这一叶偷偷切梁板。一次准确补建，保护核验后保存下载原生重开；整体任务继续。
''',encoding='utf8')
print('Activated one exact missing corner jamb; all38vent assemblies and existing frames protected;17immutable backup')
