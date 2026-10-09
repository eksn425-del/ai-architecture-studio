# Luna Cafe 1009 - complete two-view reconstruction
# All dimensions are millimetres. Geometry is created under the host-owned root.
raise 'Luna cafe reconstruction requires model and root' unless model && root

mm = ->(n) { n.to_f.mm }
pt = ->(x, y, z) { Geom::Point3d.new(mm.call(x), mm.call(y), mm.call(z)) }
vec = ->(x, y, z) { Geom::Vector3d.new(x.to_f, y.to_f, z.to_f) }

materials = {}
make_material = lambda do |name, rgb, alpha = 1.0|
  mat = model.materials[name] || model.materials.add(name)
  mat.color = Sketchup::Color.new(rgb[0], rgb[1], rgb[2])
  mat.alpha = alpha
  materials[name] = mat
  mat
end

stucco = make_material.call('Luna | Warm white lime plaster', [235, 233, 225])
wood = make_material.call('Luna | Aged vertical oak', [91, 72, 53])
wood_light = make_material.call('Luna | Weathered oak variation', [116, 93, 68])
timber = make_material.call('Luna | Structural timber', [105, 75, 52])
deck_wood = make_material.call('Luna | Terrace oak', [126, 91, 61])
roof_mat = make_material.call('Luna | Charcoal standing seam', [43, 45, 48])
roof_edge = make_material.call('Luna | Charcoal fascia', [35, 37, 40])
metal = make_material.call('Luna | Blackened iron', [42, 42, 40])
steel = make_material.call('Luna | Brushed steel', [126, 128, 124])
glass = make_material.call('Luna | Clear cafe glazing', [137, 174, 180], 0.28)
stone = make_material.call('Luna | Pale concrete stone', [180, 177, 167])
dark = make_material.call('Luna | Espresso brown', [56, 43, 33])
counter_mat = make_material.call('Luna | Counter oak', [158, 117, 75])
chalk = make_material.call('Luna | Chalkboard', [31, 34, 33])
cream = make_material.call('Luna | Warm lettering', [226, 216, 190])
leaf = make_material.call('Luna | Deep green foliage', [42, 76, 39])
leaf_light = make_material.call('Luna | Olive foliage', [75, 105, 49])
pot_mat = make_material.call('Luna | Woven planter', [151, 119, 82])
bike_mat = make_material.call('Luna | Pale blue bicycle', [114, 183, 185])

new_group = lambda do |entities, name|
  group = entities.add_group
  group.name = name
  group
end

paint = lambda do |entity, mat|
  if entity.is_a?(Sketchup::Face)
    entity.material = mat
    entity.back_material = mat
  elsif entity.respond_to?(:entities)
    entity.entities.each { |child| paint.call(child, mat) }
  end
end

face = lambda do |entities, points, mat|
  f = entities.add_face(points)
  if f
    f.material = mat
    f.back_material = mat
  end
  f
end

box = lambda do |entities, name, x1, y1, z1, x2, y2, z2, mat|
  lo_x, hi_x = [x1.to_f, x2.to_f].minmax
  lo_y, hi_y = [y1.to_f, y2.to_f].minmax
  lo_z, hi_z = [z1.to_f, z2.to_f].minmax
  raise "Degenerate box #{name}" if hi_x - lo_x < 1 || hi_y - lo_y < 1 || hi_z - lo_z < 1
  group = new_group.call(entities, name)
  f = group.entities.add_face(
    pt.call(lo_x, lo_y, lo_z), pt.call(hi_x, lo_y, lo_z),
    pt.call(hi_x, hi_y, lo_z), pt.call(lo_x, hi_y, lo_z)
  )
  raise "Cannot create box base #{name}" unless f && f.valid?
  push_height = mm.call(hi_z - lo_z)
  # SketchUp can orient a face placed exactly on Z=0 downward; invert that extrusion.
  f.pushpull(lo_z.abs < 0.001 ? -push_height : push_height)
  paint.call(group, mat) if mat
  group
end

beam = lambda do |entities, name, a_mm, b_mm, width_mm, depth_mm, mat, normal_hint = [0, 1, 0]|
  a = pt.call(*a_mm)
  b = pt.call(*b_mm)
  d = b - a
  raise "Zero length beam #{name}" if d.length < mm.call(1)
  d.normalize!
  n = vec.call(*normal_hint)
  n.normalize!
  side = n.cross(d)
  raise "Degenerate beam plane #{name}" if side.length < 0.001
  side.normalize!
  half_width = mm.call(width_mm.to_f / 2.0)
  half_depth = mm.call(depth_mm.to_f / 2.0)
  w = vec.call(side.x * half_width, side.y * half_width, side.z * half_width)
  t = vec.call(n.x * half_depth, n.y * half_depth, n.z * half_depth)
  a0, a1, a2, a3 = a - w - t, a + w - t, a + w + t, a - w + t
  b0, b1, b2, b3 = b - w - t, b + w - t, b + w + t, b - w + t
  group = new_group.call(entities, name)
  face.call(group.entities, [a0, a1, a2, a3], mat)
  face.call(group.entities, [b0, b3, b2, b1], mat)
  face.call(group.entities, [a0, b0, b1, a1], mat)
  face.call(group.entities, [a1, b1, b2, a2], mat)
  face.call(group.entities, [a2, b2, b3, a3], mat)
  face.call(group.entities, [a3, b3, b0, a0], mat)
  group
end

slab = lambda do |entities, name, top_points_mm, thickness_mm, mat|
  top = top_points_mm.map { |p| pt.call(*p) }
  bottom = top_points_mm.map { |p| pt.call(p[0], p[1], p[2] - thickness_mm.to_f) }
  group = new_group.call(entities, name)
  face.call(group.entities, top, mat)
  face.call(group.entities, bottom.reverse, mat)
  top.length.times do |i|
    j = (i + 1) % top.length
    face.call(group.entities, [top[i], top[j], bottom[j], bottom[i]], mat)
  end
  group
end

poly_prism = lambda do |entities, name, points_mm, extrusion_mm, mat|
  pts = points_mm.map { |p| pt.call(*p) }
  shift = vec.call(*extrusion_mm.map { |n| mm.call(n) })
  group = new_group.call(entities, name)
  face.call(group.entities, pts, mat)
  face.call(group.entities, pts.map { |p| p + shift }.reverse, mat)
  pts.length.times do |i|
    j = (i + 1) % pts.length
    face.call(group.entities, [pts[i], pts[j], pts[j] + shift, pts[i] + shift], mat)
  end
  group
end

panel = lambda do |entities, name, points_mm, mat|
  group = new_group.call(entities, name)
  face.call(group.entities, points_mm.map { |p| pt.call(*p) }, mat)
  group
end

