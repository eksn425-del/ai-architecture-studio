# Final targeted correction for this turn: strengthen the annex footprint and
# roof profile, steepen the visible main roof plane, and clarify the open sash.
raise 'Luna correction requires model and root' unless model && root

mm = ->(n) { n.to_f.mm }
pt = ->(x, y, z) { Geom::Point3d.new(mm.call(x), mm.call(y), mm.call(z)) }
vec = ->(x, y, z) { Geom::Vector3d.new(x.to_f, y.to_f, z.to_f) }
materials = {
  plaster: model.materials['Luna | Warm white lime plaster'],
  stone: model.materials['Luna | Pale concrete stone'],
  roof: model.materials['Luna | Charcoal standing seam'],
  edge: model.materials['Luna | Charcoal fascia'],
  metal: model.materials['Luna | Brushed steel'],
  timber: model.materials['Luna | Structural timber']
}
raise 'Required Luna materials are missing' if materials.values.any?(&:nil?)

paint = lambda do |group, material|
  group.entities.grep(Sketchup::Face).each do |f|
    f.material = material
    f.back_material = material
  end
end

profile_solid = lambda do |entities, name, points_mm, depth_mm, material|
  points = points_mm.map { |p| pt.call(*p) }
  raise "Degenerate profile #{name}" if points.length < 3 || depth_mm.to_f.abs < 1
  group = entities.add_group
  group.name = name
  face = group.entities.add_face(points)
  raise "Could not form profile #{name}" unless face && face.valid?
  face.material = material
  face.back_material = material
  face.pushpull(mm.call(depth_mm))
  raise "Profile extrusion failed for #{name}" if group.entities.grep(Sketchup::Face).empty?
  paint.call(group, material)
  group
end

solid_box = lambda do |entities, name, bounds, material|
  x1, y1, z1, x2, y2, z2 = bounds
  lx, hx = [x1.to_f, x2.to_f].minmax
  ly, hy = [y1.to_f, y2.to_f].minmax
  lz, hz = [z1.to_f, z2.to_f].minmax
  raise "Degenerate box #{name}" if hx - lx < 1 || hy - ly < 1 || hz - lz < 1
  group = entities.add_group
  group.name = name
  face = group.entities.add_face(pt.call(lx, ly, lz), pt.call(hx, ly, lz),
                                 pt.call(hx, hy, lz), pt.call(lx, hy, lz))
  raise "Could not form box #{name}" unless face && face.valid?
  face.pushpull(mm.call(hz - lz))
  paint.call(group, material)
  group
end

beam = lambda do |entities, name, a_mm, b_mm, width_mm, depth_mm, material, normal_hint|
  a, b = pt.call(*a_mm), pt.call(*b_mm)
  d = b - a
  raise "Zero length beam #{name}" if d.length < mm.call(1)
  d.normalize!
  n = vec.call(*normal_hint)
  raise "Zero normal #{name}" if n.length < 0.001
  n.normalize!
  side = n.cross(d)
  raise "Degenerate beam plane #{name}" if side.length < 0.001
  side.normalize!
  hw, hd = mm.call(width_mm.to_f / 2.0), mm.call(depth_mm.to_f / 2.0)
  w = vec.call(side.x * hw, side.y * hw, side.z * hw)
  t = vec.call(n.x * hd, n.y * hd, n.z * hd)
  a0, a1, a2, a3 = a - w - t, a + w - t, a + w + t, a - w + t
  b0, b1, b2, b3 = b - w - t, b + w - t, b + w + t, b - w + t
  g = entities.add_group
  g.name = name
  [[a0,a1,a2,a3],[b0,b3,b2,b1],[a0,b0,b1,a1],[a1,b1,b2,a2],[a2,b2,b3,a3],[a3,b3,b0,a0]].each do |poly|
    f = g.entities.add_face(poly)
    raise "Could not form beam #{name}" unless f && f.valid?
    f.material = material
    f.back_material = material
  end
  g
end

# Rebuild only the previously added annex children; keep every reviewed main-volume path.
%w[ANNEX_LOW_WHITE_VOLUME ANNEX_LOW_ROOF ANNEX_SITE_PAD].each do |name|
  remove_owned_group.call(name) if root.entities.grep(Sketchup::Group).any? { |g| g.name == name }
end
remove_owned_group.call('MAIN_ROOF_PITCH_ADJUSTMENT') if root.entities.grep(Sketchup::Group).any? { |g| g.name == 'MAIN_ROOF_PITCH_ADJUSTMENT' }
if root.entities.grep(Sketchup::Group).any? { |g| g.name == 'BICYCLE_CORNER_PLANT_SCREEN' }
  remove_owned_group.call('BICYCLE_CORNER_PLANT_SCREEN')
end

