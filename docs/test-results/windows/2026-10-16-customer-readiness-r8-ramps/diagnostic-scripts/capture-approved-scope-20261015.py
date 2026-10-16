from pathlib import Path
import sys,json,time,argparse
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);parser.add_argument('--revision',type=int,required=True);a=parser.parse_args()
D=R/'runtime/customer-readiness-20261015';P=R/'runtime/projects/architecture-project-4f0e4';policy=json.loads((P/'runtime/active_edit_scope.json').read_text(encoding='utf-8'));ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));identity=ad.get_active_model_identity();assert Path(identity['model_path']).resolve()==Path(policy['model_path']).resolve()
source='\n'.join(['# ARCHFLOW_GENERATED_SCRIPT','require "json"',
 'load '+json.dumps((R/'app/path_scope_guard.rb').as_posix(),ensure_ascii=False),
 'load '+json.dumps((R/'tests/ruby/path_scope_guard_test.rb').as_posix(),ensure_ascii=False),
 'm=Sketchup.active_model','raise "Wrong GUID" unless m.guid=='+json.dumps(identity['model_guid']),
 'r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}',
 'raise "Unexpected native revision" unless r.get_attribute("sketchup_architect","revision")=='+str(a.revision),
 'p=JSON.parse('+json.dumps(json.dumps(policy['allowed_paths']))+')',
 '{collector:"KStudioPathScopeNative/1",revision:r.get_attribute("sketchup_architect","revision"),snapshot:KStudioPathScopeGuard.capture(r,p),geometry_writes:0,identity_proof:{collector:"KStudioOwnedGuidReadback/1",read_only:true,model_path:m.path,model_guid:m.guid,root_pid:r.persistent_id,project_id:r.get_attribute("sketchup_architect","project_id"),revision:r.get_attribute("sketchup_architect","revision")}}'])
f=_generated_script_dir()/f'studio-approved-scope-{time.time_ns()}.rb';f.write_text(source,encoding='utf-8');raw=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'READ ONLY approved exact scope '+a.label})
if isinstance(raw,dict) and 'result' in raw:raw=raw['result']
if isinstance(raw,str):raw=json.loads(raw)
assert raw['collector']=='KStudioPathScopeNative/1',str(raw)[:400]
dest=D/f'scope-{a.label}.json';assert not dest.exists();dest.write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','revision':raw['revision'],'file':dest.name,'geometry_writes':0}))
