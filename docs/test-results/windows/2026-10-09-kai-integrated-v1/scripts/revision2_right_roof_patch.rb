# Targeted revision 2: correct only the right facade openings and roof edge.
# All dimensions are millimetres; all new geometry stays inside the owned root.

W = 10_500.0
D = 8_500.0
WALL = 200.0
LEVEL1_TOP = 3_150.0
LEVEL2_BASE = 3_350.0
ROOF_BASE = 6_150.0
ROOF_TOP = 6_350.0
PARAPET_TOP = 6_850.0

def villa_revision2_point(x, y, z)
  Geom::Point3d.new(x.mm, y.mm, z.mm)
end

def villa_revision2_box(entities, name, x0, y0, z0, x1, y1, z1, material)
  raise "Degenerate box #{name}" if (x1 - x0).abs < 0.1 || (y1 - y0).abs < 0.1 || (z1 - z0).abs < 0.1
  group = entities.add_group
  group.name = name
  face = group.entities.add_face(
    villa_revision2_point(x0, y0, z0), villa_revision2_point(x1, y0, z0),
    villa_revision2_point(x1, y1, z0), villa_revision2_point(x0, y1, z0)
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

def villa_revision2_rect(y0, z0, y1, z1)
  [[y0, z0], [y1, z0], [y1, z1], [y0, z1]]
end

def villa_revision2_material(model, name)
  material = model.materials[name]
  raise "Missing expected material #{name}" unless material
  material
end

shell_mat = villa_revision2_material(model, "Villa warm white render")
frame_mat = villa_revision2_material(model, "Villa charcoal aluminum")
glass_mat = villa_revision2_material(model, "Villa clear gray glass")
coping_mat = villa_revision2_material(model, "Villa pale concrete")
roof_joint_mat = villa_revision2_material(model, "Villa roof tile joints")
roof_joint_mat.color = Sketchup::Color.new(145, 149, 149)

# Remove only the two affected right-wall hosts and their six incorrect narrow
# window assemblies. The entry door, canopy and steps remain intact.
remove_owned_group.call("SHELL_RIGHT_GROUND")
remove_owned_group.call("SHELL_RIGHT_UPPER")
1.upto(3) do |i|
  %w[JAMB_FRONT JAMB_REAR HEAD SILL GLASS].each do |part|
    remove_owned_group.call("RIGHT_GROUND_WIN_#{i}_#{part}")
    remove_owned_group.call("RIGHT_UPPER_WIN_#{i}_#{part}")
  end
end

ground_entry = villa_revision2_rect(500, 100, 1_450, 2_350)
ground_result = adai_geometry.profile_with_holes(
  root.entities, "SHELL_RIGHT_GROUND",
  villa_revision2_rect(0, 0, D, LEVEL1_TOP), [ground_entry], WALL, "yz", W - WALL, shell_mat
)
raise "ADAI right ground entry wall failed" if ground_result.nil? || ground_result == false

upper_double = villa_revision2_rect(5_400, 3_850, 7_300, 5_500)
upper_result = adai_geometry.profile_with_holes(
  root.entities, "SHELL_RIGHT_UPPER",
  villa_revision2_rect(0, LEVEL2_BASE, D, ROOF_BASE), [upper_double], WALL, "yz", W - WALL, shell_mat
)
raise "ADAI right upper double-window wall failed" if upper_result.nil? || upper_result == false

# A true 1900 x 1650 mm wall opening with two glazed leaves and a central mullion.
villa_revision2_box(root.entities, "RIGHT_UPPER_DOUBLE_WIN_JAMB_FRONT", 10_380, 5_400, 3_850, 10_535, 5_458, 5_500, frame_mat)
villa_revision2_box(root.entities, "RIGHT_UPPER_DOUBLE_WIN_JAMB_REAR", 10_380, 7_242, 3_850, 10_535, 7_300, 5_500, frame_mat)
villa_revision2_box(root.entities, "RIGHT_UPPER_DOUBLE_WIN_HEAD", 10_380, 5_458, 5_442, 10_535, 7_242, 5_500, frame_mat)
villa_revision2_box(root.entities, "RIGHT_UPPER_DOUBLE_WIN_SILL", 10_380, 5_458, 3_850, 10_535, 7_242, 3_908, frame_mat)
villa_revision2_box(root.entities, "RIGHT_UPPER_DOUBLE_WIN_MULLION", 10_380, 6_300, 3_908, 10_535, 6_400, 5_442, frame_mat)
villa_revision2_box(root.entities, "RIGHT_UPPER_DOUBLE_WIN_GLASS_LEFT", 10_448, 5_458, 3_908, 10_468, 6_300, 5_442, glass_mat)
villa_revision2_box(root.entities, "RIGHT_UPPER_DOUBLE_WIN_GLASS_RIGHT", 10_448, 6_400, 3_908, 10_468, 7_242, 5_442, glass_mat)

# Rebuild only parapet/coping solids. Lower the parapet body to the wall-top
# datum, overlap the exterior by 1 mm to hide the roof-edge gap, and thin the
# coping to 30 mm while retaining the approved 6850 mm overall top.
%w[PARAPET_FRONT PARAPET_REAR PARAPET_LEFT PARAPET_RIGHT
   PARAPET_COPING_FRONT PARAPET_COPING_REAR PARAPET_COPING_LEFT PARAPET_COPING_RIGHT].each do |name|
  remove_owned_group.call(name)
end
villa_revision2_box(root.entities, "PARAPET_FRONT", 0, -1, ROOF_BASE, W, WALL, PARAPET_TOP - 30, shell_mat)
villa_revision2_box(root.entities, "PARAPET_REAR", 0, D - WALL, ROOF_BASE, W, D + 1, PARAPET_TOP - 30, shell_mat)
villa_revision2_box(root.entities, "PARAPET_LEFT", -1, WALL, ROOF_BASE, WALL, D - WALL, PARAPET_TOP - 30, shell_mat)
villa_revision2_box(root.entities, "PARAPET_RIGHT", W - WALL, WALL, ROOF_BASE, W + 1, D - WALL, PARAPET_TOP - 30, shell_mat)
villa_revision2_box(root.entities, "PARAPET_COPING_FRONT", 0, -15, PARAPET_TOP - 30, W, WALL + 15, PARAPET_TOP, coping_mat)
villa_revision2_box(root.entities, "PARAPET_COPING_REAR", 0, D - WALL - 15, PARAPET_TOP - 30, W, D + 15, PARAPET_TOP, coping_mat)
villa_revision2_box(root.entities, "PARAPET_COPING_LEFT", -15, WALL, PARAPET_TOP - 30, WALL + 15, D - WALL, PARAPET_TOP, coping_mat)
villa_revision2_box(root.entities, "PARAPET_COPING_RIGHT", W - WALL - 15, WALL, PARAPET_TOP - 30, W + 15, D - WALL, PARAPET_TOP, coping_mat)

# Replace the 10 mm dark relief bars with 3 mm light gray joints at 600 mm pitch.
1.upto(16) { |i| remove_owned_group.call("ROOF_TILE_JOINT_X_#{i}") }
1.upto(13) { |i| remove_owned_group.call("ROOF_TILE_JOINT_Y_#{i}") }
x = 800.0
index = 1
while x < W - 280
  villa_revision2_box(root.entities, "ROOF_TILE_JOINT_X_#{index}", x - 1.5, 280, ROOF_TOP, x + 1.5, D - 280, ROOF_TOP + 1.5, roof_joint_mat)
  x += 600
  index += 1
end
y = 800.0
index = 1
while y < D - 280
  villa_revision2_box(root.entities, "ROOF_TILE_JOINT_Y_#{index}", 280, y - 1.5, ROOF_TOP, W - 280, y + 1.5, ROOF_TOP + 1.5, roof_joint_mat)
  y += 600
  index += 1
end

root.set_attribute("KStudioReconstruction", "construction_note", "revision 2: right side true door and double-leaf window; continuous parapet-to-wall junction; fine roof joints")
