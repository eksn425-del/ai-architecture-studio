from pathlib import Path
import json,sys,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
D=R/'runtime/basic-closeout-20261017';D.mkdir(exist_ok=True);a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity()
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Project' unless r&&r.get_attribute('sketchup_architect','project_id')=='architecture-project-4f0e4'
def bc_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def bc_inventory(g,t,path,out)
 w=t*g.transformation;b=g.definition.bounds;pts=(0..7).map{|j|w*b.corner(j)};mins=(0..2).map{|j|pts.map{|p|p[j].to_mm}.min};maxs=(0..2).map{|j|pts.map{|p|p[j].to_mm}.max}
 out<<{path:path,pid:g.persistent_id,type:g.typename,definition:g.definition.name,instances:g.definition.instances.length,locked:g.locked?,bounds_mm:{min:mins,max:maxs}}
 bc_es(g).each{|x|bc_inventory(x,w,path+[x.name],out) if x.is_a?(Sketchup::Group)||x.is_a?(Sketchup::ComponentInstance)}
end
rows=[];bc_inventory(r,Geom::Transformation.new,[],rows)
{geometry_writes:0,model_path:m.path,model_guid:m.guid,revision:r.get_attribute('sketchup_architect','revision'),root_pid:r.persistent_id,site:rows.select{|x|x[:path].first=='SITE_GROUND'},basic_nodes:rows.select{|x|x[:path].length<=2||x[:path].join('/').match?(/DOOR|WINDOW|GLASS|SPIRAL|STAIR|COLUMN|PARTITION/)},total_instance_occurrences:rows.length}
'''.replace('GUID',json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-basic-closeout-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');(D/'basic-inventory-source.rb').write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only basic building and existing site before owner closeout'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(D/'basic-inventory-r19.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'revision':v['revision'],'site':v['site'],'basic_nodes':len(v['basic_nodes']),'all_occurrences':v['total_instance_occurrences']},ensure_ascii=False))
