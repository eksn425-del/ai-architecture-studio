# Final bounded correction: mask the remaining wall/parapet edge and soften
# roof-tile lines while preserving the approved roof recess and coping height.
W = 10_500.0
D = 8_500.0
ROOF_BASE = 6_150.0
ROOF_TOP = 6_350.0
PARAPET_TOP = 6_850.0

def villa_revision3_point(x, y, z)
  Geom::Point3d.new(x.mm, y.mm, z.mm)
end

def villa_revision3_box(entities, name, x0, y0, z0, x1, y1, z1, material)
  raise "Degenerate box #{name}" if (x1 - x0).abs < 0.1 || (y1 - y0).abs < 0.1 || (z1 - z0).abs < 0.1
  group = entities.add_group
  group.name = name
  face = group.entities.add_face(
    villa_revision3_point(x0, y0, z0), villa_revision3_point(x1, y0, z0),
    villa_revision3_point(x1, y1, z0), villa_revision3_point(x0, y1, z0)
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

def villa_revision3_material(model, name)
  material = model.materials[name]
  raise "Missing expected material #{name}" unless material
  material
end

render_mat = villa_revision3_material(model, "Villa warm white render")
roof_joint_mat = villa_revision3_material(model, "Villa roof tile joints")
roof_joint_mat.color = Sketchup::Color.new(151, 154, 154)

%w[PARAPET_FRONT PARAPET_REAR PARAPET_LEFT PARAPET_RIGHT].each do |name|
  remove_owned_group.call(name)
end
villa_revision3_box(root.entities, "PARAPET_FRONT", 0, -1, ROOF_BASE - 2, W, 200, PARAPET_TOP - 30, render_mat)
villa_revision3_box(root.entities, "PARAPET_REAR", 0, D - 200, ROOF_BASE - 2, W, D + 1, PARAPET_TOP - 30, render_mat)
villa_revision3_box(root.entities, "PARAPET_LEFT", -1, 200, ROOF_BASE - 2, 200, D - 200, PARAPET_TOP - 30, render_mat)
villa_revision3_box(root.entities, "PARAPET_RIGHT", W - 200, 200, ROOF_BASE - 2, W + 1, D - 200, PARAPET_TOP - 30, render_mat)

1.upto(16) { |i| remove_owned_group.call("ROOF_TILE_JOINT_X_#{i}") }
1.upto(13) { |i| remove_owned_group.call("ROOF_TILE_JOINT_Y_#{i}") }
x = 800.0
index = 1
while x < W - 280
  joint = villa_revision3_box(root.entities, "ROOF_TILE_JOINT_X_#{index}", x - 1.5, 280, ROOF_TOP, x + 1.5, D - 280, ROOF_TOP + 1.5, roof_joint_mat)
  joint.entities.grep(Sketchup::Edge).each { |edge| edge.hidden = true }
  x += 600
  index += 1
end
y = 800.0
index = 1
while y < D - 280
  joint = villa_revision3_box(root.entities, "ROOF_TILE_JOINT_Y_#{index}", 280, y - 1.5, ROOF_TOP, W - 280, y + 1.5, ROOF_TOP + 1.5, roof_joint_mat)
  joint.entities.grep(Sketchup::Edge).each { |edge| edge.hidden = true }
  y += 600
  index += 1
end
