# ============================================================
# build_villa.rb (rev D —— 合并基线) 六视图别墅整稿源（replace 模式备用，勿执行旧版）
# 已合并：①mp() 米/英寸统一 ②基面法线朝 +Z 保护 ③通高墙（每面一次建成，跨层不再断开）
#          ④接缝隐藏：水平分段线 + 洞口两侧贯通竖线 ⑤楼板/屋面结构板边线隐藏
#          ⑥修订 B 开口表（后 3 窄窗/层、左 1/层、右仅门 + 二层中梃窗）
#          ⑦屋面卷材分格缝 ⑧柔和浅棕木色 (196,158,112)
# 日常小改用各 patch_*.rb（edit 模式）；本文件供将来整稿重建
# 参数 m；X 面宽 0..10（左→右），Y 进深 0..8（正面 y=0），Z 标高
# ============================================================
VX  = Geom::Vector3d.new( 1, 0, 0)
VY  = Geom::Vector3d.new( 0, 1, 0)
VZ  = Geom::Vector3d.new( 0, 0, 1)
VNX = Geom::Vector3d.new(-1, 0, 0)
VNY = Geom::Vector3d.new( 0,-1, 0)
ORG = Geom::Point3d.new(0, 0, 0)

def mp(x, y, z); Geom::Point3d.new(x.m, y.m, z.m); end

def smat(model, name, r, g, b, alpha = nil)
  m = model.materials[name]
  m = model.materials.add(name) if m.nil?
  m.color = Sketchup::Color.new(r, g, b)
  m.alpha = alpha unless alpha.nil?
  m
end

def add_solid(parent, name, p0, uv, ulen, nv, nlen, h, fmat, bmat = nil)
  g = parent.entities.add_group
  g.name = name
  p1 = p0.offset(uv, ulen.m)
  p2 = p1.offset(nv, nlen.m)
  p3 = p0.offset(nv, nlen.m)
  f = g.entities.add_face(p0, p1, p2, p3)
  unless f.nil?
    f.reverse! if f.normal.z < 0.0
    f.pushpull(h.abs.m)
    g.entities.grep(Sketchup::Face).each do |fc|
      fc.material = fmat
      fc.back_material = bmat.nil? ? fmat : bmat
    end
  end
  g
end

def add_local(parent, name, o, uv, nv, u0, u1, n0, n1, z0, z1, fmat, bmat = nil)
  u0, u1 = u1, u0 if u0 > u1
  n0, n1 = n1, n0 if n0 > n1
  z0, z1 = z1, z0 if z0 > z1
  p0 = o.offset(uv, u0.m).offset(nv, n0.m)
  p0 = Geom::Point3d.new(p0.x, p0.y, z0.m)
  add_solid(parent, name, p0, uv, (u1 - u0), nv, (n1 - n0), (z1 - z0), fmat, bmat)
end

def add_box(parent, name, x0, x1, y0, y1, z0, z1, fmat, bmat = nil)
  add_local(parent, name, ORG, VX, VY, x0, x1, y0, y1, z0, z1, fmat, bmat)
end

def add_cyl(parent, name, x, y, z0, r, h, fmat)
  g = parent.entities.add_group
  g.name = name
  e = g.entities
  f = e.add_face(e.add_circle(Geom::Point3d.new(x.m, y.m, z0.m), VZ, r.m, 16))
  unless f.nil?
    f.reverse! if f.normal.z < 0.0
    f.pushpull(h.abs.m)
    g.entities.grep(Sketchup::Face).each { |fc| fc.material = fmat; fc.back_material = fmat }
  end
  g
end

def add_plant(parent, name, x, y, z0, s = 1.0)
  add_cyl(parent, "#{name}_POT",   x, y, z0,            0.19 * s, 0.36 * s, MAT[:pot])
  add_cyl(parent, "#{name}_LEAF1", x, y, z0 + 0.30 * s, 0.30 * s, 0.55 * s, MAT[:leaf])
  add_cyl(parent, "#{name}_LEAF2", x, y, z0 + 0.72 * s, 0.22 * s, 0.40 * s, MAT[:leaf])
end

