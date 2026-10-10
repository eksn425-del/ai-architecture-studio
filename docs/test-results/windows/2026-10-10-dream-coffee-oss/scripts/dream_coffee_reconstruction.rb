# Dream Coffee: complete editable reconstruction from the approved multi-view sheet.
# All dimensions below are millimeters and are converted at the geometry boundary.

def dc_p(x, y, z)
  Geom::Point3d.new(x.mm, y.mm, z.mm)
end

def dc_vec(x, y, z)
  Geom::Vector3d.new(x, y, z)
end

def dc_scale(vector, length_mm)
  length_internal = length_mm.to_f.mm.to_f
  Geom::Vector3d.new(vector.x * length_internal, vector.y * length_internal, vector.z * length_internal)
end

def dc_material(model, name, rgb, alpha = 0)
  m = model.materials[name] || model.materials.add(name)
  m.color = Sketchup::Color.new(rgb[0], rgb[1], rgb[2])
  m.alpha = 1.0 - alpha.to_f / 100.0
  m
end

def dc_group(entities, name)
  g = entities.add_group
  g.name = name
  g
end

def dc_apply_face_material(entities, material)
  entities.each do |e|
    if e.is_a?(Sketchup::Face)
      e.material = material
      e.back_material = material
    elsif e.is_a?(Sketchup::Group)
      dc_apply_face_material(e.entities, material)
    end
  end
end

def dc_box(entities, name, x0, y0, z0, x1, y1, z1, material)
  return nil if (x1 - x0).abs < 0.01 || (y1 - y0).abs < 0.01 || (z1 - z0).abs < 0.01
  g = dc_group(entities, name)
  v = [
    dc_p(x0, y0, z0), dc_p(x1, y0, z0), dc_p(x1, y1, z0), dc_p(x0, y1, z0),
    dc_p(x0, y0, z1), dc_p(x1, y0, z1), dc_p(x1, y1, z1), dc_p(x0, y1, z1)
  ]
  loops = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
  loops.each do |ids|
    f = g.entities.add_face(ids.map { |i| v[i] })
    next unless f
    f.material = material
    f.back_material = material
  end
  g
end

def dc_prism(entities, name, origin, u, v, w, lu_mm, lv_mm, lw_mm, material)
  return nil if lu_mm <= 0 || lv_mm <= 0 || lw_mm <= 0
  uu = u.clone
  vv = v.clone
  ww = w.clone
  return nil if uu.length < 0.001 || vv.length < 0.001 || ww.length < 0.001
  uu.normalize!
  vv.normalize!
  ww.normalize!
  a = origin
  b = a + dc_scale(uu, lu_mm)
  c = a + dc_scale(vv, lv_mm)
  d = b + dc_scale(vv, lv_mm)
  e = a + dc_scale(ww, lw_mm)
  f = b + dc_scale(ww, lw_mm)
  h = c + dc_scale(ww, lw_mm)
  i = d + dc_scale(ww, lw_mm)
  g = dc_group(entities, name)
  [[a, c, d, b], [e, f, i, h], [a, b, f, e], [b, d, i, f], [d, c, h, i], [c, a, e, h]].each do |pts|
    face = g.entities.add_face(pts)
    next unless face
    face.material = material
    face.back_material = material
  end
  g
end

def dc_beam(entities, name, a, b, width_mm, depth_mm, material)
  direction = b - a
  return nil if direction.length < 0.01
  direction.normalize!
  ref = dc_vec(0, 1, 0)
  ref = dc_vec(1, 0, 0) if direction.cross(ref).length < 0.001
  side = direction.cross(ref)
  return nil if side.length < 0.001
  side.normalize!
  up = direction.cross(side)
  return nil if up.length < 0.001
  up.normalize!
  origin = a - dc_scale(side, width_mm / 2.0) - dc_scale(up, depth_mm / 2.0)
  dc_prism(entities, name, origin, direction, side, up, a.distance(b) / 1.mm, width_mm, depth_mm, material)
end

def dc_quad(entities, name, pts, material)
  g = dc_group(entities, name)
  face = g.entities.add_face(pts.map { |q| dc_p(q[0], q[1], q[2]) })
  if face
    face.material = material
    face.back_material = material
  end
  g
end

def dc_cylinder(entities, name, cx, cy, z0, radius, height, material, sides = 16)
  g = dc_group(entities, name)
  low = []
  high = []
  sides.times do |i|
    a = 2.0 * Math::PI * i / sides
    x = cx + Math.cos(a) * radius
    y = cy + Math.sin(a) * radius
    low << dc_p(x, y, z0)
    high << dc_p(x, y, z0 + height)
  end
  top = g.entities.add_face(high)
  bottom = g.entities.add_face(low.reverse)
  [top, bottom].compact.each { |f| f.material = material; f.back_material = material }
  sides.times do |i|
    face = g.entities.add_face([low[i], low[(i + 1) % sides], high[(i + 1) % sides], high[i]])
    next unless face
    face.material = material
    face.back_material = material
  end
  g
