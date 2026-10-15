from pathlib import Path
import sys,json,time,shutil
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
from app.project_ruby import ProjectRubyExecutor
from app.agent_tools import AgentToolSurface
D=ROOT/'runtime/quality-diagnosis-20261015';P=ROOT/'runtime/projects/architecture-project-4f0e4';model=P/'outputs/model/blank-disposable-r4-quality-diagnosis-20261015.skp'
client=ConfiguredSketchUpMCP(timeout_seconds=120);ad=SketchUpAdapter(client);identity=ad.get_active_model_identity();assert Path(identity['model_path']).resolve()==model.resolve()
state=json.loads((P/'runtime/project_ruby_state.json').read_text(encoding='utf-8'))['scripts']
ex=ProjectRubyExecutor(ROOT/'runtime',P.name,expected_model_path=model,expected_model_guid=identity['model_guid'],mcp=client,ruby_state=state,adapter=ad)
surface=AgentToolSurface(ROOT/'runtime',client,oss_backends={});(D/'views').mkdir(exist_ok=True);views={};events=[]
for name in ['front','rear','left','right','roof','oblique']:
 started=time.monotonic();r=surface.dispatch('sketchup_capture_canonical_view',{'script_id':'glass_curved_roof','view_name':name},project_dir=P,project_ruby=ex);e=r['visual_evidence'];p=P/e['path'];views[name]=e['path'];shutil.copy2(p,D/f'views/{name}.png');shutil.copy2(p.with_suffix('.evidence.json'),D/f'views/{name}.evidence.json');events.append({'action':'canonical','view':name,'elapsed_ms':round((time.monotonic()-started)*1000)})
cameras={
 'source01-ramp-end':([-68,12,10],[20,12,8],[0,0,1]),
 'source02-oblique':([-54,-47,29],[22,11,8],[0,0,1]),
 'source03-entry':([-25,-34,7],[8,7,3],[0,0,1]),
 'source03-gallery':([2,-2,1.7],[42,-2,3],[0,0,1]),
 'source04-upper-interior':([9,10,12.5],[44,10,12.5],[0,0,1]),
 'source04-double-height':([7,4,5],[35,11,6],[0,0,1]),
 'brace-close':([9,33,8],[10,22,9],[0,0,1]),
 'brace-connection':([8,25,15],[10,20,15.52],[0,0,1]),
 'ramp-junction':([-20,-10,5],[-5,-4,3.6],[0,0,1]),
 'floor-plan':([25,10,75],[25,10,0],[0,1,0])}
matched={}
for name,(eye,target,up) in cameras.items():
 started=time.monotonic();ad.set_camera(eye,target,up);dest=P/'outputs/renders'/f'diagnosis-r4-{name}-20261015.png';ad.capture_view(dest,width=1500,height=950,zoom_extents=False)
 receipt={'path':dest.relative_to(P).as_posix(),'width':1500,'height':950,'model_revisions':{'glass_curved_roof':4},'camera':{'eye_m':eye,'target_m':target,'up_m':up},'role':name,'source_alignment':'Matching source-facing orientation by observed landmarks; source intrinsics unknown, not calibrated photogrammetry.','native_model_path':str(model),'native_model_guid':identity['model_guid']}
 dest.with_suffix('.evidence.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copy2(dest,D/'views'/f'{name}.png');shutil.copy2(dest.with_suffix('.evidence.json'),D/'views'/f'{name}.evidence.json');matched[name]=dest.relative_to(P).as_posix();events.append({'action':'matched_camera','view':name,'elapsed_ms':round((time.monotonic()-started)*1000)})
(D/'views-manifest.json').write_text(json.dumps({'canonical':views,'matched':matched,'events':events,'geometry_writes':0},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'views':len(views),'matched':len(matched),'geometry_writes':0,'elapsed_ms':sum(e['elapsed_ms'] for e in events)}))
