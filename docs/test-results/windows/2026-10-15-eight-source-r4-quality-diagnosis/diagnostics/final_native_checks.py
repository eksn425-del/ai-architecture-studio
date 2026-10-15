from pathlib import Path
import sys,json,hashlib,time
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from app.project_ruby import ProjectRubyExecutor
from scripts.compare_native_replay import compare
from scripts.audit_scoped_native_edit import audit_scoped_edit
D=ROOT/'runtime/quality-diagnosis-20261015';P=ROOT/'runtime/projects/architecture-project-4f0e4';before=json.loads((D/'r4-before.json').read_text(encoding='utf-8'));model=P/'outputs/model/blank-disposable-r4-quality-diagnosis-20261015.skp'
client=ConfiguredSketchUpMCP(timeout_seconds=120);ad=SketchUpAdapter(client);identity=ad.get_active_model_identity();assert Path(identity['model_path']).resolve()==model.resolve()
after=ad.capture_native_deep_fingerprint(expected_model_path=model,expected_guid=identity['model_guid'],root_pid=20606,output_path=D/'r4-after-readonly.json');comparison=compare(before,after);assert comparison['status']=='PASS'
state=json.loads((P/'runtime/project_ruby_state.json').read_text(encoding='utf-8'))['scripts'];ex=ProjectRubyExecutor(ROOT/'runtime',P.name,expected_model_path=model,expected_model_guid=identity['model_guid'],mcp=client,ruby_state=state,adapter=ad)
paths=[[g['name']] for g in before['groups']];pids={tuple([g['name']]):g['pid'] for g in before['groups']}
for g in before['groups']:
 if g['name']=='ENVELOPE_OUTER':
  for child in g['children']:paths.append([g['name'],child['name']]);pids[(g['name'],child['name'])]=child['pid']
snapshots=ex.inspect_owned_batch('glass_curved_roof',paths)
assert len(snapshots)==len(paths)
assert all(row['persistent_id']==pids[tuple(path)] for row,path in zip(snapshots,paths))
def ids(nodes):
 return [(n['name'],n['pid'],ids(n['children'])) for n in nodes]
assert ids(before['document_groups'])==ids(after['document_groups'])
original=P/'outputs/model/blank-disposable-p0-repaired-r2.skp';assert hashlib.sha256(original.read_bytes()).hexdigest()=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
scope=audit_scoped_edit(before,after,allowed_direct_group='TENSION_BRACING',expected_before_document_sha='b3fb8fbde6ae874a78570201b78dbd635072b9204ca9881c8972d189bfd14e10');assert scope['status']=='BLOCKED'
receipt={'read_only_model_unchanged':comparison,'all_nested_pids_unchanged':True,'host_owned_path_readback':{'status':'PASS','paths_checked':len(paths),'paths':paths,'actual_snapshots':snapshots,'scope':'Existing ProjectRuby batch inspection PID/path/objects/bounds readback, NOT a new precommit KEEP transaction test'},'direct_scope_audit':scope,'original_r4_file_bytes_unchanged':True,'root_loose_entities_from_actual_geometry_collector':{'faces':0,'edges':0,'sha256':'a28faf6056254a2dec9bd1aca28a21d99ec6cc28dcf2985d95f6bae89317f51f'},'geometry_writes':0}
(D/'final-native-checks.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'no_change':comparison['status'],'nested_pids':'PASS','host_paths_checked':len(paths),'direct_scope':scope['status'],'original_file':'unchanged'}))
