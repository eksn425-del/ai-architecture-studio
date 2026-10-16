from pathlib import Path
import json,sys,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();policy=json.loads((P/'runtime/active_edit_scope.json').read_text(encoding='utf8'))
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'Wrong GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Not before r13' unless r.get_attribute('sketchup_architect','revision')==12
def en(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def resolve(r,path)
 g=r;parent=r.transformation
 path.each_with_index{|n,j|v=en(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Ambiguous '+n unless v.length==1;g=v.first;parent*=g.transformation if j<path.length-1}
 [g,parent]
end
def bb(g,parent);p=(0..7).map{|j|parent*g.bounds.corner(j)};[(0..2).map{|k|p.map{|v|v[k].to_mm}.min},(0..2).map{|k|p.map{|v|v[k].to_mm}.max}];end
paths=JSON.parse(PATHS);creates=JSON.parse(CREATES)
rows=(paths-creates).map do |path|
 g,parent=resolve(r,path);w=parent*g.transformation;posts=en(g).select{|e|e.respond_to?(:name)&&e.name.include?('POST')}.map{|e|{name:e.name,world_bounds_mm:bb(e,w)}}
 {path:path,pid:g.persistent_id,local_transform_column_major_native_inches:g.transformation.to_a,world_transform_column_major_native_inches:w.to_a,world_bounds_mm:bb(g,parent),post_world_bounds_mm:posts}
end
internal,parent=resolve(r,['CIRCULATION_INTERNAL']);it=parent*internal.transformation;treads=en(internal).select{|e|e.respond_to?(:name)&&e.name.start_with?('END_TREAD_')}.map{|g|{path:['CIRCULATION_INTERNAL',g.name],pid:g.persistent_id,world_bounds_mm:bb(g,it)}}
{revision:12,root_pid:20606,geometry_writes:0,coordinate_contract:'SketchUp Transformation.to_a column-major; translations are native inches, world bounds/post bounds explicitly mm. Convert world vertices through actual target-world inverse before writing local entities. Current ramp rail groups contain actual mirrored transforms; preserve source signed direction.',targets:rows,protected_existing_remote_treads:treads}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('PATHS',json.dumps(json.dumps(policy['allowed_paths']))).replace('CREATES',json.dumps(json.dumps(policy['allowed_creation_paths'])))
f=_generated_script_dir()/('studio-circulation-coordinates-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual mirrored rail transforms and protected end-tread coordinates'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v
for dest in [D/'circulation-preparation/native-coordinates-before-r13.json',P/'runtime/agent_workspace/notes/native-circulation-coordinate-readback.json']:dest.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
with (P/'runtime/agent_workspace/notes/reconstruction_card.md').open('a',encoding='utf8') as out:out.write('\n\nHost native coordinate proof: notes/native-circulation-coordinate-readback.json now contains actual31target matrices/world bounds/post bounds and72protected end tread bounds at r12. Matrices are column-major native inches; bounds explicitlymm. Preserve actual mirrored ramp-rail transforms; map world through target inverse rather than building world coordinates inside mirrored local groups. No geometry changed by this probe.\n')
print('Native before-r13 coordinates exported:',len(v['targets']),'existing targets,',len(v['protected_existing_remote_treads']),'protected treads')
