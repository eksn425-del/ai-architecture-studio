# Persistent source for the approved six-view villa reconstruction.
# All dimensions below are millimetres; geometry is authored only beneath root.

W = 10_500.0
D = 8_500.0
WALL = 200.0
LEVEL1_TOP = 3_150.0
LEVEL2_BASE = 3_350.0
ROOF_BASE = 6_150.0
ROOF_TOP = 6_350.0
PARAPET_TOP = 6_850.0

def villa_material(model, name, rgb, alpha = 1.0)
  material = model.materials[name] || model.materials.add(name)
  material.color = Sketchup::Color.new(rgb[0], rgb[1], rgb[2])
  material.alpha = alpha
  material
end

def villa_point(x, y, z)
  Geom::Point3d.new(x.mm, y.mm, z.mm)
end

def villa_box(entities, name, x0, y0, z0, x1, y1, z1, material)
  raise "Degenerate box #{name}" if (x1 - x0).abs < 0.1 || (y1 - y0).abs < 0.1 || (z1 - z0).abs < 0.1
  group = entities.add_group
  group.name = name
  face = group.entities.add_face(
    villa_point(x0, y0, z0), villa_point(x1, y0, z0),
    villa_point(x1, y1, z0), villa_point(x0, y1, z0)
  )
  raise "Could not create base face for #{name}" unless face && face.valid?
  face.reverse! if face.normal.z < 0
  face.pushpull((z1 - z0).mm)
  group.entities.grep(Sketchup::Face).each do |f|
    f.material = material
    f.back_material = material
  end
  group.material = material
  group
end

def villa_cylinder(entities, name, cx, cy, z0, radius, height, material, segments = 12)
  group = entities.add_group
  group.name = name
  center = villa_point(cx, cy, z0)
  edges = group.entities.add_circle(center, Geom::Vector3d.new(0, 0, 1), radius.mm, segments)
  face = group.entities.add_face(edges)
  raise "Could not create cylinder #{name}" unless face && face.valid?
  face.reverse! if face.normal.z < 0
  face.pushpull(height.mm)
  group.entities.grep(Sketchup::Face).each do |f|
    f.material = material
    f.back_material = material
  end
  group
end

def villa_profile(geometry_api, entities, name, outer, holes, depth, plane, offset, material)
  result = if holes.empty?
    geometry_api.profile(entities, name, outer, depth, plane, offset, material)
  else
    geometry_api.profile_with_holes(entities, name, outer, holes, depth, plane, offset, material)
  end
  raise "ADAI profile failed: #{name}" if result == false || result.nil?
  result
end

