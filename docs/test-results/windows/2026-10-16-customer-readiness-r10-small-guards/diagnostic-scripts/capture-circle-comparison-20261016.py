from pathlib import Path
import json,sys,time,argparse
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.modeling_quality import capture_camera_receipt,verified_camera_match
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['before','after'],required=True);p.add_argument('--revision',type=int,required=True);a=p.parse_args()
D=R/'runtime/customer-readiness-20261015/circle-camera-comparison';O=D/f'{a.stage}-r{a.revision}';O.mkdir(parents=True,exist_ok=True)
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));identity=ad.get_active_model_identity();model=Path(identity['model_path']);assert model.name=='blank-disposable-customer-readiness-r4-20261015.skp'
before=ad.capture_native_deep_fingerprint(expected_model_path=model,expected_guid=identity['model_guid'],root_pid=20606,output_path=O/'native-before.json',representation='definition_graph' if a.revision>=9 else 'expanded')
rows=[]
cameras={'source04-two-small-holes':([27,15,12.4],[17,10.5,11]),'small-hole-west':([15,14,12.3],[12,10.5,11]),'small-hole-east':([25.5,14,12.3],[22.5,10.5,11])}
for name,(eye,target) in cameras.items():
 ad.set_camera(eye,target,[0,0,1]);i=ad.get_active_model_identity()
 ruby='# ARCHFLOW_GENERATED_SCRIPT\nm=Sketchup.active_model\nraise "Wrong document" unless m.guid=='+json.dumps(i['model_guid'])+'\nr=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}\nraise "Wrong revision" unless r && r.get_attribute("sketchup_architect","revision")=='+str(a.revision)+'\nc=m.active_view.camera;c.perspective=true;c.aspect_ratio=0;c.fov=35\n{view_only:true,geometry_writes:0}\n'
 f=_generated_script_dir()/f'studio-view-only-circles-{time.time_ns()}.rb';f.write_text(ruby,encoding='utf-8');ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'View only actual source-facing circular guard evidence'})
 first=ad.get_camera_snapshot();dest=O/(name+'.png');ad.capture_view(dest,width=1500,height=950,zoom_extents=False);last=ad.get_camera_snapshot();meta={'revision':a.revision,'view':name,'stage':a.stage,'width':1500,'height':950,'geometry_writes':0,'source_alignment':'Source-facing landmarks; original photographic intrinsics unknown, not calibrated',**capture_camera_receipt(first,last)};assert meta['camera_verified_during_capture'];dest.with_suffix('.evidence.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');rows.append(meta)
i=ad.get_active_model_identity();after=ad.capture_native_deep_fingerprint(expected_model_path=model,expected_guid=i['model_guid'],root_pid=20606,output_path=O/'native-after.json',representation='definition_graph' if a.revision>=9 else 'expanded');assert before['document_geometry_material_sha256']==after['document_geometry_material_sha256']
(O/'capture-receipt.json').write_text(json.dumps({'captures':rows,'document_geometry_material_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
if a.stage=='after':
 prior=json.loads((D/'before-r9/capture-receipt.json').read_text(encoding='utf-8'))['captures'];pairs=[{'view':x['view'],'before_revision':9,'after_revision':a.revision,'same_actual_camera':verified_camera_match(next(z for z in prior if z['view']==x['view'])['native_camera'],x['native_camera'])} for x in rows];assert all(x['same_actual_camera'] for x in pairs);(D/'camera-pairs.json').write_text(json.dumps({'status':'PASS','pairs':pairs},ensure_ascii=False,indent=2),encoding='utf-8')
print('Three actual camera-bracketed source-facing captures, document geometry unchanged')
