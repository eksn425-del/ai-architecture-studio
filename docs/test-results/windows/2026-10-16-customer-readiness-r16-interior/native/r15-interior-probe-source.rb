# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise '"d7f0f72a-9345-45cd-835c-4033da13fc46"' unless m.guid=="d7f0f72a-9345-45cd-835c-4033da13fc46"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==15
def ip_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def ip_child(g,n);v=ip_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing '+n unless v.size==1;v.first;end
def ip_path(r,p);g=r;t=r.transformation;p.each{|n|g=ip_child(g,n);t=t*g.transformation};[g,t];end
def ip_nodes(g,t,p,out)
 out<<[g,t,p];ip_es(g).each{|e|ip_nodes(e,t*e.transformation,p+[e.name],out) if e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}
end
def ip_names(h);h ? h[1].select{|e|e.respond_to?(:name)}.map(&:name) : [];end
def ip_surfaces(g,t,x,y)
 inv=t.inverse;line=[inv*Geom::Point3d.new(x.mm,y.mm,0),Z_AXIS.transform(inv)]
 ip_es(g).grep(Sketchup::Face).filter_map{|f|p=Geom.intersect_line_plane(line,f.plane);p&&[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(p)) ? (t*p).z.to_mm : nil}
end
def ip_bounds(g,t)
 pts=ip_es(g).grep(Sketchup::Edge).flat_map{|e|e.vertices.map{|v|t*v.position}};b=Geom::BoundingBox.new;pts.each{|p|b.add(p)};b
end
head=[];contacts=[];arrivals=[];meshes=[]
3.times do |k|
 g,t=ip_path(r,['CIRCULATION_INTERNAL',"SPIRAL_L#{k}_L#{k+1}"]);core=ip_child(g,"S#{k}_CONTINUOUS_CORE");ct=t*core.transformation;cb=ip_bounds(core,ct);cx=(cb.min.x.to_mm+cb.max.x.to_mm)/2;cy=(cb.min.y.to_mm+cb.max.y.to_mm)/2;base=cb.min.z.to_mm
 24.times do |n|
  step=ip_child(g,"S#{k}_TREAD_#{n}");st=t*step.transformation;b=ip_bounds(step,st);top=b.max.z.to_mm;vs=ip_es(step).grep(Sketchup::Face).max_by{|f|f.vertices.sum{|v|(st*v.position).z}/f.vertices.size}.vertices.map{|v|st*v.position};sx=vs.sum{|p|(p.x.to_mm-cx)/Math.hypot(p.x.to_mm-cx,p.y.to_mm-cy)};sy=vs.sum{|p|(p.y.to_mm-cy)/Math.hypot(p.x.to_mm-cx,p.y.to_mm-cy)};ang=Math.atan2(sy,sx)
  [650,1150,1600].each{|rad|o=Geom::Point3d.new((cx+rad*Math.cos(ang)).mm,(cy+rad*Math.sin(ang)).mm,(top+1).mm);hit=m.raytest([o,Z_AXIS],true);d=hit ? o.distance(hit[0]).to_mm+1 : nil;head<<{spiral:k,tread:n,radius_mm:rad,first_headroom_mm:d,names:ip_names(hit),passed:d.nil?||d>=2100}}
  support=ip_child(g,"S#{k}_RADIAL_SUPPORT_#{n}");rt=t*support.transformation;sb=(0..7).map{|j|t*support.bounds.corner(j)};maxz=sb.map{|v|v.z.to_mm}.max;start=rt*Geom::Point3d.new(0,0,0);inside=ip_surfaces(core,ct,start.x.to_mm,start.y.to_mm);contacts<<{spiral:k,tread:n,tread_bottom_mm:b.min.z.to_mm,support_top_mm:maxz,core_section_z_mm:inside,support_start_z_mm:start.z.to_mm,passed:(maxz-b.min.z.to_mm).abs<0.1&&inside.length>=2&&start.z.to_mm>=inside.min&&start.z.to_mm<=inside.max}
 end
 [1150,1600,1850,2100,2350,2450].each{|rad|aa=22.5*Math::PI/180;o=Geom::Point3d.new((cx+rad*Math.cos(aa)).mm,(cy+rad*Math.sin(aa)).mm,(base+3650).mm);h=m.raytest([o,Geom::Vector3d.new(0,0,-1)],true);zz=h ? h[0].z.to_mm : nil;arrivals<<{spiral:k,radius_mm:rad,level_mm:base+3600,actual_z_mm:zz,names:ip_names(h),passed:!!(h&&(zz-base-3600).abs<0.1)}}
 [0,10,20].each do |n|
  aa=(45.0+330.0*n/24)*Math::PI/180;delta=330.0/24*Math::PI/180;j=3
  [[aa+(j+0.5)*delta/8,base+n*150+(j+0.5)*150/8+165+5.5*50,false],[aa+j*delta/8,base+n*150+j*150/8+165+5.5*50,true]].each do |angle,z,wire|
   o=Geom::Point3d.new((cx+1770*Math.cos(angle)).mm,(cy+1770*Math.sin(angle)).mm,z.mm);h=m.raytest([o,Geom::Vector3d.new(-Math.cos(angle),-Math.sin(angle),0)],true);d=h ? o.distance(h[0]).to_mm : nil;iswire=!!(h&&d<150&&ip_names(h).any?{|name|name.start_with?("S#{k}_MESH_")});meshes<<{spiral:k,tread:n,expected_wire:wire,first_distance_mm:d,names:ip_names(h),passed:wire ? iswire : (d.nil?||d>150)}
  end
 end
