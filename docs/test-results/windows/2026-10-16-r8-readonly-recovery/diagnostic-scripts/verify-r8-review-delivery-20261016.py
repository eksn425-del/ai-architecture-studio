from pathlib import Path
import sys,json,shutil,hashlib,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from scripts.audit_native_delivery_stages import audit_stages
D=R/'runtime/customer-readiness-20261015';P=R/'runtime/projects/architecture-project-4f0e4';F=D/'r8-review-record';F.mkdir(exist_ok=True)
for rel in ['state/agent_session.json','state/model_state.json','runtime/project_ruby_state.json','runtime/native_delivery_checkpoint.json','runtime/scripts','runtime/agent_workspace/qa','runtime/agent_workspace/notes','runtime/agent_workspace/scripts']:
 src=P/rel;dest=F/rel
 if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
 elif src.is_file():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
review=json.loads((P/'runtime/agent_workspace/qa/visual_review.json').read_text(encoding='utf-8'));paths=set()
for x in review['views'].values() if isinstance(review['views'],dict) else review['views']:
 if isinstance(x,str):paths.add(x)
 elif isinstance(x,dict):paths.add(x.get('path',''))
for x in review['evidence_pairs']:paths.add(x['current_path'] if 'current_path' in x else x.get('screenshot_path',x.get('current_view','')))
# Exact certified files referenced in review may use image_path/view_path keys.
def collect(x):
 if isinstance(x,dict):
  for v in x.values():collect(v)
 elif isinstance(x,list):
  for v in x:collect(v)
 elif isinstance(x,str) and x.startswith('outputs/renders/') and x.endswith('.png'):paths.add(x)
collect(review)
for rel in paths:
 if not rel:continue
 src=P/rel
 if not src.is_file():continue
 dest=F/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 side=src.with_suffix('.evidence.json')
 if side.exists():shutil.copy2(side,dest.with_suffix('.evidence.json'))
events=P/'runtime/agent_events';old=R/'runtime/backups/20261015-customer-readiness-r4/runtime/agent_events'
for f in events.glob('*.jsonl'):
 if not (old/f.name).exists():
  dest=F/'runtime/agent_events'/f.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf-8'));assert session['ruby_state']['glass_curved_roof']['revision']==8
bound=(P/session['model_path']).resolve();ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));identity=ad.get_active_model_identity();assert Path(identity['model_path']).resolve()==bound
def cap(name):
 i=ad.get_active_model_identity();return ad.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=D/name)
live=cap('r8-review-live-before-controlled-save.json')
save=ad.save_model(bound,'Verify same website r8-review bound document save',expected_root_ids=[20606]);(D/'r8-review-controlled-save.json').write_text(json.dumps(save,ensure_ascii=False,indent=2),encoding='utf-8')
receipt=json.loads((P/'runtime/native_delivery_checkpoint.json').read_text(encoding='utf-8'));candidate=P/receipt['download_candidate']['path'];download=Path.home()/'Downloads'/candidate.name
assert download.is_file();assert hashlib.sha256(download.read_bytes()).hexdigest()==receipt['download_candidate']['sha256']
modeldir=F/'models';modeldir.mkdir(exist_ok=True);shutil.copy2(download,modeldir/'r8-review-actual-browser-download.skp');shutil.copy2(bound,modeldir/'r8-review-bound-working.skp')
clean=bound.with_name('blank-disposable-r8-review-browser-download-verification-20261015.skp');assert not clean.exists();shutil.copy2(download,clean)
def open_copy(target):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(target,i['model_guid'],expected_saved_path=i['model_path']);a=ad.get_active_model_identity();assert Path(a['model_path']).resolve()==target.resolve()
open_copy(bound);reopened=cap('r8-review-bound-reopened.json')
open_copy(clean);downloaded=cap('r8-review-browser-download-reopened.json')
audit=audit_stages(live,reopened,downloaded,require_deep=True);assert audit['status']=='PASS',str(audit)
open_copy(bound);restored=cap('r8-review-working-restored.json');assert restored['document_geometry_material_sha256']==live['document_geometry_material_sha256']
original=P/'outputs/model/blank-disposable-p0-repaired-r2.skp';assert hashlib.sha256(original.read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
out={'status':'PASS','revision':8,'scope':'Native delivery consistency only; whole-source and circulation use still PARTIAL/FAIL','website_edit_and_automatic_save':'real site request and r8-review committed checkpoint','browser_download':str(download),'download_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'controlled_followup_save':'Host native diagnostic save after genuine website checkpoint; live snapshot precedes this controlled save, not the earlier automatic save','audit':audit,'original_r4_unchanged':True,'root_pid':20606,'bound_restored':True,'final_identity':ad.get_active_model_identity()}
(D/'r8-review-delivery-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'r8-review_native_delivery':audit['status'],'same_source_quality':'FAIL','original_r4':'unchanged','bound_restored':True}))