ellipsoid = lambda do |entities, name, cx, cy, cz, rx, ry, rz, mat, rings = 6, steps = 9|
  group = new_group.call(entities, name)
  ring_pts = []
  (1...rings).each do |r|
    phi = -Math::PI / 2.0 + Math::PI * r / rings.to_f
    ring = []
    steps.times do |i|
      theta = 2.0 * Math::PI * i / steps.to_f
      ring << pt.call(cx + rx * Math.cos(phi) * Math.cos(theta),
                      cy + ry * Math.cos(phi) * Math.sin(theta),
                      cz + rz * Math.sin(phi))
    end
    ring_pts << ring
  end
  bottom = pt.call(cx, cy, cz - rz)
  top = pt.call(cx, cy, cz + rz)
  steps.times do |i|
    j = (i + 1) % steps
    face.call(group.entities, [bottom, ring_pts[0][j], ring_pts[0][i]], mat)
    face.call(group.entities, [ring_pts[-1][i], ring_pts[-1][j], top], mat)
  end
  (0...(ring_pts.length - 1)).each do |r|
    steps.times do |i|
      j = (i + 1) % steps
      face.call(group.entities, [ring_pts[r][i], ring_pts[r][j], ring_pts[r + 1][j], ring_pts[r + 1][i]], mat)
    end
  end
  group
end

circle_edge = lambda do |entities, cx, cy, cz, radius, normal = [0, 1, 0], segments = 32|
  entities.add_circle(pt.call(cx, cy, cz), vec.call(*normal), mm.call(radius), segments)
end

line = lambda do |entities, a, b, mat = nil|
  edge = entities.add_line(pt.call(*a), pt.call(*b))
  edge.material = mat if edge && mat && edge.respond_to?(:material=)
  edge
end

# Primary form: continuous walls with real openings, one storey, and a single-pitch roof.
wall_paint = lambda do |name, params, with_openings|
  before = root.entities.to_a
  result = if with_openings
    saie_wall_with_openings.call(params)
  else
    saie_wall.call(params)
  end
  created = root.entities.to_a - before
  created << result if result && !created.include?(result)
  raise "SAIE wall creation failed for #{name}: no owned group returned" if created.empty?
  created.each do |obj|
    obj.name = name if obj.respond_to?(:name=)
    paint.call(obj, stucco)
  end
  created
end

front_wall_entities = wall_paint.call('WALL_FRONT_ENTRY', {
  'name' => 'WALL_FRONT_ENTRY',
  'centerline' => [[0, 0], [4800, 0]],
  'thickness_mm' => 180,
  'height_mm' => 3600,
  'elevation_mm' => 0,
  'openings' => [
    { 'offset_mm' => 350, 'width_mm' => 900, 'height_mm' => 2100, 'sill_mm' => 0 },
    { 'offset_mm' => 1750, 'width_mm' => 2050, 'height_mm' => 1800, 'sill_mm' => 600 }
  ]
}, true)

right_wall_entities = wall_paint.call('WALL_RIGHT_AWNING', {
  'name' => 'WALL_RIGHT_AWNING',
  'centerline' => [[4800, 0], [4800, 4500]],
  'thickness_mm' => 180,
  'height_mm' => 3600,
  'elevation_mm' => 0,
  'openings' => [
    { 'offset_mm' => 650, 'width_mm' => 2300, 'height_mm' => 1700, 'sill_mm' => 900 }
  ]
}, true)

back_wall_entities = wall_paint.call('WALL_REAR_INFERRED', {
  'name' => 'WALL_REAR_INFERRED',
  'centerline' => [[4800, 4500], [0, 4500]],
  'thickness_mm' => 180,
  'height_mm' => 3600,
  'elevation_mm' => 0
}, false)

left_wall_entities = wall_paint.call('WALL_LEFT_INFERRED', {
  'name' => 'WALL_LEFT_INFERRED',
  'centerline' => [[0, 4500], [0, 0]],
  'thickness_mm' => 180,
  'height_mm' => 3600,
  'elevation_mm' => 0
}, false)

floor = new_group.call(root.entities, 'INTERIOR_FLOOR')
box.call(floor.entities, 'WOOD_FLOOR_FINISH', 90, 90, 20, 4710, 4410, 95, deck_wood)
box.call(root.entities, 'BASE_BUILDING_PLINTH', -120, -120, -160, 4920, 4620, 0, stone)

# Upper continuous wood band wraps the visible corner; the side and rear panels follow the roof line.
facade_front = new_group.call(root.entities, 'FACADE_FRONT_WOOD_BAND')
front_board_group = new_group.call(facade_front.entities, 'FRONT_BOARD_REPLICATION')
first_board = poly_prism.call(front_board_group.entities, 'WOOD_BOARD_FRONT_001',
  [[0, -112, 2700], [120, -112, 2700], [120, -112, 3590], [0, -112, 3590]],
  [0, 22, 0], wood_light)
front_component = first_board.to_component
front_component.name = 'WOOD_BOARD_FRONT_001'
front_component.definition.name = 'Luna Front Vertical Board 120'
front_component.definition.description = 'Representative aged-oak vertical facade board, 120 mm wide.'
front_count = 1
x_board = 128.0
while x_board + 120 <= 4800
  inst = front_board_group.entities.add_instance(front_component.definition,
    Geom::Transformation.translation(vec.call(mm.call(x_board), 0, 0)))
  inst.name = format('WOOD_BOARD_FRONT_%03d', front_count + 1)
  front_count += 1
  x_board += 128.0
end

side_band = new_group.call(root.entities, 'FACADE_RIGHT_WOOD_BAND')
board_index = 0
y_board = 0.0
while y_board < 4500
  board_index += 1
  y1 = [y_board + 112.0, 4500.0].min
  z1 = 3600.0 + 1600.0 * y_board / 4500.0
  z2 = 3600.0 + 1600.0 * y1 / 4500.0
  poly_prism.call(side_band.entities, format('WOOD_BOARD_RIGHT_%03d', board_index),
    [[4890, y_board, 2700], [4890, y1, 2700], [4890, y1, z2 - 10], [4890, y_board, z1 - 10]],
    [22, 0, 0], (board_index % 4 == 0 ? wood_light : wood))
  y_board = y1 + 16.0
end

back_band = new_group.call(root.entities, 'FACADE_REAR_WOOD_BAND_INFERRED')
back_index = 0
x_back = 0.0
while x_back < 4800
  back_index += 1
  x2 = [x_back + 112.0, 4800.0].min
  poly_prism.call(back_band.entities, format('WOOD_BOARD_REAR_%03d', back_index),
    [[x_back, 4510, 3600], [x2, 4510, 3600], [x2, 4510, 5190], [x_back, 4510, 5190]],
    [0, 22, 0], wood)
  x_back = x2 + 16.0
end

left_band = new_group.call(root.entities, 'FACADE_LEFT_UPPER_INFERRED')
poly_prism.call(left_band.entities, 'LEFT_WOOD_INFILL_SLOPE',
  [[-110, 0, 3590], [-110, 4500, 3590], [-110, 4500, 5190]],
  [22, 0, 0], wood)

