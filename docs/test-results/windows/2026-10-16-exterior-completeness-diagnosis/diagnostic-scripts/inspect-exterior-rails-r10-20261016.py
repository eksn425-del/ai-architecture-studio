from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
O=R/'runtime/exterior-completion-20261016';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));i=a.get_active_model_identity()
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
def en(e);e.is_a?(Sketchup::Group) ? e.entities : e.definition.entities;end
def w(e,p,d,rows)
 en(e).each{|c|next unless c.is_a?(Sketchup::Group)||c.is_a?(Sketchup::ComponentInstance);q=p+[c.name];b=c.bounds;rows<<{path:q,pid:c.persistent_id,locked:c.locked?,instances:c.definition.instances.length,bounds_mm:[b.min.to_a.map(&:to_mm),b.max.to_a.map(&:to_mm)],children:en(c).select{|z|z.is_a?(Sketchup::Group)||z.is_a?(Sketchup::ComponentInstance)}.map(&:name)};w(c,q,d-1,rows) if d>1 && !(c.name.match?(/(POST|RAIL|MESH|BAR|GRATING|BEAM|BALUSTER)/))}
end
rows=[];['CIRCULATION_EXTERNAL'].each{|n|g=en(r).find{|e|e.respond_to?(:name)&&e.name==n};w(g,[n],3,rows)}
{revision:r.get_attribute('sketchup_architect','revision'),geometry_writes:0,assemblies:rows}
'''.replace('GUID',json.dumps(i['model_guid']),1) # use placeholder carefully
s=s.replace('m.guid==GUID','m.guid=='+json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-exterior-rails-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual exterior guards and landing seams'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-exterior-rail-paths.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
for x in v['assemblies']:
 p=x['path']
 if 'RAIL' in p[-1] or 'RAMP_' in p[-1] or p[1]=='LANDINGS':print('/'.join(p),x['pid'],len(x['children']))
