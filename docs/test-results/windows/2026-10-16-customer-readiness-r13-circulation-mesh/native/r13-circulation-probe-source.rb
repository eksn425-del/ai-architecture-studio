# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise '"84ee639f-c37b-40e1-9968-b1917e0d9969"' unless m.guid=="84ee639f-c37b-40e1-9968-b1917e0d9969"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==13
def cq_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def cq_child(g,n);aa=cq_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing/ambiguous '+n unless aa.length==1;aa.first;end
def cq_path(r,p);g=r;t=r.transformation;p.each{|n|g=cq_child(g,n);t=t*g.transformation};[g,t];end
def cq_bbox(g,t);b=Geom::BoundingBox.new;cq_es(g).grep(Sketchup::Edge).each{|e|e.vertices.each{|v|b.add(t*v.position)}};raise 'No direct vertices' if b.empty?;b;end
def cq_top_at(g,t,x,y)
 line=[t.inverse*Geom::Point3d.new(x.mm,y.mm,0),Geom::Vector3d.new(0,0,1).transform(t.inverse)]
 hits=cq_es(g).grep(Sketchup::Face).filter_map{|f|p=Geom.intersect_line_plane(line,f.plane);p && [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(p)) ? (t*p).z.to_mm : nil};raise 'Missing solid support surface' if hits.empty?;hits.max
end
def cq_tile(g,t)
 return [g,t] if g.is_a?(Sketchup::ComponentInstance)&&g.definition.name.start_with?('KS_FINE_WHITE_MESH_')
 cq_es(g).each{|e|next unless e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance);v=cq_tile(e,t*e.transformation);return v if v};nil
end
head=[];contacts=[];treads=[]
[0,3600,7200].each do |base|
 (0...24).each do |n|
  path=['CIRCULATION_INTERNAL',"END_TREAD_#{base}_#{n}"];g,t=cq_path(r,path);b=cq_bbox(g,t);top=b.max.z.to_mm;y=(b.min.y.to_mm+b.max.y.to_mm)/2;treads<<{path:path,pid:g.persistent_id,bounds_mm:[b.min.to_a.map(&:to_mm),b.max.to_a.map(&:to_mm)]}
  [50750,51600,52450].each{|x|o=Geom::Point3d.new(x.mm,y.mm,(top+1).mm);hit=m.raytest([o,Z_AXIS],true);d=hit ? o.distance(hit[0]).to_mm+1 : nil;head<<{base:base,tread:n,x_mm:x,walking_z_mm:top,first_overhead_mm:d,names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],passed:d.nil?||d>=2200}}
  [50500,52600].each_with_index do |x,j|
   seat,st=cq_path(r,['CIRCULATION_INTERNAL','END_STAIR_COMPLETION',"END_STAIR_Z#{base}_SUPPORT_HANDRAILS","TREAD_SEAT_#{base}_#{j}_#{n}"]);sb=cq_bbox(seat,st);str,tt=cq_path(r,['CIRCULATION_INTERNAL','END_STAIR_COMPLETION',"END_STAIR_Z#{base}_SUPPORT_HANDRAILS","STRINGER_#{base}_#{j}"]);sz=cq_top_at(str,tt,x+50,y);contact=(sb.max.z.to_mm-b.min.z.to_mm).abs<0.01&&sz>=sb.min.z.to_mm&&sz<=sb.max.z.to_mm
   contacts<<{base:base,tread:n,side:j,seat_top_mm:sb.max.z.to_mm,tread_bottom_mm:b.min.z.to_mm,stringer_top_at_seat_mm:sz,seat_bottom_mm:sb.min.z.to_mm,passed:contact}
  end
 end
end
decks=[]
[3600,7200,10800].each do |z|
 name="GALLERY_Z#{z}_SIDE3";g,t=cq_path(r,['CIRCULATION_EXTERNAL','GALLERIES',name]);[[51600,4000,false,'stair_slot'],[51601,8400,true,'landing_bar'],[53311,4000,true,'bypass_bar']].each do |x,y,expected,label|
  o=Geom::Point3d.new(x.mm,y.mm,(z+100).mm);hit=m.raytest([o,Geom::Vector3d.new(0,0,-1)],true);d=hit ? o.distance(hit[0]).to_mm : nil;target=!!(hit&&d<200&&hit[1].include?(g));decks<<{level:z,label:label,expected_deck:expected,actual_deck:target,first_distance_mm:d,names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],passed:target==expected}
 end
