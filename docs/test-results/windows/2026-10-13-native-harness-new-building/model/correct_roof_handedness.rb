# LOCAL ONLY: keep existing roof mesh/curvature/material; exchange short-span sides.
# Source 1 ramp-end view: screen right = Y=0; screen left = Y=20000.
# Existing geometry has Y=20000 high. Mirror only roof assembly across Y=10000.
# Custom owned transform is appropriate: SAIE walls and ADAI profile extrusion
# would recreate the existing approved curved mesh and lose its persistent IDs.
find_owned=lambda do |entities, name, parent_transform|
  entities.each do |entity|
    next unless entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
    if entity.name==name
      return [entity,parent_transform]
    end
    if entity.is_a?(Sketchup::Group)
      found=find_owned.call(entity.entities,name,parent_transform*entity.transformation)
      return found if found
    end
  end
  nil
end
reflection=Geom::Transformation.scaling(Geom::Point3d.new(0,10000.mm,0),1,-1,1)
['CURVED_SHELL','ROOF_SUPPORTS','TENSION_BRACING'].each do |name|
  match=find_owned.call(root.entities,name,Geom::Transformation.new)
  raise "Owned roof target missing: #{name}" unless match
  group,parent_transform=match
  raise "Already applied: #{name}" if group.get_attribute('KStudio','roof_right_high',false)
  # Convert reflection in owned-root coordinates to this group's parent frame.
  group.transformation=parent_transform.inverse*reflection*parent_transform*group.transformation
  group.set_attribute('KStudio','roof_right_high',true)
end
