# =====================================================================
# Quality v1 六视图 1008 — 别墅重建持久基线脚本（V5）
# 依据：reference/a6b9e456b5-villa-six-view-sheet.png（2x3 六视角，同一栋）
# 坐标（全栋统一，单位 m）：X 0..10 前(阳台)立面宽；Y 0..8 进深；Z 0 室外地坪
# 标高：L1 +0.30 / L2 +3.50 / 外墙顶 +6.70 / 女儿墙顶 +7.20 / 压顶 +7.26
# 开口（锁定，不额外增加）：
#   前立面 L1 落地玻璃 5.40x2.60 | L2 推拉门 x2 2.10x2.20（墙垛 1.00）
#   东立面 L1 门 1.10x2.30 + 雨篷 | L2 宽窗 1 樘 2.40x1.40
#   背立面 L1/L2 各 3 樘 1.00x1.20 ；西立面 L1/L2 各 1 樘 0.60x1.10
# V5 修正：外墙改用"分段实体墙 + 自动隐藏共面拼缝边"（洞口为真实空缺），
#         避免实体内挖洞在 SketchUp 中不可靠的问题。
# =====================================================================

Z_GRADE   = 0.00
Z_L1      = 0.30
Z_L2      = 3.50
Z_ROOF_B  = 6.40
Z_WALL_T  = 6.70
Z_PAR_TOP = 7.20
Z_CAP_TOP = 7.26

T_WALL = 0.30

GLZ_X1 = 1.00
GLZ_X2 = 6.40
GLZ_Z1 = Z_L1
GLZ_Z2 = 2.90

SLD_A = [2.00, 4.10]
SLD_B = [5.10, 7.20]
SLD_Z1 = Z_L2
SLD_Z2 = 5.70

def vpt(x, y, z)
  Geom::Point3d.new(x.m, y.m, z.m)
end

def vmat(model, key, rgb, alpha = nil)
  m = model.materials[key]
  m = model.materials.add(key) unless m
  m.color = Sketchup::Color.new(rgb[0], rgb[1], rgb[2])
  m.alpha = alpha if alpha
  m
end

# 矩形实体；挤出后把起始（底）面翻转为朝下，法线一致朝外
def vsolid(root, name, x1, x2, y1, y2, z1, z2, material = nil)
  x1, x2 = [x1, x2].minmax
  y1, y2 = [y1, y2].minmax
  z1, z2 = [z1, z2].minmax
  return nil if (x2 - x1) < 1e-6 || (y2 - y1) < 1e-6 || (z2 - z1) < 1e-6
  g = root.entities.add_group
  g.name = name
  f = g.entities.add_face(vpt(x1, y1, z1), vpt(x2, y1, z1), vpt(x2, y2, z1), vpt(x1, y2, z1))
  if f && f.valid?
    n = f.normal
    h = (z2 - z1).m
    d = (n.z >= 0.0) ? h : -h
    sc = f.bounds.center
    f.pushpull(d)
    g.entities.grep(Sketchup::Face).each do |fa|
      next unless fa.valid?
      n2 = fa.normal
      next if n2.length < 0.001 || !n2.parallel?(n)
      fa.reverse! if (fa.bounds.center - sc).dot(n) < -1e-6
    end
  end
  g.material = material if material
  g
rescue => e
  puts "SOLID FAIL #{name}: #{e.message}"
  nil
end

def vcyl(root, name, cx, cy, z1, z2, r, material = nil, segs = 20)
  g = root.entities.add_group
  g.name = name
  cir = g.entities.add_circle(vpt(cx, cy, z1), Geom::Vector3d.new(0, 0, 1), r.m, segs)
  f = g.entities.add_face(cir)
  if f && f.valid?
    n = f.normal
    h = (z2 - z1).m
    d = (n.z >= 0.0) ? h : -h
    f.pushpull(d)
  end
  g.material = material if material
  g
rescue => e
  puts "CYL FAIL #{name}: #{e.message}"
  nil
end

