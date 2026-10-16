# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise '"884fd0ee-4b8b-49a2-ac14-5cff4d77166d"' unless m.guid=="884fd0ee-4b8b-49a2-ac14-5cff4d77166d"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Project' unless r&&r.get_attribute('sketchup_architect','project_id')=='architecture-project-4f0e4'
def bc_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def bc_inventory(g,t,path,out)
 w=t*g.transformation;b=g.definition.bounds;pts=(0..7).map{|j|w*b.corner(j)};mins=(0..2).map{|j|pts.map{|p|p[j].to_mm}.min};maxs=(0..2).map{|j|pts.map{|p|p[j].to_mm}.max}
 out<<{path:path,pid:g.persistent_id,type:g.typename,definition:g.definition.name,instances:g.definition.instances.length,locked:g.locked?,bounds_mm:{min:mins,max:maxs}}
 bc_es(g).each{|x|bc_inventory(x,w,path+[x.name],out) if x.is_a?(Sketchup::Group)||x.is_a?(Sketchup::ComponentInstance)}
end
rows=[];bc_inventory(r,Geom::Transformation.new,[],rows)
{geometry_writes:0,model_path:m.path,model_guid:m.guid,revision:r.get_attribute('sketchup_architect','revision'),root_pid:r.persistent_id,site:rows.select{|x|x[:path].first=='SITE_GROUND'},basic_nodes:rows.select{|x|x[:path].length<=2||x[:path].join('/').match?(/DOOR|WINDOW|GLASS|SPIRAL|STAIR|COLUMN|PARTITION/)},total_instance_occurrences:rows.length}
