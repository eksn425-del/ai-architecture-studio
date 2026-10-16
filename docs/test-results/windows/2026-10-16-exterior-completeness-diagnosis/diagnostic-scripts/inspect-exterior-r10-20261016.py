from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R))
from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
O=R/'runtime/exterior-completion-20261016';O.mkdir(exist_ok=True)
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();(O/'identity-before.json').write_text(json.dumps(i,indent=2),encoding='utf8')
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model
raise 'Wrong document' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Wrong project/revision' unless r && r.get_attribute('sketchup_architect','project_id')=='architecture-project-4f0e4' && r.get_attribute('sketchup_architect','revision')==10
def en(e);e.is_a?(Sketchup::Group) ? e.entities : e.definition.entities;end
def walk(e,p,t,d,rows)
 en(e).each{|c|next unless c.is_a?(Sketchup::Group)||c.is_a?(Sketchup::ComponentInstance);q=p+[c.name];w=t*c.transformation;b=c.bounds;rows<<{path:q,pid:c.persistent_id,type:c.typename,definition_instances:c.definition.instances.length,material:c.material ? {name:c.material.name,color:c.material.color.to_a,alpha:c.material.alpha} : nil,bounds_parent_mm:[b.min.to_a.map{|x|x.to_mm},b.max.to_a.map{|x|x.to_mm}],child_groups:en(c).count{|z|z.is_a?(Sketchup::Group)||z.is_a?(Sketchup::ComponentInstance)},own_faces:en(c).grep(Sketchup::Face).length};walk(c,q,w,d-1,rows) if d>1}
end
rows=[];walk(r,[],r.transformation,3,rows)
{revision:10,root_pid:20606,sketchup_version:Sketchup.version,geometry_writes:0,groups:rows,rendering:m.rendering_options.keys.to_h{|k|[k,m.rendering_options[k]]}}
'''.replace('GUID',json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-exterior-inventory-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only complete exterior assemblies and actual dimensions'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-exterior-inventory.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'identity':i,'revision':v['revision'],'assemblies':[x for x in v['groups'] if len(x['path'])<=2],'rendering':v['rendering']},ensure_ascii=False))
a.set_camera([-35,60,24],[18,10,7],[0,0,1]);a.capture_view(O/'current-r10-exterior.png',zoom_extents=False)
