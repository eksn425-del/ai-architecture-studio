# patch_06_walls_clean.rb — 消除墙面因分段建模产生的横竖拼接线 + 补阳台座椅与盆栽
# 做法：把每面外墙的墙垛/窗下墙/窗上墙合并进同一个组（面在同一实体集合内），
#       再删除"两侧面共面"的内部边，SketchUp 会自动把共面墙面合并为整片，
#       只保留真实洞口边、墙体轮廓与窗框。
# 仅重建 6 个墙面组 + 新增阳台陈设，其余构件（屋面、格栅、门窗、栏板、场地、室内）保持不变。

VT = 200
W  = 10000
D  = 8000
Z_1F = 2980
Z_2F = 6180

def mat_get(model, name)
  model.materials[name]
end

# 直接往实体集合里放方盒（不做子组，便于后续共面合并）
def raw_box(ents, x0, y0, z0, x1, y1, z1, mat)
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

# 删除两侧面共面的内部边：共面 → 面自动合并，拼接线消失；垂直相交的真实轮廓/洞口边保留
def merge_coplanar(grp)
  ents = grp.entities
  guard = 0
  loop do
    guard += 1
    break if guard > 40
    removed = 0
    ents.grep(Sketchup::Edge).each do |e|
      next unless e.valid?
      fs = e.faces
      next unless fs.size == 2
      n0 = fs[0].normal
      n1 = fs[1].normal
      next if n0.length < 0.001 || n1.length < 0.001
      next if n0.dot(n1) < 0.999
      e.erase!
      removed += 1
    end
    break if removed.zero?
  end
end

def solid_box(parent, name, x0, y0, z0, x1, y1, z1, mat)
  g = parent.entities.add_group
  g.name = name
  raw_box(g.entities, x0, y0, z0, x1, y1, z1, mat)
  paint_ents(g.entities, mat)
  g
end

m_white = mat_get(model, 'WHITE_STUCCO')
m_sofa  = mat_get(model, 'FABRIC')
m_pot   = mat_get(model, 'POT')
m_plant = mat_get(model, 'PLANT')
m_furn  = mat_get(model, 'FURN_WOOD')

# ---------- 1) 移除旧的分段墙面 ----------
old = %w[
  Wall_Front_1F_PierL Wall_Front_1F_DoorHead Wall_Front_1F_PierR Wall_Front_1F_GrilleZone
  Wall_Front_2F_PierL Wall_Front_2F_WinA_low Wall_Front_2F_WinA_high Wall_Front_2F_PierM
  Wall_Front_2F_WinB_low Wall_Front_2F_WinB_high Wall_Front_2F_PierR Wall_Front_2F_GrilleZone
  Wall_Back_1F_A Wall_Back_1F_B_low Wall_Back_1F_B_high Wall_Back_1F_C
  Wall_Back_1F_D_low Wall_Back_1F_D_high Wall_Back_1F_E
  Wall_Back_2F_A Wall_Back_2F_B_low Wall_Back_2F_B_high Wall_Back_2F_C
  Wall_Back_2F_D_low Wall_Back_2F_D_high Wall_Back_2F_E
  Wall_Left_1F_A Wall_Left_1F_B_low Wall_Left_1F_B_high Wall_Left_1F_C
  Wall_Left_2F_A Wall_Left_2F_B_low Wall_Left_2F_B_high Wall_Left_2F_C
]
old.each { |n| remove_owned_group.call(n) }

# ---------- 2) 重建为整片合并墙 ----------
# 正面 1F：门洞 x500-6900, z0-2400
gf1 = root.entities.add_group
gf1.name = 'Wall_Front_1F'
raw_box(gf1.entities, 0, 0, 0, 500, VT, Z_1F, m_white)
raw_box(gf1.entities, 500, 0, 2400, 6900, VT, Z_1F, m_white)
raw_box(gf1.entities, 6900, 0, 0, 8600, VT, Z_1F, m_white)
raw_box(gf1.entities, 8600, 0, 0, W, VT, Z_1F, m_white)
merge_coplanar(gf1)
paint_ents(gf1.entities, m_white)

# 正面 2F：左窗 x400-3300 / 右窗 x5500-8000, z3950-5650
gf2 = root.entities.add_group
gf2.name = 'Wall_Front_2F'
raw_box(gf2.entities, 0, 0, 3200, 400, VT, Z_2F, m_white)
raw_box(gf2.entities, 400, 0, 3200, 3300, VT, 3950, m_white)
raw_box(gf2.entities, 400, 0, 5650, 3300, VT, Z_2F, m_white)
raw_box(gf2.entities, 3300, 0, 3200, 5500, VT, Z_2F, m_white)
raw_box(gf2.entities, 5500, 0, 3200, 8000, VT, 3950, m_white)
raw_box(gf2.entities, 5500, 0, 5650, 8000, VT, Z_2F, m_white)
raw_box(gf2.entities, 8000, 0, 3200, 8600, VT, Z_2F, m_white)
raw_box(gf2.entities, 8600, 0, 3200, W, VT, Z_2F, m_white)
merge_coplanar(gf2)
paint_ents(gf2.entities, m_white)

