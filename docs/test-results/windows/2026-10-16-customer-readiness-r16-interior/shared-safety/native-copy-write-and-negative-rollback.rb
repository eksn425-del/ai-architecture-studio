# ARCHFLOW_GENERATED_SCRIPT
 load "E:/K AI 产品建模网站/app/adopted_sketchup_helpers.rb"
 load "E:/K AI 产品建模网站/app/path_scope_graph_guard.rb"
 load "E:/K AI 产品建模网站/app/path_scope_guard.rb"
load "E:/K AI 产品建模网站/tests/ruby/shared_definition_scope_test.rb"
m=Sketchup.active_model;raise 'Wrong test copy' unless File.expand_path(m.path)==File.expand_path("E:\\K AI 产品建模网站\\runtime\\projects\\architecture-project-4f0e4\\outputs\\model\\blank-disposable-r16-shared-scope-test-20261016.skp")
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Wrong revision' unless r.get_attribute('sketchup_architect','revision')==16
policy=JSON.parse("{\"status\": \"active\", \"scope_contract\": \"deep_exact_paths_graph_v1\", \"model_path\": \"E:\\\\K AI 产品建模网站\\\\runtime\\\\projects\\\\architecture-project-4f0e4\\\\outputs\\\\model\\\\blank-disposable-r16-shared-scope-test-20261016.skp\", \"root_pid\": 20606, \"allowed_paths\": [[\"ENVELOPE_OUTER\", \"SOUTH_BAY_00\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_1\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_2\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_3\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_4\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_5\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_6\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_7\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_8\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_9\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_10\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_11\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_12\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_13\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_14\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_15\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_16\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_17\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_18\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_19\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_0\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_1\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_2\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_3\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_4\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_5\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_6\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_7\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_8\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_9\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_10\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_11\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_12\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_13\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_14\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_15\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_16\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_17\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_18\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_19\", \"GLASS\"]], \"allowed_creation_paths\": [], \"shared_definition_edit_paths\": [[\"ENVELOPE_OUTER\", \"SOUTH_BAY_00\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_1\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_2\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_3\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_4\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_5\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_6\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_7\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_8\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_9\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_10\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_11\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_12\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_13\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_14\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_15\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_16\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_17\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_18\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"SOUTH_BAY_19\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_0\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_1\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_2\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_3\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_4\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_5\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_6\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_7\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_8\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_9\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_10\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_11\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_12\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_13\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_14\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_15\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_16\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_17\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_18\", \"GLASS\"], [\"ENVELOPE_OUTER\", \"NORTH_BAY_19\", \"GLASS\"]], \"required_preserve_paths\": [[\"ROOF_TIMBER\"], [\"STRUCTURE_EXISTING\"], [\"FLOORS\"], [\"RAMPS\"], [\"CIRCULATION_EXTERNAL\"], [\"CIRCULATION_INTERNAL\"], [\"INTERIOR\"]]}");paths=policy['allowed_paths'];leaf=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER','SOUTH_BAY_1','GLASS'])
proof=KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths);raise 'Wrong shared count' unless proof[:occurrences].length==38
before=KStudioPathScopeGuard.capture(r,paths);oldpid=leaf.persistent_id
m.start_operation('Disposable explicit all38 shared-leaf replacement',true)
begin
 es=leaf.entities;raise 'Unexpected shared glass shape' unless es.grep(Sketchup::Face).length==1&&es.grep(Sketchup::Edge).length==4
 face=es.grep(Sketchup::Face).first;pts=face.outer_loop.vertices.map{|v|v.position.clone};mat=face.material;back=face.back_material
 cleared=KStudioProfessionalHelpers.clear_named_owned_contents(r,['ENVELOPE_OUTER','SOUTH_BAY_1','GLASS'],paths)
 f=es.add_face(pts);f.material=mat;f.back_material=back;es.add_line([400.mm,0,12600.mm],[410.mm,0,12600.mm])
 receipt=KStudioPathScopeGuard.verify!(r,before,paths);raise 'Container changed' unless oldpid==leaf.persistent_id
 m.commit_operation
rescue
 m.abort_operation;raise
end
baseline=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256]
tests=[]
['no_host_optin','missing_one_occurrence','broad_ancestor','locked_occurrence','external_occurrence','undeclared_nested_occurrence','protected_sibling'].each do |label|
 m.start_operation('Expected abort '+label,true);error=nil
 begin
  case label
  when 'no_host_optin'
   no=policy.merge('shared_definition_edit_paths'=>[]);File.write("E:\\K AI 产品建模网站\\runtime\\projects\\architecture-project-4f0e4\\runtime\\active_edit_scope.json",JSON.generate(no));KStudioProfessionalHelpers.clear_named_owned_contents(r,['ENVELOPE_OUTER','SOUTH_BAY_1','GLASS'],paths)
  when 'missing_one_occurrence'
   missing=proof[:occurrences].first[:path];KStudioPathScopeGraphGuard.capture(r,paths.reject{|p|p==missing},policy)
  when 'broad_ancestor'
   KStudioPathScopeGraphGuard.capture(r,[['ENVELOPE_OUTER']],policy)
  when 'locked_occurrence'
   bay=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER','NORTH_BAY_1']);bay.locked=true;KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths)
  when 'external_occurrence'
   m.entities.add_instance(leaf.definition,Geom::Transformation.new);KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths)
  when 'undeclared_nested_occurrence'
   env=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER']);newg=env.entities.add_instance(leaf.definition,Geom::Transformation.new);newg.name='UNDECLARED_SHARED_TEST';KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths)
  when 'protected_sibling'
   b=KStudioPathScopeGuard.capture(r,paths);other=KStudioProfessionalHelpers.named_owned_group(r,['SITE_GROUND']);other.transform!(Geom::Transformation.translation([1.mm,0,0]));KStudioPathScopeGuard.verify!(r,b,paths)
  end
 rescue=>e
  error=e.message
 ensure
  m.abort_operation;File.write("E:\\K AI 产品建模网站\\runtime\\projects\\architecture-project-4f0e4\\runtime\\active_edit_scope.json",JSON.generate(policy))
 end
 raise 'Negative case escaped '+label unless error
 after=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];raise 'Rollback changed full document '+label unless after==baseline
 tests<<{case:label,status:'PASS',rejection:error,full_document_rollback_equal:true}
end
{status:'PASS_NATIVE_DISPOSABLE_SHARED_SCOPE',native_version:Sketchup.version,revision:16,root_pid:20606,production_geometry_writes:0,disposable_committed_writes:1,actual_shared_occurrences:38,positive_scope_receipt:receipt,cleared:cleared,negative_cases:tests,scope:'Actual same-case safety-copy host fixture, not website UX/model quality PASS'}
