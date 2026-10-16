from pathlib import Path
import json,sys,time,shutil,hashlib
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/shared-envelope-guard-20261016';D.mkdir(exist_ok=True)
P=R/'runtime/projects/architecture-project-4f0e4';pf=P/'runtime/active_edit_scope.json';saved=pf.read_bytes()
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=240));i=a.get_active_model_identity();working=Path(i['model_path']);assert working.name=='blank-disposable-customer-readiness-r4-20261015.skp'
copy=working.with_name('blank-disposable-r16-shared-scope-test2-20261016.skp');assert not copy.exists();shutil.copy2(working,copy)
paths=json.loads((D/'actual-long-glass-all-occurrences-readonly.json').read_text(encoding='utf8'))['all_long_glass_paths']
policy={'status':'active','scope_contract':'deep_exact_paths_graph_v1','model_path':str(copy),'root_pid':20606,'allowed_paths':paths,'allowed_creation_paths':[],'shared_definition_edit_paths':paths,'required_preserve_paths':[['ROOF_TIMBER'],['STRUCTURE_EXISTING'],['FLOORS'],['RAMPS'],['CIRCULATION_EXTERNAL'],['CIRCULATION_INTERNAL'],['INTERIOR']]}
def open_(p):
 i=a.get_active_model_identity();a.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
def evaluate(source,label):
 f=_generated_script_dir()/('studio-shared-test-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');(D/(label+'.rb')).write_text(source,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Disposable same-case shared-definition guard test '+label});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(D/(label+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');return v
try:
 open_(copy);pf.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
 source='''# ARCHFLOW_GENERATED_SCRIPT
 load HELPER
 load GRAPH
 load APP
load FIXTURE
m=Sketchup.active_model;raise 'Wrong test copy' unless File.expand_path(m.path)==File.expand_path(COPY)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Wrong revision' unless r.get_attribute('sketchup_architect','revision')==16
policy=JSON.parse(POLICY);paths=policy['allowed_paths'];leaf=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER','SOUTH_BAY_1','GLASS'])
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
   no=policy.merge('shared_definition_edit_paths'=>[]);File.write(POLICYFILE,JSON.generate(no));KStudioProfessionalHelpers.clear_named_owned_contents(r,['ENVELOPE_OUTER','SOUTH_BAY_1','GLASS'],paths)
  when 'missing_one_occurrence'
   missing=proof[:occurrences].first[:path];KStudioPathScopeGraphGuard.capture(r,paths.reject{|p|p==missing},policy)
  when 'broad_ancestor'
   KStudioPathScopeGraphGuard.capture(r,[['ENVELOPE_OUTER']],policy)
  when 'locked_occurrence'
   bay=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER','NORTH_BAY_1']);bay.locked=true;KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths)
  when 'external_occurrence'
   m.entities.add_instance(leaf.definition,Geom::Transformation.new);KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths)
  when 'undeclared_nested_occurrence'
   env=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER']);bay=KStudioProfessionalHelpers.named_owned_group(r,['ENVELOPE_OUTER','SOUTH_BAY_1']);newg=env.entities.add_instance(bay.definition,Geom::Transformation.new);newg.name='UNDECLARED_SHARED_TEST';raise 'Fixture failed to share actual bay prototype' unless newg.definition==bay.definition;KStudioSharedDefinitionScope.prove!(r,leaf,paths,paths)
  when 'protected_sibling'
   b=KStudioPathScopeGuard.capture(r,paths);other=KStudioProfessionalHelpers.named_owned_group(r,['SITE_GROUND']);other.transform!(Geom::Transformation.translation([1.mm,0,0]));KStudioPathScopeGuard.verify!(r,b,paths)
  end
 rescue=>e
  error=e.message
 ensure
  m.abort_operation;File.write(POLICYFILE,JSON.generate(policy))
 end
 raise 'Negative case escaped '+label unless error
 after=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];raise 'Rollback changed full document '+label unless after==baseline
 tests<<{case:label,status:'PASS',rejection:error,full_document_rollback_equal:true}
end
{status:'PASS_NATIVE_DISPOSABLE_SHARED_SCOPE',native_version:Sketchup.version,revision:16,root_pid:20606,production_geometry_writes:0,disposable_committed_writes:1,actual_shared_occurrences:38,positive_scope_receipt:receipt,cleared:cleared,negative_cases:tests,scope:'Actual same-case safety-copy host fixture, not website UX/model quality PASS'}
'''
 for key,value in [('HELPER',(R/'app/adopted_sketchup_helpers.rb').as_posix()),('GRAPH',(R/'app/path_scope_graph_guard.rb').as_posix()),('APP',(R/'app/path_scope_guard.rb').as_posix()),('FIXTURE',(R/'tests/ruby/shared_definition_scope_test.rb').as_posix()),('COPY',str(copy)),('POLICYFILE',str(pf)),('POLICY',json.dumps(policy,ensure_ascii=False))]:source=source.replace(key,json.dumps(value,ensure_ascii=False))
 result=evaluate(source,'native-copy-write-and-negative-rollback2')
finally:
 pf.write_bytes(saved);open_(working)
 i=a.get_active_model_identity();raw=a.capture_native_deep_fingerprint(expected_model_path=working,expected_guid=i['model_guid'],root_pid=20606,output_path=D/'production-r16-restored2.json',representation='definition_graph')
 original=json.loads((R/'runtime/exterior-completion-20261016/r16-graph-working-restored.json').read_text(encoding='utf8'))
 from app.native_stable_geometry import compare_stable_geometry
 check=compare_stable_geometry(original,raw);assert check['status']=='PASS',check
 (D/'production-restore-verification2.json').write_text(json.dumps({'status':'PASS','native_equality':check,'active_policy_bytes_restored':pf.read_bytes()==saved,'original_r4_unchanged':hashlib.sha256((P/'outputs/model/blank-disposable-p0-repaired-r2.skp').read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'},indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ['positive_scope_receipt']},ensure_ascii=False))
