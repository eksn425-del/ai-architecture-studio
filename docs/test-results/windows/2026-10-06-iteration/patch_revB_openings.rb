# ============================================================
# patch_revB_openings.rb —— 修订 B 局部 edit 补丁（下次执行轮运行）
# 保留：SHELL_主体 / OPENINGS_门窗 顶层组 ID；正立面玻璃、入户门/雨棚/台阶、场地、阳台、室内 ID
# 只替换：后墙 / 左墙 / 右墙的墙段 child + 其对应小窗 child
# 追加：屋面分格缝 ROOF_JOINT_X1/X2/Y1；木格栅只调色（不动几何、不动根数）
# 单位纪律：所有坐标经 mp()；体块基面法线强制朝 +Z；墙面接缝隐藏；楼板内缩保持
# ============================================================
VX  = Geom::Vector3d.new( 1, 0, 0)
VY  = Geom::Vector3d.new( 0, 1, 0)
VZ  = Geom::Vector3d.new( 0, 0, 1)
VNX = Geom::Vector3d.new(-1, 0, 0)
VNY = Geom::Vector3d.new( 0,-1, 0)
ORG = Geom::Point3d.new(0, 0, 0)

def mp(x, y, z)
  Geom::Point3d.new(x.m, y.m, z.m)
end

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

# 干净分解：墙垛整高成块，只在洞口列出现窗台/窗楣分段（不产生额外水平接缝）
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

# 窄竖窗 0.70 x 1.45，框内凹 70mm（框深 80mm，框宽 60mm）
def add_narrow_window(parent, base, o, uv, nv, u0, z0)
  w = 0.70; h = 1.45; fw = 0.06; n0 = 0.070; n1 = 0.150
  add_local(parent, "#{base}_SILL",   o, uv, nv, u0, u0 + w, n0, n1, z0, z0 + fw, MAT[:frame])
  add_local(parent, "#{base}_HEAD",   o, uv, nv, u0, u0 + w, n0, n1, z0 + h - fw, z0 + h, MAT[:frame])
  add_local(parent, "#{base}_JAMB_L", o, uv, nv, u0, u0 + fw, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_JAMB_R", o, uv, nv, u0 + w - fw, u0 + w, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_GLASS",  o, uv, nv, u0 + fw, u0 + w - fw, 0.105, 0.125, z0 + fw, z0 + h - fw, MAT[:glassd])
end

# 带中梃窗 1.00 x 1.45（中梃居中），框内凹 70mm
def add_mullion_window(parent, base, o, uv, nv, u0, z0)
  w = 1.00; h = 1.45; fw = 0.06; n0 = 0.070; n1 = 0.150
  add_local(parent, "#{base}_SILL",   o, uv, nv, u0, u0 + w, n0, n1, z0, z0 + fw, MAT[:frame])
  add_local(parent, "#{base}_HEAD",   o, uv, nv, u0, u0 + w, n0, n1, z0 + h - fw, z0 + h, MAT[:frame])
  add_local(parent, "#{base}_JAMB_L", o, uv, nv, u0, u0 + fw, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_JAMB_R", o, uv, nv, u0 + w - fw, u0 + w, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_MULLION", o, uv, nv, u0 + w / 2 - 0.025, u0 + w / 2 + 0.025, n0, n1, z0 + fw, z0 + h - fw, MAT[:frame])
  add_local(parent, "#{base}_GLASS_L", o, uv, nv, u0 + fw, u0 + w / 2 - 0.025, 0.105, 0.125, z0 + fw, z0 + h - fw, MAT[:glassd])
  add_local(parent, "#{base}_GLASS_R", o, uv, nv, u0 + w / 2 + 0.025, u0 + w - fw, 0.105, 0.125, z0 + fw, z0 + h - fw, MAT[:glassd])
end

def find_group(host, name)
  host.entities.each { |e| return e if e.is_a?(Sketchup::Group) && e.name == name }
  nil
end

def kids_with_prefix(host, prefix)
  host.entities.grep(Sketchup::Group).select { |c| c.name.to_s.start_with?(prefix) }
end

MAT = {}
MAT[:wall]   = smat(model, "MAT_WALL_WHITE",     238, 236, 232)
MAT[:wood]   = smat(model, "MAT_WOOD_SLAT",      214, 152,  84)   # 暖木色（本轮调暖）
MAT[:frame]  = smat(model, "MAT_FRAME_DARK",      42,  45,  48)
MAT[:glassd] = smat(model, "MAT_GLASS_DARK",      62,  76,  84, 0.75)
MAT[:joint]  = smat(model, "MAT_ROOF_JOINT",     122, 124, 124)

