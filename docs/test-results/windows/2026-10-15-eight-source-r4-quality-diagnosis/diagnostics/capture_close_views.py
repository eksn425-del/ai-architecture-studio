from pathlib import Path
import sys,json,time,shutil
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.agent_tools import canonical_camera_from_bounds_mm
from app.project_ruby import ProjectRubyExecutor
D=ROOT/'runtime/quality-diagnosis-20261015';P=ROOT/'runtime/projects/architecture-project-4f0e4';client=ConfiguredSketchUpMCP(timeout_seconds=120);ad=SketchUpAdapter(client)
identity=ad.get_active_model_identity();model=Path(identity['model_path']);assert model.name=='blank-disposable-r4-quality-diagnosis-20261015.skp'
state=json.loads((P/'runtime/project_ruby_state.json').read_text(encoding='utf-8'))['scripts'];ex=ProjectRubyExecutor(ROOT/'runtime',P.name,expected_model_path=model,expected_model_guid=identity['model_guid'],mcp=client,ruby_state=state,adapter=ad)
root_readback=ex.inspect_owned({'script_id':'glass_curved_roof','path':[],'offset':0,'limit':1})
bounds=json.loads(root_readback['contentItems'][0]['text'])['bounds_mm'];result={}
for name in ['front','rear','left','right','roof','oblique']:
 camera=canonical_camera_from_bounds_mm(bounds,name);ad.set_camera(camera['eye_m'],camera['target_m'],camera['up_m'])
 f=_generated_script_dir()/f'studio-camera-only-fov-{time.time_ns()}.rb';f.write_text('# ARCHFLOW_GENERATED_SCRIPT\nm=Sketchup.active_model\n'+f'raise "Wrong document" unless m.path=={json.dumps(str(model),ensure_ascii=False)} && m.guid=={json.dumps(identity["model_guid"])}\n'+'c=m.active_view.camera\nc.fov=15.0\nm.active_view.camera=c\n{fov:c.fov, eye:c.eye.to_a.map{|x|x.to_m},target:c.target.to_a.map{|x|x.to_m}}\n',encoding='utf-8')
 measured=client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'CAMERA ONLY closer canonical framing; no geometry edit'})
 target=P/'outputs/renders'/f'diagnosis-r4-canonical-close-{name}-20261015.png';ad.capture_view(target,width=1500,height=950,zoom_extents=False)
 receipt={'path':target.relative_to(P).as_posix(),'width':1500,'height':950,'quality_status':'not_accepted','model_revisions':{'glass_curved_roof':4},'camera_contract_version':1,'canonical_view':name,'canonical_script_id':'glass_curved_roof','camera':camera,'focus_bounds_mm':bounds,'camera_fov_degrees':15,'measured_camera':measured,'native_model_path':str(model),'native_model_guid':identity['model_guid'],'note':'Same deterministic eye/target/up, narrower FOV for readable QA. Camera-only; original wide shots retained.'}
 target.with_suffix('.evidence.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copy2(target,D/f'views/close-{name}.png');shutil.copy2(target.with_suffix('.evidence.json'),D/f'views/close-{name}.evidence.json');result[name]=target.relative_to(P).as_posix()
(D/'close-views-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result))
