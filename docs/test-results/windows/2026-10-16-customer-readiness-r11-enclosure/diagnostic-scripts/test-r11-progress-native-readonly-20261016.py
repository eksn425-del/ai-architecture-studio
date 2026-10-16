from pathlib import Path
import json,sys,time
R=Path.cwd();sys.path.insert(0,str(R));from app.project_ruby import ProjectRubyExecutor
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from app.strategy_progress import collect_verified_strategy_paths,assess_strategy_progress
from app.construction_strategy import load_construction_strategy
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';mcp=ConfiguredSketchUpMCP(timeout_seconds=180);a=SketchUpAdapter(mcp);i=a.get_active_model_identity();state=json.loads((P/'runtime/project_ruby_state.json').read_text(encoding='utf8'))['scripts'];assert state['glass_curved_roof']['revision']==11
ex=ProjectRubyExecutor(R/'runtime',P.name,expected_model_path=Path(i['model_path']),expected_model_guid=i['model_guid'],mcp=mcp,ruby_state=state,adapter=a);strategy=load_construction_strategy(P,strict=True)
root=json.loads(ex.inspect_owned({'script_id':'glass_curved_roof','path':[],'offset':0,'limit':100})['contentItems'][0]['text']);assert root['objects_total']==len(root['objects']) and root['next_offset'] is None
rows=[]
def batch(paths):
 vals=ex.inspect_owned_batch('glass_curved_roof',paths);rows.extend(vals);return vals
start=time.monotonic();names=collect_verified_strategy_paths(strategy,[[v['name']] for v in root['objects']],batch);updated,report=assess_strategy_progress(strategy,script_id='glass_curved_roof',revision=11,root_pid=20606,named_paths=names,full_readback=True)
assert all(not x['missing_paths'] for x in report['systems'])
(D/'r11-native-progress-nested-probe.json').write_text(json.dumps({'status':'PASS_ACTUAL_NATIVE_READONLY','elapsed_ms':round((time.monotonic()-start)*1000),'geometry_writes':0,'persisted_project_strategy_changed':False,'root_only_old_receipt':state['glass_curved_roof']['last_strategy_progress'],'native_nested_snapshots':rows,'new_progress_report':report},ensure_ascii=False,indent=2),encoding='utf8');print('Actual native planned nested path readback PASS',len(rows),'nested targets, no missing paths; no notes/model mutation')
