# ARCHFLOW_GENERATED_SCRIPT; HOST READ ONLY geometry diagnosis, no save or entity writes.
require 'json'
load File.join(Dir.pwd, 'app', 'native_deep_fingerprint.rb') unless defined?(KStudioNativeDeepFingerprint)
m=Sketchup.active_model
raise 'Wrong document' unless File.expand_path(m.path)==File.expand_path(ENV.fetch('KS_DIAG_PATH',''))
raise 'Wrong GUID' unless m.guid==ENV.fetch('KS_DIAG_GUID','')
raise 'Exit active edit' unless m.active_path.nil?
root=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise 'Wrong root' unless root && root.name=='Architecture architecture-project-4f0e4'
def diag_mm(p,t)
 q=t*p;[q.x.to_mm.round(3),q.y.to_mm.round(3),q.z.to_mm.round(3)]
end
def diag_material(x)
 return nil unless x
 {name:x.name,rgba:[x.color.red,x.color.green,x.color.blue,x.alpha]}
end
def diag_node(e,parent,path,inherited=nil)
 world=parent*e.transformation
 entities=e.is_a?(Sketchup::Group) ? e.entities : e.definition.entities
 points=entities.grep(Sketchup::Edge).flat_map{|edge|edge.vertices.map{|v|diag_mm(v.position,world)}}.uniq
 material=e.material || inherited
 {
  path:path+[e.name],pid:e.persistent_id,name:e.name,local_transform:KStudioNativeDeepFingerprint.matrix(e.transformation),world_transform:KStudioNativeDeepFingerprint.matrix(world),
  material:diag_material(e.material),effective_material:diag_material(material),hidden:e.hidden?,locked:e.locked?,definition_instances:e.definition.instances.length,
  faces:entities.grep(Sketchup::Face).map{|f|{pid:f.persistent_id,loops:f.loops.map{|l|{outer:l.outer?,points:l.vertices.map{|v|diag_mm(v.position,world)}}},normal:f.normal.transform(world).to_a,material:diag_material(f.material || material),back_material:diag_material(f.back_material || material),hidden:f.hidden?,area_mm2:(f.area(world)*25.4**2).round(3)}},
  edges:entities.grep(Sketchup::Edge).map{|edge|{pid:edge.persistent_id,points:edge.vertices.map{|v|diag_mm(v.position,world)},length_mm:edge.length(world).to_mm.round(3),soft:edge.soft?,smooth:edge.smooth?,hidden:edge.hidden?}},
  vertices_world_mm:points,
  children:entities.select{|x|x.is_a?(Sketchup::Group)||x.is_a?(Sketchup::ComponentInstance)}.map{|x|diag_node(x,world,path+[e.name],material)}
 }
end
groups=root.entities.select{|e|e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}
names=['ENVELOPE_OUTER','RAMPS','FLOORS','INTERIOR','CIRCULATION_EXTERNAL','CIRCULATION_INTERNAL','ROOF_TIMBER']
selected=groups.select{|e|names.include?(e.name)}
scan_root=KStudioNativeDeepFingerprint.scan(root.entities,root.transformation,[],0,{count:0})
scan_document=KStudioNativeDeepFingerprint.scan(m.entities,Geom::Transformation.new,[],0,{count:0})
{
 schema_version:1,collector:'KStudioReadOnlySourceGeometryDiagnosis/1',sketchup_version:Sketchup.version,
 model_path:m.path,model_guid:m.guid,root_pid:root.persistent_id,root_transform:KStudioNativeDeepFingerprint.matrix(root.transformation),
 root_own_loose:{faces:scan_root[:faces],edges:scan_root[:edges],sha256:KStudioNativeDeepFingerprint.sha({faces:scan_root[:faces],edges:scan_root[:edges]})},
 document_own_loose:{faces:scan_document[:faces],edges:scan_document[:edges],sha256:KStudioNativeDeepFingerprint.sha({faces:scan_document[:faces],edges:scan_document[:edges]})},
 rendering_options:m.rendering_options.map{|k,v|[k,v]}.to_h,
 camera:{eye_m:m.active_view.camera.eye.to_a.map{|x|x.to_m},target_m:m.active_view.camera.target.to_a.map{|x|x.to_m},perspective:m.active_view.camera.perspective?},
 groups:selected.map{|e|diag_node(e,root.transformation,[])},geometry_write_count:0
}
