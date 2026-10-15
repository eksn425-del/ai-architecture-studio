from pathlib import Path
import sys,json,copy,shutil,hashlib
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from app.project_ruby import ProjectRubyExecutor
D=R/'runtime/customer-readiness-20261015';P=R/'runtime/projects/architecture-project-4f0e4';T=D/'host-required-keep-probe';T.mkdir(exist_ok=True)
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));working=Path(ad.get_active_model_identity()['model_path']);probe=working.with_name('blank-disposable-r7-host-required-keep-probe-20261015.skp');assert not probe.exists();shutil.copy2(working,probe)
files=[P/'runtime/project_ruby_state.json',P/'runtime/active_edit_scope.json',P/'runtime/scripts/glass_curved_roof.rb'];saved={p:p.read_bytes() for p in files};state=json.loads(saved[files[0]])['scripts']
def open_(p):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
def cap(name):
 i=ad.get_active_model_identity();return ad.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=T/(name+'.json'))
try:
 open_(probe);before=cap('before');scope=[['ENVELOPE_OUTER','NORTH_BAY_0']];(P/'runtime/active_edit_scope.json').write_text(json.dumps({'status':'active','model_path':str(probe),'root_pid':20606,'allowed_paths':scope,'required_preserve_paths':[['ENVELOPE_OUTER','NORTH_BAY_0','MULLION']]}),encoding='utf-8')
 ex=ProjectRubyExecutor(R/'runtime',P.name,expected_model_path=probe,expected_model_guid=ad.get_active_model_identity()['model_guid'],mcp=ad.client,ruby_state=copy.deepcopy(state),adapter=ad)
 keep=json.loads(ex.inspect_owned({'script_id':'glass_curved_roof','paths':[['ENVELOPE_OUTER','NORTH_BAY_0','MULLION']]} )['contentItems'][0]['text'])['snapshots'];assert len(keep[0]['deep_geometry_material_sha256'])==64
 source="""env=root.entities.find{|e|e.respond_to?(:name)&&e.name=='ENVELOPE_OUTER'}
b=env.entities.find{|e|e.respond_to?(:name)&&e.name=='NORTH_BAY_0'}
es=b.is_a?(Sketchup::Group) ? b.entities : b.definition.entities
g=es.find{|e|e.respond_to?(:name)&&e.name=='GLASS'};g.transform!(Geom::Transformation.translation([0,0,1.mm]))
p=es.find{|e|e.respond_to?(:name)&&e.name=='MULLION'}
p.material=model.materials.find{|m|m!=p.material}
"""
 error=None
 try:ex.run({'script_id':'glass_curved_roof','ruby_source':source,'update_mode':'edit','allowed_mutation_paths':scope,'_keep_expectations':[]})
 except Exception as err:error=str(err)
 assert error and 'Path scope regression' in error,error
 assert (P/'runtime/scripts/glass_curved_roof.rb').read_bytes()==saved[files[2]], 'Aborted candidate source did not restore without legacy KEEP'
 after=cap('after');assert before['document_geometry_material_sha256']==after['document_geometry_material_sha256']
 (T/'actual-keep-before.json').write_text(json.dumps(keep,ensure_ascii=False,indent=2),encoding='utf-8')
 (T/'result.json').write_text(json.dumps({'status':'PASS','revision_unchanged':7,'fault':'Allowed bay glass mutated, then protected nested mullion material mutated with identical bounds/count/PID. Builder omitted preserve_paths/KEEP; host-required nested deep snapshot still rejects before commit. Entire transaction and candidate source rolled back.','error':error,'same_full_document_deep_sha':True,'real_website_model_modified':False},ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 for p,data in saved.items():p.write_bytes(data)
 open_(working);restored=cap('working-restored');assert restored['document_geometry_material_sha256']==before['document_geometry_material_sha256']
 for p in (P/'runtime/scripts/reports').glob('glass_curved_roof-r8*'):
  shutil.copy2(p,T/p.name)
print('Native HOST-required deep KEEP and failed candidate source restoration without legacy KEEP: PASS; working r7 restored')
