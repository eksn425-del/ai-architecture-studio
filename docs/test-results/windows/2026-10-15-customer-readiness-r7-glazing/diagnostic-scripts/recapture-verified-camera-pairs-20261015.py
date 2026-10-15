from pathlib import Path
import sys,json,shutil,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
from app.modeling_quality import capture_camera_receipt,verified_camera_match
D=R/'runtime/customer-readiness-20261015';P=R/'runtime/projects/architecture-project-4f0e4';F=D/'verified-camera-comparison';F.mkdir(exist_ok=True)
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));working=Path(ad.get_active_model_identity()['model_path'])
versions={4:P/'outputs/model/blank-disposable-p0-repaired-r2.skp',5:D/'r5-record/models/r5-actual-browser-download.skp',6:D/'r6-record/models/r6-actual-browser-download.skp',7:D/'r7-record/models/r7-actual-browser-download.skp'}
cameras={'source01-ramp-end':([-68,12,10],[20,12,8],[0,0,1]),'source02-oblique':([-54,-47,29],[22,11,8],[0,0,1]),'source03-entry':([-25,-34,7],[8,7,3],[0,0,1]),'source03-gallery':([2,-2,1.7],[42,-2,3],[0,0,1]),'source04-upper-interior':([9,10,12.5],[44,10,12.5],[0,0,1]),'source04-double-height':([7,4,5],[35,11,6],[0,0,1]),'brace-close':([9,33,8],[10,22,9],[0,0,1]),'ramp-junction':([-20,-10,5],[-5,-4,3.6],[0,0,1])}
allrows=[]
def open_(p):
 i=ad.get_active_model_identity();ad.open_copy_from_unsaved_model(p,i['model_guid'],expected_saved_path=i['model_path'])
try:
 for rev,source in versions.items():
  target=P/'outputs/model'/f'blank-disposable-camera-proof-r{rev}-20261015.skp';assert not target.exists();shutil.copy2(source,target);open_(target)
  out=F/f'r{rev}';out.mkdir(exist_ok=True);i=ad.get_active_model_identity()
  before=ad.capture_native_deep_fingerprint(expected_model_path=target,expected_guid=i['model_guid'],root_pid=20606,output_path=out/'native-before.json')
  for name,(eye,look,up) in cameras.items():
   ad.set_camera(eye,look,up);a=ad.get_camera_snapshot();dest=out/(name+'.png');ad.capture_view(dest,width=1500,height=950,zoom_extents=False);b=ad.get_camera_snapshot();receipt=capture_camera_receipt(a,b);assert receipt['camera_verified_during_capture']
   meta={'revision':rev,'path':dest.relative_to(F).as_posix(),'width':1500,'height':950,'role':name,'geometry_writes':0,'temporal_scope':'Fresh recapture from immutable historical saved revision, not contemporaneous pre-edit evidence','source_alignment':'Same source-facing orientation selected by landmarks; original photograph intrinsics unknown, not calibrated source camera',**receipt};dest.with_suffix('.evidence.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');allrows.append(meta)
  i=ad.get_active_model_identity();after=ad.capture_native_deep_fingerprint(expected_model_path=target,expected_guid=i['model_guid'],root_pid=20606,output_path=out/'native-after.json');assert before['document_geometry_material_sha256']==after['document_geometry_material_sha256']
finally:open_(working)
pairs=[]
for a in allrows:
 if a['revision']!=4:continue
 for rev in [5,6,7]:
  b=next(x for x in allrows if x['revision']==rev and x['role']==a['role']);pairs.append({'before':a['path'],'after':b['path'],'role':a['role'],'revision_pair':[4,rev],'same_actual_camera':verified_camera_match(a['native_camera'],b['native_camera']),'before_camera':a['native_camera'],'after_camera':b['native_camera'],'image_size_equal':[a['width'],a['height']]==[b['width'],b['height']]})
assert len(pairs)==24 and all(x['same_actual_camera'] and x['image_size_equal'] for x in pairs)
(F/'camera-pairs.json').write_text(json.dumps({'status':'PASS','pair_count':24,'capture_count':32,'pairs':pairs,'prior_null_camera_pair_claim':'INVALID; old missing camera sidecars cannot prove equality; preserved as historical error','scope':'New controlled recapture comparison only; source photographic camera uncalibrated','working_restored':True},ensure_ascii=False,indent=2),encoding='utf-8');print('32 actual camera-bracketed captures /24 matched pairs PASS; model unchanged, working restored')
