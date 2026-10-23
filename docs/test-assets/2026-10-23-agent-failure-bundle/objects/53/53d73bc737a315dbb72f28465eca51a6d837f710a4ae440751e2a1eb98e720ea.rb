# 修正补丁 R1 — 只改可见材质与两处收口，不动墙体/洞口/层高
# 目标: 玻璃深色反光 + 玻璃后室内面深、凹阳台绿植可见、屋顶围屏浅灰通透
mdl = model

def rk_mat_new(mdl, name, rgb, alpha)
  m = mdl.materials[name]
  m = mdl.materials.add(name) if m.nil?
  m.color = Sketchup::Color.new(rgb[0], rgb[1], rgb[2])
  m.opacity = alpha
  m
end

g_deep  = rk_mat_new(mdl, "GLASS_DEEP_TINT", [46, 62, 58], 0.86)
cur_l   = rk_mat_new(mdl, "CURTAIN_LINEN",   [238, 229, 210], 1.0)
steel_l = rk_mat_new(mdl, "STEEL_LIGHTGREY", [176, 178, 182], 1.0)
room_l  = rk_mat_new(mdl, "ROOM_BACK_LIGHT", [212, 206, 194], 1.0)
green_m = mdl.materials["GREEN_PLANT"]

def rk_paint_named(ents, names, m, depth = 0)
  return if depth > 8
  ents.each do |e|
    next unless e.respond_to?(:entities)
    sub = e.entities
    if names.include?(e.name.to_s)
      sub.grep(Sketchup::Face).each do |f|
        f.material = m
        f.back_material = m
      end
    end
    rk_paint_named(sub, names, m, depth + 1)
  end
end

def rk_child(parent, name)
  return nil if parent.nil?
  parent.entities.each do |e|
    return e if e.respond_to?(:entities) && e.name.to_s == name
  end
  nil
end

root_children = root.entities.grep(Sketchup::Group)
mods = root_children.find { |g| g.name == "MODULES" }
roof = root_children.find { |g| g.name == "ROOF" }
intr = root_children.find { |g| g.name == "INTERIOR" }
fac  = root_children.find { |g| g.name == "FACADE" }

# 1) 正立面窗玻璃与阳台后墙玻璃 -> 深色反光
rk_paint_named(mods.entities, ["GLASS", "BACK_GLASS"], g_deep) if mods

# 2) 侧/背窗玻璃同步深色（推断面，保持材料一致）
if fac
  rw = rk_child(fac, "REAR_WINDOWS")
  sw = rk_child(fac, "SIDE_WINDOWS")
  rk_paint_named(rw.entities, ["WIN_GLASS"], g_deep) if rw
  rk_paint_named(sw.entities, ["WIN_GLASS"], g_deep) if sw
end

# 3) 凹阳台内绿植抬升至栏板之上（原图可见绿植越出栏板）
lg_def = mdl.definitions["LOGGIA_UNIT_4650x1500_DEF"]
if lg_def
  ["GREEN_A", "GREEN_B"].each do |gn|
    grp = lg_def.entities.grep(Sketchup::Group).find { |x| x.name.to_s == gn }
    next if grp.nil?
    base = Geom::Point3d.new(0, 0, 4060.mm)
    grp.transform!(Geom::Transformation.scaling(base, 1.0, 1.0, 1.9))
  end
end

# 4) 玻璃后室内：窗帘提亮 + 房间背面（避免看穿到天空）
if intr
  cs = rk_child(intr, "CURTAIN_SCREENS")
  if cs
    cs.entities.each do |e|
      next unless e.respond_to?(:entities)
      next unless e.name.to_s.start_with?("CURTAIN_F_")
      e.entities.grep(Sketchup::Face).each do |f|
        f.material = cur_l
        f.back_material = cur_l
      end
    end
    (1..7).each do |k|
      z = 3600.0 + (k - 1) * 3000.0
      g = cs.entities.add_group
      g.name = "ROOM_BACK_L#{k}"
      f = g.entities.add_face(Geom::Point3d.new(5650.mm, 1700.mm, (z + 150).mm),
                              Geom::Point3d.new(12650.mm, 1700.mm, (z + 150).mm),
                              Geom::Point3d.new(12650.mm, 1700.mm, (z + 2500).mm),
                              Geom::Point3d.new(5650.mm, 1700.mm, (z + 2500).mm))
      if f && f.valid?
        f.material = room_l
        f.back_material = room_l
      end
    end
  end