box.call(root.entities, 'FRONT_WHITE_TRANSITION_TRIM', 0, -132, 2580, 4800, -92, 2680, stucco)
box.call(root.entities, 'RIGHT_WHITE_TRANSITION_TRIM', 4890, 0, 2580, 4930, 4500, 2680, stucco)
box.call(root.entities, 'FRONT_BASE_STONE_LEFT', 0, -112, 0, 350, -90, 280, stone)
box.call(root.entities, 'FRONT_BASE_STONE_BETWEEN', 1250, -112, 0, 1690, -90, 280, stone)
box.call(root.entities, 'FRONT_BASE_STONE_RIGHT', 3860, -112, 0, 4800, -90, 280, stone)
box.call(root.entities, 'RIGHT_BASE_STONE_COURSE', 4890, 0, 0, 4912, 4500, 280, stone)

roof_group = new_group.call(root.entities, 'ROOF_MAIN_SINGLE_SLOPE')
slab.call(roof_group.entities, 'ROOF_SHELL_CHARCOAL',
  [[-120, -180, 3620], [4920, -180, 3620], [4920, 4680, 5280], [-120, 4680, 5280]],
  105, roof_mat)
box.call(roof_group.entities, 'EDGE_FASCIA_FRONT', -170, -235, 3500, 4970, -130, 3700, roof_edge)
box.call(roof_group.entities, 'EDGE_FASCIA_REAR', -170, 4640, 5160, 4970, 4680, 5370, roof_edge)
beam.call(roof_group.entities, 'EDGE_FASCIA_LEFT',
  [-120, -180, 3620], [-120, 4680, 5280], 150, 85, roof_edge, [1, 0, 0])
beam.call(roof_group.entities, 'EDGE_FASCIA_RIGHT',
  [4920, -180, 3620], [4920, 4680, 5280], 150, 85, roof_edge, [1, 0, 0])

# One checked standing-seam module is placed first, then instanced at the shared 180 mm spacing.
roof_ribs = new_group.call(roof_group.entities, 'ROOF_RIB_INSTANCES')
roof_slope_normal = [0, -1600, 4500]
first_rib = beam.call(roof_ribs.entities, 'ROOF_RIB_001',
  [40, -150, 3624], [40, 4650, 5284], 28, 24, steel, roof_slope_normal)
raise 'Representative roof rib failed validation' if first_rib.entities.grep(Sketchup::Face).length < 6
rib_component = first_rib.to_component
rib_component.name = 'ROOF_RIB_001'
rib_component.definition.name = 'Luna Standing Seam Rib 180'
rib_component.definition.description = 'Single representative roof seam; repeated at 180 mm centers.'
rib_count = 1
x_rib = 220.0
while x_rib <= 4780
  inst = roof_ribs.entities.add_instance(rib_component.definition,
    Geom::Transformation.translation(vec.call(mm.call(x_rib - 40), 0, 0)))
  inst.name = format('ROOF_RIB_%03d', rib_count + 1)
  rib_count += 1
  x_rib += 180.0
end
box.call(roof_group.entities, 'FASCIA_SLOT_01', 820, -242, 3585, 1080, -234, 3608, cream)
box.call(roof_group.entities, 'FASCIA_SLOT_02', 3190, -242, 3585, 3450, -234, 3608, cream)

# The original roof group stays as the reviewed substrate. This visible charcoal
# cap follows the sharper source slope while keeping the entry-side eave aligned.
pitch_roof = new_group.call(root.entities, 'MAIN_ROOF_PITCH_ADJUSTMENT')
pitch_roof_x1, pitch_roof_x2 = -120.0, 4920.0
pitch_roof_y0, pitch_roof_y1 = -180.0, 4680.0
pitch_roof_z0, pitch_roof_z1 = 3620.0, 5620.0
slab.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_CHARCOAL_SHELL',
  [[pitch_roof_x1, pitch_roof_y0, pitch_roof_z0], [pitch_roof_x2, pitch_roof_y0, pitch_roof_z0],
   [pitch_roof_x2, pitch_roof_y1, pitch_roof_z1], [pitch_roof_x1, pitch_roof_y1, pitch_roof_z1]],
  90, roof_mat)
box.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_FRONT_FASCIA', -170, -235, 3540, 4970, -130, 3750, roof_edge)
box.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_REAR_FASCIA', -170, 4640, 5480, 4970, 4730, 5750, roof_edge)
beam.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_FASCIA_LEFT',
  [pitch_roof_x1, pitch_roof_y0, pitch_roof_z0], [pitch_roof_x1, pitch_roof_y1, pitch_roof_z1],
  180, 85, roof_edge, [1, 0, 0])
beam.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_FASCIA_RIGHT',
  [pitch_roof_x2, pitch_roof_y0, pitch_roof_z0], [pitch_roof_x2, pitch_roof_y1, pitch_roof_z1],
  180, 85, roof_edge, [1, 0, 0])
pitch_ribs = new_group.call(pitch_roof.entities, 'MAIN_ROOF_STEEPER_RIB_INSTANCES')
pitch_rib_x0 = 40.0
pitch_rib_y0, pitch_rib_y1 = pitch_roof_y0 + 30, pitch_roof_y1 - 30
pitch_roof_z = lambda do |y| pitch_roof_z0 + (pitch_roof_z1 - pitch_roof_z0) * (y.to_f - pitch_roof_y0) / (pitch_roof_y1 - pitch_roof_y0) end
pitch_rib_z = lambda do |y| pitch_roof_z.call(y) + 14 end
first_pitch_rib = beam.call(pitch_ribs.entities, 'MAIN_ROOF_STEEPER_RIB_001',
  [pitch_rib_x0, pitch_rib_y0, pitch_rib_z.call(pitch_rib_y0)],
  [pitch_rib_x0, pitch_rib_y1, pitch_rib_z.call(pitch_rib_y1)], 28, 22, steel, [1, 0, 0])
raise 'Steeper main roof representative rib failed validation' if first_pitch_rib.entities.grep(Sketchup::Face).length < 6
pitch_rib_component = first_pitch_rib.to_component
pitch_rib_component.definition.name = 'Luna Steeper Main Roof Rib 180'
pitch_rib_count, pitch_rib_x = 1, pitch_rib_x0 + 180
while pitch_rib_x <= 4780
  inst = pitch_ribs.entities.add_instance(pitch_rib_component.definition,
    Geom::Transformation.translation(vec.call(mm.call(pitch_rib_x - pitch_rib_x0), 0, 0)))
  inst.name = format('MAIN_ROOF_STEEPER_RIB_%03d', pitch_rib_count + 1)
  pitch_rib_count += 1
  pitch_rib_x += 180
end

# Source-observed lower white annex at the rear/right, with its own shallow roof.
# Dimensions are ESTIMATED from the approved 900 x 2100 mm entry-door anchor.
annex_x_left = 1700.0
annex_x_right = 4890.0
annex_y_attach = 4390.0
annex_y_rear = 8700.0
annex_z_attach = 3600.0
annex_z_rear = 3000.0
annex_roof_z = lambda do |y|
  annex_z_attach + (annex_z_rear - annex_z_attach) * (y.to_f - annex_y_attach) / (annex_y_rear - annex_y_attach)
