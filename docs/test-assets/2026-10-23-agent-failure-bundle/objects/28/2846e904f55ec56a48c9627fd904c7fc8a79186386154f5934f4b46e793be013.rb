# 修正补丁 R6 — 洞口顶对齐 + 玻璃满洞口
# 参数卡: loggia_opening_height=2400 / window 2400(sill100)。凹阳台曾按 2750 实现，本轮加下挂梁回到 2400。
# 仅动 MODULES。
mdl = model
dark = mdl.materials["GLASS_TINT_DARK"]
dark = mdl.materials["CLAD_DARKGREY"] if dark.nil?
dark = mdl.materials["SHUTTER_GREY"] if dark.nil?
conc = mdl.materials["CONC_FAIRFACE"]

def rk_solid(parent, name, xa, xb, ya, yb, za, zb, mat)
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
  end
  g
end

mods = root.entities.grep(Sketchup::Group).find { |g| g.name == "MODULES" }
removed = 0
added = 0
if mods
  (1..7).each do |k|
    z0 = 3600.0 + (k - 1) * 3000.0
    ["GLASS_BAND_A_L#{k}", "GLASS_BAND_B_L#{k}", "GLASS_FIX_LOG_L#{k}"].each do |nm|
      begin
        remove_owned_group.call(["MODULES", nm])
        removed += 1
      rescue StandardError
        nil
      end
    end
    # 玻璃铺满洞口（留 3mm 安装缝，厚度加深到 60 避免露出浅色返边）
    rk_solid(mods, "GLASS_BAND_A_L#{k}", 5553.0, 9047.0, 60.0, 120.0,
             z0 + 103.0, z0 + 2497.0, dark)
    rk_solid(mods, "GLASS_BAND_B_L#{k}", 9253.0, 12747.0, 60.0, 120.0,
             z0 + 103.0, z0 + 2497.0, dark)
    # 凹阳台后墙玻璃：随洞口改为 2400 高
    rk_solid(mods, "GLASS_LOG_L#{k}", 500.0, 5050.0, 1725.0, 1745.0,
             z0 + 110.0, z0 + 2330.0, dark)
    # 凹阳台洞口下挂梁：洞顶由 2750 回到 2400，与右跨窗洞顶接近齐平
    rk_solid(mods, "BEAM_LOG_L#{k}", 450.0, 5100.0, 0.0, 420.0,
             z0 + 2400.0, z0 + 2750.0, conc)
    added += 4
  end
end

kids = mods ? mods.entities.grep(Sketchup::Group).map(&:name) : []
"R6 removed=#{removed} added=#{added} modules_children=#{kids.size} " \
"beams=#{kids.count { |n| n.to_s.start_with?('BEAM_LOG') }} glass=#{kids.count { |n| n.to_s.start_with?('GLASS_') }}"
