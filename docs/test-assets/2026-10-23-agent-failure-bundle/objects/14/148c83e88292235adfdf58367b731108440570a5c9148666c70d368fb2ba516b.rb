# architecture-project-964f3 — 窄板式公寓（首层 + 7 住宅层 + 开放屋顶露台）
# 源: inputs/reference/6649b42845-image.png（唯一正立面透视；侧/背/屋顶为推断）
# 坐标系: mm，原点=正立面左端外角、首层地坪；+X 观者右，+Y 进深向后，+Z 上。
# 阶段: 主形体 -> 代表单元 -> 复制 -> 变体 -> 收口（单文件持久基线）

# ---------------- 共享参数（唯一来源） ----------------
W      = 13200.0   # 正立面总宽（估算）
D      = 12000.0   # 总进深（推断）
GF     = 3600.0    # 首层
FH     = 3000.0    # 标准层
NF     = 7         # 住宅层数（原图可数）
SLAB   = 250.0     # 板厚
ROOF_Z = GF + NF * FH          # 24600 屋面板顶 = 露台面
PARA_H = 700.0
PARA_TOP = ROOF_Z + PARA_H     # 25300
SCREEN_TOP = ROOF_Z + 2200.0   # 26800 围屏顶
WALL_T = 250.0
GF_TOP = GF - SLAB             # 3350 首层墙体顶

PIER   = 450.0
LOG_X0 = 450.0
LOG_X1 = 5100.0
LOG_W  = LOG_X1 - LOG_X0       # 4650
GLA_X0 = 5550.0
GLA_X1 = 12750.0
MULL   = 200.0
WIN_W  = 3500.0
WIN_A  = GLA_X0                # 5550
WIN_B  = GLA_X0 + WIN_W + MULL # 9250
WIN_H  = 2400.0
WIN_SILL = 100.0
LOG_H  = 2750.0                # 阳台洞口高 = 层高 - 板厚
LOG_D  = 1500.0                # 凹深（墙内面之后）
GAR_X0 = 6150.0
GAR_W  = 6000.0
GAR_H  = 2700.0
ENT_X0 = 1200.0
ENT_W  = 1800.0
ENT_H  = 2600.0
CORE_X0 = 8300.0
CORE_X1 = 11100.0
CORE_Y0 = 9200.0

def lvl(k)
  GF + (k - 1) * FH
end

# ---------------- 材质 ----------------
def mcolor(model, name, r, g, b, opacity = nil)
  m = model.materials[name]
  m = model.materials.add(name) if m.nil?
  m.opacity = opacity unless opacity.nil?
  m.color = Sketchup::Color.new(r, g, b)
  m
rescue StandardError
  nil
end

CONC      = mcolor(model, "CONC_FAIRFACE", 208, 200, 186)
CONC_SOFF = mcolor(model, "CONC_SOFFIT", 224, 216, 203)
GLASS     = mcolor(model, "GLASS_DARK", 74, 90, 86, 0.55)
BAL_GLASS = mcolor(model, "GLASS_BALUSTRADE", 188, 208, 208, 0.30)
FRAME     = mcolor(model, "FRAME_DARK", 58, 60, 62)
CURTAIN   = mcolor(model, "CURTAIN_CREAM", 226, 216, 196, 0.90)
SHUTTER   = mcolor(model, "SHUTTER_GREY", 104, 106, 108)
CLAD_DARK = mcolor(model, "CLAD_DARKGREY", 96, 98, 100)
STEEL     = mcolor(model, "STEEL_SCREEN", 122, 124, 128)
PLANTER   = mcolor(model, "PLANTER_CONC", 156, 150, 140)
GREEN     = mcolor(model, "GREEN_PLANT", 88, 112, 66)
DECK      = mcolor(model, "ROOF_DECK", 182, 178, 170)
GROUND    = mcolor(model, "SITE_PAVING", 166, 163, 158)

# ---------------- 基础工具 ----------------
def rkp(x, y, z)
  Geom::Point3d.new(x.mm, y.mm, z.mm)
end

def rk_paint(ent, m)
  return ent if ent.nil? || m.nil?
  ent.material = m if ent.respond_to?(:material=)
  if ent.respond_to?(:entities)
    ent.entities.each do |e|
      e.material = m if e.respond_to?(:material=)
    end
  end
  ent
end

