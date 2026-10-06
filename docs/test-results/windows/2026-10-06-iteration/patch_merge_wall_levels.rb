# ============================================================
# patch_merge_wall_levels.rb —— 消除"双水平黑线"（edit 模式，同一 build_villa root）
# 成因：rev16 重建后/左/右墙时按 L1、L2 分两次建，二层楼面 z=3200 处两组体块共面相接，
#       产生两条贯通整墙的水平边（斜视可见）。
# 修法：每面墙改为"一次建成通高列"，z 分段只出现在真实洞口（窗台/窗楣）处。
# 只编辑 SHELL_主体 内后/左/右墙段；窗 child、正立面、阳台、场地、室内、木格栅几何均不动。
# 木格栅只改材质颜色为柔和浅棕木色（根数/几何不变）。
# ============================================================
VX  = Geom::Vector3d.new( 1, 0, 0)
VY  = Geom::Vector3d.new( 0, 1, 0)
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

# 通高墙：墙垛整高成块；洞口列只在洞口上下沿分段（跨层不再断开）
def add_wall_full(parent, name, o, uv, nv, ub, ue, thick, z0, z1, ops, fmat)
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

def find_group(host, name)
  host.entities.each { |e| return e if e.is_a?(Sketchup::Group) && e.name == name }
  nil
end

def kids_with_prefix(host, prefix)
  host.entities.grep(Sketchup::Group).select { |c| c.name.to_s.start_with?(prefix) }
end

MAT = {}
MAT[:wall] = smat(model, "MAT_WALL_WHITE", 238, 236, 232)
MAT[:wood] = smat(model, "MAT_WOOD_SLAT",  196, 158, 112)   # 柔和浅棕木色（本轮）

WALLS = [
  { key: "REAR",  o: mp(10, 8, 0), uv: VNX, nv: VNY, ub: 0.00, ue: 10.00,
    ops: [{ u: 2.15, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 4.65, w: 0.70, z0: 0.90, z1: 2.35 },
          { u: 7.15, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 2.15, w: 0.70, z0: 4.10, z1: 5.55 },
          { u: 4.65, w: 0.70, z0: 4.10, z1: 5.55 }, { u: 7.15, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "LEFT",  o: mp(0, 8, 0),  uv: VNY, nv: VX,  ub: 0.20, ue: 7.80,
    ops: [{ u: 3.65, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 3.65, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "RIGHT", o: mp(10, 0, 0), uv: VY,  nv: VNX, ub: 0.20, ue: 7.80,
    ops: [{ u: 1.00, w: 1.00, z0: 0.00, z1: 2.30 }, { u: 4.00, w: 1.00, z0: 4.10, z1: 5.55 }] }
]

shell = find_group(root, "SHELL_主体")
log = []

# ---- 1) 删除后/左/右墙的 L1、L2 段（命名路径数组，保留 SHELL 顶层组 ID）----
WALLS.each do |w|
  ["#{w[:key]}_L1_", "#{w[:key]}_L2_"].each do |pfx|
    kids_with_prefix(shell, pfx).each { |c| remove_owned_group.call(["SHELL_主体", c.name.to_s]) }
  end
end
log << "removed L1/L2 wall segs"

# ---- 2) 每面墙重建为通高（跨层不再断开）----
shell = find_group(root, "SHELL_主体")
WALLS.each do |w|
  add_wall_full(shell, w[:key], w[:o], w[:uv], w[:nv], w[:ub], w[:ue], 0.20, -0.30, 6.40, w[:ops], MAT[:wall])
end
log << "rebuilt full-height walls"

# ---- 3) 接缝隐藏（只保留真实洞口上下沿）----
hidden = 0
WALLS.each do |w|
  kids_with_prefix(shell, "#{w[:key]}_").each do |c|
    c.entities.grep(Sketchup::Edge).each do |e|
      a = e.start.position
      b = e.end.position
      next if (a.z - b.z).abs > 0.5.mm
      zmm = a.z.to_m * 1000.0
      u1 = (a - w[:o]).dot(w[:uv]).to_m * 1000.0
      u2 = (b - w[:o]).dot(w[:uv]).to_m * 1000.0
      umin = [u1, u2].min
      umax = [u1, u2].max
      real = w[:ops].any? do |op|
        ((zmm - op[:z0] * 1000.0).abs < 2.0 || (zmm - op[:z1] * 1000.0).abs < 2.0) &&
          umin >= op[:u] * 1000.0 - 8.0 && umax <= (op[:u] + op[:w]) * 1000.0 + 8.0
      end
      unless real
        e.hidden = true unless e.hidden?
        hidden += 1
      end
    end
  end
end
log << "seam hidden=#{hidden}"

# ---- 4) 木格栅：只改颜色为柔和浅棕木色（根数/几何不变）----
louv = find_group(root, "LOUVER_木格栅")
n = 0
if louv
  louv.entities.grep(Sketchup::Group).each do |s|
    n += 1
    s.entities.grep(Sketchup::Face).each { |f| f.material = MAT[:wood]; f.back_material = MAT[:wood] }
  end
end
log << "louver slats=#{n} color=(196,158,112)"

ver = []
WALLS.each do |w|
  ks = kids_with_prefix(shell, "#{w[:key]}_")
  zs = ks.map { |c| c.bounds.min.z.to_m * 1000 }.uniq.sort
  ver << format("%s n=%d zmin=%.0f", w[:key], ks.size, zs.first)
end
log.join(" | ") + " || " + ver.join(" ")
