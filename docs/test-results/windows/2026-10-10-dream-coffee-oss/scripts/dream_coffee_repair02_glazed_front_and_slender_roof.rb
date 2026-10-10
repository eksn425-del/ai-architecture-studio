# Local correction pass 02: broaden the projecting left/front glass wing,
# connect the entrance storefront glazing, and lighten the A-frame members.
# The same edits are integrated into dream_coffee_reconstruction.rb.

def dc2_point(x, y, z)
  Geom::Point3d.new(x.mm, y.mm, z.mm)
end

def dc2_scale(vector, mm_len)
  internal_len = mm_len.to_f.mm.to_f
  Geom::Vector3d.new(vector.x * internal_len, vector.y * internal_len, vector.z * internal_len)
end

def dc2_box(entities, name, x0, y0, z0, x1, y1, z1, material)
  return nil if [x1 - x0, y1 - y0, z1 - z0].any? { |d| d.abs < 0.01 }
  g = entities.add_group
  g.name = name
  v = [
    dc2_point(x0, y0, z0), dc2_point(x1, y0, z0), dc2_point(x1, y1, z0), dc2_point(x0, y1, z0),
    dc2_point(x0, y0, z1), dc2_point(x1, y0, z1), dc2_point(x1, y1, z1), dc2_point(x0, y1, z1)
  ]
  [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]].each do |ids|
    face = g.entities.add_face(ids.map { |i| v[i] })
    next unless face
    face.material = material
    face.back_material = material
  end
  g
end

def dc2_quad(entities, name, points, material)
  g = entities.add_group
  g.name = name
  face = g.entities.add_face(points.map { |p| dc2_point(p[0], p[1], p[2]) })
  if face
    face.material = material
    face.back_material = material
  end
  g
end

def dc2_beam(entities, name, a, b, width_mm, depth_mm, material)
  direction = b - a
  return nil if direction.length < 0.01
  direction.normalize!
  reference = Geom::Vector3d.new(0, 1, 0)
  reference = Geom::Vector3d.new(1, 0, 0) if direction.cross(reference).length < 0.001
  side = direction.cross(reference)
  return nil if side.length < 0.001
  side.normalize!
  up = direction.cross(side)
  return nil if up.length < 0.001
  up.normalize!
  origin = a - dc2_scale(side, width_mm / 2.0) - dc2_scale(up, depth_mm / 2.0)
  dc2_box_from_axes(entities, name, origin, direction, side, up, a.distance(b) / 1.mm, width_mm, depth_mm, material)
end

def dc2_box_from_axes(entities, name, origin, u, v, w, lu, lv, lw, material)
  return nil if [lu, lv, lw].any? { |d| d <= 0 }
  uu = u.clone; vv = v.clone; ww = w.clone
  return nil if [uu, vv, ww].any? { |vec| vec.length < 0.001 }
  uu.normalize!; vv.normalize!; ww.normalize!
  a = origin
  b = a + dc2_scale(uu, lu); c = a + dc2_scale(vv, lv); d = b + dc2_scale(vv, lv)
  e = a + dc2_scale(ww, lw); f = b + dc2_scale(ww, lw); h = c + dc2_scale(ww, lw); i = d + dc2_scale(ww, lw)
  g = entities.add_group
  g.name = name
  [[a, c, d, b], [e, f, i, h], [a, b, f, e], [b, d, i, f], [d, c, h, i], [c, a, e, h]].each do |pts|
    face = g.entities.add_face(pts)
    next unless face
    face.material = material
    face.back_material = material
  end
  g
end

def dc2_glazing_grid(entities, prefix, x0, x1, y, z0, z1, nx, nz, glass, frame)
  dx = (x1 - x0).to_f / nx
  dz = (z1 - z0).to_f / nz
  nx.times do |ix|
    nz.times do |iz|
      xa = x0 + ix * dx + 24
      xb = x0 + (ix + 1) * dx - 24
      za = z0 + iz * dz + 24
      zb = z0 + (iz + 1) * dz - 24
      dc2_quad(entities, "#{prefix}_GLASS_#{ix + 1}_#{iz + 1}", [[xa, y, za], [xb, y, za], [xb, y, zb], [xa, y, zb]], glass)
    end
  end
  (0..nx).each do |i|
    x = x0 + i * dx
    dc2_beam(entities, "#{prefix}_MULLION_#{i + 1}", dc2_point(x, y, z0), dc2_point(x, y, z1), 38, 48, frame)
  end
  (0..nz).each do |i|
    z = z0 + i * dz
    dc2_beam(entities, "#{prefix}_TRANSOM_#{i + 1}", dc2_point(x0, y, z), dc2_point(x1, y, z), 38, 48, frame)
  end