# 带洞口的实体分段：返回 [[u1,u2,v1,v2], ...]（洞口处无实体）
def vrects_with_holes(u0, u1, v0, v1, holes)
  us = ([u0, u1] + holes.flat_map { |h| [h[0], h[1]] }).uniq.sort
  bands = []
  us.each_cons(2) do |a, b|
    next if (b - a) < 1e-6
    cover = holes.select { |h| h[0] <= a + 1e-9 && h[1] >= b - 1e-9 }.map { |h| [h[2], h[3]] }
    segs = [[v0, v1]]
    cover.each do |cv|
      segs = segs.flat_map do |s|
        if cv[1] <= s[0] + 1e-9 || cv[0] >= s[1] - 1e-9
          [s]
        else
          r = []
          r << [s[0], cv[0]] if cv[0] > s[0] + 1e-9
          r << [cv[1], s[1]] if cv[1] < s[1] - 1e-9
          r
        end
      end
    end
    bands << [a, b, segs]
  end
  merged = []
  bands.each do |bd|
    if !merged.empty? && merged.last[2] == bd[2] && (merged.last[1] - bd[0]).abs < 1e-9
      merged.last[1] = bd[1]
    else
      merged << [bd[0], bd[1], bd[2]]
    end
  end
  out = []
  merged.each { |bd| bd[2].each { |s| out << [bd[0], bd[1], s[0], s[1]] } }
  out
end

# 分段实体造墙 + 隐藏共面拼缝边（同一位置/方向出现两次的边即拼缝）
def vwall_solid(root, name, axis, u0, u1, to, ti, z0, z1, holes, material)
  holder = root.entities.add_group
  holder.name = name
  segs = vrects_with_holes(u0, u1, z0, z1, holes)
  segs.each_with_index do |r, i|
    nm = "#{name}_SEG#{format('%02d', i + 1)}"
    if axis == :x
      vsolid(holder, nm, r[0], r[1], to, ti, r[2], r[3], material)
    else
      vsolid(holder, nm, to, ti, r[0], r[1], r[2], r[3], material)
    end
  end
  keys = Hash.new { |h, k| h[k] = [] }
  holder.entities.grep(Sketchup::Group).each do |sg|
    sg.entities.grep(Sketchup::Edge).each do |e|
      a = e.start.position
      b = e.end.position
      dir = Geom::Vector3d.new(b.x - a.x, b.y - a.y, b.z - a.z)
      next if dir.length < 0.0001
      dir.normalize!
      key = [((a.x + b.x) / 2.0).to_mm.round, ((a.y + b.y) / 2.0).to_mm.round, ((a.z + b.z) / 2.0).to_mm.round,
             dir.x.abs.round(3), dir.y.abs.round(3), dir.z.abs.round(3)]
      keys[key] << e
    end
  end
  hidden = 0
  keys.each_value do |list|
    next if list.length < 2
    list.each do |e|
      e.hidden = true unless e.hidden?
      hidden += 1
    end
  end
  puts format('WALL %-11s segs=%2d thick=%dmm hidden_edges=%d', name, segs.length,
              (ti - to).abs * 1000, hidden)
  holder
rescue => e
  puts "WALL FAIL #{name}: #{e.message}"
  nil
end

def vcomp(model, name)
  d = model.definitions[name]
  return d if d && d.entities.length > 0
  d || model.definitions.add(name)
end

MAT = {}
MAT[:wall]    = vmat(model, 'MAT_RENDER_WHITE',   [236, 235, 230])
MAT[:plinth]  = vmat(model, 'MAT_BASE_STONE',     [176, 176, 172])
MAT[:wood]    = vmat(model, 'MAT_WOOD_OAK',       [196, 148, 90])
MAT[:woodsub] = vmat(model, 'MAT_WOOD_SUBSTRATE', [86, 70, 58])
MAT[:frame]   = vmat(model, 'MAT_ALU_DARK',       [52, 54, 56])
MAT[:glass]   = vmat(model, 'MAT_GLASS',          [186, 210, 218], 0.30)
MAT[:roof]    = vmat(model, 'MAT_ROOF_MEMBRANE',  [198, 199, 195])
MAT[:cap]     = vmat(model, 'MAT_PARAPET_CAP',    [244, 244, 241])
MAT[:paving]  = vmat(model, 'MAT_PAVING_SLAB',    [180, 182, 180])
MAT[:lawn]    = vmat(model, 'MAT_LAWN',           [124, 160, 94])
MAT[:metal]   = vmat(model, 'MAT_METAL_RAIL',     [150, 152, 155])
MAT[:floor]   = vmat(model, 'MAT_FLOOR_INT',      [214, 206, 192])
MAT[:sofa]    = vmat(model, 'MAT_SOFA_FABRIC',    [206, 203, 196])
MAT[:furnw]   = vmat(model, 'MAT_FURN_WOOD',      [152, 112, 74])
MAT[:plant]   = vmat(model, 'MAT_PLANT_GREEN',    [92, 132, 76])
MAT[:pot]     = vmat(model, 'MAT_POT',            [186, 182, 176])
MAT[:art]     = vmat(model, 'MAT_ART',            [86, 92, 100])
MAT[:curtain] = vmat(model, 'MAT_CURTAIN',        [228, 224, 214])