end

def dc_ellipsoid(entities, name, cx, cy, cz, rx, ry, rz, material, slices = 12, rings = 6)
  g = dc_group(entities, name)
  rows = []
  (1...rings).each do |ri|
    phi = Math::PI * ri / rings
    row = []
    slices.times do |si|
      theta = 2.0 * Math::PI * si / slices
      row << dc_p(cx + rx * Math.sin(phi) * Math.cos(theta),
                  cy + ry * Math.sin(phi) * Math.sin(theta),
                  cz + rz * Math.cos(phi))
    end
    rows << row
  end
  top = dc_p(cx, cy, cz + rz)
  bottom = dc_p(cx, cy, cz - rz)
  slices.times do |si|
    f = g.entities.add_face([top, rows[0][si], rows[0][(si + 1) % slices]])
    f.material = material if f
    f.back_material = material if f
  end
  (0...(rows.length - 1)).each do |ri|
    slices.times do |si|
      ids = [[ri, si], [ri, (si + 1) % slices], [ri + 1, (si + 1) % slices], [ri + 1, si]]
      f = g.entities.add_face(ids.map { |r, c| rows[r][c] })
      f.material = material if f
      f.back_material = material if f
    end
  end
  slices.times do |si|
    f = g.entities.add_face([bottom, rows[-1][(si + 1) % slices], rows[-1][si]])
    f.material = material if f
    f.back_material = material if f
  end
  g
end

def dc_grid_glazing(entities, prefix, x0, x1, y, z0, z1, nx, nz, glass, frame, frame_w = 45, frame_d = 55)
  dx = (x1 - x0).to_f / nx
  dz = (z1 - z0).to_f / nz
  nx.times do |ix|
    nz.times do |iz|
      xa = x0 + ix * dx + 22
      xb = x0 + (ix + 1) * dx - 22
      za = z0 + iz * dz + 22
      zb = z0 + (iz + 1) * dz - 22
      dc_quad(entities, "#{prefix}_GLASS_#{ix + 1}_#{iz + 1}", [[xa, y, za], [xb, y, za], [xb, y, zb], [xa, y, zb]], glass)
    end
  end
  (0..nx).each do |i|
    x = x0 + i * dx
    dc_beam(entities, "#{prefix}_MULLION_#{i + 1}", dc_p(x, y, z0), dc_p(x, y, z1), frame_w, frame_d, frame)
  end
  (0..nz).each do |i|
    z = z0 + i * dz
    dc_beam(entities, "#{prefix}_TRANSOM_#{i + 1}", dc_p(x0, y, z), dc_p(x1, y, z), frame_w, frame_d, frame)
  end
end

def dc_gable(entities, prefix, y, glass, frame, timber)
  x0 = 3000.0
  xm = 6000.0
  x1 = 9000.0
  eave = 4700.0
  ridge = 7700.0
  dc_quad(entities, "#{prefix}_LOWER_BASE_GLASS", [[x0, y, 3600], [x1, y, 3600], [x1, y, eave], [x0, y, eave]], glass)
  lower_bays = 6
  (0...lower_bays).each do |i|
    xa = x0 + i * 1000 + 25
    xb = x0 + (i + 1) * 1000 - 25
    dc_quad(entities, "#{prefix}_LOWER_PANE_#{i + 1}", [[xa, y, 3625], [xb, y, 3625], [xb, y, 4675], [xa, y, 4675]], glass)
  end
  # Main transparent triangle; timber bars preserve the observed open A-frame interior.
  tri = dc_group(entities, "#{prefix}_TRIANGULAR_GLAZING")
  face = tri.entities.add_face([dc_p(x0, y, eave), dc_p(x1, y, eave), dc_p(xm, y, ridge)])
  if face
    face.material = glass
    face.back_material = glass
  end
  dc_beam(entities, "#{prefix}_GABLE_SILL", dc_p(x0, y, eave), dc_p(x1, y, eave), 75, 95, timber)
  dc_beam(entities, "#{prefix}_GABLE_LEFT_RAKE", dc_p(x0, y, eave), dc_p(xm, y, ridge), 80, 100, timber)
  dc_beam(entities, "#{prefix}_GABLE_RIGHT_RAKE", dc_p(xm, y, ridge), dc_p(x1, y, eave), 80, 100, timber)
  dc_beam(entities, "#{prefix}_GABLE_RIDGE_POST", dc_p(xm, y, eave), dc_p(xm, y, ridge), 50, 60, frame)
  [[4.5, 6200], [7.5, 6200]].each_with_index do |(xmull, topz), i|
    dc_beam(entities, "#{prefix}_GABLE_VERTICAL_#{i + 1}", dc_p(xmull * 1000, y, eave), dc_p(xmull * 1000, y, topz), 40, 50, frame)
  end
  dc_beam(entities, "#{prefix}_GABLE_CROSSBAR_LOWER", dc_p(4200, y, 5900), dc_p(7800, y, 5900), 40, 50, frame)
  dc_beam(entities, "#{prefix}_GABLE_CROSSBAR_UPPER", dc_p(5100, y, 6800), dc_p(6900, y, 6800), 40, 50, frame)
