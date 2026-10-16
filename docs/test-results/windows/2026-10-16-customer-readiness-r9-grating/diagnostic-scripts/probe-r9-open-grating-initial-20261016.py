from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/customer-readiness-20261015';ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));i=ad.get_active_model_identity();targets=json.loads((D/'grating-target-inventory-r8.json').read_text(encoding='utf-8'))['targets']
source='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model
raise 'Wrong identity' unless m.guid==EXPECTED_GUID && File.expand_path(m.path)==File.expand_path(EXPECTED_PATH)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise 'Wrong revision' unless r && r.get_attribute('sketchup_architect','revision')==9
rows=[]
TARGETS.each do |item|
 g=r;world=r.transformation
 item['path'].each{|name|es=g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;a=es.select{|e|e.respond_to?(:name)&&e.name==name};raise 'Ambiguous target' unless a.length==1;g=a.first;world=world*g.transformation}
 raise 'Target PID changed' unless g.persistent_id==item['pid']
 # All approved leaves have identity transforms, independently verified by
 # the native precommit guard and source script outline assertions.
 b=g.bounds;x0=b.min.x.to_mm;x1=b.max.x.to_mm;y0=b.min.y.to_mm;y1=b.max.y.to_mm;z=b.max.z.to_mm
 along_x=(x1-x0)>=(y1-y0)
 probes=[['open_cell',220,280],['bearing_bar',1.5,280],['cross_bar',220,1.5]]
 samples=probes.map do |label,u,v|
  x,y=along_x ? [x0+u,y0+v] : [x1-v,y0+u]
  start=world*Geom::Point3d.new(x.mm,y.mm,(z+20).mm)
  direction=Geom::Vector3d.new(0,0,-1).transform(world).normalize
  hit=m.raytest([start,direction],true)
  distance=hit ? start.distance(hit[0]).to_mm : nil
  own=hit && hit[1].any?{|e|e.respond_to?(:persistent_id)&&e.persistent_id==g.persistent_id}
  pass=label=='open_cell' ? (!hit || distance>180.01) : (own && (distance-20).abs<0.01)
  {kind:label,point_mm:start.to_a.map{|v|v.to_mm},first_hit_distance_mm:distance,first_hit_owned_target:!!own,pass:!!pass,hit_path:hit ? hit[1].map{|e|{pid:e.persistent_id,name:e.respond_to?(:name) ? e.name : nil,type:e.typename}} : nil}
 end
 rows<<{path:item['path'],pid:g.persistent_id,local_parent_bounds_mm:[b.min.to_a.map{|v|v.to_mm},b.max.to_a.map{|v|v.to_mm}],probes:samples}
end
{collector:'KStudioNativeOpenGratingProbe/1',revision:9,model_path:m.path,model_guid:m.guid,root_pid:20606,geometry_writes:0,rows:rows,limitations:'One actual open cell plus two solid top-bar controls per selected target. Discrete evidence, not uniform load-bearing or accessibility certification.'}
'''.replace('EXPECTED_GUID',json.dumps(i['model_guid'])).replace('EXPECTED_PATH',json.dumps(i['model_path'],ensure_ascii=False)).replace('TARGETS', 'JSON.parse('+json.dumps(json.dumps(targets))+')')
f=_generated_script_dir()/f'studio-readonly-r9-grating-probe-{time.time_ns()}.rb';f.write_text(source,encoding='utf-8');v=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'READ ONLY actual open cells and solid bar controls in thirteen grating targets'});v=v.get('result',v) if isinstance(v,dict) else v;v=json.loads(v) if isinstance(v,str) else v;assert v['collector']=='KStudioNativeOpenGratingProbe/1';(D/'r9-open-grating-probe.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');print({'targets':len(v['rows']),'probes':39,'failures':[(r['path'],p['kind']) for r in v['rows'] for p in r['probes'] if not p['pass']]})