model.definitions.to_a.each do |d|
  next unless d.name.to_s.start_with?('MOD_')
  next if d.count_instances > 0
  begin
    model.definitions.remove(d)
  rescue => e
    puts "def cleanup skip #{d.name}: #{e.message}"
  end
end

root.name = 'VILLA_QV1_1008'

# =====================================================================
# 1. 场地
# =====================================================================
vsolid(root, 'SITE_LAWN', -14, 24, -14, 24, -0.10, 0.00, MAT[:lawn])
vsolid(root, 'SITE_PAVING_FRONT', -3.0, 13.0, -3.0, 0.00, 0.00, 0.03, MAT[:paving])
vsolid(root, 'SITE_PAVING_EAST',  10.00, 13.0,  0.00, 8.60, 0.00, 0.03, MAT[:paving])
vsolid(root, 'SITE_PAVING_REAR',  -1.20, 11.20, 8.00, 9.20, 0.00, 0.03, MAT[:paving])
vsolid(root, 'SITE_PAVING_WEST',  -1.20, 0.00,  0.00, 8.00, 0.00, 0.03, MAT[:paving])
vsolid(root, 'SITE_PAVING_PATH',  13.00, 20.00, 1.20, 2.80, 0.00, 0.03, MAT[:paving])

# =====================================================================
# 2. 楼板 / 屋面板 / 勒脚（内缩，避免与外墙面共面）
# =====================================================================
vsolid(root, 'SLAB_L1_FLOOR', 0.15, 9.85, 0.15, 7.85, 0.00, Z_L1, MAT[:floor])
vsolid(root, 'SLAB_L2_FLOOR', 0.35, 9.65, 0.35, 7.65, 3.20, Z_L2, MAT[:wall])
vsolid(root, 'ROOF_SLAB',     0.05, 9.95, 0.05, 7.95, Z_ROOF_B, Z_WALL_T, MAT[:roof])

vsolid(root, 'PLINTH_FRONT', -0.02, 10.02, -0.05, 0.00, 0.00, Z_L1, MAT[:plinth])
vsolid(root, 'PLINTH_EAST',  10.00, 10.05, -0.02, 8.02, 0.00, Z_L1, MAT[:plinth])
vsolid(root, 'PLINTH_REAR',  -0.02, 10.02, 8.00, 8.05, 0.00, Z_L1, MAT[:plinth])
vsolid(root, 'PLINTH_WEST',  -0.05, 0.00, -0.02, 8.02, 0.00, Z_L1, MAT[:plinth])

# =====================================================================
# 3. 外墙（分段实体，洞口真实）
# =====================================================================
front_holes = [
  [GLZ_X1, GLZ_X2, GLZ_Z1, GLZ_Z2],
  [SLD_A[0], SLD_A[1], SLD_Z1, SLD_Z2],
  [SLD_B[0], SLD_B[1], SLD_Z1, SLD_Z2]
]
vwall_solid(root, 'WALL_FRONT', :x, 0.00, 10.00, 0.00, T_WALL, Z_GRADE, Z_WALL_T, front_holes, MAT[:wall])

rear_holes = []
[2.0, 5.0, 8.0].each do |cx|
  rear_holes << [cx - 0.5, cx + 0.5, 1.20, 2.40]
  rear_holes << [cx - 0.5, cx + 0.5, 4.40, 5.60]