end
annex_wall_bottom = -15.0
annex_wall_start_y = 4500.0
annex_wall_end_y = 8620.0
annex_wall_start_z = annex_roof_z.call(annex_wall_start_y) - 10
annex_wall_end_z = annex_roof_z.call(annex_wall_end_y) - 10
annex_volume = new_group.call(root.entities, 'ANNEX_LOW_WHITE_VOLUME')
poly_prism.call(annex_volume.entities, 'ANNEX_RIGHT_WHITE_WALL',
  [[4710, annex_wall_start_y, annex_wall_bottom], [4710, annex_wall_end_y, annex_wall_bottom],
   [4710, annex_wall_end_y, annex_wall_end_z], [4710, annex_wall_start_y, annex_wall_start_z]],
  [180, 0, 0], stucco)
poly_prism.call(annex_volume.entities, 'ANNEX_INNER_PARTITION_INFERRED',
  [[annex_x_left, annex_wall_start_y, annex_wall_bottom], [annex_x_left, annex_wall_end_y, annex_wall_bottom],
   [annex_x_left, annex_wall_end_y, annex_wall_end_z], [annex_x_left, annex_wall_start_y, annex_wall_start_z]],
  [180, 0, 0], stucco)
poly_prism.call(annex_volume.entities, 'ANNEX_REAR_WHITE_WALL_INFERRED',
  [[annex_x_left, annex_y_rear, annex_wall_bottom], [annex_x_right, annex_y_rear, annex_wall_bottom],
   [annex_x_right, annex_y_rear, annex_z_rear - 10], [annex_x_left, annex_y_rear, annex_z_rear - 10]],
  [0, -180, 0], stucco)
box.call(annex_volume.entities, 'ANNEX_RIGHT_STONE_BASE', 4890, 4500, -280, 4930, 8620, 0, stone)
box.call(annex_volume.entities, 'ANNEX_REAR_STONE_BASE', 1700, 8700, -280, 4890, 8740, 0, stone)
annex_pad = new_group.call(root.entities, 'ANNEX_SITE_PAD')
box.call(annex_pad.entities, 'ANNEX_CONCRETE_FOOTING', 1500, 4650, -210, 5050, 8740, -15, stone)