# ---- 洞口表（修订 B）----
WALL_DEFS = [
  { key: "REAR",  host: "SHELL_主体", o: mp(10, 8, 0), uv: VNX, nv: VNY,
    ops_l1: [{ u: 2.15, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 4.65, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 7.15, w: 0.70, z0: 0.90, z1: 2.35 }],
    ops_l2: [{ u: 2.15, w: 0.70, z0: 4.10, z1: 5.55 }, { u: 4.65, w: 0.70, z0: 4.10, z1: 5.55 }, { u: 7.15, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "LEFT",  host: "SHELL_主体", o: mp(0, 8, 0),  uv: VNY, nv: VX,
    ops_l1: [{ u: 3.65, w: 0.70, z0: 0.90, z1: 2.35 }],
    ops_l2: [{ u: 3.65, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "RIGHT", host: "SHELL_主体", o: mp(10, 0, 0), uv: VY,  nv: VNX,
    ops_l1: [{ u: 1.00, w: 1.00, z0: 0.00, z1: 2.30 }],          # 底层只留门洞，不再留小窗
    ops_l2: [{ u: 4.00, w: 1.00, z0: 4.10, z1: 5.55 }] }         # 二层 1 樘带中梃窗
]

log = []

# ---- 1) 删除后/左/右墙段与对应小窗 child（命名路径数组，保留顶层组 ID）----
["REAR_", "LEFT_", "RIGHT_"].each do |pfx|
  kids_with_prefix(find_group(root, "SHELL_主体"), pfx).each do |c|
    remove_owned_group.call(["SHELL_主体", c.name.to_s])
  end
end
["WINDOW_REAR_", "WINDOW_LEFT_", "WINDOW_RIGHT_"].each do |pfx|
  kids_with_prefix(find_group(root, "OPENINGS_门窗"), pfx).each do |c|
    remove_owned_group.call(["OPENINGS_门窗", c.name.to_s])
  end
end
log << "removed_rear_left_right"

shell = find_group(root, "SHELL_主体")
open  = find_group(root, "OPENINGS_门窗")

# ---- 2) 重建三面墙（修订 B 开口）----
WALL_DEFS.each do |w|
  add_wall(shell, "#{w[:key]}_L1", w[:o], w[:uv], w[:nv], (w[:key] == "RIGHT" ? 0.20 : (w[:key] == "LEFT" ? 0.20 : 0.0)),
           (w[:key] == "RIGHT" ? 7.80 : (w[:key] == "LEFT" ? 7.80 : 10.0)), 0.20, -0.30, 3.20, w[:ops_l1], MAT[:wall])
  add_wall(shell, "#{w[:key]}_L2", w[:o], w[:uv], w[:nv], (w[:key] == "RIGHT" ? 0.20 : (w[:key] == "LEFT" ? 0.20 : 0.0)),
           (w[:key] == "RIGHT" ? 7.80 : (w[:key] == "LEFT" ? 7.80 : 10.0)), 0.20, 3.20, 6.40, w[:ops_l2], MAT[:wall])
end

# ---- 3) 新建 9 樘窗 ----
[["REAR_L1", 0, 0.90], ["REAR_L1", 1, 0.90], ["REAR_L1", 2, 0.90],
 ["REAR_L2", 0, 4.10], ["REAR_L2", 1, 4.10], ["REAR_L2", 2, 4.10]].each_with_index do |(tag, i, z), n|
  w = WALL_DEFS[0]
  op = (tag == "REAR_L1" ? w[:ops_l1] : w[:ops_l2])[i]
  add_narrow_window(open, "WINDOW_REAR_#{tag}_#{i + 1}", w[:o], w[:uv], w[:nv], op[:u], z)
end
[["LEFT_L1", 0.90], ["LEFT_L2", 4.10]].each_with_index do |(tag, z), i|
  w = WALL_DEFS[1]
  op = (tag == "LEFT_L1" ? w[:ops_l1] : w[:ops_l2])[0]
  add_narrow_window(open, "WINDOW_LEFT_#{tag}_#{i + 1}", w[:o], w[:uv], w[:nv], op[:u], z)
end
add_mullion_window(open, "WINDOW_RIGHT_L2_1", WALL_DEFS[2][:o], WALL_DEFS[2][:uv], WALL_DEFS[2][:nv], 4.00, 4.10)

# ---- 4) 屋面卷材分格缝（浅槽，独立命名）----
add_box(shell, "ROOF_JOINT_X1", 3.3875, 3.4125, 0.20, 7.80, 6.394, 6.400, MAT[:joint])
add_box(shell, "ROOF_JOINT_X2", 6.5875, 6.6125, 0.20, 7.80, 6.394, 6.400, MAT[:joint])
add_box(shell, "ROOF_JOINT_Y1", 0.20, 9.80, 3.9875, 4.0125, 6.394, 6.400, MAT[:joint])

# ---- 5) 新墙段接缝隐藏（只隐藏非洞口水平边，保留真实洞口上下沿）----
def clean_seams(grp, wall)
  h = 0
  grp.entities.grep(Sketchup::Edge).each do |e|
    a = e.start.position
    b = e.end.position
    next if (a.z - b.z).abs > 0.5.mm
    zmm = a.z.to_m * 1000.0
    u1 = (a - wall[:o]).dot(wall[:uv]).to_m * 1000.0
    u2 = (b - wall[:o]).dot(wall[:uv]).to_m * 1000.0
    umin = [u1, u2].min
    umax = [u1, u2].max
    real = (wall[:ops_l1] + wall[:ops_l2]).any? do |op|
      ((zmm - op[:z0] * 1000.0).abs < 2.0 || (zmm - op[:z1] * 1000.0).abs < 2.0) &&
        umin >= op[:u] * 1000.0 - 8.0 && umax <= (op[:u] + op[:w]) * 1000.0 + 8.0
    end
    unless real
      e.hidden = true unless e.hidden?
      h += 1
    end
  end
  h
end

WALL_DEFS.each do |w|
  kids_with_prefix(shell, "#{w[:key]}_").each { |c| clean_seams(c, w) }
end

# ---- 6) 木格栅：只调色（不动几何与根数）----
louv = find_group(root, "LOUVER_木格栅")
n_slat = louv ? louv.entities.grep(Sketchup::Group).count : 0
if louv
  louv.entities.grep(Sketchup::Group).each do |s|
    s.entities.grep(Sketchup::Face).each { |f| f.material = MAT[:wood]; f.back_material = MAT[:wood] }
  end
end

"REV_B_DONE walls=#{WALL_DEFS.size} windows=9 joints=3 slats=#{n_slat} | #{log.join(',')}"
