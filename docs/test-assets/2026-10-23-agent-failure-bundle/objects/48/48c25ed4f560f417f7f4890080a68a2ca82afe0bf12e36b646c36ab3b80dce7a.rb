# Apartment reconstruction — persistent builder (rev B: no boolean/erase on slabs)
# Source: inputs/reference/6649b42845-image.png (single front elevation, inferred rear/sides)
# Coordinates: mm, origin at front-left outer corner, +X right, +Y rear, +Z up.

# ---------------- shared parameters (single source of truth) ----------------
W = 13300.0
D = 12000.0
GF = 3600.0
FH = 3000.0
NF = 10
SLAB = 250.0
ROOF_Z = GF + NF * FH            # 33600
PARAPET_H = 700.0
PARAPET_TOP = ROOF_Z + PARAPET_H # 34300
SCREEN_TOP = 36500.0
WALL_T = 300.0

LOG_X0 = 600.0
LOG_X1 = 4600.0
GLA_X0 = 5300.0
GLA_X1 = 12500.0
WIN_MULL = 300.0
WIN_W = (GLA_X1 - GLA_X0 - WIN_MULL) / 2.0   # 3450
WIN_A = GLA_X0
WIN_B = GLA_X0 + WIN_W + WIN_MULL            # 9050
WIN_H = 2400.0
WIN_SILL = 100.0
LOG_W = LOG_X1 - LOG_X0                       # 4000
LOG_H = 2500.0
LOG_D = 1500.0
GAR_W = 6000.0
GAR_H = 2700.0
GAR_X0 = GLA_X0 + (7200.0 - GAR_W) / 2.0      # 5900
ENT_X0 = 1200.0
ENT_W = 1200.0
ENT_H = 2400.0
STAIR_HOLE = [5300.0, 7000.0, 8700.0, 10600.0]

def lvl(k)
  k.zero? ? 0.0 : GF + (k - 1) * FH
end

# ---------------- materials ----------------
def mcolor(model, name, r, g, b, opacity = nil)
  m = model.materials[name]
  m = model.materials.add(name) unless m
  m.color = Sketchup::Color.new(r, g, b)
  m.opacity = opacity unless opacity.nil?
  m
end

CONC       = mcolor(model, "CONC_FAIRFACE", 214, 203, 186)
CONC_SOFF  = mcolor(model, "CONC_SOFFIT", 226, 218, 204)
GLASS      = mcolor(model, "GLASS_DARK", 62, 78, 78, 0.42)
BAL_GLASS  = mcolor(model, "GLASS_BALUSTRADE", 176, 196, 198, 0.30)
FRAME      = mcolor(model, "FRAME_DARK", 58, 58, 58)
CURTAIN    = mcolor(model, "CURTAIN_CREAM", 238, 230, 213, 0.88)
SHUTTER    = mcolor(model, "SHUTTER_GREY", 108, 110, 110)
CLAD_DARK  = mcolor(model, "CLAD_DARKGREY", 92, 94, 94)
STEEL      = mcolor(model, "STEEL_SCREEN", 122, 104, 108)
PLANTER    = mcolor(model, "PLANTER_CONC", 158, 150, 138)
GREEN      = mcolor(model, "GREEN_PLANT", 78, 102, 62)
DECK       = mcolor(model, "ROOF_DECK", 198, 193, 184)
GROUND     = mcolor(model, "SITE_PAVING", 162, 158, 150)

# ---------------- helpers ----------------
def add_group(parent, name, material = nil)
  g = parent.entities.add_group
  g.name = name
  g.material = material if material
  g
end

def raw_box(parent, xa, ya, za, xb, yb, zb)
  return nil unless (xb - xa) > 0.5 && (yb - ya) > 0.5 && (zb - za) > 0.5
  pts = [[xa, ya, za], [xb, ya, za], [xb, yb, za], [xa, yb, za]].map do |x, y, z|
    Geom::Point3d.new(x.mm, y.mm, z.mm)
  end
  f = parent.entities.add_face(pts)
  return nil unless f && f.valid?
  f.reverse! if f.normal.z < -0.5
  f.pushpull((zb - za).mm)
  f
end

def part(parent, name, xa, ya, za, xb, yb, zb, material = nil)
  g = add_group(parent, name, material)
  raw_box(g, xa, ya, za, xb, yb, zb)
  g
end

def find_group(parent, name)
  return nil unless parent.respond_to?(:entities)
  parent.entities.each do |e|
    next unless e.respond_to?(:name)
    return e if e.name == name
    next unless e.is_a?(Sketchup::Group)
    r = find_group(e, name)
    return r if r
  end
  nil
end

