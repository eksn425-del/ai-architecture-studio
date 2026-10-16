from pathlib import Path
import sys,json,shutil,hashlib,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from scripts.audit_native_delivery_stages import audit_stages
from scripts.audit_native_stable_delivery_stages import audit_stable_stages
from app.native_stable_geometry import compare_stable_geometry
D=R/'runtime/basic-closeout-20261017';P=R/'runtime/projects/architecture-project-4f0e4';F=D/'r20-record';F.mkdir(exist_ok=True)
for rel in ['state/agent_session.json','state/model_state.json','runtime/project_ruby_state.json','runtime/native_delivery_checkpoint.json','runtime/scripts','runtime/agent_workspace/qa','runtime/agent_workspace/notes','runtime/agent_workspace/scripts']:
 src=P/rel;dest=F/rel
 if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
 elif src.is_file():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
q=json.loads((P/'runtime/agent_workspace/qa/visual_review.json').read_text(encoding='utf8'));assert q['model_revisions']=={'glass_curved_roof':20};assert len({v['source_ref'] for v in q['evidence_pairs']})==8;paths=set()
coverage={'actual_pairs':len(q['evidence_pairs']),'planned_pairs':8,'all_eight_source_refs_present':True,'status':'PARTIAL' if len(q['evidence_pairs'])<8 else 'COUNT_MET','limitation':'Actual reviewer received all eight whole originals, six canonical views and the actual number of pairs recorded above. All eight source refs required. Hidden interior not certified by unsectioned exterior views.'};(D/'r20-review-coverage.json').write_text(json.dumps(coverage,indent=2),encoding='utf8')
def collect(x):
 if isinstance(x,dict):
  for v in x.values():collect(v)
 elif isinstance(x,list):
  for v in x:collect(v)
 elif isinstance(x,str) and x.startswith('outputs/renders/') and x.endswith('.png'):paths.add(x)
collect(q)
for rel in paths:
 src=P/rel;dest=F/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 side=src.with_suffix('.evidence.json')
 if side.exists():shutil.copy2(side,dest.with_suffix('.evidence.json'))
event=P/'runtime/agent_events/5fafef7653e845fbb3286f976bb6c66e.jsonl';dest=F/'runtime/agent_events'/event.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(event,dest)
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf8'));assert session['status']=='ready' and session['ruby_state']['glass_curved_roof']['revision']==20
bound=(P/session['model_path']).resolve();ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=ad.get_active_model_identity();assert Path(i['model_path']).resolve()==bound
before=json.loads((D/'r20-graph-before-site-final-save.json').read_text(encoding='utf8'));proof=json.loads((D/'r20-actual-pre-site-save-ordering.json').read_text(encoding='utf8'));assert proof['before_final_r20_save_proven'] and before['document_geometry_material_sha256']==proof['document_sha']
receipt=json.loads((P/'runtime/native_delivery_checkpoint.json').read_text(encoding='utf8'));assert receipt['script_revisions']=={'glass_curved_roof':20};download=Path.home()/'Downloads'/Path(receipt['download_candidate']['path']).name;assert hashlib.sha256(download.read_bytes()).hexdigest()==receipt['download_candidate']['sha256']
models=F/'models';models.mkdir(exist_ok=True);shutil.copy2(download,models/'r20-actual-browser-download.skp');shutil.copy2(bound,models/'r20-bound-working.skp')
clean=bound.with_name('blank-disposable-r20-browser-download-verification-20261016.skp');assert not clean.exists();shutil.copy2(download,clean)
def open_(p):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path']);assert Path(ad.get_active_model_identity()['model_path']).resolve()==p.resolve()
def cap(name):
 i=ad.get_active_model_identity();return ad.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=D/name,representation='definition_graph')
display_stages=[]
def display(stage):
 i=ad.get_active_model_identity();f=_generated_script_dir()/('studio-shading-reopen-'+str(time.time_ns())+'.rb');f.write_text('# ARCHFLOW_GENERATED_SCRIPT\nm=Sketchup.active_model;raise "GUID" unless m.guid=='+json.dumps(i['model_guid'])+'\n{geometry_writes:0,model_guid:m.guid,model_path:m.path,settings:Hash[["Dark","Light","UseSunForAllShading","DisplayShadows"].map{|k|[k,m.shadow_info[k]]}]}',encoding='utf8');v=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only shading settings '+stage});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;display_stages.append({'stage':stage,**v});assert v['settings']=={'Dark':80,'Light':15,'UseSunForAllShading':True,'DisplayShadows':False},v
start=time.monotonic();display('after_site_save_before_native_reopen')
try:
 open_(bound);reopened=cap('r20-graph-bound-reopened.json');display('bound_native_reopened')
 open_(clean);downloaded=cap('r20-graph-browser-download-reopened.json');display('browser_download_native_reopened')
 raw=audit_stages(before,reopened,downloaded,require_deep=True);stable=audit_stable_stages(before,reopened,downloaded)
 (D/'r20-stable-native-delivery.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2),encoding='utf8');assert stable['status']=='PASS_WITH_DECLARED_PRECISION',str(stable)[:2000]
finally:open_(bound)
restored=cap('r20-graph-working-restored.json');assert compare_stable_geometry(before,restored)['status']=='PASS'
assert hashlib.sha256((P/'outputs/model/blank-disposable-p0-repaired-r2.skp').read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
out={'status':stable['status'],'revision':20,'root_pid':20606,'raw_strict_three_stage_status':raw['status'],'raw_strict_audit':raw,'stable_geometry_audit':stable,'actual_browser_download':str(download),'download_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'elapsed_ms':round((time.monotonic()-start)*1000),'display_stages':display_stages,'working_restored':True,'original_r4_unchanged':True,'source_fidelity':q['quality_status'],'strict_blank_program_replay':'NOT_RUN','owner_case_closeout':'BASIC_SCOPE_ACCEPTED_PENDING_FINAL_PUBLICATION','commercial_readiness':'NOT_CERTIFIED_THIS_CASE'}
(D/'r20-native-delivery-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['raw_strict_audit','stable_geometry_audit']},ensure_ascii=False))