end

def dc_table_set(entities, prefix, cx, cy, z, wood, dark, upholstery)
  g = dc_group(entities, prefix)
  # Round café table, with a clear editable top, pedestal and base.
  dc_cylinder(g.entities, "#{prefix}_TOP", 0, 0, 720, 450, 45, wood, 24)
  dc_cylinder(g.entities, "#{prefix}_PEDESTAL", 0, 0, 120, 46, 600, dark, 16)
  dc_cylinder(g.entities, "#{prefix}_BASE", 0, 0, 90, 250, 30, dark, 20)
  3.times do |i|
    a = 2.0 * Math::PI * i / 3.0 + Math::PI / 6.0
    sx = Math.cos(a) * 700
    sy = Math.sin(a) * 700
    chair = dc_group(g.entities, "#{prefix}_CHAIR_#{i + 1}")
    dc_box(chair.entities, "SEAT_CUSHION", -220, -220, 430, 220, 220, 500, upholstery)
    dc_box(chair.entities, "BACK_CUSHION", -210, 170, 500, 210, 245, 880, upholstery)
    dc_box(chair.entities, "BACK_WOOD_RAIL", -230, 145, 470, 230, 185, 900, wood)
    [[-170, -165], [170, -165], [-170, 165], [170, 165]].each_with_index do |(lx, ly), leg|
      dc_box(chair.entities, "LEG_#{leg + 1}", lx, ly, 0, lx + 45, ly + 45, 450, wood)
    end
    # Face chair backs toward the table, then distribute around it.
    chair.transformation = Geom::Transformation.translation(dc_p(sx, sy, 0)) * Geom::Transformation.rotation(ORIGIN, Z_AXIS, a + Math::PI)
  end
  g.transformation = Geom::Transformation.translation(dc_p(cx, cy, z))
  g
end

def dc_umbrella(entities, name, cx, cy, z, timber, fabric)
  g = dc_group(entities, name)
  dc_cylinder(g.entities, "#{name}_POLE", 0, 0, 0, 28, 2150, timber, 12)
  dc_cylinder(g.entities, "#{name}_BASE", 0, 0, 0, 190, 65, timber, 16)
  points = []
  8.times do |i|
    a = 2.0 * Math::PI * i / 8.0
    points << dc_p(Math.cos(a) * 1250, Math.sin(a) * 1250, 1950 + (i.even? ? 0 : 30))
  end
  hub = dc_p(0, 0, 2290)
  8.times do |i|
    face = g.entities.add_face([hub, points[i], points[(i + 1) % 8]])
    if face
      face.material = fabric
      face.back_material = fabric
    end
    dc_beam(g.entities, "#{name}_RIB_#{i + 1}", hub, points[i], 22, 28, timber)
  end
  g.transformation = Geom::Transformation.translation(dc_p(cx, cy, z))
  g
end

def dc_chair_cluster(entities, prefix, cx, cy, z, wood, upholstery)
  g = dc_group(entities, prefix)
  [-550, 550].each_with_index do |x, i|
    chair = dc_group(g.entities, "#{prefix}_CHAIR_#{i + 1}")
    dc_box(chair.entities, "SEAT", -210, -210, 420, 210, 210, 490, upholstery)
    dc_box(chair.entities, "BACK", -205, 145, 485, 205, 220, 870, upholstery)
    [[-155, -155], [155, -155], [-155, 155], [155, 155]].each_with_index do |(lx, ly), leg|
      dc_box(chair.entities, "LEG_#{leg + 1}", lx, ly, 0, lx + 42, ly + 42, 430, wood)
    end
    chair.transformation = Geom::Transformation.translation(dc_p(x, 0, 0)) * Geom::Transformation.rotation(ORIGIN, Z_AXIS, (i == 0 ? Math::PI / 2 : -Math::PI / 2))
  end
  g.transformation = Geom::Transformation.translation(dc_p(cx, cy, z))
  g
end

def dc_flowers(entities, name, x0, y0, x1, y1, z, flower_mat, leaf_mat)
  g = dc_group(entities, name)
  count = 14
  count.times do |i|
    t = (i + 0.5) / count.to_f
    x = x0 + (x1 - x0) * t
    y = y0 + (y1 - y0) * t
    h = 280 + (i % 4) * 45
    dc_beam(g.entities, "#{name}_STEM_#{i + 1}", dc_p(x, y, z), dc_p(x + ((i % 3) - 1) * 30, y, z + h), 10, 12, leaf_mat)
    dc_ellipsoid(g.entities, "#{name}_BLOOM_#{i + 1}", x + ((i % 3) - 1) * 30, y, z + h, 68, 60, 48, flower_mat, 8, 4)
    dc_ellipsoid(g.entities, "#{name}_FOLIAGE_#{i + 1}", x, y + 28, z + h * 0.55, 95, 55, 44, leaf_mat, 8, 4)
  end
