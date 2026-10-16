from pathlib import Path
import json,sys,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/customer-readiness-20261015';ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));identity=ad.get_active_model_identity()
ruby='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model
raise 'Unexpected identity' unless m.guid==EXPECTED_GUID && File.expand_path(m.path)==File.expand_path(EXPECTED_PATH)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise 'Unexpected root/revision' unless r && r.get_attribute('sketchup_architect','revision')==8
segments=[]
[-8300,-7400,-6500].each{|x|segments<<{name:'flight_1',a:[x,-3990,3600.0*10/28000],b:[x,23990,3600-3600.0*10/28000]}}
segments<<{name:'lowest_north_landing',a:[-7400,24500,3600],b:[-800,24500,3600]}
segments<<{name:'lowest_north_entry',a:[-800,24500,3600],b:[-800,23500,3600]}
[2,3].each{|i|[-3700,-2800,-1900].each{|x|segments<<{name:"flight_#{i}",a:[x,-2990,(i-1)*3600+3600.0*10/26000],b:[x,22990,i*3600-3600.0*10/26000]}}}
[3600,7200].each do |z|
 segments<<{name:"return_Z#{z}",a:[-800,23500,z],b:[-800,-3500,z]}
 segments<<{name:"departure_Z#{z}",a:[-800,-3500,z],b:[-2800,-3500,z]}
end
[7200,10800].each{|z|segments<<{name:"arrival_Z#{z}",a:[-2800,23500,z],b:[-800,23500,z]}}
rows=[];floor_samples=[]
segments.each do |s|
 (0..10).each do |k|
  t=k/10.0;xyz=(0..2).map{|j|s[:a][j]+(s[:b][j]-s[:a][j])*t}
  origin=Geom::Point3d.new(xyz[0].mm,xyz[1].mm,(xyz[2]+5).mm)
  hit=m.raytest([origin,Geom::Vector3d.new(0,0,-1)],true)
  gap=hit ? hit[0].z.to_mm-xyz[2] : nil
  floor_samples<<{name:s[:name],point_mm:xyz,support_offset_mm:gap,pass:gap && gap.abs<10}
 end
 [100,1100,1800].each do |h|
  a=Geom::Point3d.new(*s[:a].each_with_index.map{|v,i|(v+(i==2 ? h : 0)).mm})
  b=Geom::Point3d.new(*s[:b].each_with_index.map{|v,i|(v+(i==2 ? h : 0)).mm})
  v=b-a;found=m.raytest([a,v],true)
  hit=found && a.distance(found[0])<a.distance(b)-0.1.mm
  rows<<{name:s[:name],a_mm:s[:a],b_mm:s[:b],height_mm:h,clear:!hit,hit:hit ? {point_mm:found[0].to_a.map{|u|u.to_mm.round(3)},path:found[1].map{|e|{pid:e.persistent_id,name:e.respond_to?(:name) ? e.name : nil,type:e.typename}}} : nil}
 end
end
{collector:'KStudioNativeWalkingLineProbe/1',model_path:m.path,model_guid:m.guid,root_pid:r.persistent_id,revision:8,geometry_writes:0,rows:rows,floor_samples:floor_samples,limitations:'Finite center and offset body-height lines along three flights and estimated return/departure/arrival routes, with discrete support samples. Not swept-body navigation, accessibility, guard or structural certification.'}
'''.replace('EXPECTED_GUID',json.dumps(identity['model_guid'])).replace('EXPECTED_PATH',json.dumps(identity['model_path'],ensure_ascii=False))
f=_generated_script_dir()/f'studio-readonly-r8-walking-lines-{time.time_ns()}.rb';f.write_text(ruby,encoding='utf-8')
out=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'READ ONLY r8 slope and return body-height lines'})
if isinstance(out,dict) and 'result' in out:out=out['result']
if isinstance(out,str):out=json.loads(out)
assert out['collector']=='KStudioNativeWalkingLineProbe/1'
(D/'r8-walking-lines.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sampled_lines':len(out['rows']),'blocked':[x for x in out['rows'] if not x['clear']],'support_samples':len(out['floor_samples']),'support_failures':[x for x in out['floor_samples'] if not x['pass']],'geometry_writes':0},ensure_ascii=False))