# 通高墙：墙垛整高成块，洞口列只在洞口上下沿分段（跨层不断开）
def add_wall(parent, name, o, uv, nv, ub, ue, thick, z0, z1, ops, fmat)
  us = ([ub, ue] + ops.flat_map { |op| [op[:u], op[:u] + op[:w]] })
       .select { |u| u >= ub - 1e-6 && u <= ue + 1e-6 }.uniq.sort
  cnt = 0
  us.each_cons(2) do |a, b|
    next if (b - a) < 1e-6
    mid = (a + b) * 0.5
    cov = ops.select { |op| op[:u] <= mid + 1e-9 && mid <= op[:u] + op[:w] - 1e-9 }
    if cov.empty?
      cnt += 1
      add_local(parent, "#{name}_P#{cnt}", o, uv, nv, a, b, 0.0, thick, z0, z1, fmat)
    else
      zs = ([z0, z1] + cov.flat_map { |op| [op[:z0], op[:z1]] }).uniq.sort
      zs.each_cons(2) do |za, zb|
        next if (zb - za) < 1e-6
        midz = (za + zb) * 0.5
        next if cov.any? { |op| op[:z0] <= midz && midz <= op[:z1] }
        cnt += 1
        add_local(parent, "#{name}_P#{cnt}", o, uv, nv, a, b, 0.0, thick, za, zb, fmat)
      end
    end
  end
end

# 边线处理：隐藏非洞口水平边 + 洞口两侧贯通竖边
def clean_wall_edges(grp, o, uv, ops)
  hz = 0
  vt = 0
  grp.entities.grep(Sketchup::Edge).each do |e|
    a = e.start.position
    b = e.end.position
    if (a.z - b.z).abs < 0.5.mm
      zmm = a.z.to_m * 1000.0
      u1 = (a - o).dot(uv).to_m * 1000.0
      u2 = (b - o).dot(uv).to_m * 1000.0
      umin = [u1, u2].min
      umax = [u1, u2].max
      real = ops.any? do |op|
        ((zmm - op[:z0] * 1000.0).abs < 2.0 || (zmm - op[:z1] * 1000.0).abs < 2.0) &&
          umin >= op[:u] * 1000.0 - 8.0 && umax <= (op[:u] + op[:w]) * 1000.0 + 8.0
      end
      unless real
        e.hidden = true unless e.hidden?
        hz += 1
      end
    elsif (a.x - b.x).abs < 0.5.mm && (a.y - b.y).abs < 0.5.mm
      u = ((a - o).dot(uv).to_m + (b - o).dot(uv).to_m) / 2.0 * 1000.0
      if ops.any? { |op| (u - op[:u] * 1000.0).abs < 8.0 || (u - (op[:u] + op[:w]) * 1000.0).abs < 8.0 }
        e.hidden = true unless e.hidden?
        vt += 1
      end
    end
  end
  [hz, vt]
end

def hide_all_edges(grp)
  n = 0
  grp.entities.each do |e|
    if e.is_a?(Sketchup::Group)
      n += hide_all_edges(e)
    elsif e.is_a?(Sketchup::Edge)
      e.hidden = true unless e.hidden?
      n += 1
    end
  end
  n
end

def add_narrow_window(parent, base, o, uv, nv, u0, z0)
  w = 0.70; h = 1.45; fw = 0.06; n0 = 0.070; n1 = 0.150
  add_local(parent, "#{base}_SILL",   o, uv, nv, u0, u0 + w, n0, n1, z0, z0 + fw, MAT[:frame])
  add_local(parent, "#{base}_HEAD",   o, uv, nv, u0, u0 + w, n0, n1, z0 + h - fw, z0 + h, MAT[:frame])
  add_local(parent, "#{base}_JAMB_L", o, uv, nv, u0, u0 + fw, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_JAMB_R", o, uv, nv, u0 + w - fw, u0 + w, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_GLASS",  o, uv, nv, u0 + fw, u0 + w - fw, 0.105, 0.125, z0 + fw, z0 + h - fw, MAT[:glassd])
end