end

def dc_tree(entities, name, x, y, ground_z, timber, greens)
  g = dc_group(entities, name)
  dc_beam(g.entities, "#{name}_TRUNK", dc_p(0, 0, ground_z), dc_p(0, 0, ground_z + 3500), 210, 190, timber)
  [
    [-650, -150, 2700, -850, -250, 4050], [620, 80, 2650, 860, 160, 4100],
    [-80, 570, 2900, -100, 730, 4250], [120, -560, 2750, 210, -720, 4200]
  ].each_with_index do |v, i|
    dc_beam(g.entities, "#{name}_BRANCH_#{i + 1}", dc_p(v[0], v[1], v[2]), dc_p(v[3], v[4], v[5]), 95, 90, timber)
  end
  [[-650, -160, 4050, 790, 680, 720], [560, 170, 4020, 850, 720, 800], [-80, 660, 4140, 800, 700, 700], [80, -570, 4150, 760, 680, 720], [0, 40, 4620, 700, 660, 640]].each_with_index do |v, i|
    dc_ellipsoid(g.entities, "#{name}_CANOPY_#{i + 1}", v[0], v[1], v[2], v[3], v[4], v[5], greens[i % greens.length], 14, 7)
  end
  g.transformation = Geom::Transformation.translation(dc_p(x, y, 0))
end

def dc_label(entities, name, text, origin_mm, rotation, material, height_mm = 230)
  g = dc_group(entities, name)
  g.entities.add_3d_text(text, 0, 'Arial', false, false, height_mm.mm, 18.mm, 12.mm, true, 12.mm, material)
  g.transformation = Geom::Transformation.translation(dc_p(origin_mm[0], origin_mm[1], origin_mm[2])) * rotation
  g
end

# Materials: warm timber, muted tan fascia, charcoal framing, clear blue-gray glazing and light paving.
wood = dc_material(model, 'DreamCoffee | warm oak', [177, 126, 88])
wood_light = dc_material(model, 'DreamCoffee | pale timber', [207, 165, 125])
wood_dark = dc_material(model, 'DreamCoffee | structural timber', [105, 73, 51])
metal = dc_material(model, 'DreamCoffee | charcoal metal', [35, 39, 42])
glass = dc_material(model, 'DreamCoffee | clear glazing', [171, 203, 210], 38)
roof_glass = dc_material(model, 'DreamCoffee | roof glazing', [188, 211, 216], 48)
concrete = dc_material(model, 'DreamCoffee | pale concrete', [207, 207, 201])
stone = dc_material(model, 'DreamCoffee | dark planter concrete', [93, 96, 96])
upholstery = dc_material(model, 'DreamCoffee | ivory upholstery', [239, 237, 229])
soil = dc_material(model, 'DreamCoffee | planter soil', [78, 65, 51])
leaf = dc_material(model, 'DreamCoffee | foliage', [83, 122, 76])
leaf_light = dc_material(model, 'DreamCoffee | foliage light', [115, 148, 89])
leaf_dark = dc_material(model, 'DreamCoffee | foliage shade', [62, 101, 68])
flower = dc_material(model, 'DreamCoffee | flower coral', [196, 104, 104])
flower_light = dc_material(model, 'DreamCoffee | flower rose', [219, 144, 133])
white_fabric = dc_material(model, 'DreamCoffee | umbrella canvas', [247, 245, 237])
sign_ink = dc_material(model, 'DreamCoffee | signage lettering', [40, 34, 30])

# PRIMARY FORM — level plate, openings, roof silhouette, glass gables and inclined glass wing.
shell = dc_group(root.entities, 'GROUND_SHELL')
dc_box(shell.entities, 'GROUND_FLOOR_PLATE', -120, -120, -80, 12120, 8520, 80, concrete)
dc_box(shell.entities, 'UPPER_FLOOR_PLATE', 3000, 900, 3450, 9000, 7500, 3600, concrete)

# A real continuous SAIE opening host is used for the front glazed entrance band.
front_wall = saie_wall_with_openings.call({
  'name' => 'FRONT_ENTRY_OPENING_HOST',
  'centerline' => [[4200, 0], [12000, 0]],
  'thickness_mm' => 180,
  'height_mm' => 3100,
  'elevation_mm' => 0,
  'openings' => [
    { 'offset_mm' => 200, 'width_mm' => 5100, 'height_mm' => 3000, 'sill_mm' => 0 },
    # Source shows the right-front bay open below the terrace fascia; retain
    # narrow end returns around the square supports and adjacent annex.
    { 'offset_mm' => 5400, 'width_mm' => 2300, 'height_mm' => 3100, 'sill_mm' => 0 }
  ]
})
front_wall.material = concrete if front_wall.respond_to?(:material=)
dc_apply_face_material(front_wall.entities, concrete) if front_wall.respond_to?(:entities)