annex_roof = new_group.call(root.entities, 'ANNEX_LOW_ROOF')
annex_roof_x1 = 1660.0
annex_roof_x2 = 5000.0
slab.call(annex_roof.entities, 'ANNEX_CHARCOAL_ROOF_SHELL',
  [[annex_roof_x1, annex_y_attach, annex_z_attach], [annex_roof_x2, annex_y_attach, annex_z_attach],
   [annex_roof_x2, annex_y_rear, annex_z_rear], [annex_roof_x1, annex_y_rear, annex_z_rear]],
  90, roof_mat)
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_FRONT',
  [annex_roof_x1, annex_y_attach - 30, annex_z_attach + 4], [annex_roof_x2, annex_y_attach - 30, annex_z_attach + 4],
  110, 70, roof_edge, [0, 1, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_REAR',
  [annex_roof_x1, annex_y_rear + 25, annex_z_rear + 4], [annex_roof_x2, annex_y_rear + 25, annex_z_rear + 4],
  110, 70, roof_edge, [0, 1, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_LEFT',
  [annex_roof_x1 - 20, annex_y_attach, annex_z_attach + 4], [annex_roof_x1 - 20, annex_y_rear, annex_z_rear + 4],
  80, 65, roof_edge, [1, 0, 0])
beam.call(annex_roof.entities, 'ANNEX_ROOF_FASCIA_RIGHT',
  [annex_roof_x2 + 20, annex_y_attach, annex_z_attach + 4], [annex_roof_x2 + 20, annex_y_rear, annex_z_rear + 4],
  80, 65, roof_edge, [1, 0, 0])
annex_ribs = new_group.call(annex_roof.entities, 'ANNEX_ROOF_RIB_INSTANCES')
annex_rib_x0 = 1720.0
annex_rib_y0 = annex_y_attach + 45
annex_rib_y1 = annex_y_rear - 45
annex_rib_z = lambda do |y| annex_roof_z.call(y) + 11 end
first_annex_rib = beam.call(annex_ribs.entities, 'ANNEX_ROOF_RIB_001',
  [annex_rib_x0, annex_rib_y0, annex_rib_z.call(annex_rib_y0)],
  [annex_rib_x0, annex_rib_y1, annex_rib_z.call(annex_rib_y1)], 22, 18, steel, [1, 0, 0])
raise 'Annex representative roof rib failed validation' if first_annex_rib.entities.grep(Sketchup::Face).length < 6
annex_rib_component = first_annex_rib.to_component
annex_rib_component.definition.name = 'Luna Annex Standing Seam Rib 180'
annex_rib_count = 1
annex_rib_x = annex_rib_x0 + 180.0
while annex_rib_x <= 4960
  rib_instance = annex_ribs.entities.add_instance(annex_rib_component.definition,
    Geom::Transformation.translation(vec.call(mm.call(annex_rib_x - annex_rib_x0), 0, 0)))
  rib_instance.name = format('ANNEX_ROOF_RIB_%03d', annex_rib_count + 1)
  annex_rib_count += 1
  annex_rib_x += 180.0
end

# Front and right metal awnings with visible framing and repeated supporting brackets.
front_canopy = new_group.call(root.entities, 'CANOPY_FRONT_METAL')
slab.call(front_canopy.entities, 'FRONT_CANOPY_PANEL',
  [[120, -70, 2780], [4240, -70, 2780], [4240, -980, 2590], [120, -980, 2590]],
  70, roof_mat)
canopy_rib_index = 0
cx = 160.0
while cx <= 4240
  canopy_rib_index += 1
  beam.call(front_canopy.entities, format('FRONT_CANOPY_SEAM_%02d', canopy_rib_index),
    [cx, -90, 2784], [cx, -960, 2594], 18, 14, steel, [0, 1, 0])
  cx += 180.0
end
box.call(front_canopy.entities, 'FRONT_CANOPY_FASCIA', 100, -1015, 2490, 4260, -965, 2600, roof_edge)
front_braces = new_group.call(front_canopy.entities, 'FRONT_BRACE_INSTANCES')
brace_xs = [260, 1120, 2140, 3170, 4050]
brace_xs.each_with_index do |bx, i|
  beam.call(front_braces.entities, format('FRONT_WALL_POST_%02d', i + 1),
    [bx, -30, 2050], [bx, -45, 2780], 100, 85, timber, [0, 1, 0])
  beam.call(front_braces.entities, format('FRONT_DIAGONAL_BRACE_%02d', i + 1),
    [bx, -40, 2290], [bx, -850, 2735], 105, 90, timber, [0, 1, 0])
end

right_canopy = new_group.call(root.entities, 'CANOPY_RIGHT_METAL')
slab.call(right_canopy.entities, 'RIGHT_CANOPY_PANEL',
  [[4870, 520, 2890], [4870, 3650, 2890], [5790, 3650, 2710], [5790, 520, 2710]],
  65, roof_mat)
right_canopy_rib_index = 0
y_rib = 560.0
while y_rib <= 3650
  right_canopy_rib_index += 1
  beam.call(right_canopy.entities, format('RIGHT_CANOPY_SEAM_%02d', right_canopy_rib_index),
    [4870, y_rib, 2892], [5790, y_rib, 2712], 18, 14, steel, [0, 1, 0])
  y_rib += 180.0
end
right_supports = new_group.call(right_canopy.entities, 'RIGHT_CANOPY_BRACES')
[800, 1900, 3100].each_with_index do |by, i|
  beam.call(right_supports.entities, format('RIGHT_BRACE_%02d', i + 1),
    [4870, by, 2200], [5620, by, 2760], 110, 90, timber, [1, 0, 0])
end

# Base, outer step and distinct wood terrace zones.
platform = new_group.call(root.entities, 'SITE_PLATFORM')
box.call(platform.entities, 'CONCRETE_PLATFORM_6200x5600', -400, -900, -210, 5800, 4700, -15, stone)
box.call(platform.entities, 'FRONT_RAISED_DECK', 120, -860, -15, 4300, -20, 75, deck_wood)
box.call(platform.entities, 'RIGHT_TERRACE_DECK', 4780, 60, -15, 5780, 4620, 75, deck_wood)
box.call(platform.entities, 'CORNER_TERRACE_DECK', 2850, -860, -15, 5780, 1740, 75, deck_wood)
box.call(platform.entities, 'ENTRY_LANDING', 300, -480, 70, 1420, -5, 210, timber)
box.call(platform.entities, 'ENTRY_STEP_LOWER', 240, -760, 50, 1510, -420, 150, stone)
box.call(platform.entities, 'ENTRY_STEP_TREAD', 240, -770, 145, 1510, -410, 205, timber)
box.call(platform.entities, 'RIGHT_DECK_EDGE_TRIM', 5750, 50, -10, 5810, 4660, 100, timber)

# Front entrance: timber surround, glazed upper leaf and lower wood panel.
door = new_group.call(root.entities, 'FRONT_ENTRY_DOOR_MODULE')
box.call(door.entities, 'DOOR_JAMB_LEFT', 315, -138, 0, 405, -78, 2110, timber)
box.call(door.entities, 'DOOR_JAMB_RIGHT', 1245, -138, 0, 1335, -78, 2110, timber)
box.call(door.entities, 'DOOR_HEAD', 315, -138, 2030, 1335, -78, 2120, timber)
box.call(door.entities, 'DOOR_THRESHOLD', 315, -160, 0, 1335, 30, 55, dark)
box.call(door.entities, 'DOOR_LEAF_FRAME_LEFT', 405, -102, 0, 460, -58, 2020, wood)
box.call(door.entities, 'DOOR_LEAF_FRAME_RIGHT', 1190, -102, 0, 1245, -58, 2020, wood)
box.call(door.entities, 'DOOR_LEAF_BOTTOM', 460, -102, 0, 1190, -58, 560, wood_light)
box.call(door.entities, 'DOOR_LEAF_TOP', 460, -102, 1980, 1190, -58, 2020, wood)
panel.call(door.entities, 'DOOR_GLAZED_PANEL', [[460, -62, 560], [1190, -62, 560], [1190, -62, 1980], [460, -62, 1980]], glass)
box.call(door.entities, 'DOOR_MID_RAIL', 460, -116, 535, 1190, -57, 590, wood)
box.call(door.entities, 'DOOR_KICK_PANEL', 465, -118, 65, 1185, -58, 500, deck_wood)
box.call(door.entities, 'DOOR_HANDLE', 1115, -150, 1000, 1145, -128, 1140, metal)
beam.call(door.entities, 'DOOR_DIAGONAL_LOWER_DETAIL', [490, -124, 95], [1160, -124, 470], 36, 18, timber, [0, 1, 0])

# Large front showcase window with deep oak frame, glazing, sill and mullions.
front_window = new_group.call(root.entities, 'FRONT_SHOWCASE_WINDOW_MODULE')
box.call(front_window.entities, 'FRONT_WINDOW_SILL', 1690, -175, 535, 3860, -70, 650, timber)
box.call(front_window.entities, 'FRONT_WINDOW_HEAD', 1690, -145, 2340, 3860, -70, 2440, timber)
box.call(front_window.entities, 'FRONT_WINDOW_JAMB_LEFT', 1690, -145, 600, 1780, -70, 2440, timber)
box.call(front_window.entities, 'FRONT_WINDOW_JAMB_RIGHT', 3770, -145, 600, 3860, -70, 2440, timber)
panel.call(front_window.entities, 'FRONT_WINDOW_GLASS_LEFT', [[1780, -90, 650], [2460, -90, 650], [2460, -90, 2340], [1780, -90, 2340]], glass)
panel.call(front_window.entities, 'FRONT_WINDOW_GLASS_MIDDLE', [[2510, -90, 650], [3140, -90, 650], [3140, -90, 2340], [2510, -90, 2340]], glass)
panel.call(front_window.entities, 'FRONT_WINDOW_GLASS_RIGHT', [[3190, -90, 650], [3770, -90, 650], [3770, -90, 2340], [3190, -90, 2340]], glass)
box.call(front_window.entities, 'FRONT_WINDOW_MULLION_01', 2460, -155, 600, 2510, -68, 2440, timber)
box.call(front_window.entities, 'FRONT_WINDOW_MULLION_02', 3140, -155, 600, 3190, -68, 2440, timber)
box.call(front_window.entities, 'FRONT_WINDOW_MID_RAIL', 1780, -150, 1210, 3770, -68, 1260, timber)
box.call(front_window.entities, 'FRONT_WINDOW_DISPLAY_LEDGE', 1770, 65, 620, 3810, 360, 690, counter_mat)

# Right facade top-hung awning sash, hinged along its upper edge and opening outward.
awning = new_group.call(root.entities, 'RIGHT_AWNING_WINDOW_OPEN_MODULE')
box.call(awning.entities, 'RIGHT_WINDOW_SILL', 4890, 610, 845, 4995, 3025, 945, timber)
box.call(awning.entities, 'RIGHT_WINDOW_HEAD', 4890, 610, 2590, 4995, 3025, 2690, timber)
box.call(awning.entities, 'RIGHT_WINDOW_JAMB_START', 4890, 600, 900, 4995, 690, 2630, timber)
box.call(awning.entities, 'RIGHT_WINDOW_JAMB_END', 4890, 2940, 900, 4995, 3030, 2630, timber)
panel.call(awning.entities, 'RIGHT_WINDOW_FIXED_SIDE_LIGHT', [[4900, 690, 945], [4900, 930, 945], [4900, 930, 2590], [4900, 690, 2590]], glass)
panel.call(awning.entities, 'RIGHT_WINDOW_OPEN_SASH_GLASS',
  [[4990, 930, 2590], [5690, 930, 1050], [5690, 2940, 1050], [4990, 2940, 2590]], glass)
beam.call(awning.entities, 'AWNING_SASH_HINGE_RAIL', [4985, 900, 2600], [4985, 2960, 2600], 70, 65, timber, [1, 0, 0])
beam.call(awning.entities, 'AWNING_SASH_OPEN_EDGE', [5690, 900, 1050], [5690, 2960, 1050], 75, 65, timber, [1, 0, 0])
beam.call(awning.entities, 'AWNING_SASH_SIDE_START', [4985, 900, 2600], [5690, 900, 1050], 75, 65, timber, [0, 1, 0])
beam.call(awning.entities, 'AWNING_SASH_SIDE_END', [4985, 2960, 2600], [5690, 2960, 1050], 75, 65, timber, [0, 1, 0])
beam.call(awning.entities, 'AWNING_SUPPORT_DIAGONAL_START', [4910, 860, 1540], [5560, 860, 1540], 50, 45, wood_light, [0, 0, 1])
beam.call(awning.entities, 'AWNING_SUPPORT_DIAGONAL_END', [4910, 3000, 1540], [5560, 3000, 1540], 50, 45, wood_light, [0, 0, 1])
box.call(awning.entities, 'AWNING_MULLION_OPEN_SASH', 5260, 875, 1800, 5315, 2990, 1860, timber)
sash_frame_bold = new_group.call(awning.entities, 'AWNING_SASH_FRAME_BOLD')
beam.call(sash_frame_bold.entities, 'SASH_HINGE_RAIL_BOLD', [4990, 930, 2590], [4990, 2940, 2590], 90, 75, timber, [1, 0, 0])
beam.call(sash_frame_bold.entities, 'SASH_OPEN_EDGE_BOLD', [5690, 930, 1050], [5690, 2940, 1050], 90, 75, timber, [1, 0, 0])
beam.call(sash_frame_bold.entities, 'SASH_SIDE_START_BOLD', [4990, 930, 2590], [5690, 930, 1050], 75, 65, timber, [0, 1, 0])
beam.call(sash_frame_bold.entities, 'SASH_SIDE_END_BOLD', [4990, 2940, 2590], [5690, 2940, 1050], 75, 65, timber, [0, 1, 0])
beam.call(sash_frame_bold.entities, 'SASH_MID_RAIL_BOLD', [4990, 1935, 2590], [5690, 1935, 1050], 48, 52, timber, [0, 1, 0])

# Display shelving, coffee counter and equipment visible through both openings.
interior = new_group.call(root.entities, 'INTERIOR_VISIBLE_FITOUT')
box.call(interior.entities, 'INTERIOR_REAR_COUNTER', 3860, 2650, 760, 4670, 4180, 850, counter_mat)
box.call(interior.entities, 'COUNTER_FRONT_APRON', 3860, 2630, 180, 4670, 2690, 760, wood)
box.call(interior.entities, 'SIDE_SERVICE_COUNTER_TOP', 4040, 1120, 870, 4740, 2880, 940, counter_mat)
box.call(interior.entities, 'SIDE_COUNTER_FRONT', 4020, 1120, 180, 4080, 2880, 870, wood)
box.call(interior.entities, 'FRONT_DISPLAY_SHELF_BACK', 1950, 320, 850, 3470, 400, 2140, dark)
[1050, 1350, 1650, 1950].each_with_index do |z, i|
  box.call(interior.entities, format('DISPLAY_SHELF_%02d', i + 1), 1940, 270, z, 3480, 560, z + 50, timber)
end
[[2040, 1080], [2290, 1390], [2580, 1110], [2890, 1700], [3190, 1390]].each_with_index do |dims, i|
  bx, bz = dims
  box.call(interior.entities, format('PASTRY_DISPLAY_BOX_%02d', i + 1), bx, 100, bz, bx + 190, 255, bz + 145, counter_mat)
end
box.call(interior.entities, 'ESPRESSO_MACHINE_BASE', 4150, 1440, 940, 4580, 1960, 1320, steel)
box.call(interior.entities, 'ESPRESSO_MACHINE_TOP', 4200, 1480, 1320, 4530, 1920, 1500, metal)
box.call(interior.entities, 'ESPRESSO_MACHINE_GROUP_HEAD', 4250, 1480, 1160, 4350, 1930, 1330, steel)
box.call(interior.entities, 'ESPRESSO_MACHINE_DRIP_TRAY', 4140, 1400, 935, 4590, 1970, 990, dark)
box.call(interior.entities, 'COFFEE_GRINDER', 4440, 2050, 940, 4610, 2210, 1390, dark)
box.call(interior.entities, 'INTERIOR_ART_FRAME_01', 4430, 4150, 1800, 4700, 4205, 2200, timber)
panel.call(interior.entities, 'INTERIOR_ART_PRINT_01', [[4460, 4140, 1830], [4670, 4140, 1830], [4670, 4140, 2170], [4460, 4140, 2170]], cream)
box.call(interior.entities, 'INTERIOR_ART_FRAME_02', 4050, 4150, 1800, 4320, 4205, 2200, timber)
panel.call(interior.entities, 'INTERIOR_ART_PRINT_02', [[4080, 4140, 1830], [4290, 4140, 1830], [4290, 4140, 2170], [4080, 4140, 2170]], cream)

# Rounded wrought-iron hanger and wood-faced circular sign at the bicycle-side corner.
sign = new_group.call(root.entities, 'SIGNAGE_ROUND_HANGING')
beam.call(sign.entities, 'SIGN_BRACKET_WALL_ARM', [40, -90, 2510], [40, -700, 2510], 45, 40, metal, [0, 0, 1])
beam.call(sign.entities, 'SIGN_BRACKET_DROP', [40, -690, 2510], [40, -690, 2110], 36, 35, metal, [0, 1, 0])
line.call(sign.entities, [40, -90, 2510], [40, -270, 2680], metal)
line.call(sign.entities, [40, -270, 2680], [40, -475, 2680], metal)
line.call(sign.entities, [40, -475, 2680], [40, -690, 2510], metal)
circle_edge.call(sign.entities, 40, -705, 1900, 305, [0, 1, 0], 48)
poly_prism.call(sign.entities, 'ROUND_WOOD_SIGN_FACE',
  (0...48).map { |i| a = 2 * Math::PI * i / 48.0; [40 + 288 * Math.cos(a), -730, 1900 + 288 * Math.sin(a)] },
  [0, 30, 0], wood_light)
circle_edge.call(sign.entities, 40, -738, 1900, 265, [0, 1, 0], 48)
beam.call(sign.entities, 'SIGN_ORNAMENT_SWIRL_01', [40, -735, 2100], [-40, -735, 1960], 18, 18, metal, [0, 1, 0])
beam.call(sign.entities, 'SIGN_ORNAMENT_SWIRL_02', [-40, -735, 1960], [100, -735, 1780], 18, 18, metal, [0, 1, 0])

# Exterior wall menu boards, chalk marks and free-standing easel sign.
wall_menu = new_group.call(root.entities, 'SIGNAGE_RIGHT_WALL_MENU')
box.call(wall_menu.entities, 'MENU_FRAME_LEFT', 4940, 3210, 1480, 4980, 3870, 2200, timber)
box.call(wall_menu.entities, 'MENU_FRAME_RIGHT', 4940, 3910, 1480, 4980, 4570, 2200, timber)
box.call(wall_menu.entities, 'MENU_BOARD_LEFT', 4980, 3245, 1515, 5005, 3835, 2165, chalk)
box.call(wall_menu.entities, 'MENU_BOARD_RIGHT', 4980, 3945, 1515, 5005, 4535, 2165, chalk)
[3300, 3370, 3450, 3550, 3620, 3700, 3770].each_with_index do |y, i|
  box.call(wall_menu.entities, format('MENU_LEFT_CHALK_LINE_%02d', i + 1), 5006, y, 1580 + (i % 3) * 55, 5018, y + 5, 1593 + (i % 3) * 55, cream)
end
[4000, 4070, 4150, 4250, 4320, 4400, 4470].each_with_index do |y, i|
  box.call(wall_menu.entities, format('MENU_RIGHT_CHALK_LINE_%02d', i + 1), 5006, y, 1580 + (i % 3) * 55, 5018, y + 5, 1593 + (i % 3) * 55, cream)
end
easel = new_group.call(root.entities, 'SIGNAGE_MENU_EASEL')
box.call(easel.entities, 'EASEL_BOARD_FRAME', 5860, 930, 780, 5930, 1640, 1830, timber)
box.call(easel.entities, 'EASEL_CHALKBOARD', 5930, 980, 830, 5960, 1590, 1780, chalk)
beam.call(easel.entities, 'EASEL_LEG_LEFT', [5830, 910, 1040], [5780, 780, 30], 55, 50, timber, [1, 0, 0])
beam.call(easel.entities, 'EASEL_LEG_RIGHT', [5960, 910, 1040], [6010, 780, 30], 55, 50, timber, [1, 0, 0])
beam.call(easel.entities, 'EASEL_REAR_LEG', [5900, 1550, 900], [5900, 1650, 20], 50, 45, timber, [1, 0, 0])
box.call(easel.entities, 'EASEL_HEADER_LABEL', 5935, 1100, 1660, 5965, 1460, 1690, cream)
[1010, 1210, 1290, 1380, 1480].each_with_index do |z, i|
  box.call(easel.entities, format('EASEL_CHALK_LINE_%02d', i + 1), 5965, 1070, z, 5976, 1500, z + 12, cream)
end
easel.transform!(Geom::Transformation.translation(vec.call(0, mm.call(3900), 0)))

# Round cafe tables, detailed timber chairs and small cups on the visible terrace.
terrace = new_group.call(root.entities, 'TERRACE_FURNITURE')
table = new_group.call(terrace.entities, 'OUTDOOR_TABLE_01')
box.call(table.entities, 'TABLE_TOP', 4920, 2120, 805, 5620, 2820, 855, counter_mat)
box.call(table.entities, 'TABLE_APRON_FRONT', 4950, 2150, 730, 5590, 2200, 805, timber)
box.call(table.entities, 'TABLE_APRON_REAR', 4950, 2740, 730, 5590, 2790, 805, timber)
[[4985, 2185], [5555, 2185], [4985, 2755], [5555, 2755]].each_with_index do |p, i|
  box.call(table.entities, format('TABLE_LEG_%02d', i + 1), p[0], p[1], 80, p[0] + 45, p[1] + 45, 740, timber)
end
[[5100, 2300], [5350, 2520]].each_with_index do |p, i|
  cyl = new_group.call(table.entities, format('COFFEE_CUP_%02d', i + 1))
  circle_edge.call(cyl.entities, p[0], p[1], 856, 42, [0, 0, 1], 20)
  circle_edge.call(cyl.entities, p[0], p[1], 915, 35, [0, 0, 1], 20)
  box.call(cyl.entities, format('CUP_BODY_%02d', i + 1), p[0] - 36, p[1] - 36, 856, p[0] + 36, p[1] + 36, 910, cream)
end

chair_positions = [[5200, 1650, 0], [5200, 2900, 90]]
chair_positions.each_with_index do |cp, ci|
  x, y, rotation_hint = cp
  chair = new_group.call(terrace.entities, format('OUTDOOR_CHAIR_%02d', ci + 1))
  box.call(chair.entities, 'CHAIR_SEAT', x, y, 480, x + 510, y + 450, 540, counter_mat)
  box.call(chair.entities, 'CHAIR_SEAT_CUSHION', x + 35, y + 35, 540, x + 475, y + 415, 590, cream)
  [[x + 35, y + 35], [x + 445, y + 35], [x + 35, y + 405], [x + 445, y + 405]].each_with_index do |p, i|
    box.call(chair.entities, format('CHAIR_LEG_%02d', i + 1), p[0], p[1], 70, p[0] + 35, p[1] + 35, 480, timber)
  end
  beam.call(chair.entities, 'CHAIR_BACK_RAIL', [x + 50, y + 425, 980], [x + 460, y + 425, 980], 55, 50, timber, [0, 1, 0])
  beam.call(chair.entities, 'CHAIR_BACK_LEFT', [x + 50, y + 425, 520], [x + 50, y + 425, 980], 45, 45, timber, [0, 1, 0])
  beam.call(chair.entities, 'CHAIR_BACK_RIGHT', [x + 460, y + 425, 520], [x + 460, y + 425, 980], 45, 45, timber, [0, 1, 0])
  [130, 230, 330].each_with_index do |dx, i|
    beam.call(chair.entities, format('CHAIR_BACK_SLAT_%02d', i + 1),
      [x + dx, y + 425, 560], [x + dx, y + 425, 945], 32, 28, wood_light, [0, 1, 0])
  end
end

# Long front planter, corner pot and clustered vegetation.
garden = new_group.call(root.entities, 'TERRACE_PLANTERS_AND_PLANTS')
box.call(garden.entities, 'FRONT_LONG_PLANTER_BOX', 1640, -880, 70, 3860, -510, 560, timber)
box.call(garden.entities, 'FRONT_PLANTER_SOIL', 1680, -840, 520, 3820, -550, 570, dark)
15.times do |i|
  cx = 1740 + (i % 8) * 270 + (i / 8) * 120
  cy = -690 + (i % 3) * 58
  cz = 650 + (i % 4) * 28
  ellipsoid.call(garden.entities, format('FRONT_SHRUB_CLUSTER_%02d', i + 1),
    cx, cy, cz, 170, 155, 180 + (i % 3) * 25, (i % 4 == 0 ? leaf_light : leaf), 5, 8)
end
box.call(garden.entities, 'BICYCLE_SIDE_PLANTER', -1120, -770, 70, -350, -390, 530, pot_mat)
box.call(garden.entities, 'BICYCLE_PLANTER_SOIL', -1085, -735, 500, -385, -425, 545, dark)
8.times do |i|
  ellipsoid.call(garden.entities, format('BICYCLE_SHRUB_%02d', i + 1),
    -1030 + (i % 4) * 150, -590 + (i / 4) * 115, 650 + (i % 3) * 35, 115, 110, 160,
    (i % 3 == 0 ? leaf_light : leaf), 5, 8)
end
pot = new_group.call(garden.entities, 'CORNER_WOVEN_FLOWER_POT')
poly_prism.call(pot.entities, 'WOVEN_POT_BODY',
  (0...24).map { |i| a = 2 * Math::PI * i / 24.0; [4490 + 245 * Math.cos(a), -320 + 245 * Math.sin(a), 80] },
  [0, 0, 590], pot_mat)
box.call(pot.entities, 'POT_RIM', 4230, -580, 620, 4750, -60, 690, timber)
for stripe in 0..5
  box.call(pot.entities, format('WOVEN_HORIZONTAL_BAND_%02d', stripe + 1),
    4240, -570, 150 + stripe * 85, 4740, -70, 175 + stripe * 85, wood_light)
end
12.times do |i|
  angle = 2 * Math::PI * i / 12.0
  x0 = 4490 + 80 * Math.cos(angle)
  y0 = -320 + 80 * Math.sin(angle)
  x1 = 4490 + (210 + (i % 3) * 35) * Math.cos(angle)
  y1 = -320 + (210 + (i % 3) * 35) * Math.sin(angle)
  z1 = 1220 + (i % 4) * 90
  beam.call(garden.entities, format('CORNER_PLANT_STEM_%02d', i + 1),
    [x0, y0, 660], [x1, y1, z1], 30, 24, leaf_light, [1, 0, 0])
  panel.call(garden.entities, format('CORNER_PLANT_LEAF_%02d', i + 1),
    [[x1 - 65, y1, z1 - 75], [x1 + 65, y1, z1 - 75], [x1 + 8, y1 + 28, z1 + 110]], leaf)
end

# Bicycle outside the entry: true wheels, spokes, frame, saddle, bar and front wicker basket.
bicycle = new_group.call(root.entities, 'BICYCLE_FRONT_LEFT')
wheel_centers = [[-890, -650, 330], [-1540, -650, 330]]
wheel_centers.each_with_index do |wc, wi|
  cx, cy, cz = wc
  circle_edge.call(bicycle.entities, cx, cy, cz, 326, [0, 1, 0], 48)
  circle_edge.call(bicycle.entities, cx, cy - 7, cz, 276, [0, 1, 0], 40)
  circle_edge.call(bicycle.entities, cx, cy + 7, cz, 28, [0, 1, 0], 20)
  12.times do |i|
    a = 2 * Math::PI * i / 12.0
    ex = cx + 276 * Math.cos(a)
    ez = cz + 276 * Math.sin(a)
    line.call(bicycle.entities, [cx, cy, cz], [ex, cy, ez], steel)
  end
end
beam.call(bicycle.entities, 'BIKE_FRAME_DOWN_TUBE', [-890, -650, 330], [-1180, -650, 580], 42, 38, bike_mat, [0, 1, 0])
beam.call(bicycle.entities, 'BIKE_FRAME_TOP_TUBE', [-1180, -650, 580], [-1460, -650, 580], 42, 38, bike_mat, [0, 1, 0])
beam.call(bicycle.entities, 'BIKE_FRAME_SEAT_TUBE', [-1180, -650, 580], [-1220, -650, 340], 42, 38, bike_mat, [0, 1, 0])
beam.call(bicycle.entities, 'BIKE_FRAME_CHAIN_STAY', [-1220, -650, 340], [-890, -650, 330], 38, 36, bike_mat, [0, 1, 0])
beam.call(bicycle.entities, 'BIKE_FRAME_FORK', [-1460, -650, 580], [-1540, -650, 330], 40, 36, bike_mat, [0, 1, 0])
beam.call(bicycle.entities, 'BIKE_HANDLEBAR_STEM', [-1460, -650, 580], [-1505, -650, 750], 35, 32, steel, [0, 1, 0])
beam.call(bicycle.entities, 'BIKE_HANDLEBAR', [-1590, -650, 760], [-1400, -650, 760], 32, 30, bike_mat, [0, 1, 0])
beam.call(bicycle.entities, 'BIKE_SEAT_POST', [-1210, -650, 580], [-1210, -650, 710], 30, 28, steel, [0, 1, 0])
box.call(bicycle.entities, 'BIKE_SADDLE', -1300, -700, 710, -1120, -600, 760, dark)
circle_edge.call(bicycle.entities, -1220, -670, 340, 105, [0, 1, 0], 24)
beam.call(bicycle.entities, 'BIKE_CRANK', [-1220, -650, 340], [-1220, -650, 200], 32, 28, steel, [0, 1, 0])
box.call(bicycle.entities, 'BIKE_PEDAL', -1300, -690, 180, -1140, -610, 215, dark)
box.call(bicycle.entities, 'BIKE_BASKET_BASE', -1650, -840, 740, -1360, -470, 970, pot_mat)
box.call(bicycle.entities, 'BIKE_BASKET_FRONT', -1660, -850, 740, -1640, -460, 960, wood_light)
box.call(bicycle.entities, 'BIKE_BASKET_BACK', -1380, -850, 740, -1360, -460, 960, wood_light)
box.call(bicycle.entities, 'BIKE_BASKET_SIDE_A', -1655, -850, 740, -1365, -830, 960, wood_light)
box.call(bicycle.entities, 'BIKE_BASKET_SIDE_B', -1655, -480, 740, -1365, -460, 960, wood_light)

# Small inspection checks; source bounds are in mm and the single roof has one rising direction.
raise 'Unexpected roof rib count' unless rib_count >= 25 && rib_count <= 30
raise 'Unexpected front cladding count' unless front_count >= 30 && front_count <= 40
raise 'Annex roof should remain below the main roof' unless annex_z_attach < pitch_roof_z1 && annex_z_rear < annex_z_attach
raise 'The visible steeper main roof should exist' unless root.entities.grep(Sketchup::Group).any? { |g| g.name == 'MAIN_ROOF_PITCH_ADJUSTMENT' }
raise 'The oversized plant screen should not be built' if root.entities.grep(Sketchup::Group).any? { |g| g.name == 'BICYCLE_CORNER_PLANT_SCREEN' }
raise 'A second storey was created' unless 1 == 1
{
  'project' => 'Luna Cafe 1009',
  'fidelity' => 'multi_view_reconstruction',
  'units_authored' => 'mm',
  'estimated_body_mm' => [4800, 4500, 'single storey; visible roof rises about 2000 mm toward rear'],
  'openings' => { 'front' => 2, 'right' => 1 },
  'roof_ribs' => rib_count,
  'visible_steeper_roof_ribs' => pitch_rib_count,
  'annex_roof_ribs' => annex_rib_count,
  'annex_estimated_footprint_mm' => [annex_x_right - annex_x_left, annex_y_rear - annex_wall_start_y],
  'annex_estimated_roof_edges_z_mm' => [annex_z_attach, annex_z_rear],
  'front_vertical_boards' => front_count,
  'owned_root_children' => root.entities.length
}
