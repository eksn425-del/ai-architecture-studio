# 修正补丁 R3 — 玻璃/窗框改用已验证深色材质 + 侧窗朝向修正 + 围屏减密
mdl = model
dark = mdl.materials["CLAD_DARKGREY"]
dark = mdl.materials["SHUTTER_GREY"] if dark.nil?
grey = mdl.materials["PLANTER_CONC"]
grey = mdl.materials["STEEL_SCREEN"] if grey.nil?

def rk_child(parent, name)
  return nil if parent.nil?
  parent.entities.each do |e|
    return e if e.respond_to?(:entities) && e.name.to_s == name
  end
  nil
end

def rk_paint_named(ents, names, m, depth = 0)
  return if depth > 8 || m.nil?
  ents.each do |e|
    next unless e.respond_to?(:entities)
    sub = e.entities
    if names.include?(e.name.to_s)
      begin
        e.material = m
      rescue StandardError
        nil
      end
      sub.grep(Sketchup::Face).each do |f|
        f.material = m
        f.back_material = m
      end
    end
    rk_paint_named(sub, names, m, depth + 1)
  end
end

def rk_face_mats(ents, names, depth = 0, out = [])
  return out if depth > 8
  ents.each do |e|
    next unless e.respond_to?(:entities)
    sub = e.entities
    if names.include?(e.name.to_s)
      sub.grep(Sketchup::Face).each do |f|
        nm = 'default'
        begin
          nm = f.material.nil? ? 'default' : f.material.display_name
        rescue StandardError
          nm = 'err'
        end
        out << nm
      end
    end
    rk_face_mats(sub, names, depth + 1, out)
  end
  out
end

mods = root.entities.grep(Sketchup::Group).find { |g| g.name == "MODULES" }
fac  = root.entities.grep(Sketchup::Group).find { |g| g.name == "FACADE" }
roof = root.entities.grep(Sketchup::Group).find { |g| g.name == "ROOF" }

before = mods ? rk_face_mats(mods.entities, ["GLASS", "BACK_GLASS"]).uniq : []

# 1) 玻璃面 -> 已验证深色不透明材质
rk_paint_named(mods.entities, ["GLASS", "BACK_GLASS"], dark) if mods
# 2) 窗框/竖框/阳台立柱 -> 同族深灰（消除浅色框）
rk_paint_named(mods.entities,
               ["F_BOT", "F_HEAD", "F_JAMB_L", "F_JAMB_R",
                "BACK_MULL_1", "BACK_MULL_2", "BACK_MULL_3",
                "BAL_HANDRAIL", "BAL_POST_1", "BAL_POST_2", "BAL_POST_3"], dark) if mods

if fac
  rw = rk_child(fac, "REAR_WINDOWS")
  sw = rk_child(fac, "SIDE_WINDOWS")
  rk_paint_named(rw.entities, ["WIN_GLASS"], dark) if rw
  rk_paint_named(sw.entities, ["WIN_GLASS"], dark) if sw
  rk_paint_named(rw.entities, ["WIN_FRAME"], dark) if rw
  rk_paint_named(sw.entities, ["WIN_FRAME"], dark) if sw
end

after = mods ? rk_face_mats(mods.entities, ["GLASS", "BACK_GLASS"]).uniq : []

# 3) 侧窗实例朝向修正：局部 Z 轴竖直向上，框体落回洞口内
if sw
  (1..7).each do |k|
    zs = 3600.0 + (k - 1) * 3000.0 + 920.0
    [[1500.0, "1"], [7000.0, "2"]].each do |oy, tag|
      y0 = 250.0 + oy
      tl = Geom::Transformation.new(Geom::Point3d.new(65.mm, (y0 + 1480.0).mm, zs.mm),
                                    Geom::Vector3d.new(0, -1, 0), Geom::Vector3d.new(1, 0, 0))
      tr = Geom::Transformation.new(Geom::Point3d.new(13135.mm, (y0 + 20.0).mm, zs.mm),
                                    Geom::Vector3d.new(0, 1, 0), Geom::Vector3d.new(-1, 0, 0))
      il = rk_child(sw, "WIN_LEFT_L#{k}_#{tag}")
      ir = rk_child(sw, "WIN_RIGHT_L#{k}_#{tag}")
      il.transformation = tl if il
      ir.transformation = tr if ir
    end
  end
end

# 4) 屋顶围屏减密（杆件少而可见缝隙，浅灰）
scr = rk_child(roof, "SCREEN_RAILING")
if scr && grey
  clear_owned_contents.call(["ROOF", "SCREEN_RAILING"])
  e = scr.entities
  z0 = 25340.0
  z1 = 26730.0
  add = lambda do |xa, ya, za, xb, yb, zb|
    if (xb - xa) > 0.5 && (yb - ya) > 0.5 && (zb - za) > 0.5
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
  xx = 150.0
  while xx <= 13060.0
    add.call(xx, 112, z0, xx + 22, 134, z1)
    add.call(xx, 11866, z0, xx + 22, 11888, z1)
    xx += 300.0
  end
  yy = 450.0
  while yy <= 11550.0
    add.call(112, yy, z0, 134, yy + 22, z1)
    add.call(13066, yy, z0, 13088, yy + 22, z1)
    yy += 300.0
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
    f.material = grey
    f.back_material = grey
  end
end

"R3 dark=#{dark.nil? ? 'nil' : dark.display_name} grey=#{grey.nil? ? 'nil' : grey.display_name} " \
"glass_before=#{before.join('|')} glass_after=#{after.join('|')} faces=#{after.size}"