# Solid wood return visible in the right-hand reference view.
right_wall = saie_wall.call({
  'name' => 'GROUND_RIGHT_TIMBER_WALL',
  'centerline' => [[12000, 0], [12000, 8400]],
  'thickness_mm' => 180,
  'height_mm' => 3100,
  'elevation_mm' => 0
})
right_wall.material = wood if right_wall.respond_to?(:material=)
dc_apply_face_material(right_wall.entities, wood) if right_wall.respond_to?(:entities)

# The inferred rear wall has two high windows and a secondary door to maintain circulation.
rear_wall = saie_wall_with_openings.call({
  'name' => 'REAR_INFERRED_FACADE',
  'centerline' => [[0, 8400], [12000, 8400]],
  'thickness_mm' => 180,
  'height_mm' => 3100,
  'elevation_mm' => 0,
  'openings' => [
    { 'offset_mm' => 1450, 'width_mm' => 1800, 'height_mm' => 1700, 'sill_mm' => 700 },
    { 'offset_mm' => 4950, 'width_mm' => 1800, 'height_mm' => 1700, 'sill_mm' => 700 },
    { 'offset_mm' => 9650, 'width_mm' => 1050, 'height_mm' => 2350, 'sill_mm' => 0 }
  ]
})
rear_wall.material = wood_light if rear_wall.respond_to?(:material=)
dc_apply_face_material(rear_wall.entities, wood_light) if rear_wall.respond_to?(:entities)

# The 600 mm front fascia is an open canopy band carried on substantial timber columns.
dc_box(root.entities, 'TERRACE_FASCIA', -150, -330, 3600, 12150, 120, 4200, wood_light)
dc_box(root.entities, 'TERRACE_FASCIA_RIGHT_RETURN', 11850, -250, 3600, 12200, 8520, 4200, wood_light)
[[8750, 520], [11600, 520], [11600, 7900]].each_with_index do |(x, y), i|
  dc_box(shell.entities, "TERRACE_SUPPORT_COLUMN_#{i + 1}", x, y, 0, x + 300, y + 300, 3600, wood)
  dc_box(shell.entities, "COLUMN_DARK_COLLAR_#{i + 1}", x - 20, y - 20, 2300, x + 320, y + 320, 2550, wood_dark)
end

# Main patio roof/deck. Its upper level is a walkable terrace around the glazed pavilion.
terrace = dc_group(root.entities, 'TERRACE_DECK')
dc_box(terrace.entities, 'ROOF_TERRACE_SLAB', -100, -120, 3320, 12120, 8520, 3600, concrete)
dc_box(terrace.entities, 'TERRACE_THRESHOLD_STEP', 3600, -650, 280, 9400, 250, 360, concrete)

# Broad projecting front glass wing; the sloped plane faces the entrance view.
wing = dc_group(root.entities, 'FRONT_SLOPED_GLAZING')
wing_x0 = 150.0
wing_x1 = 4100.0
wing_y0 = -3200.0
wing_y1 = 0.0
wing_z0 = 20.0
wing_z1 = 3250.0
wing_point = lambda do |t, x|
  [x, wing_y0 + (wing_y1 - wing_y0) * t, wing_z0 + (wing_z1 - wing_z0) * t]
end
6.times do |ix|
  xa = wing_x0 + (wing_x1 - wing_x0) * ix / 6.0 + 24
  xb = wing_x0 + (wing_x1 - wing_x0) * (ix + 1) / 6.0 - 24
  2.times do |it|
    t0 = it / 2.0 + 0.018
    t1 = (it + 1) / 2.0 - 0.018
    dc_quad(wing.entities, "LOWER_WING_GLASS_BAY_#{ix + 1}_#{it + 1}", [wing_point.call(t0, xa), wing_point.call(t0, xb), wing_point.call(t1, xb), wing_point.call(t1, xa)], glass)
  end
end
0.upto(6) do |i|
  x = wing_x0 + (wing_x1 - wing_x0) * i / 6.0
  dc_beam(wing.entities, "LOWER_WING_SLOPE_RIB_#{i + 1}", dc_p(*wing_point.call(0, x)), dc_p(*wing_point.call(1, x)), 65, 85, metal)
end
[0.33, 0.66].each_with_index do |t, i|
  dc_beam(wing.entities, "LOWER_WING_LONG_TRANSOM_#{i + 1}", dc_p(*wing_point.call(t, wing_x0)), dc_p(*wing_point.call(t, wing_x1)), 45, 55, metal)
