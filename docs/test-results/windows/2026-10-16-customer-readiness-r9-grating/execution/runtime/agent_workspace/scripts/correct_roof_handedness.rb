# LOCAL ONLY: keep existing roof mesh/curvature/material; exchange short-span sides.
# Source 1 ramp-end view: screen right = Y=0; screen left = Y=20000.
# Existing geometry has Y=20000 high. Mirror only roof assembly across Y=10000.
# Custom owned transform is appropriate: SAIE walls and ADAI profile extrusion
# would recreate the existing approved curved mesh and lose its persistent IDs.
find_direct=lambda do |entities,name,pid|
  matches=entities.grep(Sketchup::Group).select{|g|g.name==name}
  raise "Expected unique owned target: #{name}" unless matches.length==1
  g=matches.first
  raise "Changed target identity: #{name}" unless g.persistent_id==pid
  raise "Locked target: #{name}" if g.locked?
  g
end
raise 'Unexpected owned root' unless root.persistent_id==20606
roof=find_direct.call(root.entities,'ROOF_TIMBER',77872)
envelope=find_direct.call(root.entities,'ENVELOPE_OUTER',41319)
ties=find_direct.call(envelope.entities,'TENSION_BRACING',44694)
reflection=Geom::Transformation.scaling(Geom::Point3d.new(0,10000.mm,0),1,-1,1)
[ [roof,Geom::Transformation.new], [ties,envelope.transformation] ].each do |group,parent_transform|
  raise "Already applied: #{group.name}" if group.get_attribute('KStudio','roof_right_high',false)
  # Convert reflection in owned-root coordinates to this group's parent frame.
  group.transformation=parent_transform.inverse*reflection*parent_transform*group.transformation
  group.set_attribute('KStudio','roof_right_high',true)
end
