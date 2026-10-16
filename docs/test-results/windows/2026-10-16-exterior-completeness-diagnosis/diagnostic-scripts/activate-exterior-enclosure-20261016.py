from pathlib import Path
import sys,json,shutil,copy
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from app.construction_strategy import validate_construction_strategy_payload
from app.strategy_progress import assess_strategy_progress
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';O=D/'enclosure-preparation';notes=P/'runtime/agent_workspace/notes'
assert json.loads((O/'validation.json').read_text(encoding='utf8'))['status']=='valid'
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf8'));assert session['status']=='ready' and session['ruby_state']['glass_curved_roof']['revision']==10
ev=[json.loads(s) for s in (P/'runtime/agent_events/22189c6daadf40278dd59189d9d152af.jsonl').read_text(encoding='utf8').splitlines()];assert any(x.get('event')=='project_budget_finished' for x in ev),'Actual website turn must finish before activation'
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));i=a.get_active_model_identity();policy=json.loads((O/'authorization-prepared.json').read_text(encoding='utf8'));assert Path(i['model_path']).resolve()==Path(policy['model_path']).resolve() and not i['active_context']
backup=O/'workspace-before';assert not backup.exists();shutil.copytree(notes,backup/'notes');shutil.copy2(P/'runtime/active_edit_scope.json',O/'original-active-edit-scope.json')
model=P/'outputs/model/blank-disposable-r10-before-exterior-completion-20261016.skp';assert not model.exists();shutil.copy2(R/'runtime/customer-readiness-20261015/r10-record/models/r10-actual-browser-download.skp',model)
for n in ['design_graph.json','buildplan.json']:shutil.copy2(O/n,notes/n)
shutil.copy2(O/'registration.json',notes/'exterior-enclosure-registration.json')
policy['status']='active';policy['model_guid_at_activation']=i['model_guid']
for path in [P/'runtime/active_edit_scope.json',notes/'local-edit-scope.json',O/'authorization-active.json']:path.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
history=notes/'history';history.mkdir(exist_ok=True)
for n in ['reconstruction_card.md','volume_inventory.md','construction_strategy.json']:shutil.copy2(backup/'notes'/n,history/('before-exterior-20261016-'+n))
card='''# 当前建筑执行卡｜2026-10-16｜外部连续补建

当前任务：所有者要求完成同八图建筑的可见外部，并允许依据相邻部分和原平剖关系推断未见处。不是停留在局部补丁、等待旧草图确认或重建整栋。最新外部巡查：exterior_completion_audit_r10.md。历史卡已完整保存在history/before-exterior-20261016-reconstruction_card.md，历史只读/屋顶单项限制不再是当前范围。

## 实际已建状态
原项目architecture-project-4f0e4，root20606，当前r10，原r4不可覆盖。原八图SHA/顺序不变，网站Sol6.1Medium、外层不变。原生已核查旧框架、五块楼板、曲面木屋顶、外层缓冲玻璃、三坡道、13块透空格栅、三处外层入口及两小洞护栏。built仅表示几何存在，全部源图保真尚未通过。完整MCP清单由host保留，实际屋顶/组变换以新读回为准。

## 当前有界补建
唯一允许新增叶组ENVELOPE_OUTER/INNER_ENCLOSURE_COMPLETION，详见local-edit-scope.json和exterior-enclosure-registration.json。补上顶层大厅两长边内层玻璃/细框（10800以上到实际屋顶边下缘），以及下部内退两短端分层围护/真实出入口。现有ROOF_SUPPORTS有端玻璃、木柱及边梁，没有两长侧上厅玻璃；不能把外围缓冲玻璃当作内层已完成。下部INNER_GLAZING只含两长边，无两短端。

根据实际屋顶高低边、木柱、楼板、原图与端部交通定位，禁止使用旧roof_low13800硬编码。源图没有可读尺寸：分格、框截面及未拍到的门窗分区都是一致估计。门洞必须落在真实楼板上，L2西端仅y11000..20000有板；远端现有核心区和直梯要避让，不能把入口封死或在既有实墙上重叠玻璃。保留敞开下外廊。

## 观察与推断
原图1/2外观、3入口/格栅、4室内侧窗、5/8剖面、6构造拆解、7三平面共同约束围护边界、退进和层级。原图内模型是参考物，不是当前SU。未见的反侧细分允许合理推断并记录，不能反复向所有者索取选择。原生现有坐标X长向、Z上；几何高低与方向从实际矩阵核对，不靠旧组名猜测。

## 当前保护与接续
本轮保留现有屋顶及端玻璃/木柱、旧框架、全部楼板/洞、既有内外玻璃和拉索、坡道/平台/格栅及内部。保护这批是为了安全完成围护；接续任务将另行精确授权上层平台、端梯/梯口、细网护栏、长侧门窗和轻框节点，不把未完成外部永久冻结。新叶组一次有界提交，修改后真实六视图/八图独立审查、原生间隙/门洞检查、保存下载重开。不能把有限目标改善当作整栋完成。
'''
(notes/'reconstruction_card.md').write_text(card,encoding='utf8')
v=json.loads((D/'native-exterior-inventory.json').read_text(encoding='utf8'));paths=[x['path'] for x in v['groups']]
strategy=json.loads((backup/'notes/construction_strategy.json').read_text(encoding='utf8'))
mapping={'frame':[['STRUCTURE_EXISTING']],'floors':[['FLOORS',n] for n in ['L0','L1','L2_PARTIAL_SOUTH','L2_PARTIAL_EAST','L3']],'roof':[['ROOF_TIMBER','CURVED_SHELL']],'envelope_bounds':[['ENVELOPE_OUTER']],'ramps':[['RAMPS']],'module':[['ENVELOPE_OUTER','SOUTH_BAY_00'],['CIRCULATION_EXTERNAL','GALLERIES','LONG_RAIL_SOUTH_Z3600']],'repeat':[['ENVELOPE_OUTER','NORTH_BAY_0'],['ENVELOPE_OUTER','SOUTH_BAY_00']],'stairs_partitions':[['CIRCULATION_INTERNAL'],['INTERIOR']],'finish':[['SITE_GROUND'],['INTERIOR','FURNITURE_SIMPLIFIED']]}
for s in strategy['systems']:
 s['target_paths']=mapping[s['id']];s['notes']=['Actual r10 named paths corrected from MCP readback; built is geometry presence only. Historical strategy retained.']
 s['method_id']={'floors':'adai.profile_with_holes','ramps':'adai.profile'}.get(s['id'],'kstudio.custom_owned_ruby')
 s['selection_reason']='Existing perforated floor/ramp native profiles use the installed ADAI adapter; preserve actual committed ledger, no new donor invocation claimed.' if s['id'] in ['floors','ramps'] else 'Existing scoped transparent frames, repeated bars and retained native assemblies require guarded in-place Ruby; straight opaque SAIE walls do not fit this correction. Planned method is not proof of execution.'
 if s['id'] in ['envelope_bounds','module','stairs_partitions']:s['status']='needs_fix'
 else:s['status']='pending'
