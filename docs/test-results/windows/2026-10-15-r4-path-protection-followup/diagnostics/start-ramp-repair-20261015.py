from pathlib import Path
import sys,json,shutil,time,hashlib
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/ramp-repair-20261015';D.mkdir(exist_ok=True);P=R/'runtime/projects/architecture-project-4f0e4'
backup=R/'runtime/backups/20261015-r4-before-ramp-repair'
if not backup.exists():shutil.copytree(P,backup)
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));identity=ad.get_active_model_identity()
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf-8'))
assert identity['model_guid']==session['model_guid'];assert Path(identity['model_path']).resolve()==(P/session['model_path']).resolve()
fp=json.loads((D/'r4-before.json').read_text(encoding='utf-8')) if (D/'r4-before.json').exists() else ad.capture_native_deep_fingerprint(expected_model_path=Path(identity['model_path']),expected_guid=identity['model_guid'],root_pid=20606,output_path=D/'r4-before.json')
assert fp['document_geometry_material_sha256']=='b3fb8fbde6ae874a78570201b78dbd635072b9204ca9881c8972d189bfd14e10'
paths=[['RAMPS','RAMP_1'],['RAMPS','RAMP_3'],['CIRCULATION_EXTERNAL','RAMP_1_OUTER'],['CIRCULATION_EXTERNAL','RAMP_1_INNER'],['CIRCULATION_EXTERNAL','RAMP_3_OUTER'],['CIRCULATION_EXTERNAL','RAMP_3_INNER'],['CIRCULATION_EXTERNAL','LANDINGS']]
source='\n'.join([
 '# ARCHFLOW_GENERATED_SCRIPT',
 'require "json"',
 'load '+json.dumps((R/'app/path_scope_guard.rb').as_posix(),ensure_ascii=False),
 'load '+json.dumps((R/'tests/ruby/path_scope_guard_test.rb').as_posix(),ensure_ascii=False),
 'm=Sketchup.active_model',
 'raise "Wrong GUID" unless m.guid=='+json.dumps(identity['model_guid']),
 'r=m.entities.find{|e| e.respond_to?(:persistent_id) && e.persistent_id==20606}',
 'paths=JSON.parse('+json.dumps(json.dumps(paths))+')',
 'a=KStudioPathScopeGuard.capture(r,paths)',
 'b=KStudioPathScopeGuard.capture(r,paths)',
 'receipt=KStudioPathScopeGuard.compare!(a,b,paths)',
 '{receipt:receipt,protected_snapshot:a,native_model_path:m.path,native_model_guid:m.guid,geometry_writes:0}'])
generated=_generated_script_dir()/f'studio-path-scope-readonly-{time.time_ns()}.rb';generated.write_text(source,encoding='utf-8')
raw=ad.client.call('sketchup_eval_project_file',{'script_path':str(generated),'operation_name':'READ ONLY exact-path native guard and negative contracts'})
if isinstance(raw,dict) and 'result' in raw:raw=raw['result']
if isinstance(raw,str):raw=json.loads(raw)
assert raw['receipt']['status']=='passed',str(raw)[:500]
(D/'path-scope-native-preflight.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
(D/'backup.json').write_text(json.dumps({'path':str(backup),'original_bytes_sha256':hashlib.sha256(Path(identity['model_path']).read_bytes()).hexdigest(),'identity':identity,'revision':4,'guard_paths':paths},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'backup':str(backup),'r4_baseline':'PASS','native_exact_path_guard':raw['receipt'],'ruby_negative_contracts':'PASS'},ensure_ascii=False))
