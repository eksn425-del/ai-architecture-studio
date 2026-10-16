from pathlib import Path
import sys,json,shutil,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';O=D/'circulation-preparation';notes=P/'runtime/agent_workspace/notes'
assert json.loads((O/'validation.json').read_text(encoding='utf8'))['status']=='valid'
assert json.loads((D/'r12-native-delivery-verification.json').read_text(encoding='utf8'))['status']=='PASS_WITH_DECLARED_PRECISION'
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf8'));assert session['status']=='ready' and session['ruby_state']['glass_curved_roof']['revision']==12
assert any(json.loads(s).get('event')=='project_budget_finished' for s in (P/'runtime/agent_events/a6bed0e29b0a42c8a756c08c2e09bf1b.jsonl').read_text(encoding='utf8').splitlines())
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((O/'authorization-prepared.json').read_text(encoding='utf8'));assert Path(i['model_path']).resolve()==Path(policy['model_path']).resolve() and not i['active_context']
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'Wrong GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Wrong revision' unless r.get_attribute('sketchup_architect','revision')==12
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
{revision:12,root_pid:20606,geometry_writes:0,targets:rows}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('PATHS',json.dumps(json.dumps(policy['allowed_paths']))).replace('CREATES',json.dumps(json.dumps(policy['allowed_creation_paths'])))
f=_generated_script_dir()/('studio-circulation-activation-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only verify 31 existing and two exact absent circulation targets'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-target-verification-r12.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
backup=O/'workspace-before';assert not backup.exists();shutil.copytree(notes,backup/'notes');shutil.copy2(P/'runtime/active_edit_scope.json',O/'original-active-edit-scope.json')
model=P/'outputs/model/blank-disposable-r12-before-exterior-circulation-20261016.skp';assert not model.exists();shutil.copy2(D/'r12-record/models/r12-actual-browser-download.skp',model)
for n in ['design_graph.json','buildplan.json']:shutil.copy2(O/n,notes/n)
reg=json.loads((O/'registration.json').read_text(encoding='utf8'));reg['status']='ACTIVE_NATIVE_VERIFIED_R11';reg['actual_target_verification']=v;(notes/'exterior-circulation-registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf8')
policy['status']='active';policy['model_guid_at_activation']=i['model_guid']
for path in [P/'runtime/active_edit_scope.json',notes/'local-edit-scope.json',O/'authorization-active.json']:path.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
(notes/'reconstruction_card.md').write_text('''# 当前外部连续补建卡｜r12→交通连接｜2026-10-16

同八整图、原项目/root20606，原r4/r10/r12版本不覆盖。所有者授权完成外部并合理推断未见细节，不等待旧草图选择。围护四组在r11已提交、r12已修正西端中层门扇：40上厅窗跨及16真实敞开入口；已完成保护、保存下载重开，构造细分为源图约束估计，非测绘。继续外部交通，后续细网/长侧门窗/轻框，不是补一处后结案。

当前准确范围见local-edit-scope.json/exterior-circulation-registration.json：L2/L3两个实际平台容器、远端三层GALLERY_Z*_SIDE3板件，新增CIRCULATION_INTERNAL/END_STAIR_COMPLETION与CIRCULATION_EXTERNAL/REMOTE_END_EDGE_GUARDS。保持目标容器PID；已有72踏步、坡道本体、屋顶、楼板、刚补围护和其他构件均保护。不要把范围扩大到父组。

把外挑上层余段收回矩形外玻璃内，同时保留当前坡道端和环廊连接的内侧平段。端梯实际世界变换和每踏步顶面须读回，补离散支承/侧防护/落脚平台与地面接顺；三块远端格栅仅局部留需要的梯口/支承连接，保持槽外透空格栅与通路，不用实板替代。接入r12远端入口y7600..9600和上层15200..17400，平台要有真实支承/净空。未见细部参照原图5/7与相邻细白构造推断，不复制坡道端，不删拉索换取画面干净。

上一步进度程序只列根目录造成深层楼板/屋顶假缺失，真实14目标原生读回都存在；新代码补准确路径批量读取。历史错误收据保留。built只表示实际几何存在，不能当视觉通过。按当前八图与真实几何执行，勿因旧pending/needs_fix再重建受保护结构。

执行后做当前六视图、八原图及端梯/梯口/平台细部独立复核，原生通路/净空/支承控制、作用域审计、保存下载重开。本轮同时完成批准范围内所有长环廊、坡道两侧、平台及槽边细白网护栏；准确33目标是一个协调的外部交通系统，不要只补一个栏杆后停止。先验证一个真实细网组件，使用重复实例，避免每根丝都创建全新定义而超出原生物理实体上限。保留真实门口/栏杆开口、坡道当前世界方向，按实际局部/世界矩阵构造，不二次镜像。提交时使用完整登记的协调范围，所有已有目标容器PID保持。后续为实墙/玻璃、不透明带、长侧入口和进退关系。
''',encoding='utf8')
print('Activated31existing +2new exact circulation targets after r12 delivery; correct enclosure/roof/slabs/treads protected')