strategy['notes']=['Owner16Oct authorizes exterior completion and coherent unseen inference. Current card/scope supersede historic read-only roof-only notes.','Missing upper long-side and lower short-end inner enclosure first; then circulation and mesh.','Do not infer native geometry absence from old pending status or nonexistent historical target names.']
for param in strategy.get('shared_parameters',{}).values():
 if isinstance(param.get('source'),str):param['source']='Original source-based metric estimate, not surveyed; latest actual native geometry controls local fit.'
updated,report=assess_strategy_progress(strategy,script_id='glass_curved_roof',revision=10,root_pid=20606,named_paths=paths,full_readback=True)
report['source']='actual host MCP r10 inventory depth3; all listed strategy target paths genuinely present';(notes/'construction_strategy.json').write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding='utf8');(notes/'construction_progress.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');(O/'strategy-reconciliation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(notes/'volume_inventory.md').write_text('# Current source/model inventory r10\n\nFull real-site eight-source/four-side10-view diagnosis: exterior_completion_audit_r10.md. Native named paths verified by host. Actual present groups are geometry presence, not source-fidelity acceptance.\n\nMissing: upper hall two long-side inner glazing; lower two inner short-end enclosure/entrances. Unfinished: upper platform outline, remote end stairs/slots/guards, exterior fine mesh, long-side door variants and lightweight canopy/frame joints. Current phase exact new enclosure leaf only; subsequent coherent systems follow.\n\nOriginal r4 immutable, same eight source SHA/order. Hidden detail inference owner-authorized. Historical inventory retained in history/before-exterior-20261016-volume_inventory.md.\n',encoding='utf8')
print('Activated missing enclosure leaf; archived stale pending/readonly memory and reconciled actual named paths without visual promotion')
