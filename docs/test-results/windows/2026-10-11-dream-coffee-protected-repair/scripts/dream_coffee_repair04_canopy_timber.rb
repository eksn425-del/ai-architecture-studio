# Dream Coffee r4 final scoped correction; edit mode only.
# Replace exactly the six authorized r4 groups and leave the original 110 groups untouched.

repair04_target_names = [
  'UPPER_TERRACE_CANOPY_PANEL',
  'UPPER_TERRACE_CANOPY_INNER_BEAM',
  'UPPER_TERRACE_CANOPY_OUTER_BEAM',
  'UPPER_TERRACE_CANOPY_POST_01',
  'UPPER_TERRACE_CANOPY_POST_02',
  'RIGHT_WALL_TIMBER_BOARD_REVEALS'
]
repair04_target_names.each { |name| remove_owned_group.call(name) }

repair04_pale_timber = model.materials['DreamCoffee | pale timber']
repair04_dark_timber = model.materials['DreamCoffee | structural timber']
raise 'Dream Coffee repair materials are missing' unless repair04_pale_timber && repair04_dark_timber

# These are constant rectangular profiles, which match ADAI's verified extrusion contract.
# Capture the injected proxy in this lambda so its local binding remains available at call time.
repair04_adai_proxy = adai_geometry
repair04_profile = lambda do |name, outline_mm, depth_mm, plane, offset_mm, material|
  repair04_adai_proxy.profile(root.entities, name, outline_mm, depth_mm, plane, offset_mm, material)
end

# Compact upper terrace shade panel, fully east of the glazed A-frame and outside the three umbrella bounds.
# Slab bounds: X=11100..12000, Y=850..2650, Z=5930..6050 mm.
repair04_profile.call('UPPER_TERRACE_CANOPY_PANEL',
  [[11100,850],[12000,850],[12000,2650],[11100,2650]], 120, 'xy', 5930, repair04_pale_timber)
repair04_profile.call('UPPER_TERRACE_CANOPY_INNER_BEAM',
  [[11100,5760],[11280,5760],[11280,5930],[11100,5930]], 1800, 'xz', 850, repair04_dark_timber)
repair04_profile.call('UPPER_TERRACE_CANOPY_OUTER_BEAM',
  [[11820,5760],[12000,5760],[12000,5930],[11820,5930]], 1800, 'xz', 850, repair04_dark_timber)
repair04_profile.call('UPPER_TERRACE_CANOPY_POST_01',
  [[11820,1000],[12000,1000],[12000,1180],[11820,1180]], 2160, 'xy', 3600, repair04_pale_timber)
repair04_profile.call('UPPER_TERRACE_CANOPY_POST_02',
  [[11820,2320],[12000,2320],[12000,2500],[11820,2500]], 2160, 'xy', 3600, repair04_pale_timber)

# Ten restrained vertical joints stay within the existing right timber-cladding field.
repair04_reveals = root.entities.add_group
repair04_reveals.name = 'RIGHT_WALL_TIMBER_BOARD_REVEALS'
repair04_add_joint = lambda do |name, y0, y1|
  joint = repair04_reveals.entities.add_group
  joint.name = name
  x0, x1, z0, z1 = 12114, 12120, 80, 3040
  points = [
    Geom::Point3d.new(x0.mm,y0.mm,z0.mm), Geom::Point3d.new(x1.mm,y0.mm,z0.mm),
    Geom::Point3d.new(x1.mm,y1.mm,z0.mm), Geom::Point3d.new(x0.mm,y1.mm,z0.mm),
    Geom::Point3d.new(x0.mm,y0.mm,z1.mm), Geom::Point3d.new(x1.mm,y0.mm,z1.mm),
    Geom::Point3d.new(x1.mm,y1.mm,z1.mm), Geom::Point3d.new(x0.mm,y1.mm,z1.mm)
  ]
  [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]].each do |ids|
    face = joint.entities.add_face(ids.map { |index| points[index] })
    next unless face && face.valid?
    face.material = repair04_dark_timber
    face.back_material = repair04_dark_timber
  end
  joint
end
[1700,2260,2820,3380,3940,4500,5060,5620,6180,6740].each_with_index do |center_y, index|
  repair04_add_joint.call("RIGHT_WALL_BOARD_JOINT_#{index + 1}", center_y - 4, center_y + 4)
end
