# patch_08_walls_fix.rb — 修正推穿方向后重建六面外墙
# 上一版用无条件 reverse! 定方向，二层窗/侧窗/背窗的洞口面法线本就朝内，被反转成朝外 → 推成凸出白块盖住窗。
# 本版按“墙体厚度方向”确定推穿方向：面法线必须与墙内方向一致才 pushpull 正向。

VT = 200
W  = 10000
D  = 8000
Z_1F = 2980
Z_2F = 6180

def raw_box(ents, x0, y0, z0, x1, y1, z1)
  return nil if x1 <= x0 || y1 <= y0 || z1 <= z0
  f = ents.add_face(
    Geom::Point3d.new(x0.mm, y0.mm, z0.mm),
    Geom::Point3d.new(x1.mm, y0.mm, z0.mm),
    Geom::Point3d.new(x1.mm, y1.mm, z0.mm),
    Geom::Point3d.new(x0.mm, y1.mm, z0.mm)
  )
  return nil if f.nil?
  f.reverse! if f.normal.z < 0
  f.pushpull((z1 - z0).mm)
  f
end

def paint_ents(ents, mat)
  ents.grep(Sketchup::Face).each { |f| f.material = mat; f.back_material = mat }
  ents.grep(Sketchup::Group).each { |g| paint_ents(g.entities, mat) }
end

# axis: :y 面在 y=face_at，洞口沿 X；axis: :x 面在 x=face_at，洞口沿 Y
# inner_at: 墙体另一侧坐标（判断“墙内”方向）
def cut_opening(grp, axis, face_at, inner_at, c0, c1, z0, z1, depth)
  ents = grp.entities
  pts = if axis == :y
          [Geom::Point3d.new(c0.mm, face_at.mm, z0.mm),
           Geom::Point3d.new(c1.mm, face_at.mm, z0.mm),
           Geom::Point3d.new(c1.mm, face_at.mm, z1.mm),
           Geom::Point3d.new(c0.mm, face_at.mm, z1.mm)]
        else
          [Geom::Point3d.new(face_at.mm, c0.mm, z0.mm),
           Geom::Point3d.new(face_at.mm, c1.mm, z0.mm),
           Geom::Point3d.new(face_at.mm, c1.mm, z1.mm),
           Geom::Point3d.new(face_at.mm, c0.mm, z1.mm)]
        end
  (0...4).each { |i| ents.add_line(pts[i], pts[(i + 1) % 4]) }

  target = nil
  ents.grep(Sketchup::Face).each do |f|
    bb = f.bounds
    ca = (axis == :y ? bb.min.x : bb.min.y)
    cb = (axis == :y ? bb.max.x : bb.max.y)
    next unless (ca - c0.mm).abs < 1.mm && (cb - c1.mm).abs < 1.mm
    next unless (bb.min.z - z0.mm).abs < 1.mm && (bb.max.z - z1.mm).abs < 1.mm
    target = f
    break
  end
  return nil if target.nil?

  inward = inner_at > face_at ? 1.0 : -1.0
  if axis == :y
    target.reverse! if target.normal.y * inward < 0
  else
    target.reverse! if target.normal.x * inward < 0
  end
  target.pushpull(depth.mm)
  target
end

m_white = model.materials['WHITE_STUCCO']

%w[Wall_Front_1F Wall_Front_2F Wall_Back_1F Wall_Back_2F Wall_Left_1F Wall_Left_2F].each do |n|
  remove_owned_group.call(n)
end

# 正面 1F：门洞 x500-6900, z0-2400（外表面 y=0，墙内 +Y）
g = root.entities.add_group
g.name = 'Wall_Front_1F'
raw_box(g.entities, 0, 0, 0, W, VT, Z_1F)
cut_opening(g, :y, 0, VT, 500, 6900, 0, 2400, VT)
paint_ents(g.entities, m_white)

# 正面 2F：左窗 x400-3300、右窗 x5500-8000, z3950-5650
g = root.entities.add_group
g.name = 'Wall_Front_2F'
raw_box(g.entities, 0, 0, 3200, W, VT, Z_2F)
cut_opening(g, :y, 0, VT, 400, 3300, 3950, 5650, VT)
cut_opening(g, :y, 0, VT, 5500, 8000, 3950, 5650, VT)
paint_ents(g.entities, m_white)

# 背面 1F：2 樘窗（外表面 y=8000，墙内 -Y）
g = root.entities.add_group
g.name = 'Wall_Back_1F'
raw_box(g.entities, 0, D - VT, 0, W, D, Z_1F)
cut_opening(g, :y, D, D - VT, 2050, 3550, 900, 2400, VT)
cut_opening(g, :y, D, D - VT, 6450, 7950, 900, 2400, VT)
paint_ents(g.entities, m_white)

# 背面 2F
g = root.entities.add_group
g.name = 'Wall_Back_2F'
raw_box(g.entities, 0, D - VT, 3200, W, D, Z_2F)
cut_opening(g, :y, D, D - VT, 2050, 3550, 4100, 5600, VT)
cut_opening(g, :y, D, D - VT, 6450, 7950, 4100, 5600, VT)
paint_ents(g.entities, m_white)

# 左面 1F：窄窗 y5050-5750, z600-1950（外表面 x=0，墙内 +X）
g = root.entities.add_group
g.name = 'Wall_Left_1F'
raw_box(g.entities, 0, 0, 0, VT, D, Z_1F)
cut_opening(g, :x, 0, VT, 5050, 5750, 600, 1950, VT)
paint_ents(g.entities, m_white)

# 左面 2F
g = root.entities.add_group
g.name = 'Wall_Left_2F'
raw_box(g.entities, 0, 0, 3200, VT, D, Z_2F)
cut_opening(g, :x, 0, VT, 5050, 5750, 3800, 5150, VT)
paint_ents(g.entities, m_white)

'walls rebuilt with corrected punch direction'
