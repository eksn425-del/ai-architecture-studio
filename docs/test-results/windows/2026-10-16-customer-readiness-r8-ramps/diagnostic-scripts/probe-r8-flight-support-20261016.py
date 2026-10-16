from pathlib import Path
import json,sys,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/customer-readiness-20261015'
ad=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));identity=ad.get_active_model_identity()
ruby='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model
raise 'Unexpected native identity' unless m.guid==EXPECTED_GUID && File.expand_path(m.path)==File.expand_path(EXPECTED_PATH)
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise 'Unexpected project/revision' unless r && r.get_attribute('sketchup_architect','project_id')=='architecture-project-4f0e4' && r.get_attribute('sketchup_architect','revision')==8
rows=[]
def probe(m,x,y,z,kind)
 p=Geom::Point3d.new(x.mm,y.mm,(z+5).mm)
 below=m.raytest([p,Geom::Vector3d.new(0,0,-1)],true)
 above=m.raytest([p,Geom::Vector3d.new(0,0,1)],true)
 describe=lambda{|h| h ? {point_mm:h[0].to_a.map{|v|v.to_mm.round(3)},path:h[1].map{|e|{pid:e.persistent_id,name:(e.respond_to?(:name) ? e.name : nil),type:e.typename}}} : nil}
 gap=below ? below[0].z.to_mm-z : nil
 clear=above ? above[0].z.to_mm-z : nil
 {kind:kind,point_mm:[x,y,z],support:describe.call(below),support_offset_mm:gap,head_obstruction:describe.call(above),head_clearance_mm:clear,support_pass:gap && gap.abs<10,headroom_pass:clear.nil? || clear>=2200}
end
[2,3].each{|i|[-3800,-2800,-1800].each{|x|(0..26).each{|k|y=-3000+k*1000.0;z=(i-1)*3600+3600.0*(y+3000)/26000;rows<<probe(m,x,y,z,"RAMP_#{i}")}}}
[[3600,-3500],[7200,-3500],[7200,23500],[10800,23500]].each{|z,y|[-3800,-2800,-1800].each{|x|rows<<probe(m,x,y,z,'flat_receiver')}}
[7200,10800].each{|z|[-3500,10000,23500].each{|y|rows<<probe(m,-800,y,z,'retained_return_strip')}}
{collector:'KStudioNativeFlightSupportAndHeadroom/1',model_path:m.path,model_guid:m.guid,root_pid:r.persistent_id,revision:8,geometry_writes:0,rows:rows,limitations:'Discrete vertical samples of actual native visible geometry. Not whole-route navigation, accessibility, guard completeness or structural certification.'}
'''.replace('EXPECTED_GUID',json.dumps(identity['model_guid'])).replace('EXPECTED_PATH',json.dumps(identity['model_path'],ensure_ascii=False))
f=_generated_script_dir()/f'studio-readonly-r8-support-{time.time_ns()}.rb';f.write_text(ruby,encoding='utf-8')
out=ad.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'READ ONLY r8 flight support and head clearance'})
if isinstance(out,dict) and 'result' in out:out=out['result']
if isinstance(out,str):out=json.loads(out)
assert out['collector']=='KStudioNativeFlightSupportAndHeadroom/1'
(D/'r8-flight-support-and-headroom.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'samples':len(out['rows']),'support_failures':sum(not x['support_pass'] for x in out['rows']),'headroom_failures':sum(not x['headroom_pass'] for x in out['rows']),'geometry_writes':0}))
