from pathlib import Path
import json,sys,time
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=ROOT/'runtime/customer-readiness-20261015';P=ROOT/'runtime/projects/architecture-project-4f0e4';model=P/'outputs/model/blank-disposable-customer-readiness-r4-20261015.skp'
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));identity=ad.get_active_model_identity();assert Path(identity['model_path']).resolve()==model.resolve()
helper=(ROOT/'runtime/quality-diagnosis-20261015/read_geometry.rb').read_text(encoding='utf-8').replace("load File.join(Dir.pwd, 'app', 'native_deep_fingerprint.rb')",'load '+json.dumps((ROOT/'app/native_deep_fingerprint.rb').as_posix(),ensure_ascii=False))
helper=helper.replace("ENV.fetch('KS_DIAG_PATH','')",json.dumps(model.as_posix(),ensure_ascii=False)).replace("ENV.fetch('KS_DIAG_GUID','')",json.dumps(identity['model_guid']))
generated=_generated_script_dir()/f'studio-readonly-source-diagnosis-{time.time_ns()}.rb';generated.write_text(helper,encoding='utf-8')
start=time.monotonic();raw=ad.client.call('sketchup_eval_project_file',{'script_path':str(generated),'operation_name':'READ ONLY same-source r8 cross-sections and topology'})
if not isinstance(raw,dict) or raw.get('collector')!='KStudioReadOnlySourceGeometryDiagnosis/1':
 raw=raw.get('result') if isinstance(raw,dict) else raw
 if isinstance(raw,str):raw=json.loads(raw)
assert raw['collector']=='KStudioReadOnlySourceGeometryDiagnosis/1';assert ad.get_active_model_identity()==identity
(D/'r8-geometry-topology.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
env=next(g for g in raw['groups'] if g['name']=='ENVELOPE_OUTER');ties=next(g for g in env['children'] if g['name']=='TENSION_BRACING')
summary={'elapsed_ms':round((time.monotonic()-start)*1000),'sketchup':raw['sketchup_version'],'brace_path':ties['path'],'brace_pid':ties['pid'],'brace_count':len(ties['children']),'bars':[{'name':c['name'],'pid':c['pid'],'edge_lengths_mm':sorted(set(e['length_mm'] for e in c['edges'])),'bounds_mm':[[min(p[k] for p in c['vertices_world_mm']),max(p[k] for p in c['vertices_world_mm'])] for k in range(3)],'material':c['effective_material']} for c in ties['children']],'root_loose_faces':len(raw['root_own_loose']['faces']),'root_loose_edges':len(raw['root_own_loose']['edges']),'document_loose_faces':len(raw['document_own_loose']['faces']),'document_loose_edges':len(raw['document_own_loose']['edges'])}
(D/'r8-geometry-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False)[:4500])
