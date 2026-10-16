from pathlib import Path
import sys,json,time
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
O=R/'runtime/exterior-completion-20261016';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity()
s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'Wrong GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Wrong revision' unless r.get_attribute('sketchup_architect','revision')==11
def es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def find(g,n);a=es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing or ambiguous '+n unless a.length==1;a.first;end
def points(g,t)
 es(g).flat_map{|e|e.is_a?(Sketchup::Face) ? e.vertices.map{|v|t*v.position} : ((e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)) ? points(e,t*e.transformation) : [])}
end
def supported(floors,world,tf)
 es(floors).select{|e|e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}.any? do |g|
  p=(tf*g.transformation).inverse*world
  es(g).grep(Sketchup::Face).any?{|f|f.normal.z.abs>0.99 && [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(p))}
 end
end
def beam_bottom(g,t,x,y)
 line=[t.inverse*Geom::Point3d.new(x,y,0),Geom::Vector3d.new(0,0,1).transform(t.inverse)]
 hits=es(g).grep(Sketchup::Face).filter_map do |face|
  p=Geom.intersect_line_plane(line,face.plane)
  next nil unless p && [Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(face.classify_point(p))
  (t*p).z.to_mm
 end
 raise 'No actual beam intersection at frame plane' if hits.empty?
 hits.min
end
env=find(r,'ENVELOPE_OUTER');roof=find(r,'ROOF_TIMBER');rs=find(roof,'ROOF_SUPPORTS');floors=find(r,'FLOORS');frame=find(r,'STRUCTURE_EXISTING');rt=r.transformation;et=rt*env.transformation;ft=rt*floors.transformation
names=['HALL_LONG_SOUTH_ADDITION','HALL_LONG_NORTH_ADDITION','LOWER_END_WEST_ADDITION','LOWER_END_EAST_ADDITION'];rows=[];doors=[];joints=[];rays=[]
names.each do |n|
 leaf=find(env,n);raise 'Invalid new leaf' unless leaf.is_a?(Sketchup::Group) && !leaf.locked? && leaf.definition.instances.length==1
 lt=et*leaf.transformation;long=n.start_with?('HALL_LONG');sign=(n.include?('SOUTH')||n.include?('WEST')) ? -1 : 1;panels=es(leaf).select{|g|g.is_a?(Sketchup::Group)||g.is_a?(Sketchup::ComponentInstance)}
 rows<<{path:['ENVELOPE_OUTER',n],pid:leaf.persistent_id,panels:panels.length,unique_definitions:panels.map{|g|g.definition.entityID}.uniq.length}
 panels.each do |p|
  pt=lt*p.transformation;contents=es(p);lj=contents.find{|g|g.respond_to?(:name)&&g.name=='DOOR_LEFT_JAMB'};rj=contents.find{|g|g.respond_to?(:name)&&g.name=='DOOR_RIGHT_JAMB'}
  if lj && rj
   lo=long ? lj.bounds.max.x : lj.bounds.max.y;hi=long ? rj.bounds.min.x : rj.bounds.min.y;z=lj.bounds.min.z;local=long ? Geom::Point3d.new((lo+hi)/2,0,z+1100.mm) : Geom::Point3d.new(0,(lo+hi)/2,z+1100.mm);normal=(Geom::Vector3d.new(*(long ? [0,sign,0] : [sign,0,0]))).transform(pt);normal.normalize!;center=pt*local;origin=center.offset(normal,-100.mm);hit=m.raytest([origin,normal],true);dist=hit ? origin.distance(hit[0]).to_mm : nil;clear=!hit||dist>1200;threshold=pt*(long ? Geom::Point3d.new((lo+hi)/2,-sign*100.mm,z) : Geom::Point3d.new(-sign*100.mm,(lo+hi)/2,z));floor=supported(floors,threshold,ft)
   doors<<{leaf:n,panel:p.name,clear_width_mm:(hi-lo).to_mm,clear_height_mm:(lj.bounds.max.z-z).to_mm,first_hit_distance_mm:dist,first_hit_names:hit ? hit[1].select{|e|e.respond_to?(:name)}.map(&:name) : [],inside_floor_supported:floor,portal_center_clear_1200mm:clear,passed:clear&&floor}
  end
  top=find(p,'TOP_RAIL');top_points=points(top,pt*top.transformation);topz=top_points.map{|v|v.z.to_mm}.max;cx=(top_points.map(&:x).min+top_points.map(&:x).max)/2;cy=(top_points.map(&:y).min+top_points.map(&:y).max)/2
  if long
   # Independent actual existing edge-beam vertices, not a copied roof formula.
   axis_y=n.include?('SOUTH') ? 0 : 20000
   beams=es(rs).select{|g|g.respond_to?(:name)&&g.name.start_with?('HIGH_EDGE_')}.map{|g|pp=points(g,rt*roof.transformation*rs.transformation*g.transformation);[g,pp]}
   beam,pp=beams.min_by{|g,vs|(((vs.map(&:y).min+vs.map(&:y).max)/2).to_mm-axis_y).abs};bottom=beam_bottom(beam,rt*roof.transformation*rs.transformation*beam.transformation,cx,axis_y.mm)
  else
   base=points(p,pt).map{|v|v.z.to_mm}.min;level=(base/3600).round*3600;column=n.include?('WEST') ? 0 : 10;beam=find(frame,"CROSS_BEAM_Z#{level+3600}_X#{column}");bottom=beam_bottom(beam,rt*frame.transformation*beam.transformation,cx,cy)
  end
  joints<<{leaf:n,panel:p.name,top_rail_world_z_mm:topz,existing_beam_bottom_world_z_mm:bottom,signed_gap_mm:bottom-topz,passed:(bottom-topz).abs<0.1}
  if long
   pp=points(top,pt*top.transformation);cx=(pp.map(&:x).min+pp.map(&:x).max)/2;cy=axis_y.mm;normal=Geom::Vector3d.new(0,sign,0);[12000.0,topz-150].each do |z|
    center=Geom::Point3d.new(cx,cy,z.mm);origin=center.offset(normal,-100.mm);hit=m.raytest([origin,normal],true);dist=hit ? origin.distance(hit[0]).to_mm : nil;target=!!(hit&&dist<200&&hit[1].include?(leaf));expected=!(lj&&rj&&z==12000.0)
    rays<<{leaf:n,panel:p.name,z_mm:z,expected_new_glass_hit:expected,actual_new_hit:target,first_hit_distance_mm:dist,passed:expected ? target : (!hit||dist>1200)}
   end
  end
 end
end
{revision:11,root_pid:20606,geometry_writes:0,new_leaves:rows,doors:doors,frame_existing_beam_joints:joints,upper_glass_rays:rays,status:doors.length==16&&doors.all?{|x|x[:passed]}&&joints.all?{|x|x[:passed]}&&rays.all?{|x|x[:passed]} ? 'PASS_SAMPLED_GEOMETRY_ONLY' : 'FAIL',limitation:'Actual native ray/threshold/frame contact controls. Not whole-route clearance, structural certification or whole-source fidelity.'}
'''.replace('GUID',json.dumps(i['model_guid']))
f=_generated_script_dir()/('studio-enclosure-probe-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');(O/'r11-enclosure-probe-source.rb').write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only actual new enclosure panes door thresholds and beam joints'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'r11-enclosure-probe.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':v['status'],'doors_passed':sum(x['passed'] for x in v['doors']),'doors':len(v['doors']),'joints_passed':sum(x['passed'] for x in v['frame_existing_beam_joints']),'joints':len(v['frame_existing_beam_joints']),'glass_rays_passed':sum(x['passed'] for x in v['upper_glass_rays']),'glass_rays':len(v['upper_glass_rays'])}))