def window_def(model, name, w, h, transom_z, frame, glass)
  d = model.definitions.add(name)
  fd = 120.0
  fw = 60.0
  part(d, "JAMB_L", 0, 0, 0, fw, fd, h, frame)
  part(d, "JAMB_R", w - fw, 0, 0, w, fd, h, frame)
  part(d, "HEAD", fw, 0, h - fw, w - fw, fd, h, frame)
  part(d, "SILL", fw, 0, 0, w - fw, fd, fw, frame)
  part(d, "TRANSOM", fw, 0, transom_z - 20, w - fw, fd, transom_z + 20, frame) if transom_z
  part(d, "GLASS", fw, 50, fw, w - fw, 70, h - fw, glass)
  d
end

def loggia_def(model, name, w, depth, h, conc, frame, glass, bal_glass, steel, planter, green)
  d = model.definitions.add(name)
  ret = 150.0
  fw = 60.0
  y0 = depth - 120.0
  part(d, "RETURN_L", 0, 0, 0, ret, depth, h, conc)
  part(d, "RETURN_R", w - ret, 0, 0, w, depth, h, conc)
  part(d, "BACK_JAMB_L", ret, y0, 0, ret + fw, depth, h, frame)
  part(d, "BACK_JAMB_R", w - ret - fw, y0, 0, w - ret, depth, h, frame)
  part(d, "BACK_HEAD", ret + fw, y0, h - fw, w - ret - fw, depth, h, frame)
  part(d, "BACK_SILL", ret + fw, y0, 0, w - ret - fw, depth, fw, frame)
  part(d, "BACK_GLASS", ret + fw, y0 + 40, fw, w - ret - fw, y0 + 60, h - fw, glass)
  part(d, "BAL_GLASS", ret, 100, 50, w - ret, 120, 1150, bal_glass)
  part(d, "BAL_SHOE", ret, 80, 0, w - ret, 140, 50, steel)
  part(d, "BAL_TOP", ret, 80, 1150, w - ret, 140, 1190, steel)
  part(d, "PLANTER_BOX", 300, 180, 0, 1700, 650, 400, planter)
  part(d, "GREEN_A", 350, 220, 400, 1000, 600, 900, green)
  part(d, "GREEN_B", 1060, 250, 400, 1650, 620, 780, green)
  d
end

# ---------------- SITE ----------------
site = add_group(root, "SITE", nil)
part(site, "GROUND_PLANE", -6000, -8000, -200, 19300, 20000, -50, GROUND)

# ---------------- LEVELS: floor plates ----------------
levels = add_group(root, "LEVELS", nil)
(0..NF).each do |k|
  ztop = lvl(k)
  part(levels, "SLAB_L#{k}", 0, 0, ztop - SLAB, W, D, ztop, CONC)
end

# ---------------- FACADE: four wall planes (SAIE continuous walls) ----------------
front_open = []
(1..NF).each do |k|
  zb = (k - 1) * FH
  front_open << { "offset_mm" => LOG_X0, "width_mm" => LOG_W, "height_mm" => LOG_H, "sill_mm" => zb }
  front_open << { "offset_mm" => WIN_A, "width_mm" => WIN_W, "height_mm" => WIN_H, "sill_mm" => zb + WIN_SILL }
  front_open << { "offset_mm" => WIN_B, "width_mm" => WIN_W, "height_mm" => WIN_H, "sill_mm" => zb + WIN_SILL }
end