def add_mullion_window(parent, base, o, uv, nv, u0, z0)
  w = 1.00; h = 1.45; fw = 0.06; n0 = 0.070; n1 = 0.150
  add_local(parent, "#{base}_SILL",    o, uv, nv, u0, u0 + w, n0, n1, z0, z0 + fw, MAT[:frame])
  add_local(parent, "#{base}_HEAD",    o, uv, nv, u0, u0 + w, n0, n1, z0 + h - fw, z0 + h, MAT[:frame])
  add_local(parent, "#{base}_JAMB_L",  o, uv, nv, u0, u0 + fw, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_JAMB_R",  o, uv, nv, u0 + w - fw, u0 + w, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_MULLION", o, uv, nv, u0 + w / 2 - 0.025, u0 + w / 2 + 0.025, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_GLASS_L", o, uv, nv, u0 + fw, u0 + w / 2 - 0.025, 0.105, 0.125, z0 + fw, z0 + h - fw, MAT[:glassd])
  add_local(parent, "#{base}_GLASS_R", o, uv, nv, u0 + w / 2 + 0.025, u0 + w - fw, 0.105, 0.125, z0 + fw, z0 + h - fw, MAT[:glassd])
end

def add_glazing(parent, base, o, uv, nv, u0, w, z0, h, panels, gmat)
  fw = 0.07
  add_local(parent, "#{base}_SILL",   o, uv, nv, u0, u0 + w, 0.03, 0.11, z0, z0 + fw, MAT[:frame])
  add_local(parent, "#{base}_HEAD",   o, uv, nv, u0, u0 + w, 0.03, 0.11, z0 + h - fw, z0 + h, MAT[:frame])
  add_local(parent, "#{base}_JAMB_L", o, uv, nv, u0, u0 + fw, 0.03, 0.11, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_JAMB_R", o, uv, nv, u0 + w - fw, u0 + w, 0.03, 0.11, z0 + fw, z0 + h - fw, MAT[:frame])
  xs = (1...panels).map { |i| u0 + w * i / panels.to_f }
  xs.each_with_index { |x, i| add_local(parent, "#{base}_MULL#{i + 1}", o, uv, nv, x - 0.025, x + 0.025, 0.03, 0.11, z0 + fw, z0 + h - fw, MAT[:frame]) }
  bounds = [u0 + fw] + xs + [u0 + w - fw]
  bounds.each_cons(2).with_index { |(a, b), i| add_local(parent, "#{base}_GLASS#{i + 1}", o, uv, nv, a + 0.02, b - 0.02, 0.05, 0.07, z0 + fw, z0 + h - fw, gmat) }
end

def add_entry_door(parent, base, o, uv, nv, u0)
  w = 1.00; h = 2.30; fw = 0.06
  add_local(parent, "#{base}_SILL",   o, uv, nv, u0, u0 + w, 0.02, 0.12, 0.0, fw, MAT[:frame])
  add_local(parent, "#{base}_HEAD",   o, uv, nv, u0, u0 + w, 0.02, 0.12, h - fw, h, MAT[:frame])
  add_local(parent, "#{base}_JAMB_L", o, uv, nv, u0, u0 + fw, 0.02, 0.12, fw, h - fw, MAT[:frame])
  add_local(parent, "#{base}_JAMB_R", o, uv, nv, u0 + w - fw, u0 + w, 0.02, 0.12, fw, h - fw, MAT[:frame])
  add_local(parent, "#{base}_LEAF",   o, uv, nv, u0 + fw, u0 + w - fw, 0.05, 0.09, 0.0, h - fw, MAT[:door])
  add_local(parent, "#{base}_HANDLE", o, uv, nv, u0 + w - 0.28, u0 + w - 0.22, 0.01, 0.05, 0.95, 1.10, MAT[:metal])
end

# ---------------- 材质 ----------------
MAT = {}
MAT[:wall]   = smat(model, "MAT_WALL_WHITE",     238, 236, 232)
MAT[:plinth] = smat(model, "MAT_PLINTH_GRAY",    168, 168, 166)
MAT[:roof]   = smat(model, "MAT_ROOF_MEMBRANE",  158, 160, 160)
MAT[:joint]  = smat(model, "MAT_ROOF_JOINT",     122, 124, 124)
MAT[:coping] = smat(model, "MAT_COPING_WHITE",   244, 243, 240)
MAT[:wood]   = smat(model, "MAT_WOOD_SLAT",      196, 158, 112)   # 柔和浅棕木色
MAT[:frame]  = smat(model, "MAT_FRAME_DARK",      42,  45,  48)
MAT[:door]   = smat(model, "MAT_DOOR_DARK",       58,  60,  62)
MAT[:glassc] = smat(model, "MAT_GLASS_CLEAR",    178, 200, 205, 0.30)
MAT[:glassd] = smat(model, "MAT_GLASS_DARK",      62,  76,  84, 0.75)
MAT[:metal]  = smat(model, "MAT_METAL_DARK",      96,  98, 100)
MAT[:pave]   = smat(model, "MAT_PAVING",         196, 197, 196)
MAT[:lawn]   = smat(model, "MAT_LAWN",           108, 152,  74)
MAT[:floor]  = smat(model, "MAT_FLOOR_LIGHT",    226, 223, 218)
MAT[:fab]    = smat(model, "MAT_FABRIC",         214, 212, 206)
MAT[:woodf]  = smat(model, "MAT_WOOD_FURN",      168, 132,  96)
MAT[:leaf]   = smat(model, "MAT_LEAF",            74, 122,  58)
MAT[:pot]    = smat(model, "MAT_POT",            120, 118, 114)
MAT[:rug]    = smat(model, "MAT_RUG",            224, 216, 200)
MAT[:art]    = smat(model, "MAT_ART",            240, 238, 234)

g_site  = root.entities.add_group; g_site.name  = "SITE_场地"
g_shell = root.entities.add_group; g_shell.name = "SHELL_主体"
g_open  = root.entities.add_group; g_open.name  = "OPENINGS_门窗"
g_bal   = root.entities.add_group; g_bal.name   = "BALCONY_阳台"
g_louv  = root.entities.add_group; g_louv.name  = "LOUVER_木格栅"
g_int   = root.entities.add_group; g_int.name   = "INTERIOR_室内示意"

# ---------------- 勒脚 / 楼板 ----------------
add_box(g_shell, "PLINTH_FRONT", -0.03, 10.03, -0.03, 0.00, -0.30, 0.05, MAT[:plinth])
add_box(g_shell, "PLINTH_REAR",  -0.03, 10.03,  8.00, 8.03, -0.30, 0.05, MAT[:plinth])
add_box(g_shell, "PLINTH_RIGHT", 10.00, 10.03, -0.03, 8.03, -0.30, 0.05, MAT[:plinth])
add_box(g_shell, "PLINTH_LEFT",  -0.03,  0.00, -0.03, 8.03, -0.30, 0.05, MAT[:plinth])
add_box(g_shell, "FLOOR_GF", 0.01, 9.99, 0.01, 7.99, -0.15, 0.00, MAT[:floor], MAT[:wall])
add_box(g_shell, "FLOOR_2F", 0.01, 9.99, 0.01, 7.99,  3.00, 3.20, MAT[:floor], MAT[:wall])

# ---------------- 四面通高外墙（修订 B 开口；每面一次建成）----------------
WALLS = [
  { key: "FRONT", o: mp(0, 0, 0),  uv: VX,  nv: VY,  ub: 0.00, ue: 10.00,
    ops: [{ u: 2.00, w: 5.80, z0: 0.00, z1: 2.70 }, { u: 2.30, w: 1.90, z0: 3.20, z1: 5.80 }, { u: 5.80, w: 1.90, z0: 3.20, z1: 5.80 }] },
  { key: "REAR",  o: mp(10, 8, 0), uv: VNX, nv: VNY, ub: 0.00, ue: 10.00,
    ops: [{ u: 2.15, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 4.65, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 7.15, w: 0.70, z0: 0.90, z1: 2.35 },
          { u: 2.15, w: 0.70, z0: 4.10, z1: 5.55 }, { u: 4.65, w: 0.70, z0: 4.10, z1: 5.55 }, { u: 7.15, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "LEFT",  o: mp(0, 8, 0),  uv: VNY, nv: VX,  ub: 0.20, ue: 7.80,
    ops: [{ u: 3.65, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 3.65, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "RIGHT", o: mp(10, 0, 0), uv: VY,  nv: VNX, ub: 0.20, ue: 7.80,
    ops: [{ u: 1.00, w: 1.00, z0: 0.00, z1: 2.30 }, { u: 4.00, w: 1.00, z0: 4.10, z1: 5.55 }] }
]
WALLS.each { |w| add_wall(g_shell, w[:key], w[:o], w[:uv], w[:nv], w[:ub], w[:ue], 0.20, -0.30, 6.40, w[:ops], MAT[:wall]) }

# ---------------- 屋面 / 分格缝 / 泛水 / 女儿墙 / 压顶 ----------------
add_box(g_shell, "ROOF_SLAB", 0.01, 9.99, 0.01, 7.99, 6.20, 6.38, MAT[:roof], MAT[:wall])
add_box(g_shell, "ROOF_DECK", 0.20, 9.80, 0.20, 7.80, 6.38, 6.40, MAT[:roof], MAT[:roof])
add_box(g_shell, "ROOF_JOINT_X1", 3.3875, 3.4125, 0.20, 7.80, 6.394, 6.400, MAT[:joint])
add_box(g_shell, "ROOF_JOINT_X2", 6.5875, 6.6125, 0.20, 7.80, 6.394, 6.400, MAT[:joint])
add_box(g_shell, "ROOF_JOINT_Y1", 0.20, 9.80, 3.9875, 4.0125, 6.394, 6.400, MAT[:joint])
add_box(g_shell, "ROOF_UPTURN_FRONT", 0.20, 9.80, 0.20, 0.25, 6.40, 6.50, MAT[:roof])
add_box(g_shell, "ROOF_UPTURN_REAR",  0.20, 9.80, 7.75, 7.80, 6.40, 6.50, MAT[:roof])
add_box(g_shell, "ROOF_UPTURN_RIGHT", 9.75, 9.80, 0.25, 7.75, 6.40, 6.50, MAT[:roof])
add_box(g_shell, "ROOF_UPTURN_LEFT",  0.20, 0.25, 0.25, 7.75, 6.40, 6.50, MAT[:roof])
add_box(g_shell, "PARAPET_FRONT", 0.00, 10.00, 0.00, 0.20, 6.40, 6.75, MAT[:wall])
add_box(g_shell, "PARAPET_REAR",  0.00, 10.00, 7.80, 8.00, 6.40, 6.75, MAT[:wall])
add_box(g_shell, "PARAPET_RIGHT", 9.80, 10.00, 0.20, 7.80, 6.40, 6.75, MAT[:wall])
add_box(g_shell, "PARAPET_LEFT",  0.00,  0.20, 0.20, 7.80, 6.40, 6.75, MAT[:wall])
add_box(g_shell, "COPING_FRONT", -0.02, 10.02, -0.02, 0.20, 6.75, 6.79, MAT[:coping])
add_box(g_shell, "COPING_REAR",  -0.02, 10.02,  7.80, 8.02, 6.75, 6.79, MAT[:coping])
add_box(g_shell, "COPING_RIGHT",  9.80, 10.02, -0.02, 8.02, 6.75, 6.79, MAT[:coping])
add_box(g_shell, "COPING_LEFT",  -0.02,  0.20, -0.02, 8.02, 6.75, 6.79, MAT[:coping])

# ---------------- 窗与门 ----------------
add_narrow_window(g_open, "WINDOW_REAR_L1_1", WALLS[1][:o], VNX, VNY, 2.15, 0.90)
add_narrow_window(g_open, "WINDOW_REAR_L1_2", WALLS[1][:o], VNX, VNY, 4.65, 0.90)
add_narrow_window(g_open, "WINDOW_REAR_L1_3", WALLS[1][:o], VNX, VNY, 7.15, 0.90)
add_narrow_window(g_open, "WINDOW_REAR_L2_1", WALLS[1][:o], VNX, VNY, 2.15, 4.10)
add_narrow_window(g_open, "WINDOW_REAR_L2_2", WALLS[1][:o], VNX, VNY, 4.65, 4.10)
add_narrow_window(g_open, "WINDOW_REAR_L2_3", WALLS[1][:o], VNX, VNY, 7.15, 4.10)
add_narrow_window(g_open, "WINDOW_LEFT_L1_1", WALLS[2][:o], VNY, VX, 3.65, 0.90)
add_narrow_window(g_open, "WINDOW_LEFT_L2_1", WALLS[2][:o], VNY, VX, 3.65, 4.10)
add_mullion_window(g_open, "WINDOW_RIGHT_L2_1", WALLS[3][:o], VY, VNX, 4.00, 4.10)
add_glazing(g_open, "GLAZING_FRONT_L1", WALLS[0][:o], VX, VY, 2.00, 5.80, 0.00, 2.70, 4, MAT[:glassc])
add_glazing(g_open, "DOOR_FRONT_L2_A",  WALLS[0][:o], VX, VY, 2.30, 1.90, 3.20, 2.60, 2, MAT[:glassc])
add_glazing(g_open, "DOOR_FRONT_L2_B",  WALLS[0][:o], VX, VY, 5.80, 1.90, 3.20, 2.60, 2, MAT[:glassc])
add_entry_door(g_open, "ENTRY_DOOR", WALLS[3][:o], VY, VNX, 1.00)
add_box(g_open, "ENTRY_CANOPY", 10.00, 10.90, 0.65, 2.35, 2.55, 2.70, MAT[:coping], MAT[:wall])

# ---------------- 阳台 ----------------
add_box(g_bal, "BALCONY_SLAB", 1.20, 8.80, -1.80, 0.00, 3.00, 3.20, MAT[:floor], MAT[:wall])
(0..7).each { |k| x = 1.20 + k * 1.08; add_local(g_bal, "RAIL_POST_#{k + 1}", ORG, VX, VY, x, x + 0.04, -1.82, -1.78, 3.20, 4.30, MAT[:metal]) }
(0..6).each { |k| add_local(g_bal, "RAIL_GLASS_#{k + 1}", ORG, VX, VY, 1.24 + k * 1.08, 2.28 + k * 1.08, -1.806, -1.794, 3.24, 4.28, MAT[:glassc]) }
add_local(g_bal, "RAIL_TOP", ORG, VX, VY, 1.20, 8.80, -1.83, -1.77, 4.30, 4.35, MAT[:metal])
add_local(g_bal, "RAIL_RETURN_L_GLASS", ORG, VNY, VX, 0.02, 1.78, 1.200, 1.212, 3.24, 4.28, MAT[:glassc])
add_local(g_bal, "RAIL_RETURN_L_TOP",   ORG, VNY, VX, -0.03, 1.83, 1.200, 1.260, 4.30, 4.35, MAT[:metal])
add_local(g_bal, "RAIL_RETURN_R_GLASS", ORG, VNY, VX, 0.02, 1.78, 8.788, 8.800, 3.24, 4.28, MAT[:glassc])
add_local(g_bal, "RAIL_RETURN_R_TOP",   ORG, VNY, VX, -0.03, 1.83, 8.740, 8.800, 4.30, 4.35, MAT[:metal])
add_box(g_bal, "BAL_CONSOLE", 4.30, 5.90, -1.55, -0.95, 3.20, 3.66, MAT[:fab])
add_box(g_bal, "BAL_TABLE",   6.35, 6.95, -1.45, -0.95, 3.20, 3.62, MAT[:woodf])   # 含上一轮 +50mm
add_plant(g_bal, "BAL_PLANT_A", 1.85, -1.35, 3.20, 1.0)
add_plant(g_bal, "BAL_PLANT_B", 8.15, -1.35, 3.20, 1.0)

# ---------------- 木格栅（正立面 15 根 + 转角 14 根，边线隐藏）----------------
15.times { |k| x = 9.025 + k * 0.065; add_local(g_louv, format("LOUVER_FRONT_%02d", k + 1), ORG, VX, VY, x, x + 0.04, -0.03, 0.0, 0.05, 6.75, MAT[:wood]) }
14.times { |k| y = 0.0 + k * 0.065;   add_local(g_louv, format("LOUVER_RIGHT_%02d", k + 1), mp(10, 0, 0), VY, VNX, y, y + 0.04, -0.03, 0.0, 0.05, 6.75, MAT[:wood]) }
g_louv.entities.grep(Sketchup::Group).each { |s| hide_all_edges(s) }

# ---------------- 室内示意 ----------------
add_box(g_int, "GF_RUG", 3.00, 5.60, 3.00, 5.00, 0.000, 0.012, MAT[:rug])
add_box(g_int, "GF_SOFA_SEAT", 3.30, 5.30, 4.10, 4.95, 0.050, 0.420, MAT[:fab])
add_box(g_int, "GF_SOFA_BACK", 3.30, 5.30, 4.75, 4.95, 0.420, 0.820, MAT[:fab])
add_box(g_int, "GF_SOFA_ARM_L", 3.30, 3.45, 4.10, 4.95, 0.420, 0.600, MAT[:fab])
add_box(g_int, "GF_SOFA_ARM_R", 5.15, 5.30, 4.10, 4.95, 0.420, 0.600, MAT[:fab])
add_box(g_int, "GF_TABLE", 3.90, 4.90, 3.30, 3.80, 0.000, 0.380, MAT[:woodf])
add_box(g_int, "GF_DINING_TOP", 6.40, 7.80, 3.40, 4.30, 0.700, 0.760, MAT[:woodf])
add_box(g_int, "GF_DINING_BASE", 6.55, 7.65, 3.60, 4.10, 0.096, 0.700, MAT[:woodf])
[[6.55, 3.02, 1], [7.25, 3.02, 1], [6.55, 4.34, -1], [7.25, 4.34, -1]].each_with_index do |(cx, cy, dir), i|
  add_box(g_int, "GF_CHAIR#{i + 1}_SEAT", cx, cx + 0.42, cy - 0.21, cy + 0.21, 0.000, 0.450, MAT[:fab])
  by = dir > 0 ? cy - 0.27 : cy + 0.21
  add_box(g_int, "GF_CHAIR#{i + 1}_BACK", cx, cx + 0.42, by, by + 0.06, 0.450, 0.850, MAT[:fab])
end
add_box(g_int, "GF_ART_FRAME", 4.02, 4.98, 7.74, 7.80, 1.25, 2.45, MAT[:frame])
add_box(g_int, "GF_ART_PANEL", 4.06, 4.94, 7.70, 7.74, 1.29, 2.41, MAT[:art])
add_plant(g_int, "GF_PLANT_A", 2.55, 1.05, 0.00, 1.0)
add_plant(g_int, "GF_PLANT_B", 7.25, 1.05, 0.00, 1.0)
add_box(g_int, "2F_RUG", 3.00, 5.60, 1.20, 3.00, 3.200, 3.212, MAT[:rug])
add_box(g_int, "2F_CABINET", 5.60, 6.60, 2.60, 3.05, 3.200, 3.650, MAT[:woodf])
add_plant(g_int, "2F_PLANT", 3.20, 1.00, 3.20, 0.9)

# ---------------- 场地 ----------------
add_box(g_site, "LAWN", -8.00, 18.00, -6.00, 14.00, -0.340, -0.300, MAT[:lawn])
add_box(g_site, "PAVING_ENTRY", 8.00, 12.60, -2.40, 3.20, -0.300, -0.280, MAT[:pave])
add_box(g_site, "STEP_LOWER", 10.00, 10.70, 0.85, 2.15, -0.300, -0.150, MAT[:pave])
add_box(g_site, "STEP_UPPER", 10.00, 10.35, 0.85, 2.15, -0.300, 0.000, MAT[:pave])
add_plant(g_site, "ENTRY_PLANT", 10.75, 2.55, -0.30, 1.0)

# ---------------- 收尾：墙面接缝/洞口竖线隐藏 + 楼板与屋面板边线隐藏 ----------------
WALLS.each do |w|
  g_shell.entities.grep(Sketchup::Group).select { |c| c.name.to_s.start_with?("#{w[:key]}_") }.each do |c|
    clean_wall_edges(c, w[:o], w[:uv], w[:ops])
  end
end
["FLOOR_GF", "FLOOR_2F", "ROOF_SLAB"].each do |nm|
  g = g_shell.entities.grep(Sketchup::Group).find { |c| c.name == nm }
  hide_all_edges(g) unless g.nil?
end

"BUILD_REV_D_OK groups=#{root.entities.count}"