end
dc_beam(wing.entities, 'LOWER_WING_EAVE_BEAM', dc_p(*wing_point.call(1, wing_x0)), dc_p(*wing_point.call(1, wing_x1)), 80, 95, wood_dark)
dc_beam(wing.entities, 'LOWER_WING_BASE_BEAM', dc_p(*wing_point.call(0, wing_x0)), dc_p(*wing_point.call(0, wing_x1)), 75, 90, wood_dark)

# Upper A-frame greenhouse, floor-level curtain walls and two triangular glazed ends.
upper = dc_group(root.entities, 'UPPER_GLASS_PAVILION')
dc_box(upper.entities, 'UPPER_PAVILION_FLOOR', 3000, 900, 3600, 9000, 7500, 3690, wood_light)
dc_gable(upper.entities, 'FRONT_GABLE', 900, glass, metal, wood)
dc_gable(upper.entities, 'REAR_GABLE', 7500, glass, metal, wood)

# Low curtain wall on each long side of the upper room.
[3000, 9000].each_with_index do |x, side_i|
  segments = 7
  segments.times do |i|
    y0 = 900 + i * 900 + 24
    y1 = 900 + (i + 1) * 900 - 24
    dc_quad(upper.entities, "PAVILION_SIDE_#{side_i + 1}_GLASS_#{i + 1}", [[x, y0, 3650], [x, y1, 3650], [x, y1, 4660], [x, y0, 4660]], glass)
  end
  dc_beam(upper.entities, "PAVILION_SIDE_#{side_i + 1}_SILL", dc_p(x, 900, 3640), dc_p(x, 7500, 3640), 90, 100, wood)
  dc_beam(upper.entities, "PAVILION_SIDE_#{side_i + 1}_HEAD", dc_p(x, 900, 4680), dc_p(x, 7500, 4680), 80, 110, wood_dark)
  dc_beam(upper.entities, "PAVILION_SIDE_#{side_i + 1}_TRANSOM", dc_p(x, 900, 4150), dc_p(x, 7500, 4150), 45, 55, metal)
  (0..7).each do |i|
    yy = 900 + i * 900
    dc_beam(upper.entities, "PAVILION_SIDE_#{side_i + 1}_MULLION_#{i + 1}", dc_p(x, yy, 3640), dc_p(x, yy, 4680), 45, 55, metal)
  end
end

# Roof-glass A-frame panels and its black mullion grid.
def dc_roof_point(side, t, y)
  if side == :left
    [3000 + 3000 * t, y, 4700 + 3000 * t]
  else
    [9000 - 3000 * t, y, 4700 + 3000 * t]
  end
end

[:left, :right].each do |side|
  4.times do |ti|
    t0 = ti / 4.0 + 0.018
    t1 = (ti + 1) / 4.0 - 0.018
    7.times do |yi|
      y0 = 900 + yi * 900 + 28
      y1 = 900 + (yi + 1) * 900 - 28
      dc_quad(root.entities, "ROOF_GLASS_#{side}_T#{ti + 1}_Y#{yi + 1}", [dc_roof_point(side, t0, y0), dc_roof_point(side, t0, y1), dc_roof_point(side, t1, y1), dc_roof_point(side, t1, y0)], roof_glass)
    end
  end
  0.upto(7) do |yi|
    yy = 900 + yi * 900
    dc_beam(root.entities, "ROOF_RAFTER_#{side}_#{yi + 1}", dc_p(*dc_roof_point(side, 0.0, yy)), dc_p(*dc_roof_point(side, 1.0, yy)), 95, 110, wood_dark)
  end
  0.upto(4) do |ti|
    tt = ti / 4.0
    dc_beam(root.entities, "ROOF_GLASS_MULLION_#{side}_#{ti + 1}", dc_p(*dc_roof_point(side, tt, 900)), dc_p(*dc_roof_point(side, tt, 7500)), 48, 62, metal)
  end
end

# ADAI's verified profile extrusion creates slender longitudinal constant-section purlins.
# Each 100 x 120 mm member runs 6,600 mm along the roof section.
9.times do |i|
  cx = 3000 + i * 750.0
  cz = 4700 + (i <= 4 ? i : 8 - i) * 750.0
  outline = [[cx - 50, cz - 60], [cx + 50, cz - 60], [cx + 50, cz + 60], [cx - 50, cz + 60]]
  adai_geometry.profile(root.entities, "ROOF_LONGITUDINAL_PURLIN_#{i + 1}", outline, 6600, 'xz', 900, wood)
end

# One correct representative glass-roof bay is followed by the repeated framing above.
# The pavilion remains transparent; no filled roof wedge is used.

# Continuous clear storefront fills its rectangular host opening with a light mullion grid.
storefront = dc_group(root.entities, 'FRONT_STORE_FRONT_GLAZING')
dc_grid_glazing(storefront.entities, 'FRONT_STORE_FRONT', 4400, 9500, -96, 0, 3000, 6, 2, glass, metal, 38, 48)

