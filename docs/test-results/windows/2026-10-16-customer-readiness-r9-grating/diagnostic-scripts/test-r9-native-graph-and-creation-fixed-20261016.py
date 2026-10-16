from pathlib import Path
import json,sys,shutil,time,hashlib,copy
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.project_ruby import ProjectRubyExecutor
D=R/'runtime/customer-readiness-20261015/native-r9-graph-faults';D.mkdir(exist_ok=True);P=R/'runtime/projects/architecture-project-4f0e4';ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));working=Path(ad.get_active_model_identity()['model_path']);target=P/'outputs/model/blank-disposable-r9-definition-graph-faults-fixed-20261016.skp';assert not target.exists();shutil.copy2(Path.home()/'Downloads/agent-checkpoint-5374ca398451.skp',target)
def open_(p):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
def eval_(source,label):
 f=_generated_script_dir()/f'studio-native-r9-fault-{time.time_ns()}.rb';f.write_text(source,encoding='utf-8');raw=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':label});v=raw.get('result',raw) if isinstance(raw,dict) else raw;return json.loads(v) if isinstance(v,str) else v
try:
 open_(target);i=ad.get_active_model_identity()
 source='''# ARCHFLOW_GENERATED_SCRIPT
LOADS
m=Sketchup.active_model
raise 'Wrong disposable identity' unless m.guid==GUID && File.expand_path(m.path)==File.expand_path(PATH)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise 'Wrong actual revision' unless r && r.get_attribute('sketchup_architect','revision')==9
def find_(g,n);a=g.entities.select{|e|e.respond_to?(:name)&&e.name==n};raise 'Ambiguous native path' unless a.length==1;a.first;end
ext=find_(r,'CIRCULATION_EXTERNAL');gal=find_(ext,'GALLERIES');deck=find_(gal,'GALLERY_Z3600_SIDE0');field=deck.entities.find{|e|e.respond_to?(:name)&&e.name.end_with?('_OPEN_GRID')};panel=field.entities.grep(Sketchup::ComponentInstance).first
raise 'Expected genuinely reused grating definition' unless panel && panel.definition.instances.length>1
base=KStudioNativeDefinitionGraph.capture(m,root_pid:20606);base_sha=base[:document_geometry_material_sha256];base_counts=base[:counts];base=nil
faults=[]
['one_instance_transform','shared_definition_material','document_loose_edge'].each do |kind|
 m.start_operation('Disposable graph fault '+kind,true)
 begin
  if kind=='one_instance_transform';panel.transform!(Geom::Transformation.translation([1.mm,0,0]))
  elsif kind=='shared_definition_material';bar=panel.definition.entities.grep(Sketchup::Group).first;face=bar.entities.grep(Sketchup::Face).first;face.material=m.materials['KS_Timber_Honey']
  else;m.entities.add_line([0,0,0],[1.mm,0,0]);end
  changed=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)
  raise 'Native graph missed changed geometry/material/loose edge' if changed[:document_geometry_material_sha256]==base_sha
  faults<<{case:kind,detected:true,owned_counts_equal:changed[:counts]==base_counts}
 ensure;m.abort_operation;end
 restored=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)
 raise 'Fault rollback changed document' unless restored[:document_geometry_material_sha256]==base_sha
 faults.last[:rollback_document_equal]=true
end
parent=find_(r,'CIRCULATION_INTERNAL');paths=[['CIRCULATION_INTERNAL','TEST_NEW_CIRCULAR_GUARD']]
policy={'status'=>'active','model_path'=>m.path,'root_pid'=>20606,'allowed_paths'=>paths,'allowed_creation_paths'=>paths}
def add_probe_(parent);g=parent.entities.add_group;g.name='TEST_NEW_CIRCULAR_GUARD';g.entities.add_face([[0,0,0],[10.mm,0,0],[10.mm,10.mm,0],[0,10.mm,0]]);g;end
before=KStudioExactPathCreationGuard.capture(r,paths,policy)
m.start_operation('Disposable positive exact absent-leaf creation',true)
begin
 created=add_probe_(parent);after=KStudioExactPathCreationGuard.capture(r,paths,policy,phase: :after)
 receipt=KStudioExactPathCreationGuard.compare!(before,after,paths);new_pid=created.persistent_id;m.commit_operation
rescue Exception;m.abort_operation;raise;end
raise 'Positive creation not committed on fault copy' unless parent.entities.any?{|e|e.respond_to?(:persistent_id)&&e.persistent_id==new_pid}
m.start_operation('Remove only explicit disposable probe',true);found=parent.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==new_pid};raise 'Wrong cleanup target' unless found.name=='TEST_NEW_CIRCULAR_GUARD';found.erase!;m.commit_operation
raise 'Positive test cleanup changed document geometry' unless KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256]==base_sha
creation_faults=[]
['undeclared_sibling','parent_transform','protected_shared_panel_material','document_loose_edge','missing_target','empty_target','duplicate_target'].each do |kind|
 before=KStudioExactPathCreationGuard.capture(r,paths,policy);m.start_operation('Disposable creation fence negative '+kind,true);rejected=false
 begin
  created=kind=='missing_target' ? nil : add_probe_(parent)
  if kind=='undeclared_sibling';g=parent.entities.add_group;g.name='UNAPPROVED';g.entities.add_line([0,0,0],[2.mm,0,0])
  elsif kind=='parent_transform';parent.transform!(Geom::Transformation.translation([1.mm,0,0]))
  elsif kind=='protected_shared_panel_material';panel.material=m.materials['KS_Timber_Honey']
  elsif kind=='document_loose_edge';m.entities.add_line([0,0,0],[2.mm,0,0])
  elsif kind=='empty_target';created.entities.erase_entities(created.entities.to_a)
  elsif kind=='duplicate_target';add_probe_(parent);end
  after=KStudioExactPathCreationGuard.capture(r,paths,policy,phase: :after);KStudioExactPathCreationGuard.compare!(before,after,paths)
 rescue RuntimeError=>e;rejected=true;reason=e.message
 ensure;m.abort_operation;end
 raise 'Creation fence allowed '+kind unless rejected
 restored=KStudioNativeDefinitionGraph.capture(m,root_pid:20606);raise 'Creation fault rollback changed document' unless restored[:document_geometry_material_sha256]==base_sha
 creation_faults<<{case:kind,rejected:true,reason:reason,rollback_document_equal:true}
end
{status:'PASS_ON_DISPOSABLE_COPY_ONLY',root_pid:20606,website_revision:9,production_geometry_commits:0,graph_faults:faults,creation_positive:{committed_on_copy:true,created_pid:new_pid,explicit_probe_cleanup_equal:true,receipt:receipt},creation_negatives:creation_faults,document_sha_before_after:base_sha,limitation:'Candidate creation guard is not deployed to live writer and does not certify missing-circle geometry quality.'}
'''
 loads='\n'.join('load '+json.dumps(p.as_posix(),ensure_ascii=False) for p in [R/'app/native_definition_graph.rb',R/'app/path_scope_guard.rb',R/'runtime/exact_path_creation_guard_candidate.rb'])
 source=source.replace('LOADS',loads).replace('GUID',json.dumps(i['model_guid'])).replace('PATH',json.dumps(i['model_path'],ensure_ascii=False));(D/'native-fault-source.rb').write_text(source,encoding='utf-8');start=time.monotonic();result=eval_(source,'Disposable native graph mutations and exact missing-leaf guard acceptance');result['elapsed_ms']=round((time.monotonic()-start)*1000);result['candidate_source_sha256']=hashlib.sha256((R/'runtime/exact_path_creation_guard_candidate.rb').read_bytes()).hexdigest();(D/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'graph_faults':len(result['graph_faults']),'creation_negatives':len(result['creation_negatives']),'elapsed_ms':result['elapsed_ms']}))
finally:
 open_(working)

