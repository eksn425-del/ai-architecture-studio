# 修正补丁 R4 — 在洞口内新建 20mm 厚深色玻璃实体（不再改写既有单面材质）
# 影响范围仅 MODULES：新增 GLASS_FIX_* 子组，原有窗/阳台实例几何不动
mdl = model

cand = nil
begin
  m = mdl.materials["GLASS_TINT_DARK"]
  m = mdl.materials.add("GLASS_TINT_DARK") if m.nil?
  if m
    m.color = Sketchup::Color.new(58, 72, 68)
    m.opacity = 1.0
    c = m.color.to_a
    cand = m if (c[0] - 58).abs < 10 && (c[1] - 72).abs < 10 && (c[2] - 68).abs < 10
  end
rescue StandardError
  cand = nil
end
dark = cand
dark = mdl.materials["CLAD_DARKGREY"] if dark.nil?
dark = mdl.materials["SHUTTER_GREY"] if dark.nil?

def glass_solid(parent, name, xa, xb, ya, yb, za, zb, mat)
  g = parent.entities.add_group
  g.name = name
  f = g.entities.add_face(Geom::Point3d.new(xa.mm, ya.mm, za.mm),
                          Geom::Point3d.new(xb.mm, ya.mm, za.mm),
                          Geom::Point3d.new(xb.mm, yb.mm, za.mm),
                          Geom::Point3d.new(xa.mm, yb.mm, za.mm))
  if f && f.valid?
    f.reverse! if f.normal.z < -0.5
    f.pushpull((zb - za).mm)
  end
  if mat
    g.entities.grep(Sketchup::Face).each do |ff|
      ff.material = mat
      ff.back_material = mat
    end
    begin
      g.material = mat
    rescue StandardError
      nil
    end
  end
  g
end

mods = root.entities.grep(Sketchup::Group).find { |g| g.name == "MODULES" }
made = 0
if mods && dark
  (1..7).each do |k|
    z0 = 3600.0 + (k - 1) * 3000.0
    [[5570.0, 9030.0, "A"], [9270.0, 12730.0, "B"]].each do |xa, xb, tag|
      glass_solid(mods, "GLASS_FIX_#{tag}_L#{k}", xa, xb, 118.0, 138.0,
                  z0 + 120.0, z0 + 2480.0, dark)
      made += 1
    end
    glass_solid(mods, "GLASS_FIX_LOG_L#{k}", 600.0, 4950.0, 1725.0, 1745.0,
                z0 + 110.0, z0 + 2640.0, dark)
    made += 1
  end
end

mat_name = 'nil'
if dark
  begin
    mat_name = "#{dark.display_name}/#{dark.color.to_a[0, 3].inspect}"
  rescue StandardError
    mat_name = 'read_err'
  end
end

"R4 mat=#{mat_name} solids=#{made} mods=#{mods ? mods.entities.grep(Sketchup::Group).size : 'n/a'}"
