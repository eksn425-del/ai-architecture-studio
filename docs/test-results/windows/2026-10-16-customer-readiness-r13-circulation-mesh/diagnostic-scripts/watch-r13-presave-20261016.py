from pathlib import Path
import sys,json,time,hashlib
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';receipt=P/'runtime/native_delivery_checkpoint.json';state=P/'runtime/project_ruby_state.json';dest=D/'r13-graph-before-site-final-save.json';assert not dest.exists()
while True:
 s=json.loads(state.read_text(encoding='utf8'))['scripts']['glass_curved_roof']
 if s['revision']>=13:break
 time.sleep(2)
old=json.loads(receipt.read_text(encoding='utf8'));assert s['revision']==13 and old['script_revisions']=={'glass_curved_roof':12},'Cannot claim presave proof after final save'
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();assert Path(i['model_path']).resolve()==(P/'outputs/model/blank-disposable-customer-readiness-r4-20261015.skp').resolve()
start=time.time_ns();raw=a.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=dest,representation='definition_graph');end=time.time_ns();new=json.loads(receipt.read_text(encoding='utf8'))
out={'captured_start_ns':start,'captured_end_ns':end,'receipt_revision_before':old['script_revisions'],'receipt_revision_after':new['script_revisions'],'native_committed_revision':s['revision'],'before_final_r13_save_proven':old['script_revisions']==new['script_revisions']=={'glass_curved_roof':12},'collector':raw['collector'],'document_sha':raw['document_geometry_material_sha256'],'native_helper_source_sha256':hashlib.sha256((R/'app/native_definition_graph.rb').read_bytes()).hexdigest(),'geometry_writes':0};assert out['before_final_r13_save_proven'];(D/'r13-actual-pre-site-save-ordering.json').write_text(json.dumps(out,indent=2),encoding='utf8');print('Actual r13 full native baseline captured before website final save; receipt stillr12',flush=True)