end
floors,ft=ip_path(r,['FLOORS']);floor_nodes=ip_es(floors).select{|g|g.is_a?(Sketchup::Group)}.map{|g|[g,ft*g.transformation]};tables=[]
furn,t=ip_path(r,['INTERIOR','FURNITURE_SIMPLIFIED']);ip_es(furn).select{|g|g.respond_to?(:name)&&g.name.start_with?('TABLE_Z')}.each do |table|
 tt=t*table.transformation;body=ip_bounds(table,tt);ip_es(table).select{|g|g.respond_to?(:name)&&g.name.include?('_LEG_')}.each do |leg|
  lt=tt*leg.transformation;p=lt*Geom::Point3d.new(0,0,0);q=lt*Geom::Point3d.new(0,0,1.mm);zs=floor_nodes.flat_map{|g,t|ip_surfaces(g,t,p.x.to_mm,p.y.to_mm)};tables<<{table:table.name,leg:leg.name,base_z_mm:p.z.to_mm,tip_z_mm:q.z.to_mm,table_underside_mm:body.min.z.to_mm,actual_floor_faces_z_mm:zs,passed:zs.any?{|z|(z-p.z.to_mm).abs<0.1}&&(q.z.to_mm-body.min.z.to_mm).abs<0.1}
 end
end
shell,sh=ip_path(r,['ROOF_TIMBER','CURVED_SHELL']);curtains,cu=ip_path(r,['INTERIOR','HALL_CURTAINS']);nodes=[];ip_nodes(curtains,cu,['INTERIOR','HALL_CURTAINS'],nodes);hangers=[]
nodes.select{|g,t,p|g.name.match?(/^C\d+_SUSPENSION_\d+$/)}.each do |g,t,p|
 tip=t*Geom::Point3d.new(0,0,1.mm);zs=ip_surfaces(shell,sh,tip.x.to_mm,tip.y.to_mm);z=zs.select{|v|v>13000}.min;hangers<<{path:p,actual_tip_z_mm:tip.z.to_mm,actual_roof_soffit_z_mm:z,passed:!!(z&&(z-tip.z.to_mm).abs<0.2)}
end
fabric=nodes.sum{|g,t,p|ip_es(g).grep(Sketchup::Face).count{|f|f.material&&f.material.name.start_with?('IC_Translucent_White_Fabric')&&f.material.alpha<1}}
all=head+contacts+arrivals+meshes+tables+hangers
{revision:15,root_pid:20606,geometry_writes:0,status:all.all?{|x|x[:passed]}&&fabric>=600 ? 'PASS_SELECTED_NATIVE_INTERIOR_CONTROLS' : 'FAIL',headroom:head,tread_core_contacts:contacts,arrival_surface_controls:arrivals,spiral_mesh_controls:meshes,table_leg_contacts:tables,curtain_hanger_contacts:hangers,actual_translucent_fabric_faces:fabric,limitation:'Actual selected rays/solid surface intersections/endpoints, not complete body-volume routes or structural/code compliance. Full protected graph and finish-only shape audit separate.'}
