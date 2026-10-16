from pathlib import Path
import sys,json,shutil,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/basic-closeout-20261017';E=R/'runtime/exterior-completion-20261016';O=D/'site-preparation';notes=P/'runtime/agent_workspace/notes'
assert json.loads((O/'validation.json').read_text(encoding='utf8'))['status']=='valid'
assert json.loads((E/'r19-native-delivery-verification.json').read_text(encoding='utf8'))['status']=='PASS_WITH_DECLARED_PRECISION'
assert any(json.loads(x).get('event')=='project_budget_finished' for x in (P/'runtime/agent_events/b5c48124cbbc4cab9e4c9b094b2d7180.jsonl').read_text(encoding='utf8').splitlines())
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((O/'authorization-prepared.json').read_text(encoding='utf8'));assert Path(i['model_path']).resolve()==Path(policy['model_path']).resolve() and not i['active_context']
source='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Project/revision' unless r&&r.get_attribute('sketchup_architect','project_id')=='architecture-project-4f0e4'&&r.get_attribute('sketchup_architect','revision')==19
v=r.entities.select{|e|e.respond_to?(:name)&&e.name=='SITE_GROUND'};raise 'Site ambiguous' unless v.length==1;g=v.first;raise 'Site shared/locked/PID' unless g.persistent_id==76256&&g.definition.instances.length==1&&!g.locked?
raise 'Leaf exists' if g.entities.any?{|e|e.respond_to?(:name)&&e.name=='SIMPLE_SURROUNDINGS'}
old=g.entities.select{|e|e.respond_to?(:name)&&e.name=='ADJACENT_GROUND'};raise 'Original ground' unless old.length==1&&old.first.persistent_id==76258
{geometry_writes:0,revision:19,root_pid:20606,site_parent_pid:g.persistent_id,new_leaf_absent:true,existing_ground_pid:old.first.persistent_id,ground_bounds_mm:[old.first.bounds.min.to_a.map(&:to_mm),old.first.bounds.max.to_a.map(&:to_mm)]}
'''.replace('GUID',json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-site-closeout-activation-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only site exact target and original ground before final environment'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-target-verification-r19.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
backup=O/'workspace-before';assert not backup.exists();shutil.copytree(notes,backup/'notes');shutil.copy2(P/'runtime/active_edit_scope.json',O/'original-active-edit-scope.json')
backupmodel=P/'outputs/model/blank-disposable-r19-before-basic-surroundings-20261017.skp';assert not backupmodel.exists();shutil.copy2(E/'r19-record/models/r19-actual-browser-download.skp',backupmodel)
for n in ['design_graph.json','buildplan.json']:shutil.copy2(O/n,notes/n)
registration=json.loads((O/'registration.json').read_text(encoding='utf8'));registration.update(status='ACTIVE_NATIVE_VERIFIED_R19',native_verification=v);(notes/'site-closeout-registration.json').write_text(json.dumps(registration,ensure_ascii=False,indent=2),encoding='utf8')
policy.update(status='active',model_guid_at_activation=i['model_guid'])
for p in [P/'runtime/active_edit_scope.json',notes/'local-edit-scope.json',O/'authorization-active.json']:p.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
sessionfile=P/'state/agent_session.json';old=sessionfile.read_bytes();(O/'agent-session-before-fresh-environment-context.json').write_bytes(old);session=json.loads(old);oldthread=session['thread_id'];session['thread_id']='';sessionfile.write_text(json.dumps(session,ensure_ascii=False,indent=2),encoding='utf8');(O/'fresh-context-receipt.json').write_text(json.dumps({'old_thread':oldthread,'new_thread_pending':True,'reason':'Owner final bounded basic-surroundings task; avoid260kold context detail loop','same_project_sources_model_root':True,'source_or_usage_history_deleted':False,'local_caps_reset':False,'outer_model_changed':False,'prior_builder_input_recorded':107488248},indent=2),encoding='utf8')
(notes/'reconstruction_card.md').write_text('''# 所有者最终收尾2026-10-17：基本建筑保留，只补简洁周边，然后结束

所有者说当前已经差不多，不要再精细化构件，只完善基本门、窗、楼梯、墙、柱及周围环境，上传记录后结束本案例。不要继续旧无限质量攻坚。原八张整图/原顺序/architecture-project-4f0e4/root20606；原r4/19不可覆盖，已备份。实际网站Sol6.1Medium，外层不变。本地Token/工具/总时限0无限、全部累计历史107488248输入已保留；这是同项目新原生上下文，不是新案例、整栋重建或原版CLI对照。

持久script_id=glass_curved_roof，当前实际19；最新保存、浏览器下载、SU24三阶段声明精度一致已验证，rawstrictdoubleFAIL保留。基本建筑已经历真实门洞/窗框、入口通路、端梯/螺旋梯/支承、墙柱验证；19新增短托架216接触、平台18接触、216净空点、15天花V、25饰面、158软边通过。19独立Critic仍NEEDS_FIX横梁遮挡和帘幕显示；全模型还原并未完全通过，但所有者明确停止这类精修，不得再切梁板、改圆洞/帘幕或追细节。

唯一可写新叶SITE_GROUND/SIMPLE_SURROUNDINGS；准确父组PID76256唯一未锁，叶不存在；原ADJACENT_GROUND/PID76258完全保护。local-edit-scope.json给全部27KEEP，所有门窗楼梯墙柱/屋顶/坡道/楼板/内部都保持。只加这个新叶，别扩大SITE父组范围或改变旧地面。原生实际场地范围X[-12000,59000]Y[-9000,33000]mm，原地面顶Z=-280mm，建筑L0/坡道最低平台顶0mm。新铺地要真实落原地，必要厚度280mm到入口0标高，不能悬浮；别把旧原地面移到0。

在场地空余边缘补简单连续步道/入口连接，几块低矮绿地和4至6棵低细节示意树。原图01显示校园铺地/树木绿化，位置、树种、具体尺寸按现有场地合理推定，不需向所有者问选择。建议保留低坡道落脚区X[-8500,-6300]Y[-6200,-4000]、东侧端梯落脚区及各门前通路；树和绿地远离这些区域，不挡路不插柱。可用北侧外缘Y27000..33000及南/东侧空余带；步道连接现有入口。树干/树冠用真正共享原型，低面数即可，不做叶片、花坛细节、景观家具、灯具、相邻建筑或新渲染。沿用当前真实明暗80/15/Suntrue/noShadows，不改其他查看设置。

可用kstudio.custom_owned_ruby作简单场地实体和实例，既有SAIE/ADAI墙洞能力不适合树冠/绿地，记录选择理由，不装新库。批准一个有界环境提交，保护不变并核实路径连续、树落地、无阻门/坡道/端梯。只需当前新六视角+原图01周边/入口现场图交独立只读Critic，其他原八整图保持原始事实；不要再拍24个细部或对同一修订反复评审。不改reconstruction_evidence.json来塞施工计划，写notes/site_closeout_plan.json与qa。评审发现旧细节仍记NEEDS_FIX，不为它再追加几何。

完成后正常保存、给出清楚可下载模型和简短收尾说明；宿主会真实浏览器下载/SU2024重开/完整保护及三阶段一致性核验、上传GitHub。严格原程序空白重放及独立付费provider/客户发布测试保留NOT_RUN/未认证，不在这次结束前另开工作。付费API0，不启动新案例。场地做完本案例即结束。
''',encoding='utf8');print('Activated exact new surroundings leaf;27KEEP/basicbuilding frozen;19backedup; fresh native same-case context')