# Expanded ESTIMATED annex: a 3190 x 4200 mm attached body, with a separate low roof.
x_left, x_right = 1700.0, 4890.0
y_attach, y_rear = 4390.0, 8700.0
z_attach, z_rear = 3600.0, 3000.0
roof_z = lambda { |y| z_attach + (z_rear - z_attach) * (y.to_f - y_attach) / (y_rear - y_attach) }
wall_bottom, wall_y0, wall_y1 = -15.0, 4500.0, 8620.0
wall_z0, wall_z1 = roof_z.call(wall_y0) - 10, roof_z.call(wall_y1) - 10
annex = root.entities.add_group
annex.name = 'ANNEX_LOW_WHITE_VOLUME'
profile_solid.call(annex.entities, 'ANNEX_RIGHT_WHITE_WALL',
  [[4710, wall_y0, wall_bottom], [4710, wall_y1, wall_bottom], [4710, wall_y1, wall_z1], [4710, wall_y0, wall_z0]],
  180, materials[:plaster])
profile_solid.call(annex.entities, 'ANNEX_INNER_PARTITION_INFERRED',
  [[x_left, wall_y0, wall_bottom], [x_left, wall_y1, wall_bottom], [x_left, wall_y1, wall_z1], [x_left, wall_y0, wall_z0]],
  180, materials[:plaster])
profile_solid.call(annex.entities, 'ANNEX_REAR_WHITE_WALL_INFERRED',
  [[x_left, y_rear, wall_bottom], [x_right, y_rear, wall_bottom], [x_right, y_rear, z_rear - 10], [x_left, y_rear, z_rear - 10]],
  -180, materials[:plaster])
solid_box.call(annex.entities, 'ANNEX_RIGHT_STONE_BASE', [4890, 4500, 0, 4930, 8620, 280], materials[:stone])
solid_box.call(annex.entities, 'ANNEX_REAR_STONE_BASE', [1700, 8700, 0, 4890, 8740, 280], materials[:stone])
pad = root.entities.add_group
pad.name = 'ANNEX_SITE_PAD'
solid_box.call(pad.entities, 'ANNEX_CONCRETE_FOOTING', [1500, 4650, -210, 5050, 8740, -15], materials[:stone])

annex_roof = root.entities.add_group
annex_roof.name = 'ANNEX_LOW_ROOF'
annex_x1, annex_x2 = 1660.0, 5000.0
profile_solid.call(annex_roof.entities, 'ANNEX_CHARCOAL_ROOF_SHELL',
  [[annex_x1, y_attach, z_attach], [annex_x2, y_attach, z_attach], [annex_x2, y_rear, z_rear], [annex_x1, y_rear, z_rear]],
  -90, materials[:roof])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_FRONT',
  [annex_x1, y_attach - 30, z_attach + 4], [annex_x2, y_attach - 30, z_attach + 4], 110, 70, materials[:edge], [0, 1, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_REAR',
  [annex_x1, y_rear + 25, z_rear + 4], [annex_x2, y_rear + 25, z_rear + 4], 110, 70, materials[:edge], [0, 1, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_LEFT',
  [annex_x1 - 20, y_attach, z_attach + 4], [annex_x1 - 20, y_rear, z_rear + 4], 80, 65, materials[:edge], [1, 0, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_RIGHT',
  [annex_x2 + 20, y_attach, z_attach + 4], [annex_x2 + 20, y_rear, z_rear + 4], 80, 65, materials[:edge], [1, 0, 0])
annex_ribs = annex_roof.entities.add_group
annex_ribs.name = 'ANNEX_ROOF_RIB_INSTANCES'
annex_rib_x0, annex_rib_y0, annex_rib_y1 = 1720.0, y_attach + 45, y_rear - 45
annex_rib_z = lambda { |y| roof_z.call(y) + 11 }
first_annex_rib = beam.call(annex_ribs.entities, 'ANNEX_ROOF_RIB_001',
  [annex_rib_x0, annex_rib_y0, annex_rib_z.call(annex_rib_y0)],
  [annex_rib_x0, annex_rib_y1, annex_rib_z.call(annex_rib_y1)], 22, 18, materials[:metal], [1, 0, 0])
raise 'Annex representative roof rib failed validation' if first_annex_rib.entities.grep(Sketchup::Face).length < 6
annex_rib_component = first_annex_rib.to_component
annex_rib_component.definition.name = 'Luna Annex Standing Seam Rib 180'
annex_rib_count, annex_rib_x = 1, annex_rib_x0 + 180
while annex_rib_x <= 4960
  instance = annex_ribs.entities.add_instance(annex_rib_component.definition,
    Geom::Transformation.translation(vec.call(mm.call(annex_rib_x - annex_rib_x0), 0, 0)))
  instance.name = format('ANNEX_ROOF_RIB_%03d', annex_rib_count + 1)
  annex_rib_count += 1
  annex_rib_x += 180
end

# Keep the reviewed main-roof group intact; this visible, same-material shell gives
# the source-matched roof a stronger rise while preserving its low entry eave.
pitch_roof = root.entities.add_group
pitch_roof.name = 'MAIN_ROOF_PITCH_ADJUSTMENT'
roof_x1, roof_x2, roof_y0, roof_y1 = -120.0, 4920.0, -180.0, 4680.0
roof_z0, roof_z1 = 3620.0, 5620.0
steeper_z = lambda { |y| roof_z0 + (roof_z1 - roof_z0) * (y.to_f - roof_y0) / (roof_y1 - roof_y0) }
profile_solid.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_CHARCOAL_SHELL',
  [[roof_x1, roof_y0, roof_z0], [roof_x2, roof_y0, roof_z0], [roof_x2, roof_y1, roof_z1], [roof_x1, roof_y1, roof_z1]],
  -90, materials[:roof])
solid_box.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_FRONT_FASCIA', [-170, -235, 3540, 4970, -130, 3750], materials[:edge])
solid_box.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_REAR_FASCIA', [-170, 4640, 5480, 4970, 4730, 5750], materials[:edge])
beam.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_FASCIA_LEFT',
  [roof_x1, roof_y0, roof_z0], [roof_x1, roof_y1, roof_z1], 180, 85, materials[:edge], [1, 0, 0])
