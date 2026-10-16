from pathlib import Path
import json,sys,time,shutil
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.native_stable_geometry import compare_stable_geometry
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/surface-guard-20261016';D.mkdir(exist_ok=True);pf=P/'runtime/active_edit_scope.json';saved=pf.read_bytes();O=R/'runtime/exterior-completion-20261016/interior-finish-preparation';policy=json.loads((O/'authorization-prepared.json').read_text(encoding='utf8'))
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=240));i=a.get_active_model_identity();working=Path(i['model_path']);assert working.name=='blank-disposable-customer-readiness-r4-20261015.skp';copy=working.with_name('blank-disposable-r18-surface-guard-20261016.skp');assert not copy.exists();shutil.copy2(working,copy);policy.update(status='active',model_path=str(copy));paths=policy['constrained_surface_edits']['paths']
def open_(p):
 i=a.get_active_model_identity();a.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
try:
 open_(copy);pf.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
 source='''# ARCHFLOW_GENERATED_SCRIPT
load HELPER
load SURFACE
load GRAPH
load GUARD
m=Sketchup.active_model;raise 'Wrong safe copy' unless File.expand_path(m.path)==File.expand_path(COPY)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==18
policy=JSON.parse(POLICY);paths=policy['constrained_surface_edits']['paths'];before=KStudioPathScopeGuard.capture(r,paths)
floor=KStudioProfessionalHelpers.named_owned_group(r,['FLOORS','L0']);roof=KStudioProfessionalHelpers.named_owned_group(r,['ROOF_TIMBER','CURVED_SHELL']);top=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z>0.99};steel=m.materials['KS_White_Steel']
m.start_operation('Surface positive: only approved material and seams',true)
begin
 top.material=steel;top.back_material=steel
 roof.entities.grep(Sketchup::Edge).select{|e|policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)}.each{|e|e.soft=true;e.smooth=true}
 positive=KStudioPathScopeGuard.verify!(r,before,paths);raise 'Surface guard not proven' unless positive['constrained_surface_edits']
 m.commit_operation
rescue
 m.abort_operation;raise
end
baseline=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];results=[]
['vertex_shift','face_reverse','new_edge','unapproved_material','hidden_seam','unapproved_soft_edge','unknown_mask_id'].each do |label|
 b=KStudioPathScopeGuard.capture(r,paths);m.start_operation('Expected constrained-surface abort '+label,true);error=nil
 begin
  case label
  when 'vertex_shift'
   floor.entities.transform_entities(Geom::Transformation.translation([1.mm,0,0]),floor.entities.to_a)
  when 'face_reverse'
   top.reverse!
  when 'new_edge'
   floor.entities.add_line([1000.mm,1000.mm,0],[1001.mm,1000.mm,0])
  when 'unapproved_material'
   bottom=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z< -0.99};bottom.material=steel
  when 'hidden_seam'
   edge=roof.entities.grep(Sketchup::Edge).find{|e|policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)};edge.hidden=true
  when 'unapproved_soft_edge'
   edge=roof.entities.grep(Sketchup::Edge).find{|e|!policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)};edge.soft=true
  when 'unknown_mask_id'
   wrong=Marshal.load(Marshal.dump(policy));wrong['constrained_surface_edits']['face_material_pids']<<9999999999;KStudioPathScopeGraphGuard.capture(r,paths,wrong)
  end
  KStudioPathScopeGuard.verify!(r,b,paths)
 rescue=>e
  error=e.message
 ensure
  m.abort_operation
 end
 raise 'Expected surface protection did not reject '+label+'; actual='+error.inspect unless error&&(error.include?('Protected geometry changed outside approved exact paths')||label=='unknown_mask_id'&&error.include?('Unknown or out-of-target surface face ID'))
 after=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];raise 'Whole-document rollback failed '+label unless after==baseline
 results<<{case:label,status:'PASS',native_rejection:error,complete_document_rollback_equal:true}
 top=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z>0.99}
end
{status:'PASS_NATIVE_CONSTRAINED_SURFACE_GUARD',native_version:Sketchup.version,root_pid:20606,revision:18,production_geometry_writes:0,disposable_committed_operations:1,actual_positive_receipt:positive,negative_cases:results,original_source_masks:{face_material_count:policy['constrained_surface_edits']['face_material_pids'].length,soft_smooth_edge_count:policy['constrained_surface_edits']['soft_smooth_edge_pids'].length},scope:'Safety-copy guard test; no live website geometry/finish modification or source-quality PASS'}
'''
 for k,v in [('HELPER',(R/'app/adopted_sketchup_helpers.rb').as_posix()),('SURFACE',(R/'app/surface_edit_guard.rb').as_posix()),('GRAPH',(R/'app/path_scope_graph_guard.rb').as_posix()),('GUARD',(R/'app/path_scope_guard.rb').as_posix()),('COPY',str(copy)),('POLICY',json.dumps(policy,ensure_ascii=False))]:
  source=source.replace('load '+k,'load '+json.dumps(v,ensure_ascii=False)) if k in ['HELPER','SURFACE','GRAPH','GUARD'] else source.replace(k,json.dumps(v,ensure_ascii=False))
 f=_generated_script_dir()/('studio-surface-native-test-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');(D/'actual-native-fixture.rb').write_text(source,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Actual safety-copy material/seam-only positive and seven surface mutation rollback checks'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(D/'actual-native-results.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
except Exception as e:
 (D/'actual-failure.json').write_text(json.dumps({'status':'FAIL','actual_error':str(e)},ensure_ascii=False,indent=2),encoding='utf8');raise
finally:
 pf.write_bytes(saved);open_(working);i=a.get_active_model_identity();raw=a.capture_native_deep_fingerprint(expected_model_path=working,expected_guid=i['model_guid'],root_pid=20606,output_path=D/'production18-restored.json',representation='definition_graph');old=json.loads((R/'runtime/exterior-completion-20261016/r18-graph-working-restored.json').read_text(encoding='utf8'));check=compare_stable_geometry(old,raw);assert check['status']=='PASS';(D/'production-restore.json').write_text(json.dumps({'status':'PASS','native_equality':check,'active_policy_bytes_restored':pf.read_bytes()==saved,'production_geometry_writes':0},indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in v.items() if k!='actual_positive_receipt'},ensure_ascii=False))
