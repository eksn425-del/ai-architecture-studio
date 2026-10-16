from pathlib import Path
import json,sys,shutil,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.modeling_quality import capture_camera_receipt,verified_camera_match
D=R/'runtime/customer-readiness-20261015';P=R/'runtime/projects/architecture-project-4f0e4';F=D/'grating-corrected-recaptures';F.mkdir(exist_ok=True)
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));working=Path(ad.get_active_model_identity()['model_path']);rows=[]
versions={8:P/'outputs/model/blank-disposable-r8-before-grating-20261016.skp',9:Path.home()/'Downloads/agent-checkpoint-5374ca398451.skp'}
cameras={'source03-underside':([2,-2,1.7],[42,-2,3]),'source03-deck':([6,-12,7],[18,2,5.2]),'ramp-slots':([-15,-10,9],[-2,10,7])}
def open_(target):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(target,i['model_guid'],expected_saved_path=i['model_path'])
def cap(target,out,rep):
 i=ad.get_active_model_identity();return ad.capture_native_deep_fingerprint(expected_model_path=target,expected_guid=i['model_guid'],root_pid=20606,output_path=out,representation=rep)
try:
 for rev,source in versions.items():
  target=P/'outputs/model'/f'blank-disposable-grating-camera-r{rev}-20261016.skp';assert not target.exists();shutil.copy2(source,target);open_(target);O=F/f'r{rev}';O.mkdir(exist_ok=True);rep='definition_graph' if rev==9 else 'expanded';before=cap(target,O/'native-before.json',rep)
  if rev==8:
   graph=cap(target,O/'native-definition-graph.json','definition_graph')
   assert graph['counts']==before['counts']
   assert {n['name']:n['counts'] for n in graph['groups']}=={n['name']:n['counts'] for n in before['groups']}
   (O/'legacy-versus-graph-coverage.json').write_text(json.dumps({'status':'COUNTS_AND_ALL_DIRECT_GROUP_COUNTS_MATCH','legacy_document_sha':before['document_geometry_material_sha256'],'graph_document_sha':graph['document_geometry_material_sha256'],'hashes_not_interchangeable':True,'counts':graph['counts']},indent=2),encoding='utf-8')
  for name,(eye,target_) in cameras.items():
   ad.set_camera(eye,target_,[0,0,1]);i=ad.get_active_model_identity();s='# ARCHFLOW_GENERATED_SCRIPT\nm=Sketchup.active_model\nraise "Wrong identity" unless m.guid=='+json.dumps(i['model_guid'])+'\nc=m.active_view.camera;c.perspective=true;c.aspect_ratio=0;c.fov=35;m.active_view.refresh\n{view_only:true,geometry_writes:0}\n';f=_generated_script_dir()/f'studio-grating-view-{time.time_ns()}.rb';f.write_text(s,encoding='utf-8');ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'View only corrected source-facing camera, fixed-aspect mask disabled'})
   a=ad.get_camera_snapshot();dest=O/(name+'.png');ad.capture_view(dest,width=1500,height=950,zoom_extents=False);b=ad.get_camera_snapshot();meta={'revision':rev,'view':name,'width':1500,'height':950,'geometry_writes':0,'temporal_scope':'Fresh controlled recapture from saved r8/r9; original fixed-aspect dark captures retained as failed visual evidence','source_alignment':'Source-facing landmarks; original photographic intrinsics unknown',**capture_camera_receipt(a,b)};assert meta['camera_verified_during_capture'];dest.with_suffix('.evidence.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');rows.append(meta)
  after=cap(target,O/'native-after.json',rep);assert before['document_geometry_material_sha256']==after['document_geometry_material_sha256']
finally:
 open_(working)
pairs=[]
for x in rows:
 if x['revision']!=8:continue
 y=next(v for v in rows if v['revision']==9 and v['view']==x['view']);pairs.append({'view':x['view'],'same_actual_camera':verified_camera_match(x['native_camera'],y['native_camera']),'before':x['native_camera'],'after':y['native_camera']})
assert len(pairs)==3 and all(x['same_actual_camera'] for x in pairs)
(F/'camera-pairs.json').write_text(json.dumps({'status':'PASS','pairs':pairs,'capture_count':6,'working_restored':True,'note':'Corrected fresh saved-version recaptures; original contemporaneous fixed-aspect captures are dark and not quality acceptance.'},ensure_ascii=False,indent=2),encoding='utf-8');print('6 corrected recaptures /3 actual camera matches; saved models unchanged; native r8 legacy/graph coverage matches')
