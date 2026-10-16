# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model
raise 'Wrong "66c91fdf-8b99-4927-860a-b47dcf359aa4"' unless m.guid=="66c91fdf-8b99-4927-860a-b47dcf359aa4"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606}
raise 'Wrong owned revision' unless r && r.get_attribute('sketchup_architect','revision')==10 && r.get_attribute('sketchup_architect','project_id')=='architecture-project-4f0e4'
def ents_(e);e.is_a?(Sketchup::Group) ? e.entities : e.definition.entities;end
def child_(e,name);a=ents_(e).select{|x|x.respond_to?(:name)&&x.name==name};raise 'Missing or ambiguous '+name unless a.length==1;a.first;end
parent=child_(r,'CIRCULATION_INTERNAL');leaf=child_(parent,'SMALL_CIRCULAR_VOID_GUARDS');raise 'Expected two guard instances' unless ents_(leaf).length==2
floor=child_(child_(r,'FLOORS'),'L3');tops=ents_(floor).grep(Sketchup::Face).select{|f|f.normal.z>0.99 && f.vertices.all?{|v|(v.position.z.to_mm-10800).abs<0.001}}
raise 'Actual upper floor top face unavailable' if tops.empty?
checks=[];supports=[];groups=[]
[[12000,10500,'SMALL_HOLE_01_FINE_WHITE_MESH'],[22500,10500,'SMALL_HOLE_02_FINE_WHITE_MESH']].each do |cx,cy,name|
 guard=child_(leaf,name);groups<<{name:name,pid:guard.persistent_id,center_mm:[cx,cy],height_expected_mm:1100}
 8.times do |j|
  [['open_cell',j*45+1.25,525,false],['vertical_wire',j*45+2.5,525,true],['horizontal_wire',j*45+1.25,501.5,true]].each do |kind,degrees,z,target_expected|
   angle=degrees*Math::PI/180;origin=Geom::Point3d.new(cx.mm,cy.mm,(10800+z).mm);dir=Geom::Vector3d.new(Math.cos(angle),Math.sin(angle),0);hit=m.raytest([origin,dir],true);dist=hit ? origin.distance(hit[0]).to_mm : nil;names=hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [];inside=hit && dist<1400;target=inside && hit[1].include?(leaf) && hit[1].include?(guard)
   passed=target_expected ? !!target : !inside
   checks<<{guard:name,kind:kind,degrees:degrees,height_above_floor_mm:z,expected_target_hit:target_expected,first_hit_distance_mm:dist,first_hit_names:names,passed:passed}
  end
 end
 base=child_(guard,'H01_BASE_RING');world=r.transformation*parent.transformation*leaf.transformation*guard.transformation*base.transformation;bottom=ents_(base).grep(Sketchup::Face).flat_map(&:vertices).uniq.map{|v|world*v.position}.select{|p|(p.z.to_mm-10800).abs<0.001}.uniq{|p|[p.x,p.y,p.z]}
 supported=bottom.count{|point|tops.any?{|face|[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(face.classify_point(point))}}
 supports<<{guard:name,actual_bottom_vertices:bottom.length,vertices_on_existing_floor_face:supported,passed:!bottom.empty? && supported==bottom.length}
end
{status:checks.all?{|v|v[:passed]} && supports.all?{|v|v[:passed]} ? 'PASS_SAMPLED_GEOMETRY_ONLY' : 'FAIL',root_pid:20606,revision:10,geometry_writes:0,ray_checks:checks,base_floor_contacts:supports,actual_guard_instances:groups,limitation:'Tests actual selected open cells, wire solids and base-to-existing-floor geometry. Source mesh size/height estimated; no load/safety certification or whole-building fidelity verdict.'}
