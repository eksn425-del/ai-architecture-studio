# Local edit only; never run in replace mode.
# DREAM_COFFEE_R3_REPAIR_03_CANOPY_AND_TIMBER
# Source-visible local repair. Dimensions are estimated millimeters.
# ADAI was selected for these constant sections, but the guarded SU host returned
# NameError: adai_geometry is not injected in this runtime. Use local owned Ruby
# extrusion because these are simple rectangular constant sections.
def dc_repair03_profile(entities, name, outline_mm, depth_mm, plane, offset_mm, material)
  return entities.grep(Sketchup::Group).find { |e| e.name == name } if entities.grep(Sketchup::Group).any? { |e| e.name == name }
  raise "unsupported repair profile plane: #{plane}" unless ['xy','xz','yz'].include?(plane)
  raise 'repair profile has invalid dimensions' if outline_mm.length < 3 || depth_mm.to_f <= 0
  g = entities.add_group
  g.name = name
  points = outline_mm.map do |u,v|
    case plane
    when 'xy' then Geom::Point3d.new(u.mm, v.mm, offset_mm.mm)
    when 'xz' then Geom::Point3d.new(u.mm, offset_mm.mm, v.mm)
    when 'yz' then Geom::Point3d.new(offset_mm.mm, u.mm, v.mm)
    end
  end
  face = g.entities.add_face(points)
  raise "repair profile face failed: #{name}" unless face && face.valid?
  axis = case plane
    when 'xy' then Geom::Vector3d.new(0,0,1)
    when 'xz' then Geom::Vector3d.new(0,1,0)
    when 'yz' then Geom::Vector3d.new(1,0,0)
  end
  face.reverse! if face.normal.dot(axis) < 0
  face.material = material
  face.back_material = material
  face.pushpull(depth_mm.mm, false)
  g.entities.grep(Sketchup::Face).each do |f|
    f.material = material
    f.back_material = material
  end
  g
end

repair03_pale_timber = model.materials['DreamCoffee | pale timber']
repair03_dark_timber = model.materials['DreamCoffee | structural timber']
raise 'Dream Coffee repair materials are missing' unless repair03_pale_timber && repair03_dark_timber

# Independent upper canopy at Z=5930..6050; it is separate from the lower fascia (Z=3600..4200)
# and starts outside the right slope of the A-frame, leaving the existing roof glass clear.
dc_repair03_profile(root.entities, 'UPPER_TERRACE_CANOPY_PANEL',
  [[8150, 1500], [10600, 1500], [10600, 4600], [8150, 4600]], 120, 'xy', 5930, repair03_pale_timber)
dc_repair03_profile(root.entities, 'UPPER_TERRACE_CANOPY_INNER_BEAM',
  [[8150, 5760], [8330, 5760], [8330, 5930], [8150, 5930]], 3100, 'xz', 1500, repair03_dark_timber)
dc_repair03_profile(root.entities, 'UPPER_TERRACE_CANOPY_OUTER_BEAM',
  [[10420, 5750], [10600, 5750], [10600, 5930], [10420, 5930]], 3100, 'xz', 1500, repair03_dark_timber)
dc_repair03_profile(root.entities, 'UPPER_TERRACE_CANOPY_POST_01',
  [[10420, 1600], [10600, 1600], [10600, 1780], [10420, 1780]], 2150, 'xy', 3600, repair03_pale_timber)
dc_repair03_profile(root.entities, 'UPPER_TERRACE_CANOPY_POST_02',
  [[10420, 4320], [10600, 4320], [10600, 4500], [10420, 4500]], 2150, 'xy', 3600, repair03_pale_timber)

# One fenced semantic group adds five shallow board-joint reveals over the existing broad right-wall cladding.
unless root.entities.grep(Sketchup::Group).any? { |e| e.name == 'RIGHT_WALL_TIMBER_BOARD_REVEALS' }
  reveals = root.entities.add_group
  reveals.name = 'RIGHT_WALL_TIMBER_BOARD_REVEALS'
  seam_material = repair03_dark_timber
  add_box = lambda do |name, x0, y0, z0, x1, y1, z1|
    next nil if (x1-x0).abs < 0.01 || (y1-y0).abs < 0.01 || (z1-z0).abs < 0.01
    g = reveals.entities.add_group
    g.name = name
    p = [
      Geom::Point3d.new(x0.mm,y0.mm,z0.mm), Geom::Point3d.new(x1.mm,y0.mm,z0.mm),
      Geom::Point3d.new(x1.mm,y1.mm,z0.mm), Geom::Point3d.new(x0.mm,y1.mm,z0.mm),
      Geom::Point3d.new(x0.mm,y0.mm,z1.mm), Geom::Point3d.new(x1.mm,y0.mm,z1.mm),
      Geom::Point3d.new(x1.mm,y1.mm,z1.mm), Geom::Point3d.new(x0.mm,y1.mm,z1.mm)
    ]
    [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]].each do |ids|
      face = g.entities.add_face(ids.map { |i| p[i] })
      next unless face
      face.material = seam_material
      face.back_material = seam_material
    end
    g
  end
  [1400,2800,4200,5600,7000].each_with_index do |y,i|
    add_box.call("RIGHT_WALL_BOARD_JOINT_#{i+1}",12114,y-6,80,12122,y+6,3040)
  end
end
