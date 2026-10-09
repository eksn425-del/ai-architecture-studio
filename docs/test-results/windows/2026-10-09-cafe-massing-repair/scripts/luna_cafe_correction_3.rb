# Targeted correction 3: add the observed lower rear/right annex and remove the
# builder-added oversized plant screen. All geometry stays under the owned root.
raise 'Luna correction requires model and root' unless model && root

mm = ->(n) { n.to_f.mm }
pt = ->(x, y, z) { Geom::Point3d.new(mm.call(x), mm.call(y), mm.call(z)) }
vec = ->(x, y, z) { Geom::Vector3d.new(x.to_f, y.to_f, z.to_f) }
plaster = model.materials['Luna | Warm white lime plaster']
stone = model.materials['Luna | Pale concrete stone']
roof_mat = model.materials['Luna | Charcoal standing seam']
edge_mat = model.materials['Luna | Charcoal fascia']
metal = model.materials['Luna | Brushed steel']
raise 'Required Luna finish materials are missing' if [plaster, stone, roof_mat, edge_mat, metal].any?(&:nil?)

paint = lambda do |group, material|
  group.entities.grep(Sketchup::Face).each do |f|
    f.material = material
    f.back_material = material
  end
end

# Extrude a planar source profile into one real, closed solid.
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

solid_box = lambda do |entities, name, bounds_mm, material|
  x1, y1, z1, x2, y2, z2 = bounds_mm
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
  a = pt.call(*a_mm)
  b = pt.call(*b_mm)
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

# All dimensions below remain ESTIMATED from the approved 900 x 2100 mm door
# anchor and the annex-to-main-volume ratios visible in both references.
%w[ANNEX_LOW_WHITE_VOLUME ANNEX_LOW_ROOF ANNEX_SITE_PAD].each do |name|
  next unless root.entities.grep(Sketchup::Group).any? { |g| g.name == name }
  remove_owned_group.call(name)
end
if root.entities.grep(Sketchup::Group).any? { |g| g.name == 'BICYCLE_CORNER_PLANT_SCREEN' }
  remove_owned_group.call('BICYCLE_CORNER_PLANT_SCREEN')
end

x_left, x_right = 2500.0, 4890.0
y_attach, y_rear = 4390.0, 7500.0
z_attach, z_rear = 3600.0, 3000.0
roof_z = lambda { |y| z_attach + (z_rear - z_attach) * (y.to_f - y_attach) / (y_rear - y_attach) }
wall_bottom, wall_start_y, wall_end_y = -15.0, 4500.0, 7420.0
wall_start_z = roof_z.call(wall_start_y) - 10
wall_end_z = roof_z.call(wall_end_y) - 10
annex = root.entities.add_group
annex.name = 'ANNEX_LOW_WHITE_VOLUME'
profile_solid.call(annex.entities, 'ANNEX_RIGHT_WHITE_WALL',
  [[4710, wall_start_y, wall_bottom], [4710, wall_end_y, wall_bottom],
   [4710, wall_end_y, wall_end_z], [4710, wall_start_y, wall_start_z]], 180, plaster)
profile_solid.call(annex.entities, 'ANNEX_INNER_PARTITION_INFERRED',
  [[x_left, wall_start_y, wall_bottom], [x_left, wall_end_y, wall_bottom],
   [x_left, wall_end_y, wall_end_z], [x_left, wall_start_y, wall_start_z]], 180, plaster)
profile_solid.call(annex.entities, 'ANNEX_REAR_WHITE_WALL_INFERRED',
  [[x_left, y_rear, wall_bottom], [x_right, y_rear, wall_bottom],
   [x_right, y_rear, z_rear - 10], [x_left, y_rear, z_rear - 10]], 180, plaster)
solid_box.call(annex.entities, 'ANNEX_RIGHT_STONE_BASE', [4890, 4500, 0, 4930, 7420, 280], stone)
solid_box.call(annex.entities, 'ANNEX_REAR_STONE_BASE', [2500, 7500, 0, 4890, 7540, 280], stone)

# Extend the concrete grade at the same level, leaving the existing terrace group intact.
pad = root.entities.add_group
pad.name = 'ANNEX_SITE_PAD'
solid_box.call(pad.entities, 'ANNEX_CONCRETE_FOOTING', [2300, 4650, -210, 5050, 7540, -15], stone)

annex_roof = root.entities.add_group
annex_roof.name = 'ANNEX_LOW_ROOF'
roof_x1, roof_x2 = 2460.0, 5000.0
profile_solid.call(annex_roof.entities, 'ANNEX_CHARCOAL_ROOF_SHELL',
  [[roof_x1, y_attach, z_attach], [roof_x2, y_attach, z_attach],
   [roof_x2, y_rear, z_rear], [roof_x1, y_rear, z_rear]], -90, roof_mat)
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_FRONT',
  [roof_x1, y_attach - 30, z_attach + 4], [roof_x2, y_attach - 30, z_attach + 4], 110, 70, edge_mat, [0, 1, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_REAR',
  [roof_x1, y_rear + 25, z_rear + 4], [roof_x2, y_rear + 25, z_rear + 4], 110, 70, edge_mat, [0, 1, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_LEFT',
  [roof_x1 - 20, y_attach, z_attach + 4], [roof_x1 - 20, y_rear, z_rear + 4], 80, 65, edge_mat, [1, 0, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_RIGHT',
  [roof_x2 + 20, y_attach, z_attach + 4], [roof_x2 + 20, y_rear, z_rear + 4], 80, 65, edge_mat, [1, 0, 0])

# Verified representative seam, then component instances at the shared 180 mm rhythm.
ribs = annex_roof.entities.add_group
ribs.name = 'ANNEX_ROOF_RIB_INSTANCES'
rib_x0, rib_y0, rib_y1 = 2560.0, y_attach + 45, y_rear - 45
rib_z = lambda { |y| roof_z.call(y) + 11 }
first = beam.call(ribs.entities, 'ANNEX_ROOF_RIB_001',
  [rib_x0, rib_y0, rib_z.call(rib_y0)], [rib_x0, rib_y1, rib_z.call(rib_y1)], 22, 18, metal, [1, 0, 0])
raise 'Annex representative rib failed validation' if first.entities.grep(Sketchup::Face).length < 6
component = first.to_component
component.definition.name = 'Luna Annex Standing Seam Rib 180'
rib_count, rib_x = 1, rib_x0 + 180
while rib_x <= 4900
  instance = ribs.entities.add_instance(component.definition,
    Geom::Transformation.translation(vec.call(mm.call(rib_x - rib_x0), 0, 0)))
  instance.name = format('ANNEX_ROOF_RIB_%03d', rib_count + 1)
  rib_count += 1
  rib_x += 180
end

raise 'Annex roof must stay below the main roof' unless z_attach < 5200 && z_rear < z_attach
raise 'The oversized plant screen remains in the owned root' if root.entities.grep(Sketchup::Group).any? { |g| g.name == 'BICYCLE_CORNER_PLANT_SCREEN' }
{
  'correction' => 3,
  'annex_status' => 'built_as_separate_volume_and_low_roof',
  'estimated_footprint_mm' => [x_right - x_left, y_rear - wall_start_y],
  'estimated_roof_edge_z_mm' => [z_attach, z_rear],
  'door_scale_anchor_mm' => [900, 2100],
  'annex_roof_rib_instances' => rib_count,
  'removed_owned_plant_screen' => true,
  'outside_template_objects_touched' => false
}
