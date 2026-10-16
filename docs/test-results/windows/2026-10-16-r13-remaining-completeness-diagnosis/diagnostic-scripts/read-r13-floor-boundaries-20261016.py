from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/exterior-completion-20261016';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity()
s='''# ARCHFLOW_GENERATED_SCRIPT
begin
m=Sketchup.active_model;raise 'Identity' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==13
def fb_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def fb_child(g,n);v=fb_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing' unless v.size==1;v.first;end
fl=fb_child(r,'FLOORS');rows=fb_es(fl).select{|e|e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}.map do |g|
 t=r.transformation*fl.transformation*g.transformation;faces=fb_es(g).grep(Sketchup::Face);tops=faces.select{|f|f.normal.z>0.9};raise 'Missing top' if tops.empty?
 {path:['FLOORS',g.name],pid:g.persistent_id,top_faces:tops.map{|f|{normal:f.normal.to_a,loops:f.loops.map{|l|{outer:l.outer?,vertices_mm:l.vertices.map{|v|(t*v.position).to_a.map(&:to_mm)}}}}}}
end
en=fb_child(r,'ENVELOPE_OUTER');can=fb_child(en,'BUFFER_CANOPIES');inner=fb_child(en,'INNER_GLAZING')
{revision:13,geometry_writes:0,actual_floor_top_boundaries:rows,canopy_children:fb_es(can).select{|g|g.respond_to?(:name)}.map{|g|{name:g.name,pid:g.persistent_id,bounds_mm:[g.bounds.min.to_a.map(&:to_mm),g.bounds.max.to_a.map(&:to_mm)],own_faces:fb_es(g).grep(Sketchup::Face).size}},inner_glazing_children:fb_es(inner).select{|g|g.respond_to?(:name)}.map{|g|{name:g.name,pid:g.persistent_id,bounds_mm:[g.bounds.min.to_a.map(&:to_mm),g.bounds.max.to_a.map(&:to_mm)]}}}
rescue => e
 {diagnostic_error:e.message,backtrace:e.backtrace.first(5),geometry_writes:0}
end
'''.replace('GUID',json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-r13-floor-boundaries-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual floor top loops and remaining enclosure targets'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v
(D/'r13-floor-boundaries-native.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');assert 'diagnostic_error' not in v,str(v);print(json.dumps({'floors':len(v['actual_floor_top_boundaries']),'canopy':v['canopy_children'],'inner_children':len(v['inner_glazing_children'])},ensure_ascii=False))