end
vwall_solid(root, 'WALL_REAR', :x, 0.00, 10.00, 7.70, 8.00, Z_GRADE, Z_WALL_T, rear_holes, MAT[:wall])

west_holes = [
  [3.30, 3.90, 1.30, 2.40],
  [3.30, 3.90, 4.40, 5.50]
]
vwall_solid(root, 'WALL_WEST', :y, 0.00, 8.00, 0.00, T_WALL, Z_GRADE, Z_WALL_T, west_holes, MAT[:wall])

east_holes = [
  [1.20, 2.30, Z_L1, 2.60],
  [2.00, 4.40, 4.30, 5.70]
]
vwall_solid(root, 'WALL_EAST', :y, 0.00, 8.00, 9.70, 10.00, Z_GRADE, Z_WALL_T, east_holes, MAT[:wall])

# =====================================================================
# 4. 女儿墙 + 压顶
# =====================================================================
vsolid(root, 'PARAPET_FRONT', 0.00, 10.00, 0.00, 0.30, Z_WALL_T, Z_PAR_TOP, MAT[:wall])
vsolid(root, 'PARAPET_REAR',  0.00, 10.00, 7.70, 8.00, Z_WALL_T, Z_PAR_TOP, MAT[:wall])
vsolid(root, 'PARAPET_WEST',  0.00, 0.30, 0.00, 8.00, Z_WALL_T, Z_PAR_TOP, MAT[:wall])
vsolid(root, 'PARAPET_EAST',  9.70, 10.00, 0.00, 8.00, Z_WALL_T, Z_PAR_TOP, MAT[:wall])
vsolid(root, 'PARAPET_CAP_FRONT', -0.02, 10.02, -0.03, 0.33, Z_PAR_TOP, Z_CAP_TOP, MAT[:cap])
vsolid(root, 'PARAPET_CAP_REAR',  -0.02, 10.02, 7.67, 8.03, Z_PAR_TOP, Z_CAP_TOP, MAT[:cap])
vsolid(root, 'PARAPET_CAP_WEST',  -0.03, 0.33, -0.02, 8.02, Z_PAR_TOP, Z_CAP_TOP, MAT[:cap])
vsolid(root, 'PARAPET_CAP_EAST',  9.67, 10.03, -0.02, 8.02, Z_PAR_TOP, Z_CAP_TOP, MAT[:cap])

# =====================================================================
# 5. 前立面 L1 落地玻璃
# =====================================================================
gx1, gx2, gz1, gz2 = GLZ_X1, GLZ_X2, GLZ_Z1, GLZ_Z2
fy1, fy2 = 0.10, 0.20
vsolid(root, 'OPEN_FRONT_L1_GLAZING_THRESHOLD', gx1, gx2, fy1, fy2, gz1, gz1 + 0.06, MAT[:frame])
vsolid(root, 'OPEN_FRONT_L1_GLAZING_HEAD',      gx1, gx2, fy1, fy2, gz2 - 0.06, gz2, MAT[:frame])
vsolid(root, 'OPEN_FRONT_L1_GLAZING_JAMB_W', gx1, gx1 + 0.06, fy1, fy2, gz1, gz2, MAT[:frame])
vsolid(root, 'OPEN_FRONT_L1_GLAZING_JAMB_E', gx2 - 0.06, gx2, fy1, fy2, gz1, gz2, MAT[:frame])
vsolid(root, 'OPEN_FRONT_L1_GLAZING_MULLION_1', 2.80, 2.86, fy1, fy2, gz1, gz2, MAT[:frame])
vsolid(root, 'OPEN_FRONT_L1_GLAZING_MULLION_2', 4.60, 4.66, fy1, fy2, gz1, gz2, MAT[:frame])
[[1.06, 2.80], [2.86, 4.60], [4.66, 6.34]].each_with_index do |p, i|
  vsolid(root, "OPEN_FRONT_L1_GLAZING_PANE_#{i + 1}", p[0], p[1], 0.144, 0.156, gz1 + 0.06, gz2 - 0.06, MAT[:glass])
end

