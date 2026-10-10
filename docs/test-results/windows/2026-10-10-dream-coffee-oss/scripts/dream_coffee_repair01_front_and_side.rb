# Local correction pass 01: open the source-visible front terrace bay and
# simplify the annex-side timber cladding. The full reconstruction baseline
# contains the same accepted changes for repeatable rebuilds.

def dc_repair01_point(x, y, z)
  Geom::Point3d.new(x.mm, y.mm, z.mm)
end

def dc_repair01_box(entities, name, x0, y0, z0, x1, y1, z1, material)
  return nil if (x1 - x0).abs < 0.01 || (y1 - y0).abs < 0.01 || (z1 - z0).abs < 0.01
  g = entities.add_group
  g.name = name
  v = [
    dc_repair01_point(x0, y0, z0), dc_repair01_point(x1, y0, z0),
    dc_repair01_point(x1, y1, z0), dc_repair01_point(x0, y1, z0),
    dc_repair01_point(x0, y0, z1), dc_repair01_point(x1, y0, z1),
    dc_repair01_point(x1, y1, z1), dc_repair01_point(x0, y1, z1)
  ]
  [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]].each do |ids|
    face = g.entities.add_face(ids.map { |i| v[i] })
    next unless face
    face.material = material
    face.back_material = material
  end
  g
end

# Rebuild only the front continuous wall host with the right-front bay open.
remove_owned_group.call('FRONT_ENTRY_OPENING_HOST')
front_wall = saie_wall_with_openings.call({
  'name' => 'FRONT_ENTRY_OPENING_HOST',
  'centerline' => [[4200, 0], [12000, 0]],
  'thickness_mm' => 180,
  'height_mm' => 3100,
  'elevation_mm' => 0,
  'openings' => [
    { 'offset_mm' => 200, 'width_mm' => 2500, 'height_mm' => 2850, 'sill_mm' => 0 },
    { 'offset_mm' => 3100, 'width_mm' => 2200, 'height_mm' => 2500, 'sill_mm' => 250 },
    { 'offset_mm' => 5400, 'width_mm' => 2300, 'height_mm' => 3100, 'sill_mm' => 0 }
  ]
})
front_wall.material = model.materials['DreamCoffee | pale concrete'] if front_wall.respond_to?(:material=)
if front_wall.respond_to?(:entities)
  front_wall.entities.each do |e|
    next unless e.is_a?(Sketchup::Face)
    e.material = model.materials['DreamCoffee | pale concrete']
    e.back_material = model.materials['DreamCoffee | pale concrete']
  end
end

# The former third glazed opening lies inside the newly open porch bay.
[
  'FRONT_OPENING_GLASS_3',
  'FRONT_OPENING_JAMB_L_3', 'FRONT_OPENING_JAMB_R_3',
  'FRONT_OPENING_HEAD_3', 'FRONT_OPENING_SILL_3',
  'FRONT_OPENING_MULLION_3_1', 'FRONT_OPENING_MULLION_3_2'
].each { |name| remove_owned_group.call(name) }

# Replace twenty close vertical fins with three broad timber panels and two
# fine shadow joints, retaining all other contents of MATERIAL_ZONES.
zones = root.entities.grep(Sketchup::Group).find { |g| g.name == 'MATERIAL_ZONES' }
raise 'MATERIAL_ZONES group is missing' unless zones
20.times do |i|
  remove_owned_group.call(['MATERIAL_ZONES', "RIGHT_WALL_WOOD_PANEL_#{i + 1}"])
end
wood_light = model.materials['DreamCoffee | pale timber']
wood_dark = model.materials['DreamCoffee | structural timber']
raise 'Required timber materials are missing' unless wood_light && wood_dark
dc_repair01_box(zones.entities, 'RIGHT_WALL_WOOD_BACKING', 12091, 0, 80, 12092, 8400, 3040, wood_dark)
[[16, 2784], [2800, 5584], [5600, 8384]].each_with_index do |(y0, y1), i|
  dc_repair01_box(zones.entities, "RIGHT_WALL_WOOD_PANEL_#{i + 1}", 12092, y0, 80, 12114, y1, 3040, wood_light)
end