# Warm timber facade treatment on the exposed right wall and restrained service counter inside.
right_clad = dc_group(root.entities, 'MATERIAL_ZONES')
# The observed annex side is a broad timber-clad plane with only two fine joints.
dc_box(right_clad.entities, 'RIGHT_WALL_WOOD_BACKING', 12091, 0, 80, 12092, 8400, 3040, wood_dark)
[[16, 2784], [2800, 5584], [5600, 8384]].each_with_index do |(y0, y1), i|
  dc_box(right_clad.entities, "RIGHT_WALL_WOOD_PANEL_#{i + 1}", 12092, y0, 80, 12114, y1, 3040, wood_light)
end
dc_box(right_clad.entities, 'GROUND_CAFE_SERVICE_COUNTER', 7900, 5600, 920, 10800, 6400, 1900, wood_light)
dc_box(right_clad.entities, 'SERVICE_COUNTER_DARK_PLINTH', 7850, 5570, 840, 10850, 6440, 920, wood_dark)

# Terrace glass balustrade: build one true panel component, then repeat along two exposed edges.
rail = dc_group(root.entities, 'TERRACE_RAILING')
seed = dc_group(rail.entities, 'RAILING_PANEL_FRONT_01')
dc_box(seed.entities, 'LOWER_RAIL', 0, -42, 0, 1200, 42, 65, metal)
dc_box(seed.entities, 'TOP_RAIL', 0, -42, 990, 1200, 42, 1050, wood_dark)
dc_box(seed.entities, 'LEFT_POST', -28, -40, 0, 28, 40, 1050, metal)
dc_box(seed.entities, 'RIGHT_POST', 1172, -40, 0, 1228, 40, 1050, metal)
dc_quad(seed.entities, 'CLEAR_GLASS_PANEL', [[38, -8, 68], [1162, -8, 68], [1162, -8, 985], [38, -8, 985]], glass)
seed_component = seed.to_component
seed_component.name = 'RAILING_PANEL_1200_COMPONENT'
definition = seed_component.definition
seed_component.transformation = Geom::Transformation.translation(dc_p(8400, 220, 4200))
front_count = 1
while front_count < 3
  inst = rail.entities.add_instance(definition, Geom::Transformation.translation(dc_p(8400 + front_count * 1200, 220, 4200)))
  inst.name = "RAILING_PANEL_FRONT_#{front_count + 1}"
  front_count += 1
end
side_rot = Geom::Transformation.rotation(ORIGIN, Z_AXIS, Math::PI / 2.0)
0.upto(6) do |i|
  inst = rail.entities.add_instance(definition, Geom::Transformation.translation(dc_p(12000, i * 1200, 4200)) * side_rot)
  inst.name = "RAILING_PANEL_RIGHT_#{i + 1}"
end

# Exterior stair on the left; 20 estimated risers and a continuous dark handrail.
stairs = dc_group(root.entities, 'EXTERIOR_STAIR')
20.times do |i|
  y0 = 7500 - i * 280
  z0 = i * 180
  dc_box(stairs.entities, "STAIR_TREAD_#{i + 1}", -1500, y0 - 280, z0, -500, y0, z0 + 180, concrete)
end
dc_beam(stairs.entities, 'STAIR_STRINGER_LEFT', dc_p(-1580, 7480, 0), dc_p(-1580, 1880, 3600), 120, 180, wood_dark)
dc_beam(stairs.entities, 'STAIR_STRINGER_RIGHT', dc_p(-420, 7480, 0), dc_p(-420, 1880, 3600), 120, 180, wood_dark)
dc_beam(stairs.entities, 'STAIR_HANDRAIL', dc_p(-1520, 7480, 980), dc_p(-1520, 1880, 4580), 70, 90, metal)
0.upto(10) do |i|
  yy = 7480 - i * 560
  zz = i * 360 + 980
  dc_beam(stairs.entities, "STAIR_HANDRAIL_POST_#{i + 1}", dc_p(-1520, yy, zz - 900), dc_p(-1520, yy, zz), 45, 50, metal)
end
dc_box(stairs.entities, 'TOP_STAIR_LANDING', -1650, 1500, 3480, 1100, 2050, 3600, concrete)

# Source-visible low stepped site apron and entry platform.
platform = dc_group(root.entities, 'ENTRY_PLATFORM')
dc_box(platform.entities, 'SITE_APRON', -2600, -3400, -240, 13800, 10200, -80, concrete)
dc_box(platform.entities, 'FRONT_APPROACH_PLAZA', -300, -2300, -85, 12200, -250, 0, concrete)
3.times do |i|
  yy0 = -250 - i * 260
  z0 = -30 - i * 30
  dc_box(platform.entities, "ENTRY_STEP_#{i + 1}", 3800, yy0 - 260, z0 - 30, 9500, yy0, z0, concrete)
end
dc_box(platform.entities, 'SLoped_WING_EDGE_PAVING', -300, 450, -20, 400, 7550, 25, concrete)