end

glass = model.materials['DreamCoffee | clear glazing']
roof_glass = model.materials['DreamCoffee | roof glazing']
wood_dark = model.materials['DreamCoffee | structural timber']
concrete = model.materials['DreamCoffee | pale concrete']
raise 'Required reconstruction materials are missing' unless glass && roof_glass && wood_dark && concrete

# Widen the actual sloped-glass plane across the source-visible left/front bay.
remove_owned_group.call('FRONT_SLOPED_GLAZING')
['LOWER_WING_FRONT_RETURN_GLASS', 'LOWER_WING_REAR_RETURN_GLASS'].each do |name|
  remove_owned_group.call(name)
end
wing = root.entities.add_group
wing.name = 'FRONT_SLOPED_GLAZING'
wx0 = 150.0; wx1 = 4100.0
wy0 = -3200.0; wy1 = 0.0
wz0 = 20.0; wz1 = 3250.0
wing_point = lambda do |t, x|
  [x, wy0 + (wy1 - wy0) * t, wz0 + (wz1 - wz0) * t]
end
6.times do |ix|
  xa = wx0 + (wx1 - wx0) * ix / 6.0 + 24
  xb = wx0 + (wx1 - wx0) * (ix + 1) / 6.0 - 24
  2.times do |it|
    t0 = it / 2.0 + 0.018
    t1 = (it + 1) / 2.0 - 0.018
    dc2_quad(wing.entities, "LOWER_WING_GLASS_BAY_#{ix + 1}_#{it + 1}", [wing_point.call(t0, xa), wing_point.call(t0, xb), wing_point.call(t1, xb), wing_point.call(t1, xa)], glass)
  end
end
0.upto(6) do |i|
  x = wx0 + (wx1 - wx0) * i / 6.0
  dc2_beam(wing.entities, "LOWER_WING_SLOPE_RIB_#{i + 1}", dc2_point(*wing_point.call(0, x)), dc2_point(*wing_point.call(1, x)), 65, 78, metal = model.materials['DreamCoffee | charcoal metal'])
end
[0.33, 0.66].each_with_index do |t, i|
  dc2_beam(wing.entities, "LOWER_WING_LONG_TRANSOM_#{i + 1}", dc2_point(*wing_point.call(t, wx0)), dc2_point(*wing_point.call(t, wx1)), 45, 55, model.materials['DreamCoffee | charcoal metal'])
end
dc2_beam(wing.entities, 'LOWER_WING_EAVE_BEAM', dc2_point(*wing_point.call(1, wx0)), dc2_point(*wing_point.call(1, wx1)), 80, 95, wood_dark)
dc2_beam(wing.entities, 'LOWER_WING_BASE_BEAM', dc2_point(*wing_point.call(0, wx0)), dc2_point(*wing_point.call(0, wx1)), 75, 90, wood_dark)

# Rebuild the SAIE wall host as a continuous storefront opening beside the open post bay.
remove_owned_group.call('FRONT_ENTRY_OPENING_HOST')
front_wall = saie_wall_with_openings.call({
  'name' => 'FRONT_ENTRY_OPENING_HOST',
  'centerline' => [[4200, 0], [12000, 0]],
  'thickness_mm' => 180,
  'height_mm' => 3100,
  'elevation_mm' => 0,
  'openings' => [
    { 'offset_mm' => 200, 'width_mm' => 5100, 'height_mm' => 3000, 'sill_mm' => 0 },
    { 'offset_mm' => 5400, 'width_mm' => 2300, 'height_mm' => 3100, 'sill_mm' => 0 }
  ]
})
front_wall.material = concrete if front_wall.respond_to?(:material=)
if front_wall.respond_to?(:entities)
  front_wall.entities.each do |e|
    next unless e.is_a?(Sketchup::Face)
    e.material = concrete
    e.back_material = concrete
  end
end
[
  'FRONT_OPENING_GLASS_1', 'FRONT_OPENING_GLASS_2',
  'FRONT_OPENING_JAMB_L_1', 'FRONT_OPENING_JAMB_R_1', 'FRONT_OPENING_HEAD_1', 'FRONT_OPENING_SILL_1', 'FRONT_OPENING_MULLION_1_1',
  'FRONT_OPENING_JAMB_L_2', 'FRONT_OPENING_JAMB_R_2', 'FRONT_OPENING_HEAD_2', 'FRONT_OPENING_SILL_2',
  'FRONT_OPENING_MULLION_2_1', 'FRONT_OPENING_MULLION_2_2'
].each { |name| remove_owned_group.call(name) }
remove_owned_group.call('FRONT_STORE_FRONT_GLAZING') if root.entities.any? { |e| e.respond_to?(:name) && e.name == 'FRONT_STORE_FRONT_GLAZING' }
storefront = root.entities.add_group
storefront.name = 'FRONT_STORE_FRONT_GLAZING'
dc2_glazing_grid(storefront.entities, 'FRONT_STORE_FRONT', 4400, 9500, -96, 0, 3000, 6, 2, glass, model.materials['DreamCoffee | charcoal metal'])