# =====================================================================
# 6. 阳台
# =====================================================================
vsolid(root, 'BALCONY_SLAB', 1.30, 8.50, -1.20, T_WALL, 3.25, Z_L2, MAT[:wall])

RY0 = -1.20
SHOE_Z2 = Z_L2 + 0.08
RAIL_Z1 = SHOE_Z2
RAIL_Z2 = Z_L2 + 0.94
TOP_Z2  = Z_L2 + 1.00

vsolid(root, 'RAILING_SHOE_FRONT', 1.30, 8.50, RY0 + 0.03, RY0 + 0.09, Z_L2, SHOE_Z2, MAT[:frame])
vsolid(root, 'RAILING_TOP_FRONT', 1.30, 8.50, RY0 + 0.035, RY0 + 0.085, RAIL_Z2, TOP_Z2, MAT[:metal])
4.times do |i|
  x1 = 1.30 + 0.04 + i * 1.79
  x2 = x1 + 1.71
  next if x2 > 8.50
  vsolid(root, "RAILING_GLASS_FRONT_#{i + 1}", x1, x2, RY0 + 0.054, RY0 + 0.066, RAIL_Z1, RAIL_Z2, MAT[:glass])
end
5.times do |i|
  px = 1.30 + 0.02 + i * 1.79
  px = 8.46 if px > 8.46
  vsolid(root, "RAILING_POST_FRONT_#{i + 1}", px, px + 0.04, RY0 + 0.035, RY0 + 0.085, Z_L2, RAIL_Z2, MAT[:metal])
end
vsolid(root, 'RAILING_SHOE_RETURN_E', 8.44, 8.50, RY0, 0.00, Z_L2, SHOE_Z2, MAT[:frame])
vsolid(root, 'RAILING_TOP_RETURN_E',  8.445, 8.495, RY0, 0.00, RAIL_Z2, TOP_Z2, MAT[:metal])
vsolid(root, 'RAILING_GLASS_RETURN_E', 8.464, 8.476, RY0 + 0.06, -0.06, RAIL_Z1, RAIL_Z2, MAT[:glass])
vsolid(root, 'RAILING_SHOE_RETURN_W', 1.30, 1.36, RY0, 0.00, Z_L2, SHOE_Z2, MAT[:frame])
vsolid(root, 'RAILING_TOP_RETURN_W',  1.305, 1.355, RY0, 0.00, RAIL_Z2, TOP_Z2, MAT[:metal])
vsolid(root, 'RAILING_GLASS_RETURN_W', 1.324, 1.336, RY0 + 0.06, -0.06, RAIL_Z1, RAIL_Z2, MAT[:glass])

[[1.50, 2.00], [7.80, 8.30]].each_with_index do |p, i|
  x1, x2 = p
  vsolid(root, "BALCONY_PLANTER_#{i + 1}", x1, x2, -1.05, -0.35, Z_L2, Z_L2 + 0.40, MAT[:plinth])
  vcyl(root, "BALCONY_PLANT_#{i + 1}_A", (x1 + x2) / 2.0, -0.85, Z_L2 + 0.35, Z_L2 + 0.95, 0.22, MAT[:plant], 14)
  vcyl(root, "BALCONY_PLANT_#{i + 1}_B", (x1 + x2) / 2.0 - 0.10, -0.60, Z_L2 + 0.35, Z_L2 + 0.78, 0.16, MAT[:plant], 12)
end

vsolid(root, 'BALCONY_SEAT_BASE', 4.60, 5.70, -1.00, -0.42, Z_L2, Z_L2 + 0.40, MAT[:sofa])
vsolid(root, 'BALCONY_SEAT_BACK', 4.60, 5.70, -0.48, -0.42, Z_L2 + 0.40, Z_L2 + 0.78, MAT[:sofa])
vsolid(root, 'BALCONY_SEAT_CUSHION', 4.66, 5.64, -0.99, -0.50, Z_L2 + 0.40, Z_L2 + 0.52, MAT[:curtain])

