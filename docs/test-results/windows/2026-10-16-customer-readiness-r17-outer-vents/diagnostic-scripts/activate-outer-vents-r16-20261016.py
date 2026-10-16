from pathlib import Path
import json,sys,shutil,time,hashlib
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';O=D/'outer-vents-preparation';notes=P/'runtime/agent_workspace/notes'
assert json.loads((O/'validation.json').read_text(encoding='utf8'))['status']=='valid'
assert json.loads((R/'runtime/shared-envelope-guard-20261016/native-copy-write-and-negative-rollback2.json').read_text(encoding='utf8'))['status']=='PASS_NATIVE_DISPOSABLE_SHARED_SCOPE'
assert json.loads((R/'runtime/shared-envelope-guard-20261016/production-restore-verification2.json').read_text(encoding='utf8'))['status']=='PASS'
s=json.loads((P/'state/agent_session.json').read_text(encoding='utf8'));assert s['status']=='ready' and s['ruby_state']['glass_curved_roof']['revision']==16
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((O/'authorization-prepared.json').read_text(encoding='utf8'));assert Path(i['model_path']).resolve()==Path(policy['model_path']).resolve() and not i['active_context']
src='''# ARCHFLOW_GENERATED_SCRIPT
load APP
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==16
paths=JSON.parse(PATHS);proofs=paths.map{|p|g=KStudioProfessionalHelpers.named_owned_group(r,p);{path:p,pid:g.persistent_id,definition:g.definition.name,locked:g.locked?}};raise 'Target count' unless proofs.size==38
leaf=KStudioProfessionalHelpers.named_owned_group(r,paths.first);proof=KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths);raise 'Occurrences' unless proof[:occurrences].length==38
env=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER']);raise 'New leaf exists' if env.entities.any?{|e|e.respond_to?(:name)&&e.name=='OUTER_EAVE_VENTS'};raise 'Shared creation parent' unless !env.locked?&&env.definition.instances.length==1
{geometry_writes:0,native_version:Sketchup.version,revision:16,root_pid:20606,actual_targets:proofs,actual_shared_proof:proof,new_leaf_absent:true,parent_pid:env.persistent_id}
'''
for k,v in [('APP',(R/'app/path_scope_guard.rb').as_posix()),('GUID',i['model_guid']),('PATHS',json.dumps(policy['shared_definition_edit_paths']))]:src=src.replace(k,json.dumps(v,ensure_ascii=False))
f=_generated_script_dir()/('studio-outer-vents-activation-'+str(time.time_ns())+'.rb');f.write_text(src,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only exact shared outer glass targets and missing vent leaf'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-target-verification-r16.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
backup=O/'workspace-before';assert not backup.exists();shutil.copytree(notes,backup/'notes');shutil.copy2(P/'runtime/active_edit_scope.json',O/'original-active-edit-scope.json')
model=P/'outputs/model/blank-disposable-r16-before-outer-vents-20261016.skp';assert not model.exists();shutil.copy2(D/'r16-record/models/r16-actual-browser-download.skp',model)
for n in ['design_graph.json','buildplan.json']:shutil.copy2(O/n,notes/n)
reg=json.loads((O/'registration.json').read_text(encoding='utf8'));reg.update(status='ACTIVE_NATIVE_VERIFIED_R16',actual_native_verification=v);(notes/'outer-vents-registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf8')
policy.update(status='active',model_guid_at_activation=i['model_guid'])
for path in [P/'runtime/active_edit_scope.json',notes/'local-edit-scope.json',O/'authorization-active.json']:path.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
(notes/'reconstruction_card.md').write_text('''# 当前连续施工：第16版后，补真实外翻通风檐片

原八张整图/原顺序/architecture-project-4f0e4/root20606，当前16，原r4/r16不可覆盖，备份已保存。实际Studio Sol6.1Medium、外层不变、Token/工具/总运行时间0无限，历史累计完整。本阶段一次有界主提交及必要既有恢复，不是整栋重建。不要恢复上一阶段内部/材质旧任务。

准确39路径与12KEEP在local-edit-scope.json和outer-vents-registration.json：38共同原型玻璃GLASS出现位置全获批，新增唯一叶ENVELOPE_OUTER/OUTER_EAVE_VENTS。现有全38共享叶必须保留同PID41323/变换/父跨框架；2个旧唯一西端门跨SOUTH_BAY_00/NORTH_BAY_0完整KEEP，防止遮挡已验证坡道门路。不能修改/做unique整个BAY、不能放宽ENV父组。

原图05上剖面缓冲区屋面外缘确有向下外翻透明开启片，像从檐口垂挂的斜窗；现有四缓冲区盖板只是内部浅斜覆盖，不能拿它当已还原此轮廓。图08蓝曲线是气流箭头，不是屋面构件。本轮依据此明确信息完成38跨的真实外檐开启扇、细框、铰接、撑杆和背后真实高位开口；数量和450mm向外/900mm向下及开口12600..13400mm是参考比例与现有尺度的合理推断，自己核对，不询问所有者选择。保持原曲屋顶与BUFFER_CANOPIES全部不变；新开启片在南侧Y<-4000、北侧Y>24000，避免放到室内或错误翻转。实际长边20跨宽2900，X=-4000+i2900；原玻璃本地X0..2900、Y0、Z7200..13500，已有横框12000/13500均不动。已打通门跨2个不参与本轮。

已补完shared_definition_edit_paths host显式白名单，真实SU24安全副本全38路径正例和7负例(无optin/缺一处/父组放宽/锁定/外部共享/额外共享跨/误改保护兄弟)验证回滚，生产16不变。clear_owned_contents.call(准确GLASS路径)现在仅在全出现位置获批、完整图fence下允许清空共有叶。38实际位置共用一个物理GLASS叶，清空/重建一次，所有38实例会正确继承；不要循环38次反复清空同一原型。新增每跨开启扇放新语义叶内，重复杆件/板片真正共享原型以保证完整原生250k唯一实体cap，不提高上限或截断审计。目标组容器身份保持，所有框/其他玻璃/屋顶/楼板/坡道/端梯/细网/内部/帘幕都由整文档fence保护。

同源证据reconstruction_evidence.json只放八图事实与推断，禁止追加施工进度/执行计划/时间戳导致QA反复失效；施工记录另放notes/outer_vents_plan.json，QA结果在qa。只读取当前必要紧凑卡、准确scope/registration、相关屋檐脚本和原图，避免反复枚举整栋旧细网。当前完整原生189016唯一实体/6865definitions，主新增应靠共享组件；上轮先因零向量/容量失败后真实修复，均保留。

六当前截图+八原图对应+原图05檐片轮廓和真实开口/铰点近景交独立只读Critic。保护审计、实际开口射线与铰点/撑杆接触、网站保存下载/SU24重开。16版source品质仍needs_fix(粗中心柱/室内暗/挑空透视)，不在本轮偷偷删梁板。中间层30x11m实际大洞存在且9/9开，不可只凭截图横梁重叠切整片楼板。主体外部先完成，再继续其他真实缺项；本阶段结束不是整体任务结束。
''',encoding='utf8')
print('Activated39verified exact targets and12KEEP; shared38prototype leaves once; r16saved backup unchanged')
