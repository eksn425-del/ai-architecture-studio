# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise '"9f201789-0280-471f-bd34-9de0b254a985"' unless m.guid=="9f201789-0280-471f-bd34-9de0b254a985"
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==20
def fs_es(g);g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;end
def fs_child(g,n);v=fs_es(g).select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing '+n unless v.length==1;v.first;end
def fs_path(r,path);t=r.transformation;g=r;path.each{|n|g=fs_child(g,n);t=t*g.transformation};[g,t];end
def fs_z(g,t,x,y)
 inv=t.inverse;line=[inv*Geom::Point3d.new(x.mm,y.mm,0),Z_AXIS.transform(inv)]
 fs_es(g).grep(Sketchup::Face).filter_map{|f|p=Geom.intersect_line_plane(line,f.plane);p&&[Sketchup::Face::PointInside,Sketchup::Face::PointOnEdge,Sketchup::Face::PointOnVertex].include?(f.classify_point(p)) ? (t*p).z.to_mm : nil}.sort
end
site,st=fs_path(r,['SITE_GROUND','SIMPLE_SURROUNDINGS']);ground,gt=fs_path(r,['SITE_GROUND','ADJACENT_GROUND']);paths=fs_child(site,'ENTRY_WALKS');pt=st*paths.transformation;beds=fs_child(site,'LOW_GREEN_BEDS');bt=st*beds.transformation;trees=fs_child(site,'SCHEMATIC_TREES');tt=st*trees.transformation
pathrows=fs_es(paths).grep(Sketchup::Group).map do |g|
 t=pt*g.transformation;b=g.bounds;cx=(b.min.x.to_mm+b.max.x.to_mm)/2;cy=(b.min.y.to_mm+b.max.y.to_mm)/2;zs=fs_z(g,t,cx,cy);gz=fs_z(ground,gt,cx,cy)
 {name:g.name,actual_z_intersections_mm:zs,actual_original_ground_intersections_mm:gz,has_real_thickness:zs.length>=2&&zs.max>zs.min,embedded_on_original_ground:zs.length>=2&&gz.length>=2&&zs.min<=gz.max&&zs.max>=gz.max-0.1}
end
treecontacts=[]
fs_es(trees).grep(Sketchup::Group).each_with_index do |tree,i|
 wt=tt*tree.transformation;trunk=fs_child(tree,"TREE_#{i+1}_TRUNK");tr=wt*trunk.transformation;crown=fs_child(tree,"TREE_#{i+1}_CROWN");ct=wt*crown.transformation;bed=fs_child(beds,"GREEN_BED_#{i+1}");br=bt*bed.transformation
 b=trunk.bounds;cx=(b.min.x.to_mm+b.max.x.to_mm)/2;cy=(b.min.y.to_mm+b.max.y.to_mm)/2;tz=fs_z(trunk,tr,cx,cy);bz=fs_z(bed,br,cx,cy);cz=fs_z(crown,ct,cx,cy);gz=fs_z(ground,gt,cx,cy)
 treecontacts<<{tree:tree.name,center_mm:[cx,cy],trunk_z_mm:tz,bed_z_mm:bz,crown_z_mm:cz,original_ground_z_mm:gz,passed:tz.length>=2&&bz.length>=2&&cz.length>=2&&gz.length>=2&&(tz.min-bz.max).abs<0.1&&(bz.min-gz.max).abs<0.1&&tz.max>=cz.min}
end
newwest=fs_child(paths,'WEST_RAMP_APPROACH');nw=pt*newwest.transformation;landing,lt=fs_path(r,['CIRCULATION_EXTERNAL','LANDINGS','LANDING_L0']);joints=[]
[-8300,-7400,-6500].each{|x|aa=fs_z(newwest,nw,x,-6200);bb=fs_z(landing,lt,x,-6200);joints<<{type:'west ground ramp',point_mm:[x,-6200,0],approach_z:aa,existing_z:bb,passed:aa.any?{|z|z.abs<0.1}&&bb.any?{|z|z.abs<0.1}}}
# Existing remote lower approach already grades -280 to0; new east walk meets its ground end.
oldnodes=[];walk=lambda{|g,t,p|oldnodes<<[g,t,p] if g.respond_to?(:name)&&g.name.include?('GROUND_APPROACH');fs_es(g).each{|e|walk.call(e,t*e.transformation,p+[e.name]) if e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)}}
# Avoid traversing repeated mesh hierarchy: approach is a direct stair-child group.
cir,ci=fs_path(r,['CIRCULATION_INTERNAL']);fs_es(cir).select{|g|g.is_a?(Sketchup::Group)&&g.name.start_with?('STAIR')}.each{|g|fs_es(g).select{|e|e.respond_to?(:name)&&e.name.include?('APPROACH')}.each{|e|oldnodes<<[e,ci*g.transformation*e.transformation,[g.name,e.name]]}}
east=fs_child(paths,'EAST_STAIR_LINK');et=pt*east.transformation
oldnodes.each do |g,t,p|
 [51100,51500,52000].each{|x|aa=fs_z(east,et,x,-2600);bb=fs_z(g,t,x,-2600);joints<<{type:'remote stair grade',path:p,point_mm:[x,-2600,-280],approach_z:aa,existing_z:bb,passed:aa.any?{|z|(z+280).abs<0.1}&&bb.any?{|z|(z+280).abs<0.1}}}
end
{revision:20,root_pid:20606,geometry_writes:0,site_leaf_pid:site.persistent_id,original_ground_pid:ground.persistent_id,path_count:pathrows.length,green_bed_count:fs_es(beds).grep(Sketchup::Group).length,tree_count:treecontacts.length,path_solid_controls:pathrows,tree_ground_and_crown_contacts:treecontacts,entrance_joints:joints,status:pathrows.length==6&&treecontacts.length==4&&pathrows.all?{|x|x[:has_real_thickness]&&x[:embedded_on_original_ground]}&&treecontacts.all?{|x|x[:passed]}&&joints.all?{|x|x[:passed]} ? 'PASS_SELECTED_BASIC_SITE_CONTROLS' : 'FAIL',limitations:'Simple owner-approved context inference, no surveyed landscape reconstruction/full-route/civil/structural certification. Paving main surfaces are intentionally ground-level overlays; old native ground remains unchanged. Whole building protection is separate complete graph audit.'}
