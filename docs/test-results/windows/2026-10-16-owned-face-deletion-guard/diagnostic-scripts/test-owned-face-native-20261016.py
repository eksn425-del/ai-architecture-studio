from pathlib import Path
import json,sys,time,shutil
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.native_stable_geometry import compare_stable_geometry
D=R/'runtime/owned-face-guard-20261016';D.mkdir(exist_ok=True);P=R/'runtime/projects/architecture-project-4f0e4';pf=P/'runtime/active_edit_scope.json';saved=pf.read_bytes()
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=240));i=a.get_active_model_identity();working=Path(i['model_path']);assert working.name=='blank-disposable-customer-readiness-r4-20261015.skp'
copy=working.with_name('blank-disposable-r17-owned-face-guard-20261016.skp');assert not copy.exists();shutil.copy2(working,copy)
policy=json.loads(saved);policy.update(model_path=str(copy),allowed_paths=policy['shared_definition_edit_paths'],allowed_creation_paths=[])
def open_(p):
 i=a.get_active_model_identity();a.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
try:
 open_(copy);pf.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
 source='''# ARCHFLOW_GENERATED_SCRIPT
load HELPER
load GRAPH
load GUARD
m=Sketchup.active_model;raise 'Wrong safe copy' unless File.expand_path(m.path)==File.expand_path(COPY)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==17
paths=JSON.parse(PATHS);path=['ENVELOPE_OUTER','NORTH_BAY_1','GLASS'];g=KStudioProfessionalHelpers.named_owned_group(r,path);raise 'Expected holed glass' unless g.entities.grep(Sketchup::Face).length==1
original=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256]
face_record=lambda{|gg|gg.entities.grep(Sketchup::Face).map{|ff|{pid:ff.persistent_id,normal:ff.normal.to_a,area_mm2:ff.area*25.4*25.4,front:ff.material&&ff.material.name,back:ff.back_material&&ff.back_material.name,loops:ff.loops.map{|ll|{outer:ll.outer?,points:ll.vertices.map{|vv|vv.position.to_a}}}}}}
target_before=face_record.call(g)
before=KStudioPathScopeGuard.capture(r,paths);face=g.entities.grep(Sketchup::Face).first;loop=face.loops.find{|l|!l.outer?};raise 'Missing actual aperture' unless loop
m.start_operation('Disposable scoped face aperture test',true)
begin
 front=face.material;back=face.back_material
 KStudioProfessionalHelpers.clear_named_owned_contents(r,path,paths)
 g.entities.add_face([[0,0,7200],[2900,0,7200],[2900,0,13500],[0,0,13500]].map{|p|p.map(&:mm)})
 fill=g.entities.add_face([[90,0,12600],[2810,0,12600],[2810,0,13400],[90,0,13400]].map{|p|p.map(&:mm)});raise 'Fresh aperture face creation failed' unless fill
 raise 'Fixture did not create only the actual aperture fill' unless (fill.area*25.4*25.4-2720*800).abs<1
 erased_pid=fill.persistent_id
 receipt=KStudioProfessionalHelpers.erase_named_owned_faces(r,path,[erased_pid],paths)
 raise 'Face still valid after owned erase' if fill.valid?
 g.entities.grep(Sketchup::Face).each{|ff|ff.material=front;ff.back_material=back}
 guard=KStudioPathScopeGuard.verify!(r,before,paths)
 m.commit_operation
rescue
 m.abort_operation;raise
end
after=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];target_after=face_record.call(g)
raise 'Actual open aperture topology/area incorrect' unless target_after.length==1&&target_after.first[:loops].count{|ll|!ll[:outer]}==1&&(target_after.first[:area_mm2]-(2900*6300-2720*800)).abs<1
baseline=after
foreign=KStudioProfessionalHelpers.named_owned_group(r,['ROOF_TIMBER','CURVED_SHELL']).entities.grep(Sketchup::Face).first.persistent_id
own=g.entities.grep(Sketchup::Face).first.persistent_id;results=[]
cases=[['root_path',[],[own],paths],['foreign_face',path,[foreign],paths],['non_face_id',path,[g.persistent_id],paths],['duplicate_face_ids',path,[own,own],paths],['empty_ids',path,[],paths],['missing_one_shared_occurrence',path,[own],paths.reject{|p|p==['ENVELOPE_OUTER','SOUTH_BAY_1','GLASS']}]]
cases.each do |label,p,ids,declared|
 m.start_operation('Expected face rejection '+label,true);error=nil
 begin
  KStudioProfessionalHelpers.erase_named_owned_faces(r,p,ids,declared)
 rescue=>e
  error=e.message
 ensure
  m.abort_operation
 end
 raise 'Invalid face deletion escaped '+label unless error
 hash=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];raise 'Negative rollback changed document '+label unless hash==baseline
 results<<{case:label,status:'PASS',rejection:error,complete_document_equal:true}
end
{status:'PASS_NATIVE_SCOPED_FACE_DELETION',native_version:Sketchup.version,root_pid:20606,revision:17,production_geometry_writes:0,disposable_operations_committed:1,actual_removed_face:receipt,actual_shared_occurrences:guard['shared_definition_proofs'].first[:occurrences].length,positive_protected_graph_equal:guard['status']=='passed',positive_original_complete_document_equal:original==after,actual_target_faces_before:target_before,actual_target_faces_after:target_after,actual_native_before_sha:original,actual_native_after_sha:after,negative_cases:results,scope:'Safety-copy typed host helper; target Face lifecycle may change target identity/winding, actual protected graph remains exact and native aperture area/inner-loop checked. Not website UX success or model-quality PASS'}
'''
 for k,v in [('HELPER',(R/'app/adopted_sketchup_helpers.rb').as_posix()),('GRAPH',(R/'app/path_scope_graph_guard.rb').as_posix()),('GUARD',(R/'app/path_scope_guard.rb').as_posix()),('COPY',str(copy)),('PATHS',json.dumps(policy['allowed_paths']))]:source=source.replace(k,json.dumps(v,ensure_ascii=False))
 f=_generated_script_dir()/('studio-owned-face-test-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');(D/'actual-native-fixture.rb').write_text(source,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Actual safe-copy scoped-face aperture deletion and six negative cases'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(D/'actual-native-results.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
except Exception as e:
 (D/'actual-failure.json').write_text(json.dumps({'status':'FAIL','actual_error':str(e)},ensure_ascii=False,indent=2),encoding='utf8');raise
finally:
 pf.write_bytes(saved);open_(working);i=a.get_active_model_identity();restored=a.capture_native_deep_fingerprint(expected_model_path=working,expected_guid=i['model_guid'],root_pid=20606,output_path=D/'working17-restored.json',representation='definition_graph');old=json.loads((R/'runtime/exterior-completion-20261016/r17-graph-working-restored.json').read_text(encoding='utf8'));c=compare_stable_geometry(old,restored);assert c['status']=='PASS';(D/'production-restore.json').write_text(json.dumps({'status':'PASS','native_equality':c,'active_policy_bytes_restored':pf.read_bytes()==saved,'production_geometry_writes':0},indent=2),encoding='utf8')
print(json.dumps(v,ensure_ascii=False))