# =====================================================================
# 7. L2 推拉门
# =====================================================================
[SLD_A, SLD_B].each_with_index do |p, i|
  x1, x2 = p
  tag = i.zero? ? 'A' : 'B'
  vsolid(root, "DOOR_SLIDER_L2_#{tag}_THRESHOLD", x1, x2, 0.10, 0.20, Z_L2, Z_L2 + 0.06, MAT[:frame])
  vsolid(root, "DOOR_SLIDER_L2_#{tag}_HEAD", x1, x2, 0.10, 0.20, SLD_Z2 - 0.06, SLD_Z2, MAT[:frame])
  vsolid(root, "DOOR_SLIDER_L2_#{tag}_JAMB_W", x1, x1 + 0.06, 0.10, 0.20, Z_L2, SLD_Z2, MAT[:frame])
  vsolid(root, "DOOR_SLIDER_L2_#{tag}_JAMB_E", x2 - 0.06, x2, 0.10, 0.20, Z_L2, SLD_Z2, MAT[:frame])
  vsolid(root, "DOOR_SLIDER_L2_#{tag}_MULLION", (x1 + x2) / 2.0 - 0.025, (x1 + x2) / 2.0 + 0.025, 0.10, 0.20, Z_L2, SLD_Z2, MAT[:frame])
  vsolid(root, "DOOR_SLIDER_L2_#{tag}_PANE_W", x1 + 0.06, (x1 + x2) / 2.0 - 0.025, 0.144, 0.156, Z_L2 + 0.06, SLD_Z2 - 0.06, MAT[:glass])
  vsolid(root, "DOOR_SLIDER_L2_#{tag}_PANE_E", (x1 + x2) / 2.0 + 0.025, x2 - 0.06, 0.144, 0.156, Z_L2 + 0.06, SLD_Z2 - 0.06, MAT[:glass])
end

# =====================================================================
# 8. 背立面窗 x6（组件实例）
# =====================================================================
win_def = vcomp(model, 'MOD_WIN_REAR_100x120_V5')
if win_def.entities.length == 0
  vsolid(win_def, 'FRAME_SILL',  0.00, 1.00, 7.79, 7.91, 0.00, 0.06, MAT[:frame])
  vsolid(win_def, 'FRAME_HEAD',  0.00, 1.00, 7.79, 7.91, 1.14, 1.20, MAT[:frame])
  vsolid(win_def, 'FRAME_JAMB_W', 0.00, 0.06, 7.79, 7.91, 0.00, 1.20, MAT[:frame])
  vsolid(win_def, 'FRAME_JAMB_E', 0.94, 1.00, 7.79, 7.91, 0.00, 1.20, MAT[:frame])
  vsolid(win_def, 'GLASS',        0.06, 0.94, 7.844, 7.856, 0.06, 1.14, MAT[:glass])
end
wi = 0
[[1.50, 1.20], [4.50, 1.20], [7.50, 1.20], [1.50, 4.40], [4.50, 4.40], [7.50, 4.40]].each do |x, z|
  wi += 1
  inst = root.entities.add_instance(win_def, Geom::Transformation.new(vpt(x, 0, z)))
  inst.name = "WIN_REAR_#{format('%02d', wi)}"
end

# =====================================================================
# 9. 西立面窄窗 x2
# =====================================================================
[[1.30, 2.40, 'L1'], [4.40, 5.50, 'L2']].each do |z1, z2, tag|
  fy1, fy2 = 0.10, 0.20
  vsolid(root, "WIN_WEST_#{tag}_SILL", fy1, fy2, 3.30, 3.90, z1, z1 + 0.05, MAT[:frame])
  vsolid(root, "WIN_WEST_#{tag}_HEAD", fy1, fy2, 3.30, 3.90, z2 - 0.05, z2, MAT[:frame])
  vsolid(root, "WIN_WEST_#{tag}_JAMB_N", fy1, fy2, 3.30, 3.36, z1, z2, MAT[:frame])
  vsolid(root, "WIN_WEST_#{tag}_JAMB_S", fy1, fy2, 3.84, 3.90, z1, z2, MAT[:frame])
  vsolid(root, "WIN_WEST_#{tag}_GLASS", 0.144, 0.156, 3.36, 3.84, z1 + 0.05, z2 - 0.05, MAT[:glass])
end