def rk_raw_box(ents, xa, ya, za, xb, yb, zb)
  return nil unless (xb - xa) > 0.5 && (yb - ya) > 0.5 && (zb - za) > 0.5
  f = ents.add_face(rkp(xa, ya, za), rkp(xb, ya, za), rkp(xb, yb, za), rkp(xa, yb, za))
  return nil unless f && f.valid?
  f.reverse! if f.normal.z < -0.5
  f.pushpull((zb - za).mm)
  f
end

def rk_box(parent, name, xa, ya, za, xb, yb, zb, m = nil)
  g = parent.entities.add_group
  g.name = name
  rk_raw_box(g.entities, xa, ya, za, xb, yb, zb)
  rk_paint(g, m)
  g
end

def rk_pane(parent, name, xa, xb, y, za, zb, m)
  g = parent.entities.add_group
  g.name = name
  f = g.entities.add_face(rkp(xa, y, za), rkp(xb, y, za), rkp(xb, y, zb), rkp(xa, y, zb))
  if f && f.valid?
    f.material = m if m
    f.back_material = m if m
  end
  g
end

def rk_find(ents, name)
  ents.grep(Sketchup::Group).find { |g| g.name.to_s == name }
end

def rk_resolve(res, container, name)
  cand = nil
  if res.respond_to?(:valid?) && res.respond_to?(:entities)
    cand = res
  elsif res.is_a?(Hash)
    [:group, :entity, :result, :wall, :data].each do |k|
      v = res[k]
      cand ||= v if v.respond_to?(:entities)
    end
  end
  cand ||= rk_find(container.entities, name)
  cand
end

def rk_simple_window(model, name, w, h, y_depth, frame, glass)
  d = model.definitions[name]
  d = model.definitions.add(name) if d.nil?
  if d.entities.count.zero?
    g = d.entities.add_group
    g.name = "WIN_FRAME"
    rk_raw_box(g.entities, 0, 0, 0, 60, y_depth, h)
    rk_raw_box(g.entities, w - 60, 0, 0, w, y_depth, h)
    rk_raw_box(g.entities, 60, 0, h - 60, w - 60, y_depth, h)
    rk_raw_box(g.entities, 60, 0, 0, w - 60, y_depth, 60)
    rk_paint(g, frame)
    gp = d.entities.add_group
    gp.name = "WIN_GLASS"
    f = gp.entities.add_face(Geom::Point3d.new(60.mm, (y_depth / 2).mm, 60.mm),
                             Geom::Point3d.new((w - 60).mm, (y_depth / 2).mm, 60.mm),
                             Geom::Point3d.new((w - 60).mm, (y_depth / 2).mm, (h - 60).mm),
                             Geom::Point3d.new(60.mm, (y_depth / 2).mm, (h - 60).mm))
    if f && f.valid?
      f.material = glass
      f.back_material = glass
    end
  end
  d
end

# ---------------- 容器 ----------------
g_site   = root.entities.add_group; g_site.name   = "SITE"
g_levels = root.entities.add_group; g_levels.name = "LEVELS"
g_facade = root.entities.add_group; g_facade.name = "FACADE"
g_ground = g_facade.entities.add_group; g_ground.name = "GROUND_BAND"
g_mod    = root.entities.add_group; g_mod.name    = "MODULES"
g_roof   = root.entities.add_group; g_roof.name   = "ROOF"
g_int    = root.entities.add_group; g_int.name    = "INTERIOR"

# ---------------- SITE ----------------
rk_box(g_site, "GROUND_PLANE", -7000, -9000, -150, 20200, 21000, 0, GROUND)

# ---------------- LEVELS: 楼板 + 核心筒 ----------------
stack = g_levels.entities.add_group; stack.name = "SLAB_CORE_STACK"
rk_box(stack, "SLAB_GF", 250, 250, -SLAB, 12950, 11750, 0, CONC)
(1..NF).each do |k|
  z = lvl(k)
  rk_box(stack, "SLAB_L#{k}", 250, 250, z - SLAB, 12950, 11750, z, CONC)
end
core = stack.entities.add_group; core.name = "CORE_SHAFT"
rk_box(core, "CORE_WALL_W", CORE_X0, CORE_Y0, 0, CORE_X0 + 200, 11750, ROOF_Z - SLAB, CONC_SOFF)
rk_box(core, "CORE_WALL_E", CORE_X1 - 200, CORE_Y0, 0, CORE_X1, 11750, ROOF_Z - SLAB, CONC_SOFF)
rk_box(core, "CORE_WALL_S", CORE_X0, CORE_Y0, 0, CORE_X1, CORE_Y0 + 200, ROOF_Z - SLAB, CONC_SOFF)

