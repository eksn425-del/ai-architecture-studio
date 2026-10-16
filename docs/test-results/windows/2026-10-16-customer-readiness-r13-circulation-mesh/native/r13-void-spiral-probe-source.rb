# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise '"b213ce98-691e-477e-bb1c-9db62f3f76de"' unless m.guid=="b213ce98-691e-477e-bb1c-9db62f3f76de"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==13
def vp_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def vp_child(g,n);v=vp_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing '+n unless v.size==1;v.first;end
def vp_names(hit);hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [];end
stairs=vp_child(r,'CIRCULATION_INTERNAL');ss=[]
(0..2).each do |k|
 g=vp_child(stairs,"SPIRAL_L#{k}_L#{k+1}");tr=r.transformation*stairs.transformation*g.transformation
 (0...24).each do |n|
  step=vp_child(g,"TREAD_#{n}");t=tr*step.transformation;vertices=vp_es(step).grep(Sketchup::Edge).flat_map{|e|e.vertices.map{|v|t*v.position}};top=vertices.map{|p|p.z.to_mm}.max;ang=(n+0.5)*2*Math::PI/24
  [700,1400,1950].each do |radius|
   x=37000+radius*Math.cos(ang);y=6500+radius*Math.sin(ang);o=Geom::Point3d.new(x.mm,y.mm,(top+1).mm);hit=m.raytest([o,Z_AXIS],true);d=hit ? o.distance(hit[0]).to_mm+1 : nil
   ss<<{spiral:g.name,tread:n,radius_mm:radius,walking_point_mm:[x,y,top],first_overhead_mm:d,names:vp_names(hit),clear_2100mm:d.nil?||d>=2100}
  end
 end
end
void=[];[7500,17500,27500].each do |x|
 [2500,5500,8500].each do |y|
  o=Geom::Point3d.new(x.mm,y.mm,7300.mm);h=m.raytest([o,Geom::Vector3d.new(0,0,-1)],true);z=h ? h[0].z.to_mm : nil;void<<{xy_mm:[x,y],first_surface_below7300_z_mm:z,names:vp_names(h),open_at_middle_7200:z.nil?||z<6800}
 end
end
floor=vp_child(r,'FLOORS');rows=vp_es(floor).select{|e|e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}.map{|g|{name:g.name,pid:g.persistent_id,bounds_mm:[g.bounds.min.to_a.map(&:to_mm),g.bounds.max.to_a.map(&:to_mm)]}}
{revision:13,root_pid:20606,geometry_writes:0,spiral_headroom_samples:ss,void_controls:void,actual_floor_children:rows,limitation:'Selected actual tread rays and void grid, not a complete body-volume or code compliance check. Existing beam versus slab first-hit paths retained, no geometry changes.'}