def villa_rect_profile(x0, y0, x1, y1)
  [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
end

# Host one checked representative window module, then place the remaining
# frames/glazing from the shared opening schedule on the same facade assembly.
def villa_window(entities, name, axis, a0, a1, z0, z1, wall0, wall1, frame_mat, glass_mat, divisions = 1, frame = 55.0)
  span = a1 - a0
  raise "Invalid opening #{name}" if span <= frame * 2 || z1 - z0 <= frame * 2
  if axis == :y
    # X-Z facade; wall0/wall1 are Y coordinates.
    villa_box(entities, "#{name}_JAMB_L", a0, wall0, z0, a0 + frame, wall1, z1, frame_mat)
    villa_box(entities, "#{name}_JAMB_R", a1 - frame, wall0, z0, a1, wall1, z1, frame_mat)
    villa_box(entities, "#{name}_HEAD", a0 + frame, wall0, z1 - frame, a1 - frame, wall1, z1, frame_mat)
    villa_box(entities, "#{name}_SILL", a0 + frame, wall0, z0, a1 - frame, wall1, z0 + frame, frame_mat)
    gy0 = (wall0 + wall1) * 0.5 - 10.0
    gy1 = gy0 + 20.0
    villa_box(entities, "#{name}_GLASS", a0 + frame, gy0, z0 + frame, a1 - frame, gy1, z1 - frame, glass_mat)
    1.upto(divisions) do |i|
      x = a0 + span * i.to_f / (divisions + 1)
      villa_box(entities, "#{name}_MULLION_#{i}", x - 18, wall0, z0 + frame, x + 18, wall1, z1 - frame, frame_mat)
    end
  else
    # Y-Z facade; wall0/wall1 are X coordinates.
    villa_box(entities, "#{name}_JAMB_FRONT", wall0, a0, z0, wall1, a0 + frame, z1, frame_mat)
    villa_box(entities, "#{name}_JAMB_REAR", wall0, a1 - frame, z0, wall1, a1, z1, frame_mat)
    villa_box(entities, "#{name}_HEAD", wall0, a0 + frame, z1 - frame, wall1, a1 - frame, z1, frame_mat)
    villa_box(entities, "#{name}_SILL", wall0, a0 + frame, z0, wall1, a1 - frame, z0 + frame, frame_mat)
    gx0 = (wall0 + wall1) * 0.5 - 10.0
    gx1 = gx0 + 20.0
    villa_box(entities, "#{name}_GLASS", gx0, a0 + frame, z0 + frame, gx1, a1 - frame, z1 - frame, glass_mat)
    1.upto(divisions) do |i|
      y = a0 + span * i.to_f / (divisions + 1)
      villa_box(entities, "#{name}_MULLION_#{i}", wall0, y - 18, z0 + frame, wall1, y + 18, z1 - frame, frame_mat)
    end
  end
end

def villa_plant(entities, name, x, y, z, pot_mat, leaf_mat, scale = 1.0)
  villa_box(entities, "#{name}_POT", x, y, z, x + 420 * scale, y + 360 * scale, z + 390 * scale, pot_mat)
  stem_base = z + 380 * scale
  [[0.18, 0.20], [0.52, 0.18], [0.80, 0.24], [0.34, 0.65], [0.68, 0.72]].each_with_index do |(rx, ry), i|
    villa_cylinder(entities, "#{name}_STEM_#{i + 1}", x + rx * 420 * scale, y + ry * 360 * scale,
                   stem_base, 9 * scale, (430 + (i % 2) * 120) * scale, leaf_mat, 8)
    lx = x + rx * 420 * scale
    ly = y + ry * 360 * scale
    villa_box(entities, "#{name}_LEAF_#{i + 1}A", lx - 150 * scale, ly - 18 * scale,
              stem_base + 180 * scale, lx + 140 * scale, ly + 18 * scale,
              stem_base + 280 * scale, leaf_mat)
    villa_box(entities, "#{name}_LEAF_#{i + 1}B", lx - 18 * scale, ly - 125 * scale,
              stem_base + 300 * scale, lx + 18 * scale, ly + 145 * scale,
              stem_base + 400 * scale, leaf_mat)
  end
end

def villa_roof_grid(entities, x0, y0, x1, y1, z, pitch, material)
  x = x0 + pitch
  index = 1
  while x < x1 - 80
    joint = villa_box(entities, "ROOF_TILE_JOINT_X_#{index}", x - 1.5, y0 + 80, z, x + 1.5, y1 - 80, z + 1.5, material)
    joint.entities.grep(Sketchup::Edge).each { |edge| edge.hidden = true }
    x += pitch
    index += 1
  end
  y = y0 + pitch
  index = 1
  while y < y1 - 80
    joint = villa_box(entities, "ROOF_TILE_JOINT_Y_#{index}", x0 + 80, y - 1.5, z, x1 - 80, y + 1.5, z + 1.5, material)
    joint.entities.grep(Sketchup::Edge).each { |edge| edge.hidden = true }
    y += pitch
    index += 1
  end
end

m = {
  render: villa_material(model, "Villa warm white render", [236, 233, 226]),
  render_shadow: villa_material(model, "Villa reveal shadow", [177, 176, 170]),
  charcoal: villa_material(model, "Villa charcoal aluminum", [38, 42, 45]),
  glass: villa_material(model, "Villa clear gray glass", [126, 154, 164], 0.34),
  timber: villa_material(model, "Villa honey oak fins", [176, 111, 48]),
  timber_light: villa_material(model, "Villa oak edge", [202, 144, 77]),
  concrete: villa_material(model, "Villa pale concrete", [205, 204, 197]),
  paving: villa_material(model, "Villa limestone paving", [177, 178, 173]),
  grout: villa_material(model, "Villa paving joints", [129, 132, 130]),
  roof: villa_material(model, "Villa roof tile gray", [155, 160, 160]),
  roof_joint: villa_material(model, "Villa roof tile joints", [151, 154, 154]),
  interior_floor: villa_material(model, "Villa light oak floor", [191, 162, 123]),
  interior_wall: villa_material(model, "Villa interior warm white", [231, 226, 215]),
  sofa: villa_material(model, "Villa sofa warm gray", [164, 160, 149]),
  cushion: villa_material(model, "Villa cushions linen", [213, 207, 190]),
  wood: villa_material(model, "Villa interior oak", [146, 100, 60]),
  green: villa_material(model, "Villa planting green", [62, 112, 57]),
  planter: villa_material(model, "Villa planter charcoal", [76, 79, 76]),
  black: villa_material(model, "Villa dark details", [46, 47, 45])
}

# === Stage 1: primary form, true openings, balcony volume, recessed roof ===
front_ground_holes = [
  villa_rect_profile(3_050, 100, 7_450, 2_500)
]
front_upper_holes = [
  villa_rect_profile(2_050, 3_700, 3_900, 5_750),
  villa_rect_profile(6_500, 3_700, 8_350, 5_750)
]
villa_profile(adai_geometry, root.entities, "SHELL_FRONT_GROUND", villa_rect_profile(0, 0, W, LEVEL1_TOP), front_ground_holes, WALL, "xz", 0, m[:render])
villa_profile(adai_geometry, root.entities, "SHELL_FRONT_UPPER", villa_rect_profile(0, LEVEL2_BASE, W, ROOF_BASE), front_upper_holes, WALL, "xz", 0, m[:render])

rear_ground_holes = []
rear_upper_holes = []
[1_650.0, 5_250.0, 8_850.0].each_with_index do |cx, i|
  rear_ground_holes << villa_rect_profile(cx - 360, 850, cx + 360, 2_300)
  rear_upper_holes << villa_rect_profile(cx - 360, 3_850, cx + 360, 5_300)
end
villa_profile(adai_geometry, root.entities, "SHELL_REAR_GROUND", villa_rect_profile(0, 0, W, LEVEL1_TOP), rear_ground_holes, WALL, "xz", D - WALL, m[:render])
villa_profile(adai_geometry, root.entities, "SHELL_REAR_UPPER", villa_rect_profile(0, LEVEL2_BASE, W, ROOF_BASE), rear_upper_holes, WALL, "xz", D - WALL, m[:render])

left_ground_holes = [villa_rect_profile(2_900, 850, 3_600, 2_300)]
left_upper_holes = [villa_rect_profile(2_900, 3_850, 3_600, 5_300)]
villa_profile(adai_geometry, root.entities, "SHELL_LEFT_GROUND", villa_rect_profile(0, 0, D, LEVEL1_TOP), left_ground_holes, WALL, "yz", 0, m[:render])
villa_profile(adai_geometry, root.entities, "SHELL_LEFT_UPPER", villa_rect_profile(0, LEVEL2_BASE, D, ROOF_BASE), left_upper_holes, WALL, "yz", 0, m[:render])

right_ground_holes = [villa_rect_profile(500, 100, 1_450, 2_350)]
right_upper_holes = [villa_rect_profile(5_400, 3_850, 7_300, 5_500)]
villa_profile(adai_geometry, root.entities, "SHELL_RIGHT_GROUND", villa_rect_profile(0, 0, D, LEVEL1_TOP), right_ground_holes, WALL, "yz", W - WALL, m[:render])
villa_profile(adai_geometry, root.entities, "SHELL_RIGHT_UPPER", villa_rect_profile(0, LEVEL2_BASE, D, ROOF_BASE), right_upper_holes, WALL, "yz", W - WALL, m[:render])

# Ground and upper floor plates; the balcony is an independent projecting slab.
villa_box(root.entities, "GROUND_FLOOR_PLATE", 0, 0, -80, W, D, 150, m[:concrete])
villa_box(root.entities, "UPPER_FLOOR_PLATE", 0, 0, LEVEL1_TOP, W, D, LEVEL2_BASE, m[:concrete])
villa_box(root.entities, "BALCONY_SLAB", 1_100, -1_450, 3_250, 9_400, 200, 3_470, m[:concrete])

# ADAI XY profile builds a genuinely recessed roof deck inside four parapet walls.
villa_profile(adai_geometry, root.entities, "ROOF_SLAB", villa_rect_profile(200, 200, W - 200, D - 200), [], 200, "xy", ROOF_BASE, m[:roof])
villa_box(root.entities, "PARAPET_FRONT", 0, -1, ROOF_BASE - 2, W, WALL, PARAPET_TOP - 30, m[:render])
villa_box(root.entities, "PARAPET_REAR", 0, D - WALL, ROOF_BASE - 2, W, D + 1, PARAPET_TOP - 30, m[:render])
villa_box(root.entities, "PARAPET_LEFT", -1, WALL, ROOF_BASE - 2, WALL, D - WALL, PARAPET_TOP - 30, m[:render])
villa_box(root.entities, "PARAPET_RIGHT", W - WALL, WALL, ROOF_BASE - 2, W + 1, D - WALL, PARAPET_TOP - 30, m[:render])
villa_box(root.entities, "PARAPET_COPING_FRONT", 0, -15, PARAPET_TOP - 30, W, WALL + 15, PARAPET_TOP, m[:concrete])
villa_box(root.entities, "PARAPET_COPING_REAR", 0, D - WALL - 15, PARAPET_TOP - 30, W, D + 15, PARAPET_TOP, m[:concrete])
villa_box(root.entities, "PARAPET_COPING_LEFT", -15, WALL, PARAPET_TOP - 30, WALL + 15, D - WALL, PARAPET_TOP, m[:concrete])
villa_box(root.entities, "PARAPET_COPING_RIGHT", W - WALL - 15, WALL, PARAPET_TOP - 30, W + 15, D - WALL, PARAPET_TOP, m[:concrete])
villa_roof_grid(root.entities, 200, 200, W - 200, D - 200, ROOF_TOP + 2, 600, m[:roof_joint])

# Base plinth reads as the light-gray stone course in the source views.
villa_box(root.entities, "BASE_PLINTH_FRONT", -30, -20, -30, W + 30, 30, 90, m[:concrete])
villa_box(root.entities, "BASE_PLINTH_REAR", -30, D - 30, -30, W + 30, D + 20, 90, m[:concrete])
villa_box(root.entities, "BASE_PLINTH_LEFT", -30, 30, -30, 30, D - 30, 90, m[:concrete])
villa_box(root.entities, "BASE_PLINTH_RIGHT", W - 30, 30, -30, W + 30, D - 30, 90, m[:concrete])

# === Stage 2: representative openings and repeated facade assemblies ===
# The front slider is the checked representative; all other window modules use
# the same frame/glass depth and shared schedule dimensions.
villa_window(root.entities, "FRONT_SLIDER", :y, 3_050, 7_450, 100, 2_500, -35, 120, m[:charcoal], m[:glass], 3, 70)
villa_window(root.entities, "FRONT_UPPER_LEFT", :y, 2_050, 3_900, 3_700, 5_750, -20, 120, m[:charcoal], m[:glass], 1, 58)
villa_window(root.entities, "FRONT_UPPER_RIGHT", :y, 6_500, 8_350, 3_700, 5_750, -20, 120, m[:charcoal], m[:glass], 1, 58)

[1_650.0, 5_250.0, 8_850.0].each_with_index do |cx, i|
  villa_window(root.entities, "REAR_GROUND_WIN_#{i + 1}", :y, cx - 360, cx + 360, 850, 2_300, 8_380, 8_535, m[:charcoal], m[:glass], 0, 48)
  villa_window(root.entities, "REAR_UPPER_WIN_#{i + 1}", :y, cx - 360, cx + 360, 3_850, 5_300, 8_380, 8_535, m[:charcoal], m[:glass], 0, 48)
end

villa_window(root.entities, "LEFT_GROUND_SLIT", :x, 2_900, 3_600, 850, 2_300, -35, 120, m[:charcoal], m[:glass], 0, 48)
villa_window(root.entities, "LEFT_UPPER_SLIT", :x, 2_900, 3_600, 3_850, 5_300, -35, 120, m[:charcoal], m[:glass], 0, 48)
villa_window(root.entities, "RIGHT_UPPER_DOUBLE_WIN", :x, 5_400, 7_300, 3_850, 5_500, 10_380, 10_535, m[:charcoal], m[:glass], 1, 58)

# Side entry sits in the true ADAI wall aperture; add a recessed opaque door leaf.
villa_box(root.entities, "ENTRY_DOOR_LEAF", 10_390, 575, 100, 10_485, 1_375, 2_300, m[:black])
villa_box(root.entities, "ENTRY_DOOR_INSET", 10_485, 1_265, 1_050, 10_505, 1_315, 1_420, m[:charcoal])
villa_box(root.entities, "ENTRY_DOOR_HANDLE", 10_485, 1_285, 1_020, 10_520, 1_305, 1_100, m[:timber_light])
villa_box(root.entities, "ENTRY_CANOPY", 10_500, 430, 2_420, 11_050, 1_570, 2_610, m[:concrete])
villa_box(root.entities, "ENTRY_CANOPY_SHADOW", 10_500, 470, 2_405, 11_000, 1_530, 2_440, m[:render_shadow])
villa_box(root.entities, "ENTRY_STEP_LOWER", 10_500, 360, -70, 10_950, 1_580, 45, m[:concrete])
villa_box(root.entities, "ENTRY_STEP_UPPER", 10_500, 540, 45, 10_800, 1_400, 150, m[:concrete])
villa_box(root.entities, "ENTRY_LANDING", 10_500, 1_400, 140, 10_900, 1_690, 220, m[:concrete])

# Balcony and transparent guardrail: one front run plus short returning wings.
villa_box(root.entities, "BALCONY_FRONT_BASE_SHOE", 1_120, -1_475, 3_470, 9_380, -1_430, 3_515, m[:charcoal])
villa_box(root.entities, "BALCONY_FRONT_TOP_RAIL", 1_100, -1_480, 4_485, 9_400, -1_425, 4_535, m[:charcoal])
villa_box(root.entities, "BALCONY_FRONT_GLASS_01", 1_140, -1_458, 3_515, 2_300, -1_442, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_FRONT_GLASS_02", 2_320, -1_458, 3_515, 3_500, -1_442, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_FRONT_GLASS_03", 3_520, -1_458, 3_515, 4_700, -1_442, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_FRONT_GLASS_04", 4_720, -1_458, 3_515, 5_900, -1_442, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_FRONT_GLASS_05", 5_920, -1_458, 3_515, 7_100, -1_442, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_FRONT_GLASS_06", 7_120, -1_458, 3_515, 8_300, -1_442, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_FRONT_GLASS_07", 8_320, -1_458, 3_515, 9_360, -1_442, 4_485, m[:glass])
[1_100.0, 2_300.0, 3_500.0, 4_700.0, 5_900.0, 7_100.0, 8_300.0, 9_400.0].each_with_index do |x, i|
  villa_box(root.entities, "BALCONY_POST_#{i + 1}", x - 18, -1_490, 3_470, x + 18, -1_415, 4_535, m[:charcoal])
end
villa_box(root.entities, "BALCONY_RETURN_LEFT_SHOE", 1_075, -1_450, 3_470, 1_120, -480, 3_515, m[:charcoal])
villa_box(root.entities, "BALCONY_RETURN_LEFT_GLASS", 1_090, -1_430, 3_515, 1_106, -530, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_RETURN_LEFT_RAIL", 1_070, -1_450, 4_485, 1_125, -480, 4_535, m[:charcoal])
villa_box(root.entities, "BALCONY_RETURN_RIGHT_SHOE", 9_380, -1_450, 3_470, 9_425, -480, 3_515, m[:charcoal])
villa_box(root.entities, "BALCONY_RETURN_RIGHT_GLASS", 9_394, -1_430, 3_515, 9_410, -530, 4_485, m[:glass])
villa_box(root.entities, "BALCONY_RETURN_RIGHT_RAIL", 9_375, -1_450, 4_485, 9_430, -480, 4_535, m[:charcoal])

# Honey oak screen on the front-right corner; one module repeated at 100 mm.
screen = root.entities.add_group
screen.name = "FRONT_TIMBER_SCREEN"
fin_count = 0
x = 9_270.0
while x < W - 10
  fin_count += 1
  villa_box(screen.entities, "FIN_FRONT_%03d" % fin_count, x, -82, 0, x + 42, -8, PARAPET_TOP, m[:timber])
  x += 100
end
wrap_count = 0
y = 30.0
while y < 730
  wrap_count += 1
  villa_box(screen.entities, "FIN_RETURN_%03d" % wrap_count, W - 70, y, 0, W + 4, y + 42, PARAPET_TOP, m[:timber])
  y += 100
end

# Balcony furniture and planters visible in the source obliques.
villa_plant(root.entities, "BALCONY_PLANT_LEFT", 1_380, -1_100, 3_470, m[:planter], m[:green], 0.82)
villa_plant(root.entities, "BALCONY_PLANT_RIGHT", 8_700, -1_100, 3_470, m[:planter], m[:green], 0.82)
villa_box(root.entities, "BALCONY_LOUNGE_SEAT", 4_200, -1_050, 3_500, 5_250, -600, 3_950, m[:cushion])
villa_box(root.entities, "BALCONY_LOUNGE_BACK", 4_200, -620, 3_500, 5_250, -520, 4_350, m[:sofa])
villa_box(root.entities, "BALCONY_SIDE_TABLE_TOP", 5_550, -980, 3_900, 6_050, -630, 3_960, m[:wood])
villa_box(root.entities, "BALCONY_SIDE_TABLE_BASE", 5_760, -850, 3_500, 5_840, -770, 3_900, m[:charcoal])

# === Stage 3: source-visible interior and coherent inferred circulation ===
villa_box(root.entities, "GROUND_INTERIOR_OAK_FLOOR", 180, 180, 150, W - 180, D - 180, 178, m[:interior_floor])
villa_box(root.entities, "UPPER_INTERIOR_FLOOR_FINISH", 180, 180, 3_350, W - 180, D - 180, 3_385, m[:interior_floor])
# Inferred service core and stair run behind the open living/dining zone.
villa_box(root.entities, "SERVICE_CORE_PARTITION_LONG", 7_750, 1_750, 178, 7_880, 6_750, 3_050, m[:interior_wall])
villa_box(root.entities, "SERVICE_CORE_PARTITION_CROSS", 6_100, 5_000, 178, 7_880, 5_130, 3_050, m[:interior_wall])
villa_box(root.entities, "STAIR_LOW_MASS", 7_950, 2_300, 178, 9_300, 4_600, 178 + 1_450, m[:interior_wall])
1.upto(8) do |i|
  z = 178 + i * 165
  villa_box(root.entities, "STAIR_TREAD_%02d" % i, 7_950 + i * 135, 2_350, z, 8_100 + i * 135, 4_550, z + 45, m[:concrete])
end

# Living-room silhouettes immediately behind the broad front slider.
villa_box(root.entities, "LIVING_RUG", 3_050, 1_050, 178, 5_450, 3_050, 195, m[:cushion])
villa_box(root.entities, "LIVING_SOFA_SEAT", 3_250, 2_050, 205, 5_350, 2_900, 650, m[:sofa])
villa_box(root.entities, "LIVING_SOFA_BACK", 3_250, 2_820, 620, 5_350, 2_940, 1_260, m[:sofa])
villa_box(root.entities, "LIVING_SOFA_ARM_LEFT", 3_220, 2_050, 205, 3_420, 2_920, 820, m[:sofa])
villa_box(root.entities, "LIVING_SOFA_ARM_RIGHT", 5_180, 2_050, 205, 5_380, 2_920, 820, m[:sofa])
villa_box(root.entities, "LIVING_COFFEE_TABLE_TOP", 3_650, 1_100, 570, 4_950, 1_850, 640, m[:wood])
villa_box(root.entities, "LIVING_COFFEE_TABLE_LEG_1", 3_740, 1_180, 195, 3_800, 1_250, 570, m[:charcoal])
villa_box(root.entities, "LIVING_COFFEE_TABLE_LEG_2", 4_800, 1_180, 195, 4_860, 1_250, 570, m[:charcoal])
villa_plant(root.entities, "LIVING_PLANT_FRONT_LEFT", 2_680, 1_350, 178, m[:planter], m[:green], 1.0)

# Dining set sits to the other side of the glazed opening as shown in the sheet.
villa_box(root.entities, "DINING_TABLE_TOP", 5_650, 1_900, 900, 7_050, 2_800, 970, m[:wood])
villa_box(root.entities, "DINING_TABLE_LEG_1", 5_800, 2_050, 195, 5_880, 2_130, 900, m[:charcoal])
villa_box(root.entities, "DINING_TABLE_LEG_2", 6_820, 2_050, 195, 6_900, 2_130, 900, m[:charcoal])
[[5_750, 1_450], [6_650, 1_450], [5_750, 2_900], [6_650, 2_900]].each_with_index do |(cx, cy), i|
  villa_box(root.entities, "DINING_CHAIR_SEAT_#{i + 1}", cx, cy, 620, cx + 420, cy + 380, 700, m[:sofa])
  villa_box(root.entities, "DINING_CHAIR_BACK_#{i + 1}", cx, cy + 320, 700, cx + 420, cy + 390, 1_230, m[:wood])
  villa_box(root.entities, "DINING_CHAIR_LEGS_#{i + 1}", cx + 35, cy + 35, 195, cx + 90, cy + 90, 620, m[:charcoal])
  villa_box(root.entities, "DINING_CHAIR_LEGS_B_#{i + 1}", cx + 330, cy + 35, 195, cx + 385, cy + 90, 620, m[:charcoal])
end

# Upper-floor bed and bedside forms remain visible through the paired upper windows.
villa_box(root.entities, "BEDROOM_RUG", 4_200, 2_000, 3_385, 7_200, 5_700, 3_405, m[:cushion])
villa_box(root.entities, "BED_FRAME", 4_650, 3_200, 3_405, 6_850, 5_350, 3_700, m[:wood])
villa_box(root.entities, "BED_MATTRESS", 4_720, 3_250, 3_700, 6_780, 5_300, 3_930, m[:cushion])
villa_box(root.entities, "BED_HEADBOARD", 4_600, 5_250, 3_405, 6_900, 5_390, 4_230, m[:wood])
villa_box(root.entities, "BEDROOM_BEDSIDE_LEFT", 4_050, 4_700, 3_405, 4_550, 5_250, 4_050, m[:wood])
villa_box(root.entities, "BEDROOM_BEDSIDE_RIGHT", 6_950, 4_700, 3_405, 7_450, 5_250, 4_050, m[:wood])

# === Stage 4: immediate site edge / entry paving ===
villa_box(root.entities, "PAVING_FRONT_APRON", -650, -1_100, -100, W + 650, 0, -15, m[:paving])
villa_box(root.entities, "PAVING_LEFT_APRON", -650, 0, -100, 0, D, -15, m[:paving])
villa_box(root.entities, "PAVING_RIGHT_APRON", W, 0, -100, W + 650, D, -15, m[:paving])
villa_box(root.entities, "PAVING_REAR_APRON", 0, D, -100, W, D + 650, -15, m[:paving])
index = 1
x = -50.0
while x < W + 500
  villa_box(root.entities, "PAVING_FRONT_JOINT_X_#{index}", x - 5, -1_090, -18, x + 5, -20, -8, m[:grout])
  x += 600
  index += 1
end
index = 1
y = -500.0
while y < 0
  villa_box(root.entities, "PAVING_FRONT_JOINT_Y_#{index}", -640, y - 5, -18, W + 640, y + 5, -8, m[:grout])
  y += 600
  index += 1
end

# Small soffit lights under the balcony and a few understated paving joints.
[2_000.0, 4_800.0, 7_700.0].each_with_index do |x, i|
  villa_box(root.entities, "BALCONY_SOFFIT_LIGHT_#{i + 1}", x - 65, -420, 3_238, x + 65, -300, 3_252, m[:charcoal])
end

# Record the selected shared dimensions with the model's owned root for readback.
root.set_attribute("KStudioReconstruction", "source", "inputs/reference/ba48d507b3-villa-six-view-sheet.png")
root.set_attribute("KStudioReconstruction", "overall_width_mm", W)
root.set_attribute("KStudioReconstruction", "overall_depth_mm", D)
root.set_attribute("KStudioReconstruction", "parapet_top_mm", PARAPET_TOP)
root.set_attribute("KStudioReconstruction", "construction_note", "revision 3 baseline: ADAI true openings; right upper double-leaf opening; continuous parapet junction; fine roof joints")