# Shrink the roof frame members; preserve the two triangular glazing faces.
%w[left right].each do |side|
  1.upto(8) { |i| remove_owned_group.call("ROOF_RAFTER_#{side}_#{i}") }
end
9.times { |i| remove_owned_group.call("ROOF_LONGITUDINAL_PURLIN_#{i + 1}") }
roof_point = lambda do |side, t, y|
  side == 'left' ? [3000 + 3000 * t, y, 4700 + 3000 * t] : [9000 - 3000 * t, y, 4700 + 3000 * t]
end
%w[left right].each do |side|
  0.upto(7) do |yi|
    yy = 900 + yi * 900
    dc2_beam(root.entities, "ROOF_RAFTER_#{side}_#{yi + 1}", dc2_point(*roof_point.call(side, 0.0, yy)), dc2_point(*roof_point.call(side, 1.0, yy)), 95, 110, wood_dark)
  end
end
9.times do |i|
  cx = 3000 + i * 750.0
  cz = 4700 + (i <= 4 ? i : 8 - i) * 750.0
  outline = [[cx - 50, cz - 60], [cx + 50, cz - 60], [cx + 50, cz + 60], [cx - 50, cz + 60]]
  adai_geometry.profile(root.entities, "ROOF_LONGITUDINAL_PURLIN_#{i + 1}", outline, 6600, 'xz', 900, wood_dark)
end

upper = root.entities.grep(Sketchup::Group).find { |g| g.name == 'UPPER_GLASS_PAVILION' }
raise 'UPPER_GLASS_PAVILION group is missing' unless upper
gable_rows = [['FRONT_GABLE', 900.0], ['REAR_GABLE', 7500.0]]
gable_members = %w[
  GABLE_SILL GABLE_LEFT_RAKE GABLE_RIGHT_RAKE GABLE_RIDGE_POST
  GABLE_VERTICAL_1 GABLE_VERTICAL_2 GABLE_CROSSBAR_LOWER GABLE_CROSSBAR_UPPER
]
gable_rows.each do |prefix, y|
  gable_members.each { |member| remove_owned_group.call(['UPPER_GLASS_PAVILION', "#{prefix}_#{member}"]) }
  dc2_beam(upper.entities, "#{prefix}_GABLE_SILL", dc2_point(3000, y, 4700), dc2_point(9000, y, 4700), 75, 95, wood_dark)
  dc2_beam(upper.entities, "#{prefix}_GABLE_LEFT_RAKE", dc2_point(3000, y, 4700), dc2_point(6000, y, 7700), 80, 100, wood_dark)
  dc2_beam(upper.entities, "#{prefix}_GABLE_RIGHT_RAKE", dc2_point(6000, y, 7700), dc2_point(9000, y, 4700), 80, 100, wood_dark)
  dc2_beam(upper.entities, "#{prefix}_GABLE_RIDGE_POST", dc2_point(6000, y, 4700), dc2_point(6000, y, 7700), 50, 60, model.materials['DreamCoffee | charcoal metal'])
  [4500, 7500].each_with_index do |x, i|
    dc2_beam(upper.entities, "#{prefix}_GABLE_VERTICAL_#{i + 1}", dc2_point(x, y, 4700), dc2_point(x, y, 6200), 40, 50, model.materials['DreamCoffee | charcoal metal'])
  end
  dc2_beam(upper.entities, "#{prefix}_GABLE_CROSSBAR_LOWER", dc2_point(4200, y, 5900), dc2_point(7800, y, 5900), 40, 50, model.materials['DreamCoffee | charcoal metal'])
  dc2_beam(upper.entities, "#{prefix}_GABLE_CROSSBAR_UPPER", dc2_point(5100, y, 6800), dc2_point(6900, y, 6800), 40, 50, model.materials['DreamCoffee | charcoal metal'])
end

# Extend only the apron beneath the new source-matched glass projection.
remove_owned_group.call(['ENTRY_PLATFORM', 'SITE_APRON'])
platform = root.entities.grep(Sketchup::Group).find { |g| g.name == 'ENTRY_PLATFORM' }
raise 'ENTRY_PLATFORM group is missing' unless platform
dc2_box(platform.entities, 'SITE_APRON', -2600, -3400, -240, 13800, 10200, -80, concrete)