beam.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_FASCIA_RIGHT',
  [roof_x2, roof_y0, roof_z0], [roof_x2, roof_y1, roof_z1], 180, 85, materials[:edge], [1, 0, 0])
main_ribs = pitch_roof.entities.add_group
main_ribs.name = 'MAIN_ROOF_STEEPER_RIB_INSTANCES'
main_rib_x0, main_rib_y0, main_rib_y1 = 40.0, roof_y0 + 30, roof_y1 - 30
main_rib_z = lambda { |y| steeper_z.call(y) + 14 }
first_main_rib = beam.call(main_ribs.entities, 'MAIN_ROOF_STEEPER_RIB_001',
  [main_rib_x0, main_rib_y0, main_rib_z.call(main_rib_y0)],
  [main_rib_x0, main_rib_y1, main_rib_z.call(main_rib_y1)], 28, 22, materials[:metal], [1, 0, 0])
raise 'Main roof representative rib failed validation' if first_main_rib.entities.grep(Sketchup::Face).length < 6
main_rib_component = first_main_rib.to_component
main_rib_component.definition.name = 'Luna Steeper Main Roof Rib 180'
main_rib_count, main_rib_x = 1, main_rib_x0 + 180
while main_rib_x <= 4780
  instance = main_ribs.entities.add_instance(main_rib_component.definition,
    Geom::Transformation.translation(vec.call(mm.call(main_rib_x - main_rib_x0), 0, 0)))
  instance.name = format('MAIN_ROOF_STEEPER_RIB_%03d', main_rib_count + 1)
  main_rib_count += 1
  main_rib_x += 180
end

# The glazing and existing diagonal supports stay; a heavier timber frame makes
# the already outward-tilted single leaf read clearly from both source angles.
window = root.entities.grep(Sketchup::Group).find { |g| g.name == 'RIGHT_AWNING_WINDOW_OPEN_MODULE' }
raise 'The side awning-window host group is missing' unless window
if window.entities.grep(Sketchup::Group).any? { |g| g.name == 'AWNING_SASH_FRAME_BOLD' }
  remove_owned_group.call(['RIGHT_AWNING_WINDOW_OPEN_MODULE', 'AWNING_SASH_FRAME_BOLD'])
end
sash_frame = window.entities.add_group
sash_frame.name = 'AWNING_SASH_FRAME_BOLD'
beam.call(sash_frame.entities, 'SASH_HINGE_RAIL_BOLD', [4990, 930, 2590], [4990, 2940, 2590], 90, 75, materials[:timber], [1, 0, 0])
beam.call(sash_frame.entities, 'SASH_OPEN_EDGE_BOLD', [5690, 930, 1050], [5690, 2940, 1050], 90, 75, materials[:timber], [1, 0, 0])
beam.call(sash_frame.entities, 'SASH_SIDE_START_BOLD', [4990, 930, 2590], [5690, 930, 1050], 75, 65, materials[:timber], [0, 1, 0])
beam.call(sash_frame.entities, 'SASH_SIDE_END_BOLD', [4990, 2940, 2590], [5690, 2940, 1050], 75, 65, materials[:timber], [0, 1, 0])
beam.call(sash_frame.entities, 'SASH_MID_RAIL_BOLD', [4990, 1935, 2590], [5690, 1935, 1050], 48, 52, materials[:timber], [0, 1, 0])

raise 'The annex roof must remain lower than the main roof' unless z_attach < roof_z1 && z_rear < z_attach
raise 'The oversized plant screen remains in the owned root' if root.entities.grep(Sketchup::Group).any? { |g| g.name == 'BICYCLE_CORNER_PLANT_SCREEN' }
{
  'correction' => 4,
  'annex_estimated_footprint_mm' => [x_right - x_left, y_rear - wall_y0],
  'annex_roof_edges_z_mm' => [z_attach, z_rear],
  'visible_main_roof_rise_mm' => roof_z1 - roof_z0,
  'main_roof_rib_instances' => main_rib_count,
  'annex_roof_rib_instances' => annex_rib_count,
  'sash_leaf' => 'outward-tilted glazing retained; timber perimeter and midrail emphasized',
  'outside_template_objects_touched' => false
}