# Planters, low flowers and source-visible trees.
planters = dc_group(root.entities, 'PLANTERS')
dc_box(planters.entities, 'FRONT_LONG_PLANTER', -100, -100, 0, 3650, 360, 450, stone)
dc_box(planters.entities, 'FRONT_PLANTER_SOIL', 0, -35, 450, 3550, 295, 495, soil)
dc_box(planters.entities, 'RIGHT_EDGE_PLANTER', 12250, 1450, 0, 13100, 5900, 450, stone)
dc_box(planters.entities, 'RIGHT_EDGE_SOIL', 12310, 1510, 450, 13040, 5840, 495, soil)
dc_box(planters.entities, 'REAR_LOW_PLANTER', 2000, 8500, -80, 9000, 8850, 340, stone)
dc_flowers(planters.entities, 'FRONT_CORAL_FLOWERS', 100, 100, 3450, 100, 500, flower, leaf)
dc_flowers(planters.entities, 'RIGHT_CORAL_FLOWERS', 12420, 1600, 12420, 5700, 500, flower_light, leaf_light)
dc_flowers(planters.entities, 'REAR_CORAL_FLOWERS', 2200, 8680, 8800, 8680, 350, flower, leaf_dark)

trees = dc_group(root.entities, 'SOURCE_VISIBLE_TREES')
dc_tree(trees.entities, 'TREE_RIGHT_01', 13700, 6100, 0, wood_dark, [leaf, leaf_light, leaf_dark])
dc_tree(trees.entities, 'TREE_REAR_02', -500, 8800, 0, wood_dark, [leaf_light, leaf, leaf_dark])

# Interior and terrace furniture; repeated editable table/chair/umbrella modules.
furniture = dc_group(root.entities, 'FURNITURE')
dc_table_set(furniture.entities, 'UPPER_INTERIOR_TABLE_SET_01', 4650, 2100, 3690, wood, wood_dark, upholstery)
dc_table_set(furniture.entities, 'UPPER_INTERIOR_TABLE_SET_02', 6000, 4250, 3690, wood, wood_dark, upholstery)
dc_table_set(furniture.entities, 'UPPER_INTERIOR_TABLE_SET_03', 7550, 6000, 3690, wood, wood_dark, upholstery)
dc_table_set(furniture.entities, 'GROUND_CAFE_TABLE_SET_01', 5850, 3900, 80, wood_light, wood_dark, upholstery)
dc_table_set(furniture.entities, 'GROUND_CAFE_TABLE_SET_02', 9800, 3900, 80, wood_light, wood_dark, upholstery)
dc_table_set(furniture.entities, 'TERRACE_TABLE_SET_01', 9650, 1450, 3600, wood_light, wood_dark, upholstery)
dc_table_set(furniture.entities, 'TERRACE_TABLE_SET_02', 10350, 4150, 3600, wood_light, wood_dark, upholstery)
dc_table_set(furniture.entities, 'TERRACE_TABLE_SET_03', 9700, 6900, 3600, wood_light, wood_dark, upholstery)
dc_umbrella(furniture.entities, 'TERRACE_UMBRELLA_01', 9650, 1450, 3600, wood_dark, white_fabric)
dc_umbrella(furniture.entities, 'TERRACE_UMBRELLA_02', 10350, 4150, 3600, wood_dark, white_fabric)
dc_umbrella(furniture.entities, 'TERRACE_UMBRELLA_03', 9700, 6900, 3600, wood_dark, white_fabric)

# Warm wood sill, threshold and bar trim complete the principal material zones.
materials = right_clad
dc_box(materials.entities, 'PAVILION_WOOD_BASE_BAND_FRONT', 2950, 790, 3590, 9050, 880, 3750, wood_light)
dc_box(materials.entities, 'PAVILION_WOOD_BASE_BAND_REAR', 2950, 7520, 3590, 9050, 7610, 3750, wood_light)
dc_box(materials.entities, 'GROUND_ENTRY_WOOD_THRESHOLD', 4150, -180, 0, 10850, 20, 120, wood)

# Legible physical Dream Coffee signage on both front and right fascia faces.
front_rotation = Geom::Transformation.rotation(ORIGIN, X_AXIS, Math::PI / 2.0)
dc_label(root.entities, 'SIGNAGE_FRONT', 'Dream Coffee', [4000, -345, 3780], front_rotation, sign_ink, 245)
side_rotation = Geom::Transformation.rotation(ORIGIN, Z_AXIS, Math::PI / 2.0) * Geom::Transformation.rotation(ORIGIN, X_AXIS, Math::PI / 2.0)
dc_label(root.entities, 'SIGNAGE_SIDE', 'Dream Coffee', [12160, 2600, 3780], side_rotation, sign_ink, 205)

# Source-based fit-out details kept simple so all furniture remains editable and visible.
# Ground, upper room and terrace are connected by the exterior stair, with the rear service door inferred.