# ---------------- FACADE: 正立面（上段真实洞口墙） ----------------
front_open = []
(1..NF).each do |k|
  zb = lvl(k) - GF_TOP
  front_open << { "offset_mm" => LOG_X0, "width_mm" => LOG_W, "height_mm" => LOG_H, "sill_mm" => zb }
  front_open << { "offset_mm" => WIN_A,  "width_mm" => WIN_W, "height_mm" => WIN_H, "sill_mm" => zb + WIN_SILL }
  front_open << { "offset_mm" => WIN_B,  "width_mm" => WIN_W, "height_mm" => WIN_H, "sill_mm" => zb + WIN_SILL }
end

res_front = saie_wall_with_openings.call({
  "name" => "WALL_FRONT",
  "centerline" => [[0.0, 125.0], [W, 125.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => ROOF_Z - GF_TOP,
  "elevation_mm" => GF_TOP,
  "openings" => front_open
})
wf = rk_resolve(res_front, root, "WALL_FRONT")
rk_paint(wf, CONC)

# 首层：车库跨
res_gar = saie_wall_with_openings.call({
  "name" => "GROUND_GARAGE_WALL",
  "centerline" => [[LOG_X1 - 450.0, 125.0], [W, 125.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => GF_TOP,
  "elevation_mm" => 0.0,
  "openings" => [
    { "offset_mm" => GAR_X0 - (LOG_X1 - 450.0), "width_mm" => GAR_W, "height_mm" => GAR_H, "sill_mm" => 0.0 }
  ]
})
wg = rk_resolve(res_gar, root, "GROUND_GARAGE_WALL")
rk_paint(wg, CONC)

# 首层：入口跨（深灰墙面 + 内凹门厅）
res_ent = saie_wall_with_openings.call({
  "name" => "GROUND_ENTRY_WALL",
  "centerline" => [[LOG_X0, 125.0], [LOG_X1, 125.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => GF_TOP,
  "elevation_mm" => 0.0,
  "openings" => [
    { "offset_mm" => ENT_X0 - LOG_X0, "width_mm" => ENT_W, "height_mm" => ENT_H, "sill_mm" => 0.0 }
  ]
})
we = rk_resolve(res_ent, root, "GROUND_ENTRY_WALL")
rk_paint(we, CLAD_DARK)

# 首层左端柱垛 + 入口内凹 + 卷帘
rk_box(g_ground, "PIER_GROUND_LEFT", 0, 0, 0, PIER, 250, GF_TOP, CONC)
rk_box(g_ground, "ENTRY_NICHE_BACK", ENT_X0, 250, 0, ENT_X0 + ENT_W, 850, ENT_H, CLAD_DARK)
rk_box(g_ground, "ENTRY_DOOR", ENT_X0 + 300, 800, 0, ENT_X0 + ENT_W - 300, 860, 2400, FRAME)
rk_pane(g_ground, "ENTRY_DOOR_GLASS", ENT_X0 + 330, ENT_X0 + ENT_W - 330, 790, 200, 2200, GLASS)

shutter = g_ground.entities.add_group; shutter.name = "GARAGE_SHUTTER"
(0..17).each do |i|
  z0 = i * 150.0
  rk_raw_box(shutter.entities, GAR_X0 + 30, 180, z0, GAR_X0 + GAR_W - 30, 205, z0 + 138)
end
rk_paint(shutter, SHUTTER)
rk_box(g_ground, "GARAGE_FRAME_HEAD", GAR_X0, 170, GAR_H - 120, GAR_X0 + GAR_W, 215, GAR_H, FRAME)

# ---------------- FACADE: 背立面（推断） ----------------
rear_open = []
(1..NF).each do |k|
  zb = lvl(k)
  [1200.0, 3300.0, 8100.0, 10200.0].each do |ox|
    rear_open << { "offset_mm" => ox, "width_mm" => 1800.0, "height_mm" => 1800.0, "sill_mm" => zb + 900.0 }
  end
end
rear_open << { "offset_mm" => 6000.0, "width_mm" => 1200.0, "height_mm" => 2400.0, "sill_mm" => 0.0 }

res_rear = saie_wall_with_openings.call({
  "name" => "WALL_REAR",
  "centerline" => [[0.0, D - 125.0], [W, D - 125.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => ROOF_Z,
  "elevation_mm" => 0.0,
  "openings" => rear_open
})
wr = rk_resolve(res_rear, root, "WALL_REAR")
rk_paint(wr, CONC)

# ---------------- FACADE: 左右侧立面（推断） ----------------
side_open = []
(1..NF).each do |k|
  zb = lvl(k)
  [1500.0, 7000.0].each do |oy|
    side_open << { "offset_mm" => oy, "width_mm" => 1500.0, "height_mm" => 1800.0, "sill_mm" => zb + 900.0 }
  end
end
side_open << { "offset_mm" => 4000.0, "width_mm" => 1200.0, "height_mm" => 900.0, "sill_mm" => 1500.0 }

res_left = saie_wall_with_openings.call({
  "name" => "WALL_LEFT",
  "centerline" => [[125.0, 250.0], [125.0, D - 250.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => ROOF_Z,
  "elevation_mm" => 0.0,
  "openings" => side_open
})
wl = rk_resolve(res_left, root, "WALL_LEFT")
rk_paint(wl, CONC)

res_right = saie_wall_with_openings.call({
  "name" => "WALL_RIGHT",
  "centerline" => [[W - 125.0, 250.0], [W - 125.0, D - 250.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => ROOF_Z,
  "elevation_mm" => 0.0,
  "openings" => side_open
})
wrt = rk_resolve(res_right, root, "WALL_RIGHT")
rk_paint(wrt, CONC)

# ---------------- MODULES: 代表单元 ----------------
wx0 = WIN_A
wx1 = WIN_A + WIN_W
wz0 = lvl(1) + WIN_SILL
wz1 = wz0 + WIN_H
proto_w = g_mod.entities.add_group; proto_w.name = "WINDOW_PROTO"
rk_box(proto_w, "F_BOT",    wx0 + 20, 105, wz0 + 20, wx1 - 20, 165, wz0 + 80, FRAME)
rk_box(proto_w, "F_HEAD",   wx0 + 20, 105, wz1 - 80, wx1 - 20, 165, wz1 - 20, FRAME)
rk_box(proto_w, "F_JAMB_L", wx0 + 20, 105, wz0 + 80, wx0 + 80, 165, wz1 - 80, FRAME)
rk_box(proto_w, "F_JAMB_R", wx1 - 80, 105, wz0 + 80, wx1 - 20, 165, wz1 - 80, FRAME)
rk_pane(proto_w, "GLASS", wx0 + 80, wx1 - 80, 145, wz0 + 80, wz1 - 80, GLASS)
comp_w = proto_w.to_component
comp_w.name = "WINDOW_A_L1"
comp_w.definition.name = "WINDOW_UNIT_3500x2400_DEF"
wdef = comp_w.definition

lz0 = lvl(1)
lz1 = lz0 + LOG_H
proto_l = g_mod.entities.add_group; proto_l.name = "LOGGIA_PROTO"
rk_box(proto_l, "RETURN_W", LOG_X0, 250, lz0, LOG_X0 + 150, 250 + LOG_D, lz1, CONC)
rk_box(proto_l, "RETURN_E", LOG_X1 - 150, 250, lz0, LOG_X1, 250 + LOG_D, lz1, CONC)
rk_pane(proto_l, "BACK_GLASS", LOG_X0 + 150, LOG_X1 - 150, 250 + LOG_D, lz0 + 100, lz1 - 100, GLASS)
[LOG_X0 + 150, 2750.0, LOG_X1 - 210.0].each_with_index do |mx, i|
  rk_box(proto_l, "BACK_MULL_#{i + 1}", mx, 250 + LOG_D - 40, lz0 + 100, mx + 60, 250 + LOG_D + 20, lz1 - 100, FRAME)
end
rk_pane(proto_l, "LOG_CURTAIN", LOG_X0 + 220, LOG_X1 - 220, 250 + LOG_D + 80, lz0 + 140, lz1 - 180, CURTAIN)
rk_pane(proto_l, "BAL_GLASS", LOG_X0 + 20, LOG_X1 - 20, 215, lz0 + 60, lz0 + 1150, BAL_GLASS)
rk_box(proto_l, "BAL_HANDRAIL", LOG_X0 + 10, 185, lz0 + 1150, LOG_X1 - 10, 235, lz0 + 1190, STEEL)
[LOG_X0 + 160, 2750.0, LOG_X1 - 260.0].each_with_index do |px, i|
  rk_box(proto_l, "BAL_POST_#{i + 1}", px, 195, lz0 + 60, px + 40, 230, lz0 + 1150, STEEL)
end
rk_box(proto_l, "PLANTER_BOX", 700, 320, lz0, 2100, 820, lz0 + 420, PLANTER)
rk_box(proto_l, "PLANTER_SOIL", 730, 350, lz0 + 420, 2070, 790, lz0 + 460, GREEN)
rk_box(proto_l, "GREEN_A", 760, 370, lz0 + 460, 1500, 770, lz0 + 1000, GREEN)
rk_box(proto_l, "GREEN_B", 1550, 390, lz0 + 460, 2040, 760, lz0 + 860, GREEN)
comp_l = proto_l.to_component
comp_l.name = "LOGGIA_L1"
comp_l.definition.name = "LOGGIA_UNIT_4650x1500_DEF"
ldef = comp_l.definition

# ---------------- 复制：正立面 7 层 ----------------
(1..NF).each do |k|
  dz = lvl(k) - lvl(1)
  [[WIN_A, "A"], [WIN_B, "B"]].each do |wx, tag|
    next if k == 1 && tag == "A"
    t = Geom::Transformation.translation(Geom::Vector3d.new((wx - WIN_A).mm, 0, dz.mm))
    inst = g_mod.entities.add_instance(wdef, t)
    inst.name = "WINDOW_#{tag}_L#{k}"
  end
  next if k == 1
  inst = g_mod.entities.add_instance(ldef, Geom::Transformation.translation(Geom::Vector3d.new(0, 0, dz.mm)))
  inst.name = "LOGGIA_L#{k}"
end

# 背/侧窗（推断，简化窗型）
rear_def = rk_simple_window(model, "REAR_WINDOW_1800x1800_DEF", 1800.0, 1800.0, 120.0, FRAME, GLASS)
side_def = rk_simple_window(model, "SIDE_WINDOW_1500x1800_DEF", 1500.0, 1800.0, 120.0, FRAME, GLASS)

g_rear_win = g_facade.entities.add_group; g_rear_win.name = "REAR_WINDOWS"
(1..NF).each do |k|
  [1200.0, 3300.0, 8100.0, 10200.0].each_with_index do |ox, i|
    t = Geom::Transformation.new(Geom::Point3d.new((ox + 20.0).mm, (D - 175.0).mm, (lvl(k) + 920.0).mm))
    inst = g_rear_win.entities.add_instance(rear_def, t)
    inst.name = "WIN_REAR_L#{k}_#{i + 1}"
  end
end

g_side_win = g_facade.entities.add_group; g_side_win.name = "SIDE_WINDOWS"
(1..NF).each do |k|
  [1500.0, 7000.0].each_with_index do |oy, i|
    tl = Geom::Transformation.new(Geom::Point3d.new(60.mm, (250.0 + oy + 20.0).mm, (lvl(k) + 920.0).mm),
                                  Geom::Vector3d.new(0, 1, 0), Geom::Vector3d.new(1, 0, 0))
    inst = g_side_win.entities.add_instance(side_def, tl)
    inst.name = "WIN_LEFT_L#{k}_#{i + 1}"
    tr = Geom::Transformation.new(Geom::Point3d.new((W - 60.0).mm, (250.0 + oy + 20.0).mm, (lvl(k) + 920.0).mm),
                                  Geom::Vector3d.new(0, -1, 0), Geom::Vector3d.new(-1, 0, 0))
    inst = g_side_win.entities.add_instance(side_def, tr)
    inst.name = "WIN_RIGHT_L#{k}_#{i + 1}"
  end
end

# ---------------- ROOF ----------------
rk_box(g_roof, "ROOF_SLAB", 250, 250, ROOF_Z - SLAB, 12950, 11750, ROOF_Z, DECK)
para = g_roof.entities.add_group; para.name = "PARAPET_BAND"
rk_box(para, "PARA_FRONT", 0, 0, ROOF_Z, W, 250, PARA_TOP, CONC)
rk_box(para, "PARA_REAR", 0, D - 250, ROOF_Z, W, D, PARA_TOP, CONC)
rk_box(para, "PARA_LEFT", 0, 250, ROOF_Z, 250, D - 250, PARA_TOP, CONC)
rk_box(para, "PARA_RIGHT", W - 250, 250, ROOF_Z, W, D - 250, PARA_TOP, CONC)

scr = g_roof.entities.add_group; scr.name = "SCREEN_RAILING"
rod_z0 = PARA_TOP + 20.0
rod_z1 = SCREEN_TOP - 70.0
xf = 120.0
while xf <= W - 150.0
  rk_raw_box(scr.entities, xf, 115, rod_z0, xf + 25, 140, rod_z1)
  rk_raw_box(scr.entities, xf, D - 140, rod_z0, xf + 25, D - 115, rod_z1)
  xf += 200.0
end
yf = 300.0
while yf <= D - 320.0
  rk_raw_box(scr.entities, 115, yf, rod_z0, 140, yf + 25, rod_z1)
  rk_raw_box(scr.entities, W - 140, yf, rod_z0, W - 115, yf + 25, rod_z1)
  yf += 200.0
end
rk_raw_box(scr.entities, 0, 105, rod_z0 - 60, W, 150, rod_z0)
rk_raw_box(scr.entities, 0, D - 150, rod_z0 - 60, W, D - 105, rod_z0)
rk_raw_box(scr.entities, 105, 150, rod_z0 - 60, 150, D - 150, rod_z0)
rk_raw_box(scr.entities, W - 150, 150, rod_z0 - 60, W - 105, D - 150, rod_z0)
rk_raw_box(scr.entities, 0, 100, SCREEN_TOP - 70, W, 155, SCREEN_TOP)
rk_raw_box(scr.entities, 0, D - 155, SCREEN_TOP - 70, W, D - 100, SCREEN_TOP)
rk_raw_box(scr.entities, 100, 155, SCREEN_TOP - 70, 155, D - 155, SCREEN_TOP)
rk_raw_box(scr.entities, W - 155, 155, SCREEN_TOP - 70, W - 100, D - 155, SCREEN_TOP)
rk_paint(scr, STEEL)

planter_r = g_roof.entities.add_group; planter_r.name = "PLANTERS"
rk_box(planter_r, "PLANTER_R1", 450, 450, ROOF_Z, 1500, 2600, ROOF_Z + 600, PLANTER)
rk_box(planter_r, "PLANTER_R2", 450, 2850, ROOF_Z, 1500, 5200, ROOF_Z + 600, PLANTER)
rk_box(planter_r, "PLANTER_R3", 9500, 600, ROOF_Z, 11500, 1900, ROOF_Z + 600, PLANTER)

green_r = g_roof.entities.add_group; green_r.name = "GREEN_SCREEN"
rk_box(green_r, "GREEN_R1", 480, 480, ROOF_Z + 600, 1470, 2570, ROOF_Z + 2100, GREEN)
rk_box(green_r, "GREEN_R2", 480, 2880, ROOF_Z + 600, 1470, 5170, ROOF_Z + 1800, GREEN)
rk_box(green_r, "GREEN_R3", 9530, 630, ROOF_Z + 600, 11470, 1870, ROOF_Z + 1500, GREEN)
(0..5).each do |n|
  rk_raw_box(green_r.entities, 380, 400 + n * 220, ROOF_Z + 1500, 900, 420 + n * 220, ROOF_Z + 1525)
end
rk_paint(green_r, GREEN)

# ---------------- INTERIOR: 窗帘面片 ----------------
cs = g_int.entities.add_group; cs.name = "CURTAIN_SCREENS"
(1..NF).each do |k|
  z = lvl(k)
  [[WIN_A + 200.0, "A"], [WIN_B + 200.0, "B"]].each do |cx, tag|
    rk_pane(cs, "CURTAIN_F_#{tag}_L#{k}", cx, cx + 3100.0, 620, z + WIN_SILL + 120, z + WIN_SILL + WIN_H - 140, CURTAIN)
  end
end

"OK W=#{W.to_i} D=#{D.to_i} NF=#{NF} roof_z=#{ROOF_Z.to_i} screen_top=#{SCREEN_TOP.to_i} " \
"front_open=#{front_open.size} rear_open=#{rear_open.size} side_open=#{side_open.size} " \
"root=#{root.entities.grep(Sketchup::Group).map(&:name).join('|')} " \
"wdef_count=#{wdef.count_instances} ldef_count=#{ldef.count_instances}"