saie_wall_with_openings.call({
  "name" => "WALL_FRONT",
  "centerline" => [[0.0, 150.0], [W, 150.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => NF * FH,
  "elevation_mm" => GF,
  "openings" => front_open
})

saie_wall_with_openings.call({
  "name" => "WALL_FRONT_BASE",
  "centerline" => [[0.0, 150.0], [W, 150.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => GF,
  "elevation_mm" => 0.0,
  "openings" => [
    { "offset_mm" => GAR_X0, "width_mm" => GAR_W, "height_mm" => GAR_H, "sill_mm" => 0.0 },
    { "offset_mm" => ENT_X0, "width_mm" => ENT_W, "height_mm" => ENT_H, "sill_mm" => 0.0 }
  ]
})

rear_open = []
(1..NF).each do |k|
  zb = (k - 1) * FH
  rear_open << { "offset_mm" => 1600.0, "width_mm" => 2400.0, "height_mm" => 1600.0, "sill_mm" => zb + 900.0 }
  rear_open << { "offset_mm" => 8500.0, "width_mm" => 2400.0, "height_mm" => 1600.0, "sill_mm" => zb + 900.0 }
end

saie_wall_with_openings.call({
  "name" => "WALL_REAR",
  "centerline" => [[0.0, 11850.0], [W, 11850.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => NF * FH,
  "elevation_mm" => GF,
  "openings" => rear_open
})

saie_wall_with_openings.call({
  "name" => "WALL_REAR_BASE",
  "centerline" => [[0.0, 11850.0], [W, 11850.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => GF,
  "elevation_mm" => 0.0,
  "openings" => [
    { "offset_mm" => 6000.0, "width_mm" => 1200.0, "height_mm" => 2400.0, "sill_mm" => 0.0 },
    { "offset_mm" => 1800.0, "width_mm" => 1500.0, "height_mm" => 1200.0, "sill_mm" => 1200.0 }
  ]
})

side_open = []
(1..NF).each do |k|
  zb = (k - 1) * FH
  side_open << { "offset_mm" => 2400.0, "width_mm" => 1500.0, "height_mm" => 1500.0, "sill_mm" => zb + 900.0 }
  side_open << { "offset_mm" => 7500.0, "width_mm" => 1500.0, "height_mm" => 1500.0, "sill_mm" => zb + 900.0 }
end

saie_wall_with_openings.call({
  "name" => "WALL_LEFT",
  "centerline" => [[150.0, 300.0], [150.0, 11700.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => NF * FH,
  "elevation_mm" => GF,
  "openings" => side_open
})

saie_wall_with_openings.call({
  "name" => "WALL_RIGHT",
  "centerline" => [[13150.0, 300.0], [13150.0, 11700.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => NF * FH,
  "elevation_mm" => GF,
  "openings" => side_open
})

saie_wall.call({
  "name" => "WALL_LEFT_BASE",
  "centerline" => [[150.0, 300.0], [150.0, 11700.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => GF,
  "elevation_mm" => 0.0
})

saie_wall.call({
  "name" => "WALL_RIGHT_BASE",
  "centerline" => [[13150.0, 300.0], [13150.0, 11700.0]],
  "thickness_mm" => WALL_T,
  "height_mm" => GF,
  "elevation_mm" => 0.0
})

["WALL_FRONT", "WALL_FRONT_BASE", "WALL_REAR", "WALL_REAR_BASE",
 "WALL_LEFT", "WALL_RIGHT", "WALL_LEFT_BASE", "WALL_RIGHT_BASE"].each do |n|
  g = find_group(root, n)
  g.material = CONC if g
end

# ---------------- representative modules + front replication ----------------
win_def = window_def(model, "WINDOW_UNIT_3410x2360_DEF", 3410.0, 2360.0, 1500.0, FRAME, GLASS)
log_def = loggia_def(model, "LOGGIA_UNIT_4000x1500_DEF", LOG_W, LOG_D, LOG_H,
                     CONC, FRAME, GLASS, BAL_GLASS, STEEL, PLANTER, GREEN)

front = add_group(root, "FRONT_REPEAT", nil)
(1..NF).each do |k|
  z = lvl(k)
  [[WIN_A, "A"], [WIN_B, "B"]].each do |x, tag|
    t = Geom::Transformation.new(Geom::Point3d.new((x + 20).mm, 200.mm, (z + WIN_SILL + 20).mm))
    inst = front.entities.add_instance(win_def, t)
    inst.name = "WIN_F_L#{k}_#{tag}"
  end
  t = Geom::Transformation.new(Geom::Point3d.new(LOG_X0.mm, 300.mm, z.mm))
  inst = front.entities.add_instance(log_def, t)
  inst.name = "LOGGIA_L#{k}"
end

# rear windows (inferred)
rear_def = window_def(model, "REAR_WINDOW_2360x1560_DEF", 2360.0, 1560.0, nil, FRAME, GLASS)
rear_w = add_group(root, "REAR_WINDOWS", nil)
(1..NF).each do |k|
  z = lvl(k) + 900.0 + 20.0
  [[1600.0, "A"], [8500.0, "B"]].each do |x, tag|
    origin = Geom::Point3d.new((x + 20.0 + 2360.0).mm, 11900.mm, z.mm)
    t = Geom::Transformation.new(origin, Geom::Vector3d.new(-1, 0, 0), Geom::Vector3d.new(0, -1, 0))
    inst = rear_w.entities.add_instance(rear_def, t)
    inst.name = "WIN_R_L#{k}_#{tag}"
  end
end

# side windows (inferred, symmetric)
side_def = window_def(model, "SIDE_WINDOW_1460x1460_DEF", 1460.0, 1460.0, nil, FRAME, GLASS)
left_w = add_group(root, "SIDE_WINDOWS_LEFT", nil)
right_w = add_group(root, "SIDE_WINDOWS_RIGHT", nil)
(1..NF).each do |k|
  z = lvl(k) + 900.0 + 20.0
  [2400.0, 7500.0].each_with_index do |y, i|
    tl = Geom::Transformation.new(Geom::Point3d.new(40.mm, (y + 1460.0).mm, z.mm),
                                  Geom::Vector3d.new(0, -1, 0), Geom::Vector3d.new(1, 0, 0))
    inst = left_w.entities.add_instance(side_def, tl)
    inst.name = "WIN_L_L#{k}_#{i + 1}"
    tr = Geom::Transformation.new(Geom::Point3d.new((W - 160.0).mm, y.mm, z.mm),
                                  Geom::Vector3d.new(0, 1, 0), Geom::Vector3d.new(-1, 0, 0))
    inst = right_w.entities.add_instance(side_def, tr)
    inst.name = "WIN_RT_L#{k}_#{i + 1}"
  end
end

# ---------------- ground floor band (observed dark base + shutter + entry) ----------------
gb = add_group(root, "GROUND_BAND", nil)
part(gb, "CLAD_LEFT", 0, -80, 0, ENT_X0, 0, 3400, CLAD_DARK)
part(gb, "CLAD_MID", ENT_X0 + ENT_W, -80, 0, GAR_X0, 0, 3400, CLAD_DARK)
part(gb, "CLAD_RIGHT", GAR_X0 + GAR_W, -80, 0, W, 0, 3400, CLAD_DARK)
part(gb, "CLAD_ABOVE_ENTRY", ENT_X0, -80, ENT_H, ENT_X0 + ENT_W, 0, 3400, CLAD_DARK)
part(gb, "CLAD_ABOVE_GARAGE", GAR_X0, -80, GAR_H, GAR_X0 + GAR_W, 0, 3400, CLAD_DARK)

shutter = add_group(gb, "GARAGE_SHUTTER", SHUTTER)
raw_box(shutter, GAR_X0 + 20, 30, 0, GAR_X0 + GAR_W - 20, 90, GAR_H - 20)
(0..10).each do |i|
  z = 120 + i * 235
  raw_box(shutter, GAR_X0 + 20, -10, z, GAR_X0 + GAR_W - 20, 40, z + 55)
end

part(gb, "ENTRY_DOOR", ENT_X0 + 120, 40, 0, ENT_X0 + ENT_W - 120, 100, ENT_H - 100, FRAME)
part(gb, "ENTRY_GLASS", ENT_X0 + 140, 15, 100, ENT_X0 + ENT_W - 140, 35, ENT_H - 200, GLASS)

# ---------------- roof: deck plates, parapet, screen, headhouse, planting ----------------
roof = add_group(root, "ROOF", nil)
hx0, hy0, hx1, hy1 = STAIR_HOLE
part(roof, "ROOF_SLAB_FRONT", 0, 0, ROOF_Z - SLAB, W, hy0, ROOF_Z, CONC)
part(roof, "ROOF_SLAB_REAR", 0, hy1, ROOF_Z - SLAB, W, D, ROOF_Z, CONC)
part(roof, "ROOF_SLAB_LEFT", 0, hy0, ROOF_Z - SLAB, hx0, hy1, ROOF_Z, CONC)
part(roof, "ROOF_SLAB_RIGHT", hx1, hy0, ROOF_Z - SLAB, W, hy1, ROOF_Z, CONC)
part(roof, "DECK_FRONT", 300, 300, ROOF_Z, W - 300, hy0, ROOF_Z + 40, DECK)
part(roof, "DECK_REAR", 300, hy1, ROOF_Z, W - 300, D - 300, ROOF_Z + 40, DECK)
part(roof, "DECK_LEFT", 300, hy0, ROOF_Z, hx0, hy1, ROOF_Z + 40, DECK)
part(roof, "DECK_RIGHT", hx1, hy0, ROOF_Z, W - 300, hy1, ROOF_Z + 40, DECK)

para = add_group(roof, "PARAPET_BAND", CONC)
raw_box(para, 0, 0, ROOF_Z, W, 300, PARAPET_TOP)
raw_box(para, 0, D - 300, ROOF_Z, W, D, PARAPET_TOP)
raw_box(para, 0, 300, ROOF_Z, 300, D - 300, PARAPET_TOP)
raw_box(para, W - 300, 300, ROOF_Z, W, D - 300, PARAPET_TOP)

part(roof, "STAIR_HEADHOUSE", hx0, hy0, ROOF_Z, hx1, hy1, 36000, CONC)
part(roof, "HEADHOUSE_DOOR", 5300, 7050, ROOF_Z, 5320, 8050, ROOF_Z + 2200, FRAME)

scr = add_group(roof, "SCREEN_RAILING", STEEL)
rod_z0 = PARAPET_TOP
rod_z1 = SCREEN_TOP - 60.0
x = 150.0
while x <= W - 170.0
  raw_box(scr, x, 138, rod_z0, x + 20, 162, rod_z1)
  raw_box(scr, x, D - 162, rod_z0, x + 20, D - 138, rod_z1)
  x += 180.0
end
y = 300.0
while y <= D - 320.0
  raw_box(scr, 138, y, rod_z0, 162, y + 20, rod_z1)
  raw_box(scr, W - 162, y, rod_z0, W - 138, y + 20, rod_z1)
  y += 180.0
end
raw_box(scr, 138, 138, SCREEN_TOP - 60, W - 138, 162, SCREEN_TOP)
raw_box(scr, 138, D - 162, SCREEN_TOP - 60, W - 138, D - 138, SCREEN_TOP)
raw_box(scr, 138, 138, SCREEN_TOP - 60, 162, D - 138, SCREEN_TOP)
raw_box(scr, W - 162, 138, SCREEN_TOP - 60, W - 138, D - 138, SCREEN_TOP)
raw_box(scr, 138, 138, rod_z0, W - 138, 162, rod_z0 + 50)
raw_box(scr, 138, D - 162, rod_z0, W - 138, D - 138, rod_z0 + 50)
raw_box(scr, 138, 138, rod_z0, 162, D - 138, rod_z0 + 50)
raw_box(scr, W - 162, 138, rod_z0, W - 138, D - 138, rod_z0 + 50)
[150.0, 3400.0, 6650.0, 9900.0, W - 230.0].each do |px|
  raw_box(scr, px, 128, rod_z0, px + 80, 172, SCREEN_TOP)
  raw_box(scr, px, D - 172, rod_z0, px + 80, D - 128, SCREEN_TOP)
end
[3000.0, 6000.0, 9000.0].each do |py|
  raw_box(scr, 128, py, rod_z0, 172, py + 80, SCREEN_TOP)
  raw_box(scr, W - 172, py, rod_z0, W - 128, py + 80, SCREEN_TOP)
end

planters = add_group(roof, "PLANTERS", PLANTER)
raw_box(planters, 500, 700, ROOF_Z, 2400, 1500, ROOF_Z + 500)
raw_box(planters, 500, 2200, ROOF_Z, 1500, 4200, ROOF_Z + 500)
raw_box(planters, 9800, 900, ROOF_Z, 11500, 1900, ROOF_Z + 500)

greens = add_group(roof, "GREEN_SCREEN", GREEN)
raw_box(greens, 600, 780, ROOF_Z + 400, 2300, 1420, ROOF_Z + 1500)
raw_box(greens, 950, 900, ROOF_Z + 1400, 2000, 1350, ROOF_Z + 2300)
raw_box(greens, 600, 2300, ROOF_Z + 400, 1400, 3000, ROOF_Z + 1800)
raw_box(greens, 600, 3100, ROOF_Z + 400, 1400, 4100, ROOF_Z + 1200)
raw_box(greens, 9900, 980, ROOF_Z + 400, 11400, 1820, ROOF_Z + 1300)

# ---------------- interior: curtain screens behind glazing ----------------
interior = add_group(root, "INTERIOR", nil)
cs = add_group(interior, "CURTAIN_SCREENS", nil)
(1..NF).each do |k|
  z = lvl(k)
  [[WIN_A, "A", 0], [WIN_B, "B", 1]].each do |wx, tag, side|
    cw = 2400.0
    x0 = ((k + side).even? ? wx + 150.0 : wx + WIN_W - 150.0 - cw)
    part(cs, "CURTAIN_F_L#{k}_#{tag}", x0, 620, z + WIN_SILL + 60,
         x0 + cw, 660, z + WIN_SILL + WIN_H - 60, CURTAIN)
  end
  part(cs, "CURTAIN_LOGGIA_L#{k}", LOG_X0 + 320, 1750, z + 60,
       LOG_X0 + 320 + 3000, 1790, z + 2440, CURTAIN)
end

"BUILT width=#{W.to_i} depth=#{D.to_i} floors=#{NF} roof_z=#{ROOF_Z.to_i} " \
"front_openings=#{front_open.size} rear_openings=#{rear_open.size} side_openings=#{side_open.size} " \
"root_children=#{root.entities.grep(Sketchup::Group).map(&:name).join('|')} " \
"defs=#{model.definitions.map(&:name).select { |n| n.include?('_DEF') }.join('|')}"
