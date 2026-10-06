# patch_07_walls_solid.rb — 墙面彻底去拼接线：每面外墙改为「整片实体 + 外表面开洞推穿」
# 上一版仍残留窗两侧的短竖线，原因是分段方盒之间留有内部面，围合边有 3 个面无法合并。
# 本版：每面墙一个实体盒 → 在外表面画洞口轮廓 → 反向面法线后推穿墙厚，得到干净洞口。
# 同时：阳台盆栽改为上下两段冠幅并压深绿色。

VT = 200
W  = 10000
D  = 8000
Z_1F = 2980
Z_2F = 6180

def mat_get(model, name)
  model.materials[name]
end

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

# 在指定平面上画洞口轮廓并推穿墙厚
# axis: :y → 面位于 y=face_at，洞口 c0..c1 沿 X；axis: :x → 面位于 x=face_at，洞口 c0..c1 沿 Y
def cut_opening(grp, axis, face_at, c0, c1, z0, z1, depth)
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
  target.reverse!          # 让面法线指向墙内
  target.pushpull(depth.mm)
  target
end

m_white = mat_get(model, 'WHITE_STUCCO')
m_plant = mat_get(model, 'PLANT')
m_pot   = mat_get(model, 'POT')
model.materials['PLANT'].color = Sketchup::Color.new(52, 96, 48) if m_plant

# ---------- 1) 移除待重建的墙面与旧盆栽 ----------
removed = %w[
  Wall_Front_1F Wall_Front_2F Wall_Back_1F Wall_Back_2F Wall_Left_1F Wall_Left_2F
  Balcony_Plant_01_Pot Balcony_Plant_01_Leaf Balcony_Plant_02_Pot Balcony_Plant_02_Leaf
  Balcony_Plant_03_Pot Balcony_Plant_03_Leaf Balcony_Plant_04_Pot Balcony_Plant_04_Leaf
]
removed.each { |n| remove_owned_group.call(n) }

# ---------- 2) 重建墙面：整片实体 + 推穿洞口 ----------
# 正面 1F：门洞 x500-6900, z0-2400
g = root.entities.add_group
g.name = 'Wall_Front_1F'
raw_box(g.entities, 0, 0, 0, W, VT, Z_1F)
cut_opening(g, :y, 0, 500, 6900, 0, 2400, VT)
paint_ents(g.entities, m_white)

# 正面 2F：左窗 x400-3300、右窗 x5500-8000, z3950-5650
g = root.entities.add_group
g.name = 'Wall_Front_2F'
raw_box(g.entities, 0, 0, 3200, W, VT, Z_2F)
cut_opening(g, :y, 0, 400, 3300, 3950, 5650, VT)
cut_opening(g, :y, 0, 5500, 8000, 3950, 5650, VT)
paint_ents(g.entities, m_white)

# 背面 1F：2 樘窗 x2050-3550 / 6450-7950, z900-2400
g = root.entities.add_group
g.name = 'Wall_Back_1F'
raw_box(g.entities, 0, D - VT, 0, W, D, Z_1F)
cut_opening(g, :y, D, 2050, 3550, 900, 2400, VT)
cut_opening(g, :y, D, 6450, 7950, 900, 2400, VT)
paint_ents(g.entities, m_white)

# 背面 2F：z4100-5600
g = root.entities.add_group
g.name = 'Wall_Back_2F'
raw_box(g.entities, 0, D - VT, 3200, W, D, Z_2F)
cut_opening(g, :y, D, 2050, 3550, 4100, 5600, VT)
cut_opening(g, :y, D, 6450, 7950, 4100, 5600, VT)
paint_ents(g.entities, m_white)

# 左面 1F：窄窗 y5050-5750, z600-1950
g = root.entities.add_group
g.name = 'Wall_Left_1F'
raw_box(g.entities, 0, 0, 0, VT, D, Z_1F)
cut_opening(g, :x, 0, 5050, 5750, 600, 1950, VT)
paint_ents(g.entities, m_white)

# 左面 2F：窄窗 y5050-5750, z3800-5150
g = root.entities.add_group
g.name = 'Wall_Left_2F'
raw_box(g.entities, 0, 0, 3200, VT, D, Z_2F)
cut_opening(g, :x, 0, 5050, 5750, 3800, 5150, VT)
paint_ents(g.entities, m_white)

# ---------- 3) 阳台盆栽：上下两段冠幅（更接近图中盆栽轮廓）----------
ZB = 3200
plants = [[700, 1050], [2200, 2550], [3950, 4300], [9100, 9450]]
plants.each_with_index do |px, i|
  n = format('%02d', i + 1)
  pot = root.entities.add_group
  pot.name = "Balcony_Plant_#{n}_Pot"
  raw_box(pot.entities, px[0], -860, ZB, px[1], -510, ZB + 420)
  paint_ents(pot.entities, m_pot)

  l1 = root.entities.add_group
  l1.name = "Balcony_Plant_#{n}_Leaf"
  raw_box(l1.entities, px[0] - 90, -950, ZB + 400, px[1] + 90, -420, ZB + 800)
  paint_ents(l1.entities, m_plant)

  l2 = root.entities.add_group
  l2.name = "Balcony_Plant_#{n}_Leaf2"
  raw_box(l2.entities, px[0] - 30, -900, ZB + 780, px[1] + 30, -470, ZB + 1150)
  paint_ents(l2.entities, m_plant)
end

'walls rebuilt as single solids with punched openings; balcony plants updated'
