# Revision 8: local ground-level proportion correction; upper facade fixed.
# Estimated street grade lowered 500mm; all court bases and route thresholds follow.
find_group=lambda do |path|
 e=root.entities;g=nil;path.each{|n|g=e.grep(Sketchup::Group).find{|v|v.name==n};raise "Missing #{n}" unless g;e=g.entities};g
end
def grp(e,name)
 g=e.add_group;g.name=name;g
end
def box(e,name,x,y,z,w,d,h,mat)
 g=grp(e,name);f=g.entities.add_face([x.mm,y.mm,z.mm],[(x+w).mm,y.mm,z.mm],[(x+w).mm,(y+d).mm,z.mm],[x.mm,(y+d).mm,z.mm]);f.reverse! if f.normal.z<0;f.pushpull(h.mm);g.material=mat;g
end
# Scaling around unchanged heads grows lower reveals without moving upper openings.
['ENTRY','GROUND_LEFT_GLAZING'].each do |n|
 find_group.call([n]).transform!(Geom::Transformation.scaling([0,0,2720.mm],1,1,3220.0/2720))
end
# Threshold changes 260 -> -192.21mm; retain step rises and approach connection.
find_group.call(['ENTRY_STEPS']).transform!(Geom::Transformation.translation([0,0,-452.206.mm]))
# Last approach step lands 47.8mm above grade; court local entry pad bridges it.
g=find_group.call(['SITE']);g.transform!(Geom::Transformation.translation([0,0,-500.mm]))
concrete=model.materials['Warm grey concrete'];a=g.entities
box(a,'ENTRY_APPROACH_PAD',3500,-2650,0,3100,170,47.794,concrete)
# Front and enclosing wall tops stay unchanged in model coordinates. Base becomes -500.
['BOUNDARY_LEFT','BOUNDARY_RIGHT'].each do |n|
 find_group.call([n]).transform!(Geom::Transformation.scaling([0,0,1600.mm],1,1,2100.0/1600))
end
['GATE_MAIN','GATE_LEFT'].each do |n|
 find_group.call([n]).transform!(Geom::Transformation.scaling([0,0,1560.mm],1,1,2060.0/1560))
end
# Existing side/rear wall containers gain a non-overlapping foundation plinth.
brick=model.materials['Warm terracotta brick']
a=find_group.call(['INFERRED_RIGHT_WALL','INFERRED_RIGHT_WALL_INFERRED_ASSEMBLY']).entities
box(a,'GRADE_FOUNDATION_RIGHT',0,0,-500,11720,250,500,brick)
a=find_group.call(['MASS_LEFT','LEFT_RETURN','LEFT_RETURN_INFERRED_ASSEMBLY']).entities
box(a,'GRADE_FOUNDATION_LEFT',0,0,-500,11650,250,500,brick)
a=find_group.call(['INFERRED_REAR_WALL','INFERRED_REAR_WALL_INFERRED_ASSEMBLY']).entities
box(a,'GRADE_FOUNDATION_REAR',-250,0,-500,10950,250,500,brick)
# Move only new court planters, soil and foliage, preserving all original terrace planting.
a=find_group.call(['PLANTERS']).entities
6.times do |i|
 ["GROUND_PLANTER_#{i}","SOIL_#{i}","GROUND_SHRUB_#{i}"].each do |name|
  a.grep(Sketchup::Group).find{|v|v.name==name}.transform!(Geom::Transformation.translation([0,0,-500.mm]))
 end
end
# Rear entrance floor follows court grade; preserve its two steps and door clear opening.
# Rear door remains at original threshold; local platform is retained as inferred old rear access.
# Support the lowered front route continuously down to court grade.
a=find_group.call(['ENTRY_STEPS']).entities
box(a,'LOWER_ROUTE_FOUNDATION',3600,-2600,-47.794,2900,4350,47.794,concrete)
# Retain rear door and existing platform, add three coherent lower risers to new grade.
a=find_group.call(['INFERRED_REAR_WALL','REAR_LANDING_INFERRED']).entities
box(a,'LANDING_FOUNDATION',4150,12000,-500,2600,420,630,concrete)
a=find_group.call(['INFERRED_REAR_WALL','REAR_STEP_INFERRED']).entities
box(a,'OLD_STEP_FOUNDATION',4000,12420,-500,2900,400,500,concrete)
[[12820,460],[13140,290],[13460,120]].each_with_index{|v,i|box(a,"LOWER_REAR_STEP_#{i}",4000,v[0],-500,2900,320,v[1],concrete)}
