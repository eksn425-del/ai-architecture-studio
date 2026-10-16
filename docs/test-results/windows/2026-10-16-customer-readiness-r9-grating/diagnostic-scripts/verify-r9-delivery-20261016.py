from pathlib import Path
import sys,json,shutil,hashlib,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from scripts.audit_native_delivery_stages import audit_stages
D=R/'runtime/customer-readiness-20261015';P=R/'runtime/projects/architecture-project-4f0e4';F=D/'r9-record';F.mkdir(exist_ok=True)
for rel in ['state/agent_session.json','state/model_state.json','runtime/project_ruby_state.json','runtime/native_delivery_checkpoint.json','runtime/scripts','runtime/agent_workspace/qa','runtime/agent_workspace/notes','runtime/agent_workspace/scripts']:
 src=P/rel;dest=F/rel
 if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
 elif src.is_file():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
q=json.loads((P/'runtime/agent_workspace/qa/visual_review.json').read_text(encoding='utf-8'));paths=set()
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
event=P/'runtime/agent_events/251efc4d8b154f15924f618e446ddaca.jsonl';dest=F/'runtime/agent_events'/event.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(event,dest)
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf-8'));assert session['ruby_state']['glass_curved_roof']['revision']==9
bound=(P/session['model_path']).resolve();ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=ad.get_active_model_identity();assert Path(i['model_path']).resolve()==bound
before=json.loads((D/'r9-graph-before-site-final-save.json').read_text(encoding='utf-8'));assert before['document_geometry_material_sha256']=='bd267e0b3b4ca54e2e3e94342154c65bfd882cbc59df841e2ef6451ffc505118'
receipt=json.loads((P/'runtime/native_delivery_checkpoint.json').read_text(encoding='utf-8'));assert receipt['script_revisions']=={'glass_curved_roof':9}
download=Path.home()/'Downloads'/Path(receipt['download_candidate']['path']).name;assert hashlib.sha256(download.read_bytes()).hexdigest()==receipt['download_candidate']['sha256']
models=F/'models';models.mkdir(exist_ok=True);shutil.copy2(download,models/'r9-actual-browser-download.skp');shutil.copy2(bound,models/'r9-bound-working.skp')
clean=bound.with_name('blank-disposable-r9-browser-download-verification-20261016.skp');assert not clean.exists();shutil.copy2(download,clean)
def open_(p):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path']);assert Path(ad.get_active_model_identity()['model_path']).resolve()==p.resolve()
def cap(name):
 i=ad.get_active_model_identity();return ad.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=D/name,representation='definition_graph')
start=time.monotonic()
try:
 open_(bound);reopened=cap('r9-graph-bound-reopened.json')
 open_(clean);downloaded=cap('r9-graph-browser-download-reopened.json')
 audit=audit_stages(before,reopened,downloaded,require_deep=True);assert audit['status']=='PASS',str(audit)
finally:
 open_(bound)
restored=cap('r9-graph-working-restored.json');assert restored['document_geometry_material_sha256']==before['document_geometry_material_sha256']
original=P/'outputs/model/blank-disposable-p0-repaired-r2.skp';assert hashlib.sha256(original.read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
out={'status':'PASS','revision':9,'root_pid':20606,'collector':'KStudioNativeDefinitionGraph/1','before_save_ordering_proof':'r9-actual-pre-site-save-ordering.json','audit':audit,'original_r4_unchanged':True,'working_restored':True,'actual_browser_download':str(download),'download_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'elapsed_ms':round((time.monotonic()-start)*1000),'source_quality':'FAIL; independent Critic NEEDS_FIX','strict_program_replay':'NOT_RUN','customer_delivery':'NOT_READY'}
(D/'r9-native-delivery-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