end

# 5) 屋顶围屏：浅灰细杆重建（保留 2200 高度与女儿墙顶线）
scr = rk_child(roof, "SCREEN_RAILING")
if scr
  clear_owned_contents.call(["ROOF", "SCREEN_RAILING"])
  e = scr.entities
  z0 = 25340.0
  z1 = 26730.0
  add = lambda do |xa, ya, za, xb, yb, zb|
    ok = (xb - xa) > 0.5 && (yb - ya) > 0.5 && (zb - za) > 0.5
    if ok
      f = e.add_face(Geom::Point3d.new(xa.mm, ya.mm, za.mm),
                     Geom::Point3d.new(xb.mm, ya.mm, za.mm),
                     Geom::Point3d.new(xb.mm, yb.mm, za.mm),
                     Geom::Point3d.new(xa.mm, yb.mm, za.mm))
      if f && f.valid?
        f.reverse! if f.normal.z < -0.5
        f.pushpull((zb - za).mm)
      end
    end
  end
  xx = 90.0
  while xx <= 13110.0
    add.call(xx, 112, z0, xx + 16, 128, z1)
    add.call(xx, 11872, z0, xx + 16, 11888, z1)
    xx += 180.0
  end
  yy = 290.0
  while yy <= 11700.0
    add.call(112, yy, z0, 128, yy + 16, z1)
    add.call(13072, yy, z0, 13088, yy + 16, z1)
    yy += 180.0
  end
  add.call(0, 100, 25300, 13200, 140, 25340)
  add.call(0, 11860, 25300, 13200, 11900, 25340)
  add.call(100, 140, 25300, 140, 11860, 25340)
  add.call(13060, 140, 25300, 13100, 11860, 25340)
  add.call(0, 100, 26730, 13200, 140, 26790)
  add.call(0, 11860, 26730, 13200, 11900, 26790)
  add.call(100, 140, 26730, 140, 11860, 26790)
  add.call(13060, 140, 26730, 13100, 11860, 26790)
  e.grep(Sketchup::Face).each do |f|
    f.material = steel_l
    f.back_material = steel_l
  end
end

# 6) 露台绿化：退到女儿墙内侧，低于围屏顶，不与竖杆相交
grn = rk_child(roof, "GREEN_SCREEN")
if grn
  clear_owned_contents.call(["ROOF", "GREEN_SCREEN"])
  e = grn.entities
  build = lambda do |name, xa, ya, za, xb, yb, zb|
    g = e.add_group
    g.name = name
    f = g.entities.add_face(Geom::Point3d.new(xa.mm, ya.mm, za.mm),
                            Geom::Point3d.new(xb.mm, ya.mm, za.mm),
                            Geom::Point3d.new(xb.mm, yb.mm, za.mm),
                            Geom::Point3d.new(xa.mm, yb.mm, za.mm))
    if f && f.valid?
      f.reverse! if f.normal.z < -0.5
      f.pushpull((zb - za).mm)
    end
    g.entities.grep(Sketchup::Face).each do |ff|
      ff.material = green_m
      ff.back_material = green_m
    end
  end
  build.call("GREEN_T1", 520, 520, 25200, 1440, 2560, 26050)
  build.call("GREEN_T2", 640, 900, 25200, 1350, 2000, 26150)
  build.call("GREEN_T3", 520, 2900, 25200, 1440, 5150, 25950)
  build.call("GREEN_T4", 9600, 700, 25200, 11400, 1860, 25850)
end

"PATCH_OK deep=#{g_deep.valid?} roof=#{roof ? roof.entities.grep(Sketchup::Group).map(&:name).join('|') : 'n/a'} " \
"cs=#{intr ? rk_child(intr, 'CURTAIN_SCREENS').entities.grep(Sketchup::Group).size : 'n/a'}"