# =====================================================================
# 10. 东立面：入口门 + 雨篷 + 台阶 + 二层宽窗
# =====================================================================
vsolid(root, 'DOOR_ENTRY_JAMB_N', 9.75, 9.85, 1.20, 1.26, Z_L1, 2.60, MAT[:frame])
vsolid(root, 'DOOR_ENTRY_JAMB_S', 9.75, 9.85, 2.24, 2.30, Z_L1, 2.60, MAT[:frame])
vsolid(root, 'DOOR_ENTRY_HEAD',   9.75, 9.85, 1.20, 2.30, 2.54, 2.60, MAT[:frame])
vsolid(root, 'DOOR_ENTRY_PANEL',  9.77, 9.82, 1.26, 2.24, Z_L1, 2.54, MAT[:frame])
vsolid(root, 'DOOR_ENTRY_HANDLE', 9.70, 9.76, 1.32, 1.36, 1.05, 1.35, MAT[:metal])

vsolid(root, 'CANOPY_ENTRY', 9.90, 10.95, 0.95, 2.85, 2.60, 2.75, MAT[:cap])

vsolid(root, 'STEP_ENTRY_1', 10.00, 10.45, 1.05, 2.75, 0.03, 0.30, MAT[:plinth])
vsolid(root, 'STEP_ENTRY_2', 10.45, 10.90, 1.05, 2.75, 0.03, 0.16, MAT[:plinth])

vsolid(root, 'WIN_EAST_L2_SILL', 9.79, 9.91, 2.00, 4.40, 4.30, 4.36, MAT[:frame])
vsolid(root, 'WIN_EAST_L2_HEAD', 9.79, 9.91, 2.00, 4.40, 5.64, 5.70, MAT[:frame])
vsolid(root, 'WIN_EAST_L2_JAMB_N', 9.79, 9.91, 2.00, 2.06, 4.30, 5.70, MAT[:frame])
vsolid(root, 'WIN_EAST_L2_JAMB_S', 9.79, 9.91, 4.34, 4.40, 4.30, 5.70, MAT[:frame])
vsolid(root, 'WIN_EAST_L2_MULLION', 9.79, 9.91, 3.18, 3.22, 4.30, 5.70, MAT[:frame])
vsolid(root, 'WIN_EAST_L2_GLASS_W', 9.844, 9.856, 2.06, 3.18, 4.36, 5.64, MAT[:glass])
vsolid(root, 'WIN_EAST_L2_GLASS_E', 9.844, 9.856, 3.22, 4.34, 4.36, 5.64, MAT[:glass])

vcyl(root, 'ENTRY_POT', 11.30, 2.70, 0.03, 0.42, 0.18, MAT[:pot], 16)
vcyl(root, 'ENTRY_PLANT', 11.30, 2.70, 0.38, 0.95, 0.20, MAT[:plant], 14)

# =====================================================================
# 11. 木格栅带
# =====================================================================
vsolid(root, 'LOUVER_SUBSTRATE_FRONT', 8.80, 10.00, -0.01, 0.00, Z_L1, Z_WALL_T, MAT[:woodsub])
vsolid(root, 'LOUVER_SUBSTRATE_EAST', 10.00, 10.01, 0.00, 1.20, Z_L1, Z_WALL_T, MAT[:woodsub])

BAT_W = 0.05
BAT_P = 0.062
bat_def = vcomp(model, 'MOD_BATTEN_050x040_V5')
if bat_def.entities.length == 0
  vsolid(bat_def, 'BATTEN', 0.00, BAT_W, -0.06, -0.02, 0.00, 6.40, MAT[:wood])
end
19.times do |i|
  bx = 8.81 + i * BAT_P
  inst = root.entities.add_instance(bat_def, Geom::Transformation.new(vpt(bx, 0, Z_L1)))
  inst.name = "LOUVER_BATTEN_FRONT_#{format('%02d', i + 1)}"
end
19.times do |i|
  by = 0.01 + i * BAT_P
  tr = Geom::Transformation.new(vpt(10.00, by, Z_L1)) * Geom::Transformation.rotation(vpt(0, 0, 0), Geom::Vector3d.new(0, 0, 1), 90.degrees)
  inst = root.entities.add_instance(bat_def, tr)
  inst.name = "LOUVER_BATTEN_EAST_#{format('%02d', i + 1)}"
