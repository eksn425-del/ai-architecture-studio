# Targeted visual correction for revision 1. Keep all approved KEEP systems intact.
raise 'Luna correction requires model and root' unless model && root

mm = ->(n) { n.to_f.mm }
pt = ->(x, y, z) { Geom::Point3d.new(mm.call(x), mm.call(y), mm.call(z)) }
vec = ->(x, y, z) { Geom::Vector3d.new(x.to_f, y.to_f, z.to_f) }
timber = model.materials['Luna | Structural timber']
wood = model.materials['Luna | Aged vertical oak']
stone = model.materials['Luna | Pale concrete stone']
dark = model.materials['Luna | Espresso brown']
wood_light = model.materials['Luna | Weathered oak variation']
glass = model.materials['Luna | Clear cafe glazing']
roof_edge = model.materials['Luna | Charcoal fascia']

remove_owned_group.call(['ROOF_MAIN_SINGLE_SLOPE', 'EDGE_FASCIA_LEFT'])
remove_owned_group.call(['ROOF_MAIN_SINGLE_SLOPE', 'EDGE_FASCIA_RIGHT'])
roof = root.entities.grep(Sketchup::Group).find { |g| g.name == 'ROOF_MAIN_SINGLE_SLOPE' }
raise 'Main roof group missing during fascia correction' unless roof

face = lambda do |entities, points, mat|
  f = entities.add_face(points)
  if f
    f.material = mat
    f.back_material = mat
  end
  f
end

beam = lambda do |entities, name, a_mm, b_mm, width_mm, depth_mm, mat, normal_hint|
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
  hw = mm.call(width_mm.to_f / 2.0)
  hd = mm.call(depth_mm.to_f / 2.0)
  w = vec.call(side.x * hw, side.y * hw, side.z * hw)
  t = vec.call(n.x * hd, n.y * hd, n.z * hd)
  a0, a1, a2, a3 = a - w - t, a + w - t, a + w + t, a - w + t
  b0, b1, b2, b3 = b - w - t, b + w - t, b + w + t, b - w + t
  g = entities.add_group
  g.name = name
  face.call(g.entities, [a0, a1, a2, a3], mat)
  face.call(g.entities, [b0, b3, b2, b1], mat)
  face.call(g.entities, [a0, b0, b1, a1], mat)
  face.call(g.entities, [a1, b1, b2, a2], mat)
  face.call(g.entities, [a2, b2, b3, a3], mat)
  face.call(g.entities, [a3, b3, b0, a0], mat)
  g
end

beam.call(roof.entities, 'EDGE_FASCIA_LEFT',
  [-120, -180, 3620], [-120, 4680, 5280], 150, 85, roof_edge, [1, 0, 0])
beam.call(roof.entities, 'EDGE_FASCIA_RIGHT',
  [4920, -180, 3620], [4920, 4680, 5280], 150, 85, roof_edge, [1, 0, 0])

remove_owned_group.call('FRONT_BASE_STONE_LEFT')
remove_owned_group.call('FRONT_BASE_STONE_BETWEEN')
remove_owned_group.call('FRONT_BASE_STONE_RIGHT')
remove_owned_group.call('RIGHT_BASE_STONE_COURSE')

box = lambda do |entities, name, x1, y1, z1, x2, y2, z2, mat|
  lo_x, hi_x = [x1.to_f, x2.to_f].minmax
  lo_y, hi_y = [y1.to_f, y2.to_f].minmax
  lo_z, hi_z = [z1.to_f, z2.to_f].minmax
  g = entities.add_group
  g.name = name
  f = g.entities.add_face(
    pt.call(lo_x, lo_y, lo_z), pt.call(hi_x, lo_y, lo_z),
    pt.call(hi_x, hi_y, lo_z), pt.call(lo_x, hi_y, lo_z)
  )
  raise "Cannot create box #{name}" unless f && f.valid?
  h = mm.call(hi_z - lo_z)
  f.pushpull(lo_z.abs < 0.001 ? -h : h)
  g.entities.grep(Sketchup::Face).each do |fc|
    fc.material = mat
    fc.back_material = mat
  end
  g
end

box.call(root.entities, 'FRONT_BASE_STONE_LEFT', 0, -112, 0, 350, -90, 280, stone)
box.call(root.entities, 'FRONT_BASE_STONE_BETWEEN', 1250, -112, 0, 1690, -90, 280, stone)
box.call(root.entities, 'FRONT_BASE_STONE_RIGHT', 3860, -112, 0, 4800, -90, 280, stone)
box.call(root.entities, 'RIGHT_BASE_STONE_COURSE', 4890, 0, 0, 4912, 4500, 280, stone)

remove_owned_group.call('FRONT_ENTRY_DOOR_MODULE')
door = root.entities.add_group
door.name = 'FRONT_ENTRY_DOOR_MODULE'
box.call(door.entities, 'DOOR_JAMB_LEFT', 315, -138, 0, 405, -78, 2110, timber)
box.call(door.entities, 'DOOR_JAMB_RIGHT', 1245, -138, 0, 1335, -78, 2110, timber)
box.call(door.entities, 'DOOR_HEAD', 315, -138, 2030, 1335, -78, 2120, timber)
box.call(door.entities, 'DOOR_THRESHOLD', 315, -160, 0, 1335, 30, 55, dark)
box.call(door.entities, 'DOOR_LEAF_FRAME_LEFT', 405, -102, 0, 460, -58, 2020, wood)
box.call(door.entities, 'DOOR_LEAF_FRAME_RIGHT', 1190, -102, 0, 1245, -58, 2020, wood)
box.call(door.entities, 'DOOR_LEAF_BOTTOM', 460, -102, 0, 1190, -58, 560, wood_light)
box.call(door.entities, 'DOOR_LEAF_TOP', 460, -102, 1980, 1190, -58, 2020, wood)
face.call(door.entities,
  [pt.call(460, -62, 560), pt.call(1190, -62, 560), pt.call(1190, -62, 1980), pt.call(460, -62, 1980)], glass)
box.call(door.entities, 'DOOR_MID_RAIL', 460, -116, 535, 1190, -57, 590, wood)
box.call(door.entities, 'DOOR_KICK_PANEL', 465, -118, 65, 1185, -58, 500, wood_light)
box.call(door.entities, 'DOOR_HANDLE', 1115, -150, 1000, 1145, -128, 1140, dark)
beam.call(door.entities, 'DOOR_DIAGONAL_LOWER_DETAIL',
  [490, -124, 95], [1160, -124, 470], 36, 18, timber, [0, 1, 0])

easel = root.entities.grep(Sketchup::Group).find { |g| g.name == 'SIGNAGE_MENU_EASEL' }
raise 'Menu easel group missing during relocation' unless easel
easel.transform!(Geom::Transformation.translation(vec.call(0, mm.call(3900), 0))) if easel.bounds.min.y < mm.call(4400)

{
  'correction' => 1,
  'roof_side_fascia' => 'narrow slope-following beams',
  'door_frame_bounds_mm' => {
    'min' => [door.bounds.min.x.to_mm.round(1), door.bounds.min.y.to_mm.round(1), door.bounds.min.z.to_mm.round(1)],
    'max' => [door.bounds.max.x.to_mm.round(1), door.bounds.max.y.to_mm.round(1), door.bounds.max.z.to_mm.round(1)]
  },
  'easel_relocated' => true
}