# 背面 1F：2 樘窗 x2050-3550 / 6450-7950, 窗台 900, 顶 2400
gb1 = root.entities.add_group
gb1.name = 'Wall_Back_1F'
raw_box(gb1.entities, 0, D - VT, 0, 2050, D, Z_1F, m_white)
raw_box(gb1.entities, 2050, D - VT, 0, 3550, D, 900, m_white)
raw_box(gb1.entities, 2050, D - VT, 2400, 3550, D, Z_1F, m_white)
raw_box(gb1.entities, 3550, D - VT, 0, 6450, D, Z_1F, m_white)
raw_box(gb1.entities, 6450, D - VT, 0, 7950, D, 900, m_white)
raw_box(gb1.entities, 6450, D - VT, 2400, 7950, D, Z_1F, m_white)
raw_box(gb1.entities, 7950, D - VT, 0, W, D, Z_1F, m_white)
merge_coplanar(gb1)
paint_ents(gb1.entities, m_white)

# 背面 2F：窗台 4100, 顶 5600
gb2 = root.entities.add_group
gb2.name = 'Wall_Back_2F'
raw_box(gb2.entities, 0, D - VT, 3200, 2050, D, Z_2F, m_white)
raw_box(gb2.entities, 2050, D - VT, 3200, 3550, D, 4100, m_white)
raw_box(gb2.entities, 2050, D - VT, 5600, 3550, D, Z_2F, m_white)
raw_box(gb2.entities, 3550, D - VT, 3200, 6450, D, Z_2F, m_white)
raw_box(gb2.entities, 6450, D - VT, 3200, 7950, D, 4100, m_white)
raw_box(gb2.entities, 6450, D - VT, 5600, 7950, D, Z_2F, m_white)
raw_box(gb2.entities, 7950, D - VT, 3200, W, D, Z_2F, m_white)
merge_coplanar(gb2)
paint_ents(gb2.entities, m_white)

# 左面 1F：窄窗 y5050-5750, z600-1950
gl1 = root.entities.add_group
gl1.name = 'Wall_Left_1F'
raw_box(gl1.entities, 0, 0, 0, VT, 5050, Z_1F, m_white)
raw_box(gl1.entities, 0, 5050, 0, VT, 5750, 600, m_white)
raw_box(gl1.entities, 0, 5050, 1950, VT, 5750, Z_1F, m_white)
raw_box(gl1.entities, 0, 5750, 0, VT, D, Z_1F, m_white)
merge_coplanar(gl1)
paint_ents(gl1.entities, m_white)

# 左面 2F：窄窗 z3800-5150
gl2 = root.entities.add_group
gl2.name = 'Wall_Left_2F'
raw_box(gl2.entities, 0, 0, 3200, VT, 5050, Z_2F, m_white)
raw_box(gl2.entities, 0, 5050, 3200, VT, 5750, 3800, m_white)
raw_box(gl2.entities, 0, 5050, 5150, VT, 5750, Z_2F, m_white)
raw_box(gl2.entities, 0, 5750, 3200, VT, D, Z_2F, m_white)
merge_coplanar(gl2)
paint_ents(gl2.entities, m_white)

# ---------- 3) 阳台陈设：座椅 + 盆栽（按参考图）----------
ZB = 3200  # 阳台板面

solid_box(root, 'Balcony_Lounge_Seat', 6200, -820, ZB, 7700, -330, ZB + 460, m_sofa)
solid_box(root, 'Balcony_Lounge_Back', 6200, -420, ZB, 7700, -300, ZB + 980, m_sofa)
solid_box(root, 'Balcony_Lounge_ArmL', 6100, -820, ZB, 6200, -300, ZB + 620, m_sofa)
solid_box(root, 'Balcony_Lounge_ArmR', 7700, -820, ZB, 7800, -300, ZB + 620, m_sofa)
solid_box(root, 'Balcony_Table', 5450, -720, ZB, 5900, -330, ZB + 380, m_furn)

plants = [[700, 1050], [2200, 2550], [3950, 4300], [9100, 9450]]
plants.each_with_index do |px, i|
  n = format('%02d', i + 1)
  solid_box(root, "Balcony_Plant_#{n}_Pot", px[0], -860, ZB, px[1], -510, ZB + 420, m_pot)
  solid_box(root, "Balcony_Plant_#{n}_Leaf", px[0] - 60, -920, ZB + 420, px[1] + 60, -450, ZB + 1120, m_plant)
end

'walls merged + balcony furniture added'
