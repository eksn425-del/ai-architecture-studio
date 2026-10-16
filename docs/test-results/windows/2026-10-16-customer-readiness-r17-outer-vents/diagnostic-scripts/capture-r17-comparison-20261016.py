from pathlib import Path
import sys,json,time,argparse
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.modeling_quality import capture_camera_receipt,verified_camera_match
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['before','after'],required=True);p.add_argument('--revision',type=int,required=True);z=p.parse_args()
D=R/'runtime/exterior-completion-20261016/camera-comparison';O=D/f'{z.stage}-r{z.revision}';assert not O.exists();O.mkdir(parents=True)
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();model=Path(i['model_path']);assert model.name=='blank-disposable-customer-readiness-r4-20261015.skp'
before=a.capture_native_deep_fingerprint(expected_model_path=model,expected_guid=i['model_guid'],root_pid=20606,output_path=O/'native-before.json',representation='definition_graph');rows=[]
cameras={'source01-ramp-end':([-58,10,20],[12,10,7]),'source02-exterior-corner':([-49,-52,30],[19,9,7]),'source03-entrance':([-22,-30,5],[3,2,4]),'reverse-exterior-corner':([75,58,24],[30,10,7]),'guard-macro':([12,-9,5.6],[14,-4,4.1]),'remote-stair':([66,16,10],[50.7,4.5,6]),'remote-stair-low':([60,12,4.5],[51,4,2.5])}
for name,(eye,target) in cameras.items():
 a.set_camera(eye,target,[0,0,1]);i=a.get_active_model_identity()
 s='# ARCHFLOW_GENERATED_SCRIPT\nm=Sketchup.active_model\nraise "Wrong GUID" unless m.guid=='+json.dumps(i['model_guid'])+'\nr=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}\nraise "Wrong revision" unless r.get_attribute("sketchup_architect","revision")=='+str(z.revision)+'\nc=m.active_view.camera;c.perspective=true;c.aspect_ratio=0;c.fov=30\n{view_only:true,geometry_writes:0}\n'
 f=_generated_script_dir()/('studio-exterior-camera-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'View only exterior source comparison'})
 first=a.get_camera_snapshot();dest=O/(name+'.png');a.capture_view(dest,width=1500,height=950,zoom_extents=False);last=a.get_camera_snapshot();m={'revision':z.revision,'view':name,'stage':z.stage,'source_alignment':'Source-facing landmarks, original photographic intrinsics unknown; not calibrated','geometry_writes':0,**capture_camera_receipt(first,last)};assert m['camera_verified_during_capture'];dest.with_suffix('.evidence.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8');rows.append(m)
i=a.get_active_model_identity();after=a.capture_native_deep_fingerprint(expected_model_path=model,expected_guid=i['model_guid'],root_pid=20606,output_path=O/'native-after.json',representation='definition_graph');assert before['document_geometry_material_sha256']==after['document_geometry_material_sha256']
(O/'capture-receipt.json').write_text(json.dumps({'captures':rows,'document_geometry_material_unchanged':True},ensure_ascii=False,indent=2),encoding='utf8')
if z.stage=='after':
 prior=json.loads((D/'after-r16/capture-receipt.json').read_text(encoding='utf8'))['captures'];pairs=[{'view':x['view'],'before_revision':16,'after_revision':z.revision,'same_actual_camera':verified_camera_match(next(q for q in prior if q['view']==x['view'])['native_camera'],x['native_camera'])} for x in rows];assert all(q['same_actual_camera'] for q in pairs);(D/f'camera-pairs-r16-r{z.revision}.json').write_text(json.dumps({'status':'PASS','pairs':pairs},indent=2),encoding='utf8')
print('Captured7 bracketed actual cameras; no geometry changed')