end

# =====================================================================
# 12. 室内可见家具
# =====================================================================
vsolid(root, 'FURN_RUG', 1.10, 4.90, 1.20, 3.60, Z_L1, Z_L1 + 0.02, MAT[:curtain])
vsolid(root, 'FURN_SOFA_SEAT',  1.25, 2.35, 1.35, 3.45, Z_L1, Z_L1 + 0.42, MAT[:sofa])
vsolid(root, 'FURN_SOFA_BACK',  1.25, 1.45, 1.35, 3.45, Z_L1 + 0.42, Z_L1 + 0.80, MAT[:sofa])
vsolid(root, 'FURN_SOFA_CHAISE', 2.35, 3.30, 2.55, 3.45, Z_L1, Z_L1 + 0.42, MAT[:sofa])
vsolid(root, 'FURN_COFFEE_TABLE', 3.50, 4.40, 1.85, 2.70, Z_L1 + 0.28, Z_L1 + 0.36, MAT[:furnw])
vsolid(root, 'FURN_COFFEE_TABLE_LEG', 3.85, 4.05, 2.15, 2.40, Z_L1, Z_L1 + 0.28, MAT[:furnw])

vsolid(root, 'FURN_DINING_TOP', 5.60, 7.40, 5.60, 6.60, Z_L1 + 0.69, Z_L1 + 0.74, MAT[:furnw])
vsolid(root, 'FURN_DINING_PEDESTAL', 6.30, 6.70, 5.90, 6.30, Z_L1, Z_L1 + 0.69, MAT[:furnw])
chair = lambda do |name, x, y, back|
  vsolid(root, "#{name}_SEAT", x, x + 0.45, y, y + 0.45, Z_L1 + 0.28, Z_L1 + 0.45, MAT[:curtain])
  case back
  when :north then vsolid(root, "#{name}_BACK", x, x + 0.45, y + 0.39, y + 0.45, Z_L1 + 0.45, Z_L1 + 0.92, MAT[:curtain])
  when :south then vsolid(root, "#{name}_BACK", x, x + 0.45, y, y + 0.06, Z_L1 + 0.45, Z_L1 + 0.92, MAT[:curtain])
  when :west  then vsolid(root, "#{name}_BACK", x, x + 0.06, y, y + 0.45, Z_L1 + 0.45, Z_L1 + 0.92, MAT[:curtain])
  else             vsolid(root, "#{name}_BACK", x + 0.39, x + 0.45, y, y + 0.45, Z_L1 + 0.45, Z_L1 + 0.92, MAT[:curtain])
  end
end
chair.call('FURN_CHAIR_1', 5.72, 5.05, :south)
chair.call('FURN_CHAIR_2', 6.62, 5.05, :south)
chair.call('FURN_CHAIR_3', 5.72, 6.70, :north)
chair.call('FURN_CHAIR_4', 6.62, 6.70, :north)

[[6.05, 0.95, 'A'], [0.95, 6.90, 'B']].each do |x, y, tag|
  vcyl(root, "FURN_POT_#{tag}", x, y, Z_L1, Z_L1 + 0.45, 0.18, MAT[:pot], 14)
  vcyl(root, "FURN_PLANT_#{tag}", x, y, Z_L1 + 0.40, Z_L1 + 1.25, 0.24, MAT[:plant], 12)
end

vsolid(root, 'ART_FRAME', 5.60, 6.70, 7.64, 7.68, 1.55, 2.45, MAT[:frame])
vsolid(root, 'ART_CANVAS', 5.66, 6.64, 7.63, 7.66, 1.61, 2.39, MAT[:art])
vsolid(root, 'CURTAIN_PANEL', 5.85, 6.10, 0.34, 0.42, Z_L1 + 0.05, 2.80, MAT[:curtain])

bb = root.bounds
puts "BUILD V5 OK: children=#{root.entities.length}"
puts "  bounds mm: x #{bb.min.x.to_mm.round}..#{bb.max.x.to_mm.round}  y #{bb.min.y.to_mm.round}..#{bb.max.y.to_mm.round}  z #{bb.min.z.to_mm.round}..#{bb.max.z.to_mm.round}"
