from pathlib import Path
import sys,json,shutil,time,copy
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir,MCPCallError
from app.project_ruby import ProjectRubyExecutor
from app.native_stable_geometry import compare_stable_geometry
D=R/'runtime/customer-readiness-20261015/r9-guid-race';D.mkdir(exist_ok=True);P=R/'runtime/projects/architecture-project-4f0e4';base=ConfiguredSketchUpMCP(timeout_seconds=180);ad=SketchUpAdapter(base);working=Path(ad.get_active_model_identity()['model_path']);target=P/'outputs/model/blank-disposable-r9-guid-race-20261016.skp';assert not target.exists();shutil.copy2(Path.home()/'Downloads/agent-checkpoint-5374ca398451.skp',target)
def open_(p):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
def cap(name):
 i=ad.get_active_model_identity();return ad.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=D/name,representation='definition_graph')
class Race:
 def __init__(self):self.injected=False;self.errors=[];self.calls=[]
 def call(self,name,args):
  self.calls.append(args.get('operation_name'))
  if args.get('operation_name')=='Read owned groups; no geometry edit' and not self.injected:
   self.injected=True;i=ad.get_active_model_identity();f=_generated_script_dir()/('studio-guid-race-metadata-'+str(time.time_ns())+'.rb')
   source='# ARCHFLOW_GENERATED_SCRIPT\nm=Sketchup.active_model\nraise "Wrong fault-copy identity" unless m.guid=='+json.dumps(i['model_guid'])+' && File.expand_path(m.path)==File.expand_path('+json.dumps(str(target),ensure_ascii=False)+')\nr=m.entities.find{|e| e.respond_to?(:persistent_id)&&e.persistent_id==20606}\nraise "Wrong owned revision" unless r && r.get_attribute("sketchup_architect","revision")==9\nr.set_attribute("kstudio_disposable_fault","guid_race",'+str(time.time_ns())+')\n{metadata_only_on_disposable_copy:true}\n';f.write_text(source,encoding='utf8');(D/'metadata-fault-source.rb').write_text(source,encoding='utf8');base.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Inject metadata-only GUID race on disposable copy'});ad.save_model(target,'Save metadata-only GUID fault copy',expected_root_ids=[20606]);now=ad.get_active_model_identity();assert now['model_guid']!=i['model_guid'],'Fault did not advance actual GUID'
  try:return base.call(name,args)
  except MCPCallError as e:self.errors.append(str(e));raise
try:
 open_(target);before=cap('before.json');i=ad.get_active_model_identity();race=Race();states=copy.deepcopy(json.loads((P/'runtime/project_ruby_state.json').read_text(encoding='utf8'))['scripts']);executor=ProjectRubyExecutor(R/'runtime','architecture-project-4f0e4',expected_model_path=target,expected_model_guid=i['model_guid'],mcp=race,ruby_state=states,adapter=ad)
 result=executor.inspect_owned({'script_id':'glass_curved_roof','path':['ROOF_TIMBER'],'limit':1});assert result['success'];assert len(race.errors)==1 and 'Active model GUID changed' in race.errors[0];assert sum('Retry read after' in (v or '') for v in race.calls)==1
 after=cap('after.json');comparison=compare_stable_geometry(before,after);assert comparison['status']=='PASS'
 out={'status':'PASS_ON_DISPOSABLE_COPY_ONLY','production_geometry_writes':0,'actual_native_guid_race_injected':True,'first_queued_read_failed':True,'one_read_retry_succeeded':True,'owned_path_root_project_revision_proof_required':True,'raw_errors':race.errors,'tool_operations':race.calls,'stable_geometry_unchanged':comparison,'limitation':'Actual same-owned-document race tested. Different-path/failed-proof/second-race remain offline negative tests; live original writer not rerun.'};(D/'result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('PASS actual native GUID race, failed first read, proved identity, one readonly retry, geometry unchanged')
finally:open_(working)
