from pathlib import Path
import sys,json,time,argparse
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();D=R/'runtime/customer-readiness-20261015';ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));i=ad.get_active_model_identity()
ruby='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model
raise 'Wrong model' unless m.guid==EXPECTED_GUID && File.expand_path(m.path)==File.expand_path(EXPECTED_PATH)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise 'Wrong owned project' unless r && r.get_attribute('sketchup_architect','project_id')=='architecture-project-4f0e4'
rows=[]
[[3600,1],[3600,-1],[7200,1],[7200,-1],[10800,1]].each do |z,side|
 [-3640,-3500,-2550,-2000,-1460,-500].each do |x|
  [20,100,1100,1800,2300,2500].each do |height|
   # Begin INSIDE the actual landing, not outside its intentionally guarded rim.
   y0=side==1 ? 25100 : -5100; y1=side==1 ? 22000 : -2000
   direction=Geom::Vector3d.new(0,-side,0)
   start=Geom::Point3d.new(x.mm,y0.mm,(z+height).mm)
   origin=start;hits=[]
   12.times do
    found=m.raytest([origin,direction],true);break unless found
    point,path=found;break if start.distance(point).to_mm>(y1-y0).abs+0.1
    hits << {point_mm:point.to_a.map{|v|v.to_mm.round(3)},distance_mm:start.distance(point).to_mm.round(3),
      entities:path.map{|e|{type:e.typename,pid:e.persistent_id,name:(e.respond_to?(:name) ? e.name : nil),material:(e.respond_to?(:material)&&e.material ? e.material.name : nil)}}}
    origin=point.offset(direction,1.mm)
   end
   rows << {level_mm:z,side:side,x_mm:x,height_mm:height,segment_y_mm:[y0,y1],hits:hits,clear:hits.empty?}
  end
 end
end
{collector:'KStudioNativeCorridorRayProbe/1',model_path:m.path,model_guid:m.guid,root_pid:r.persistent_id,revision:r.get_attribute('sketchup_architect','revision'),geometry_writes:0,rows:rows,limitations:'Sampled straight level receiving strips across estimated door width, near-floor, chest, head and above-door height; not a full navigation/accessibility/structural certification.'}
'''.replace('EXPECTED_GUID',json.dumps(i['model_guid'])).replace('EXPECTED_PATH',json.dumps(i['model_path'],ensure_ascii=False))
f=_generated_script_dir()/f'studio-corridor-readonly-{time.time_ns()}.rb';f.write_text(ruby,encoding='utf-8');out=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'READ ONLY corridor obstructions '+a.label})
if isinstance(out,dict) and 'result' in out:out=out['result']
if isinstance(out,str):out=json.loads(out)
assert out['collector']=='KStudioNativeCorridorRayProbe/1'
dest=D/f'corridor-rays-{a.label}.json';assert not dest.exists();dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
blocked=[x for x in out['rows'] if not x['clear']];names=sorted({e['name'] for row in blocked for hit in row['hits'] for e in hit['entities'] if e['name']})
print(json.dumps({'revision':out['revision'],'rays':len(out['rows']),'blocked':len(blocked),'hit_named_groups':names},ensure_ascii=False))