end
mesh=[];paths=JSON.parse("[[\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L2\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L3\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z3600_SIDE3\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z7200_SIDE3\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z10800_SIDE3\"], [\"CIRCULATION_INTERNAL\", \"END_STAIR_COMPLETION\"], [\"CIRCULATION_EXTERNAL\", \"REMOTE_END_EDGE_GUARDS\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"LONG_RAIL_SOUTH_Z3600\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"LONG_RAIL_NORTH_Z3600\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z7200_SIDE0\", \"GALLERY_Z7200_SIDE0_SLOT_GUARD\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z7200_SIDE1\", \"GALLERY_Z7200_SIDE1_SLOT_GUARD\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z7200_SIDE2\", \"GALLERY_Z7200_SIDE2_SLOT_GUARD\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"LONG_RAIL_SOUTH_Z7200\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"LONG_RAIL_NORTH_Z7200\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z10800_SIDE0\", \"GALLERY_Z10800_SIDE0_SLOT_GUARD\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z10800_SIDE1\", \"GALLERY_Z10800_SIDE1_SLOT_GUARD\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"GALLERY_Z10800_SIDE2\", \"GALLERY_Z10800_SIDE2_SLOT_GUARD\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"LONG_RAIL_SOUTH_Z10800\"], [\"CIRCULATION_EXTERNAL\", \"GALLERIES\", \"LONG_RAIL_NORTH_Z10800\"], [\"CIRCULATION_EXTERNAL\", \"RAMP_1_OUTER\"], [\"CIRCULATION_EXTERNAL\", \"RAMP_1_INNER\"], [\"CIRCULATION_EXTERNAL\", \"RAMP_2_OUTER\"], [\"CIRCULATION_EXTERNAL\", \"RAMP_2_INNER\"], [\"CIRCULATION_EXTERNAL\", \"RAMP_3_OUTER\"], [\"CIRCULATION_EXTERNAL\", \"RAMP_3_INNER\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_0\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_1\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_2\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_3\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_4\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_5\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_6\"], [\"CIRCULATION_EXTERNAL\", \"LANDINGS\", \"LANDING_L1\", \"LANDING_L1_GUARD_7\"]]")
paths.select{|p|p.last.start_with?('LONG_RAIL_','RAMP_','LANDING_L1_GUARD_')||p.last.end_with?('_SLOT_GUARD')}.each do |path|
 g,t=cq_path(r,path);tile,tt=cq_tile(g,t);raise 'No actual mesh tile' unless tile
 vs=cq_es(tile).select{|e|e.respond_to?(:name)&&e.name.match?(/_V\d+$/)}.sort_by{|e|e.name[/_V(\d+)$/,1].to_i};hs=cq_es(tile).select{|e|e.respond_to?(:name)&&e.name.match?(/_H\d+$/)}.sort_by{|e|e.name[/_H(\d+)$/,1].to_i};raise 'Insufficient actual mesh wires' unless vs.length>=2&&hs.length>=2
 uopen=(vs[0].bounds.max.x+vs[1].bounds.min.x)/2;usolid=(vs[1].bounds.min.x+vs[1].bounds.max.x)/2;zopen=(hs[0].bounds.max.z+hs[1].bounds.min.z)/2;zsolid=(hs[1].bounds.min.z+hs[1].bounds.max.z)/2
 [[uopen,zopen,false,'open_cell'],[usolid,zopen,true,'vertical_wire'],[uopen,zsolid,true,'horizontal_wire']].each do |u,z,expected,label|
  o=tt*Geom::Point3d.new(u,-100.mm,z);normal=Y_AXIS.transform(tt);normal.normalize!;hit=m.raytest([o,normal],true);d=hit ? o.distance(hit[0]).to_mm : nil;target=!!(hit&&d<200&&hit[1].include?(tile));pass=expected ? target : (!hit||d>=200);mesh<<{path:path,label:label,expected_wire:expected,first_distance_mm:d,actual_tile:target,names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],passed:pass}
 end
end
pads=['LANDING_L2','LANDING_L3'].map do |n|
 g,t=cq_path(r,['CIRCULATION_EXTERNAL','LANDINGS',n]);parent=t*g.transformation.inverse;pts=(0..7).map{|j|parent*g.bounds.corner(j)};ys=pts.map{|p|p.y.to_mm};{name:n,world_y_mm:[ys.min,ys.max],passed:ys.min>=-4000.1&&ys.max<=24000.1}
end
{revision:13,root_pid:20606,geometry_writes:0,status:(head+contacts+decks+mesh+pads).all?{|x|x[:passed]} ? 'PASS_SAMPLED_CIRCULATION_AND_MESH' : 'FAIL',headroom_controls:head,tread_seat_stringer_contacts:contacts,remote_deck_controls:decks,mesh_controls:mesh,upper_platform_bounds:pads,existing_treads:treads,limitation:'Actual selected central stair headroom rays, support intersections, openings/grating bars, real mesh holes/wires and source outline. Not exhaustive full-route/body-volume or structural safety certification.'}
