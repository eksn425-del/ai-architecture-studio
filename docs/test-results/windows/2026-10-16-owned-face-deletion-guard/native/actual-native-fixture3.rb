# ARCHFLOW_GENERATED_SCRIPT
load "E:/K AI 产品建模网站/app/adopted_sketchup_helpers.rb"
load "E:/K AI 产品建模网站/app/path_scope_graph_guard.rb"
load "E:/K AI 产品建模网站/app/path_scope_guard.rb"
m=Sketchup.active_model;raise 'Wrong safe copy' unless File.expand_path(m.path)==File.expand_path("E:\\K AI 产品建模网站\\runtime\\projects\\architecture-project-4f0e4\\outputs\\model\\blank-disposable-r17-owned-face-guard3-20261016.skp")
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==17
paths=JSON.parse("[[\"ENVELOPE_OUTER\", \"NORTH_BAY_1\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_10\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_11\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_12\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_13\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_14\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_15\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_16\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_17\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_18\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_19\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_2\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_3\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_4\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_5\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_6\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_7\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_8\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_9\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_1\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_10\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_11\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_12\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_13\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_14\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_15\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_16\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_17\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_18\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_19\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_2\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_3\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_4\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_5\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_6\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_7\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_8\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_9\", \"GLASS\"]]");path=['ENVELOPE_OUTER','NORTH_BAY_1','GLASS'];g=KStudioProfessionalHelpers.named_owned_group(r,path);raise 'Expected holed glass' unless g.entities.grep(Sketchup::Face).length==1
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
