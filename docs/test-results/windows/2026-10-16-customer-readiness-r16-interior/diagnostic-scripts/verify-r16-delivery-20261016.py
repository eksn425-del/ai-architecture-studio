from pathlib import Path
import sys,json,shutil,hashlib,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from scripts.audit_native_delivery_stages import audit_stages
from scripts.audit_native_stable_delivery_stages import audit_stable_stages
from app.native_stable_geometry import compare_stable_geometry
D=R/'runtime/exterior-completion-20261016';P=R/'runtime/projects/architecture-project-4f0e4';F=D/'r16-record';F.mkdir(exist_ok=True)
for rel in ['state/agent_session.json','state/model_state.json','runtime/project_ruby_state.json','runtime/native_delivery_checkpoint.json','runtime/scripts','runtime/agent_workspace/qa','runtime/agent_workspace/notes','runtime/agent_workspace/scripts']:
 src=P/rel;dest=F/rel
 if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
 elif src.is_file():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
q=json.loads((P/'runtime/agent_workspace/qa/visual_review.json').read_text(encoding='utf8'));assert q['model_revisions']=={'glass_curved_roof':16};assert len({v['source_ref'] for v in q['evidence_pairs']})==8;paths=set()
coverage={'actual_pairs':len(q['evidence_pairs']),'planned_pairs':8,'all_eight_source_refs_present':True,'status':'PARTIAL' if len(q['evidence_pairs'])<8 else 'COUNT_MET','limitation':'Actual reviewer received all eight whole originals, six canonical views and the actual number of pairs recorded above. All eight source refs required. Hidden interior not certified by unsectioned exterior views.'};(D/'r16-review-coverage.json').write_text(json.dumps(coverage,indent=2),encoding='utf8')
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
event=P/'runtime/agent_events/b8a567865fbd4c8a8c59fc6a969d6599.jsonl';dest=F/'runtime/agent_events'/event.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(event,dest)
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf8'));assert session['status']=='ready' and session['ruby_state']['glass_curved_roof']['revision']==16
bound=(P/session['model_path']).resolve();ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=ad.get_active_model_identity();assert Path(i['model_path']).resolve()==bound
before=ad.capture_native_deep_fingerprint(expected_model_path=bound,expected_guid=i['model_guid'],root_pid=20606,output_path=D/'r16-post-site-save-native-baseline.json',representation='definition_graph')
receipt=json.loads((P/'runtime/native_delivery_checkpoint.json').read_text(encoding='utf8'));assert receipt['script_revisions']=={'glass_curved_roof':16};download=Path.home()/'Downloads'/Path(receipt['download_candidate']['path']).name;assert hashlib.sha256(download.read_bytes()).hexdigest()==receipt['download_candidate']['sha256']
models=F/'models';models.mkdir(exist_ok=True);shutil.copy2(download,models/'r16-actual-browser-download.skp');shutil.copy2(bound,models/'r16-bound-working.skp')
clean=bound.with_name('blank-disposable-r16-browser-download-verification-20261016.skp');assert not clean.exists();shutil.copy2(download,clean)
def open_(p):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path']);assert Path(ad.get_active_model_identity()['model_path']).resolve()==p.resolve()
def cap(name):
 i=ad.get_active_model_identity();return ad.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=D/name,representation='definition_graph')
start=time.monotonic()
try:
 open_(bound);reopened=cap('r16-graph-bound-reopened.json')
 open_(clean);downloaded=cap('r16-graph-browser-download-reopened.json')
 raw=audit_stages(before,reopened,downloaded,require_deep=True);stable=audit_stable_stages(before,reopened,downloaded)
 (D/'r16-stable-native-delivery.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2),encoding='utf8');assert stable['status']=='PASS_WITH_DECLARED_PRECISION',str(stable)[:2000]
finally:open_(bound)
restored=cap('r16-graph-working-restored.json');assert compare_stable_geometry(before,restored)['status']=='PASS'
assert hashlib.sha256((P/'outputs/model/blank-disposable-p0-repaired-r2.skp').read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
out={'status':stable['status'],'revision':16,'root_pid':20606,'raw_strict_three_stage_status':raw['status'],'raw_strict_audit':raw,'stable_geometry_audit':stable,'actual_browser_download':str(download),'download_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'elapsed_ms':round((time.monotonic()-start)*1000),'working_restored':True,'original_r4_unchanged':True,'source_fidelity':q['quality_status'],'strict_blank_program_replay':'NOT_RUN','customer_delivery':'NOT_READY','stage_limitation':'Baseline captured AFTER original website final save. Bound/download reopened equality is real; original r16 pre-site-save stage NOT_CAPTURED, no historical three-stage PASS claimed.'}
(D/'r16-native-delivery-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['raw_strict_audit','stable_geometry_audit']},ensure_ascii=False))
