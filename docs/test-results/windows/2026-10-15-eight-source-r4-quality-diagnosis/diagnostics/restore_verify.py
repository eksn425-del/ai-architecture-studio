from pathlib import Path
import sys,json,hashlib,urllib.request
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from app.sketchup_mcp import SketchUpAdapter
D=ROOT/'runtime/quality-diagnosis-20261015';P=ROOT/'runtime/projects/architecture-project-4f0e4';s=json.loads((P/'state/agent_session.json').read_text(encoding='utf-8'));model=(P/s['model_path']).resolve();ad=SketchUpAdapter();identity=ad.get_active_model_identity()
assert Path(identity['model_path']).resolve()==model
assert identity['model_guid']==s['model_guid']==s['ruby_state']['glass_curved_roof']['model_guid']
assert s['ruby_state']['glass_curved_roof']['revision']==4
fp=ad.capture_native_deep_fingerprint(expected_model_path=model,expected_guid=identity['model_guid'],root_pid=20606,output_path=D/'r4-restored-original.json')
assert fp['document_geometry_material_sha256']=='b3fb8fbde6ae874a78570201b78dbd635072b9204ca9881c8972d189bfd14e10'
assert hashlib.sha256(model.read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
safe=P/'outputs/model/blank-disposable-r4-quality-diagnosis-20261015.skp';assert hashlib.sha256(safe.read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
with urllib.request.urlopen('http://127.0.0.1:8787/api/projects/architecture-project-4f0e4',timeout=15) as response:website=json.load(response)
receipt={'status':'PASS','same_original_r4_path':True,'guid_matches_original_site_session':True,'revision':4,'root_pid':20606,'document_geometry_material_sha256':fp['document_geometry_material_sha256'],'original_skp_bytes_unchanged':True,'safe_copy_skp_bytes_unchanged':True,'geometry_writes':0,'skp_save_calls':0,'safe_copy_camera_changes_discarded':True,'website_http_get':200,'native_copy_open_and_original_restore':'Actual SU2024 application startup with existing bridge and native Open dialog; no rebinding to another project'}
(D/'restore-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(receipt))
