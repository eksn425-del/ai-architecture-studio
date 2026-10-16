from pathlib import Path
import sys,json,shutil,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';O=D/'facade-finishing-preparation';notes=P/'runtime/agent_workspace/notes'
assert json.loads((O/'validation.json').read_text(encoding='utf8'))['status']=='valid'
assert json.loads((D/'r13-native-delivery-verification.json').read_text(encoding='utf8'))['status']=='PASS_WITH_DECLARED_PRECISION'
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf8'));assert session['status']=='ready' and session['ruby_state']['glass_curved_roof']['revision']==13
assert any(json.loads(s).get('event')=='project_budget_finished' for s in (P/'runtime/agent_events/2f7a29ac0088417583d399b6db9aa660.jsonl').read_text(encoding='utf8').splitlines())
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((O/'authorization-prepared.json').read_text(encoding='utf8'));assert Path(i['model_path']).resolve()==Path(policy['model_path']).resolve() and not i['active_context']
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'Wrong GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Wrong revision' unless r.get_attribute('sketchup_architect','revision')==13
def es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def child(g,n);x=es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing or ambiguous '+n unless x.length==1;x.first;end
paths=JSON.parse(PATHS);creates=JSON.parse(CREATES);rows=paths.map do |path|
 g=r;path[0...-1].each{|n|g=child(g,n);raise 'Shared or locked ancestor' unless !g.locked?&&g.definition.instances.length==1}
 if creates.include?(path)
  raise 'Expected absent leaf' if es(g).any?{|e|e.respond_to?(:name)&&e.name==path[-1]};{path:path,absent:true,parent_pid:g.persistent_id}
 else
  leaf=child(g,path[-1]);raise 'Shared or locked target' unless !leaf.locked?&&leaf.definition.instances.length==1;{path:path,pid:leaf.persistent_id,bounds_mm:[leaf.bounds.min.to_a.map(&:to_mm),leaf.bounds.max.to_a.map(&:to_mm)]}
 end
end
{revision:13,root_pid:20606,geometry_writes:0,targets:rows}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('PATHS',json.dumps(json.dumps(policy['allowed_paths']))).replace('CREATES',json.dumps(json.dumps(policy['allowed_creation_paths'])))
f=_generated_script_dir()/('studio-circulation-activation-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only verify 44 existing and three exact absent facade targets'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-target-verification-r13.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
backup=O/'workspace-before';assert not backup.exists();shutil.copytree(notes,backup/'notes');shutil.copy2(P/'runtime/active_edit_scope.json',O/'original-active-edit-scope.json')
model=P/'outputs/model/blank-disposable-r13-before-facade-finishing-20261016.skp';assert not model.exists();shutil.copy2(D/'r13-record/models/r13-actual-browser-download.skp',model)
for n in ['design_graph.json','buildplan.json']:shutil.copy2(O/n,notes/n)
reg=json.loads((O/'registration.json').read_text(encoding='utf8'));reg['status']='ACTIVE_NATIVE_VERIFIED_R13';reg['actual_target_verification']=v;(notes/'exterior-facade-finishing-registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf8')
policy['status']='active';policy['model_guid_at_activation']=i['model_guid']
for path in [P/'runtime/active_edit_scope.json',notes/'local-edit-scope.json',O/'authorization-active.json']:path.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
(notes/'reconstruction_card.md').write_text('# 当前外部连续补建｜r13→长侧门窗与顶部收边\n\n原八张整图/原顺序、原项目/root20606，原r4/r13版本不可覆盖。实际只读报告notes/readonly_envelope_void_stair_r13.md和qa同名JSON已说明缺漏；不要重新进行一轮长达半小时的全栋只读诊断，使用新鲜原生精确目标读回与实际源图施工。\n\n当前准确47路径见local-edit-scope.json和exterior-facade-finishing-registration.json：40已有下部长侧玻璃叶组、4已有顶部盖板容器，新增内层分层框/门框语义叶LOWER_LONG_SIDE_FRAMING、房间前沿ROOM_FRONT_COMPLETION和上厅接口HALL_WINDOW_JOINTS。保留已有40立梃，准确容器PID不变，只改其中内容；所有新r13交通/细网、r11/r12端部/上厅玻璃及门、屋顶、楼板、结构与其余内容均受保护。没有授权重建整栋或改梁板。\n\n按原图3的真实出入口/混凝土门头与原图7的房间凹入口，补两长侧分层玻璃/门扇/窗扇及原有隔墙前沿，门只能落在实际楼板/环廊可达处；不要用整片固定玻璃挡在新门后面。保留正确玻璃与外层轮廓。四块100mm实盖板要发展为原图约束的轻框、次梁、覆盖分格与白色边带/收边，透明与不透明分区合理推断，不默认全玻璃或全格栅；维持现有高度/外轮廓，不能硬接到更高的曲面屋顶。上厅木柱接口、窗顶泛水等在新增HALL_WINDOW_JOINTS中合理补齐，不改变已验的上厅玻璃/六个入口。隐藏接法依据相邻构件推定并标记，不再停下来等所有者选细节。按准确原生局部/世界矩阵施工，复用适合的框/玻璃组件，避免全新重复定义。\n\n本阶段一次协调几何提交，至少六当前视角和八原图对应、长侧门窗/平台门槛/顶部支承近景独立复核与深层KEEP/作用域。后续主机另测原生洞口/实体/支承，保存下载重开；不把built当源图verified。本轮外层通风窗可合理登记待下一准确玻璃叶作用域，不得为安装窗而越权动受保护整片玻璃；后续将确证其叶路径，继续外部，而不是宣布结束。\n\n室内大挑空原生9/9点已存在，不能照前次图像批评删楼板。真实螺旋梯局部净空/扶手碰梁和桌面侵入洞口、200mm到达间隙留下一阶段准确楼梯/家具修复；保护全部梁板，优先按现有洞口合理调整梯段和连接。\n',encoding='utf8')
print('Activated44existing+3new facade targets after completed readonly diagnosis; current r13 backed up, exact geometry verification recorded')
