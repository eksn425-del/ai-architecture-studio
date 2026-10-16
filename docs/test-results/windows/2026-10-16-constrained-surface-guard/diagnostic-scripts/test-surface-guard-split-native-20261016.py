from pathlib import Path
import json,sys,time,shutil
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.native_stable_geometry import compare_stable_geometry
from scripts.audit_native_path_scope import validate_surface_protection
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/surface-guard-20261016';pf=P/'runtime/active_edit_scope.json';saved=pf.read_bytes();policy=json.loads((R/'runtime/exterior-completion-20261016/interior-finish-preparation/authorization-prepared.json').read_text(encoding='utf8'))
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=240));i=a.get_active_model_identity();working=Path(i['model_path']);assert working.name=='blank-disposable-customer-readiness-r4-20261015.skp';copy=working.with_name('blank-disposable-r18-surface-guard3-20261016.skp');assert not copy.exists();shutil.copy2(working,copy);policy.update(status='active',model_path=str(copy));results=[]
def open_(p):
 i=a.get_active_model_identity();a.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
def call(body,label):
 i=a.get_active_model_identity()
 setup='# ARCHFLOW_GENERATED_SCRIPT\nm=Sketchup.active_model;raise "Copy/GUID" unless m.guid=='+json.dumps(i['model_guid'])+'&&File.expand_path(m.path)==File.expand_path('+json.dumps(str(copy))+')\nr=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise "Revision" unless r.get_attribute("sketchup_architect","revision")==18\npolicy=JSON.parse('+json.dumps(json.dumps(policy,ensure_ascii=False),ensure_ascii=False)+');paths=policy["constrained_surface_edits"]["paths"]\n'
 source=setup+body;f=_generated_script_dir()/('studio-surface-split-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');(D/('split-'+label+'.rb')).write_text(source,encoding='utf8');start=time.monotonic();v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'One native constrained-surface case '+label});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;v['actual_call_elapsed_ms']=round((time.monotonic()-start)*1000);(D/('split-'+label+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');return v
try:
 open_(copy);pf.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
 loads='\n'.join('load '+json.dumps((R/'app'/n).as_posix(),ensure_ascii=False) for n in ['adopted_sketchup_helpers.rb','surface_edit_guard.rb','path_scope_graph_guard.rb','path_scope_guard.rb'])+'\n'
 positive=call(loads+'''before=KStudioPathScopeGuard.capture(r,paths)
floor=KStudioProfessionalHelpers.named_owned_group(r,['FLOORS','L0']);roof=KStudioProfessionalHelpers.named_owned_group(r,['ROOF_TIMBER','CURVED_SHELL']);top=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z>0.99};steel=m.materials['KS_White_Steel']
m.start_operation('Surface positive on disposable',true)
begin
 top.material=steel;top.back_material=steel
 roof.entities.grep(Sketchup::Edge).select{|e|policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)}.each{|e|e.soft=true;e.smooth=true}
 proof=KStudioPathScopeGuard.verify!(r,before,paths);raise 'Surface guard missing' unless proof['constrained_surface_edits'];m.commit_operation
rescue
 m.abort_operation;raise
end
{status:'PASS_NATIVE_SURFACE_POSITIVE',proof:proof,before_surface:before[:constrained_surface_edits],after_surface:KStudioSurfaceEditGuard.capture(r,policy),native_baseline_sha:KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256]}
''','positive')
 validate_surface_protection(positive['before_surface']);validate_surface_protection(positive['after_surface']);assert positive['before_surface']==positive['after_surface'];baseline=positive['native_baseline_sha']
 mutations={
 'vertex_shift':"floor.entities.transform_entities(Geom::Transformation.translation([1.mm,0,0]),floor.entities.to_a)",
 'face_reverse':'top.reverse!',
 'new_edge':'floor.entities.add_line([1000.mm,1000.mm,0],[1001.mm,1000.mm,0])',
 'unapproved_material':"floor.entities.grep(Sketchup::Face).find{|f|f.normal.z< -0.99}.material=steel",
 'hidden_seam':"roof.entities.grep(Sketchup::Edge).find{|e|policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)}.hidden=true",
 'unapproved_soft_edge':"roof.entities.grep(Sketchup::Edge).find{|e|!policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)}.soft=true",
 'unknown_mask_id':"wrong=Marshal.load(Marshal.dump(policy));wrong['constrained_surface_edits']['face_material_pids']<<9999999999;KStudioPathScopeGraphGuard.capture(r,paths,wrong)"}
 for label,mutation in mutations.items():
  body="floor=KStudioProfessionalHelpers.named_owned_group(r,['FLOORS','L0']);roof=KStudioProfessionalHelpers.named_owned_group(r,['ROOF_TIMBER','CURVED_SHELL']);top=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z>0.99};steel=m.materials['KS_White_Steel']\nbefore=KStudioPathScopeGuard.capture(r,paths);m.start_operation('Expected surface rejection',true);error=nil\nbegin\n"+mutation+"\nKStudioPathScopeGuard.verify!(r,before,paths)\nrescue=>e\nerror={class:e.class.name,message:e.message}\nensure\nm.abort_operation\nend\n{case:"+json.dumps(label)+",native_error:error,after_native_sha:KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256]}\n"
  v=call(body,label);assert v['native_error'],v;message=v['native_error']['message'];assert 'Protected geometry changed outside approved exact paths' in message or label=='unknown_mask_id' and 'Unknown or out-of-target surface face ID' in message,v;assert v['after_native_sha']==baseline,v;results.append(v);print('Actual native negative PASS',label,flush=True)
 (D/'split-results.json').write_text(json.dumps({'status':'PASS_NATIVE_CONSTRAINED_SURFACE_GUARD','native_version':'24.0.484','production_geometry_writes':0,'disposable_committed_operations':1,'native_fixture_eval_calls':1+len(results),'positive_surface_proof':positive['proof']['constrained_surface_edits'],'negative_cases':results,'raw_initial_failures_retained':['actual-failure.json','actual-failure2.json'],'limitation':'Safety-copy native guard proof, not website finish commit/source quality acceptance'},ensure_ascii=False,indent=2),encoding='utf8')
except Exception as e:
 (D/'split-failure.json').write_text(json.dumps({'status':'FAIL','actual_error':str(e),'completed_cases':results},ensure_ascii=False,indent=2),encoding='utf8');raise
finally:
 pf.write_bytes(saved);open_(working);i=a.get_active_model_identity();raw=a.capture_native_deep_fingerprint(expected_model_path=working,expected_guid=i['model_guid'],root_pid=20606,output_path=D/'production18-restored3.json',representation='definition_graph');old=json.loads((R/'runtime/exterior-completion-20261016/r18-graph-working-restored.json').read_text(encoding='utf8'));c=compare_stable_geometry(old,raw);assert c['status']=='PASS';(D/'production-restore3.json').write_text(json.dumps({'status':'PASS','native_equality':c,'active_policy_bytes_restored':pf.read_bytes()==saved,'production_geometry_writes':0},indent=2),encoding='utf8')
print('Actual native surface guard positive+7negativesPASS; production18restored')
