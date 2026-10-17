from pathlib import Path
import sys,json,time,argparse
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from scripts.audit_native_path_scope import validate_protected_graph
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--deep',action='store_true');p.add_argument('--expected-path');p.add_argument('--phase',default='before',choices=['before','after']);a=p.parse_args()
D=R/'runtime/su-trial-20261017';P=R/'runtime/projects/su-1017'
state=json.loads((P/'runtime/project_ruby_state.json').read_text(encoding='utf8'))
writer=state['scripts']['su1017_villa'];ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=ad.get_active_model_identity()
expected=Path(a.expected_path or state['model_path']).resolve()
if expected.is_relative_to((Path.home()/'Downloads').resolve()):
 import hashlib
 receipt=json.loads((D/'final-save-receipt.json').read_text(encoding='utf8'))
 assert hashlib.sha256(expected.read_bytes()).hexdigest()==receipt['download_candidate']['sha256']
else:
 assert expected.is_relative_to(D.resolve()) or expected==Path(state['model_path']).resolve()
assert Path(i['model_path']).resolve()==expected, 'Wrong live project'
dest=D/(a.label+'.json');assert not dest.exists()
if a.deep:
 v=ad.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=writer['root_pid'],output_path=dest,representation='definition_graph')
 print('Captured native complete graph:',a.label,'root',writer['root_pid'],'revision',writer['revision']);sys.exit()
policy=json.loads((P/'runtime/active_edit_scope.json').read_text(encoding='utf8'))
source='\n'.join(['# ARCHFLOW_GENERATED_SCRIPT; host read-only evidence',
 'load '+json.dumps((R/'app/path_scope_guard.rb').as_posix(),ensure_ascii=False),
 'm=Sketchup.active_model','raise "Wrong GUID" unless m.guid=='+json.dumps(i['model_guid']),
 'r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id=='+str(writer['root_pid'])+'}',
 'raise "Wrong project/revision" unless r && r.get_attribute("sketchup_architect","project_id")=="su-1017" && r.get_attribute("sketchup_architect","revision")=='+str(writer['revision']),
 'paths=JSON.parse('+json.dumps(json.dumps(policy['allowed_paths']))+')',
 '{collector:"KStudioPathScopeNative/1",revision:'+str(writer['revision'])+',geometry_writes:0,snapshot:KStudioPathScopeGuard.capture(r,paths,phase: :'+a.phase+'),identity_proof:{collector:"KStudioOwnedGuidReadback/1",read_only:true,model_path:m.path,model_guid:m.guid,root_pid:r.persistent_id,project_id:r.get_attribute("sketchup_architect","project_id"),revision:r.get_attribute("sketchup_architect","revision")}}'])
f=_generated_script_dir()/('studio-su-trial-readonly-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8')
v=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only SU trial native protection '+a.label});v=v.get('result',v)
if isinstance(v,str):v=json.loads(v)
assert v['geometry_writes']==0;validate_protected_graph(v['snapshot'])
dest.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print('Native exact scope captured and validated:',a.label,'revision',writer['revision'])
