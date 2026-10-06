# ============================================================
# patch_hide_jamb_lines.rb —— 隐藏洞口两侧的贯通竖线（edit 模式，同一 build_villa root）
# 现象：墙垛按整高成块后，洞口左右两侧的竖线会从墙顶贯通到勒脚，形成"分段感"。
# 处理：只隐藏"位于洞口 u 边界上"的竖直边（如 2.00 / 2.85 / 7.15 …），
#       保留墙角竖线、洞口上下沿水平线、勒脚与压顶轮廓。
# 只编辑 SHELL_主体 内的墙段；不改尺寸、不改门窗、不改其它组。
# ============================================================
VX  = Geom::Vector3d.new( 1, 0, 0)
VY  = Geom::Vector3d.new( 0, 1, 0)
VNX = Geom::Vector3d.new(-1, 0, 0)
VNY = Geom::Vector3d.new( 0,-1, 0)

def mp(x, y, z)
  Geom::Point3d.new(x.m, y.m, z.m)
end

def find_group(host, name)
  host.entities.each { |e| return e if e.is_a?(Sketchup::Group) && e.name == name }
  nil
end

WALLS = [
  { key: "FRONT", o: mp(0, 0, 0),  uv: VX,
    ops: [{ u: 2.00, w: 5.80, z0: 0.00, z1: 2.70 },
          { u: 2.30, w: 1.90, z0: 3.20, z1: 5.80 },
          { u: 5.80, w: 1.90, z0: 3.20, z1: 5.80 }] },
  { key: "REAR",  o: mp(10, 8, 0), uv: VNX,
    ops: [{ u: 2.15, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 4.65, w: 0.70, z0: 0.90, z1: 2.35 },
          { u: 7.15, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 2.15, w: 0.70, z0: 4.10, z1: 5.55 },
          { u: 4.65, w: 0.70, z0: 4.10, z1: 5.55 }, { u: 7.15, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "LEFT",  o: mp(0, 8, 0),  uv: VNY,
    ops: [{ u: 3.65, w: 0.70, z0: 0.90, z1: 2.35 }, { u: 3.65, w: 0.70, z0: 4.10, z1: 5.55 }] },
  { key: "RIGHT", o: mp(10, 0, 0), uv: VY,
    ops: [{ u: 1.00, w: 1.00, z0: 0.00, z1: 2.30 }, { u: 4.00, w: 1.00, z0: 4.10, z1: 5.55 }] }
]

shell = find_group(root, "SHELL_主体")
hidden = 0
kept = 0
WALLS.each do |w|
  shell.entities.grep(Sketchup::Group).select { |c| c.name.to_s.start_with?("#{w[:key]}_") }.each do |c|
    c.entities.grep(Sketchup::Edge).each do |e|
      a = e.start.position
      b = e.end.position
      next if (a.z - b.z).abs < 0.5.mm      # 只处理竖直边
      next if (a.x - b.x).abs > 0.5.mm || (a.y - b.y).abs > 0.5.mm
      ua = (a - w[:o]).dot(w[:uv]).to_m * 1000.0
      ub = (b - w[:o]).dot(w[:uv]).to_m * 1000.0
      u = (ua + ub) / 2.0
      at_jamb = w[:ops].any? do |op|
        (u - op[:u] * 1000.0).abs < 8.0 || (u - (op[:u] + op[:w]) * 1000.0).abs < 8.0
      end
      if at_jamb
        e.hidden = true unless e.hidden?
        hidden += 1
      else
        kept += 1
      end
    end
  end
end
"JAMB_HIDDEN=#{hidden} VERT_KEPT=#{kept}"
