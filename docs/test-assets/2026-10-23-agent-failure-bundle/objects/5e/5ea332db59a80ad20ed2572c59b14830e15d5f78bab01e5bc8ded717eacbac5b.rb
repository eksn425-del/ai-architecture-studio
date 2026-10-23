# 修正补丁 R5 — 右跨窗玻璃扩至满洞口，覆盖浅色框料，读作连续深色玻璃带
# 仅动 MODULES：替换 14 个 GLASS_FIX_* 为覆盖洞口的 GLASS_BAND_*
mdl = model
dark = mdl.materials["GLASS_TINT_DARK"]
dark = mdl.materials["CLAD_DARKGREY"] if dark.nil?
dark = mdl.materials["SHUTTER_GREY"] if dark.nil?

def rk_add_pane(parent, name, xa, xb, ya, yb, za, zb, mat)
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
if mods && dark
  (1..7).each do |k|
    z0 = 3600.0 + (k - 1) * 3000.0
    ["A", "B"].each do |tag|
      begin
        remove_owned_group.call(["MODULES", "GLASS_FIX_#{tag}_L#{k}"])
        removed += 1
      rescue StandardError
        nil
      end
    end
    # 窗 A：洞口 5550..9050；窗 B：9250..12750；玻璃覆盖洞口的 6mm 内边
    rk_add_pane(mods, "GLASS_BAND_A_L#{k}", 5556.0, 9044.0, 88.0, 108.0,
                z0 + 108.0, z0 + 2492.0, dark)
    rk_add_pane(mods, "GLASS_BAND_B_L#{k}", 9256.0, 12744.0, 88.0, 108.0,
                z0 + 108.0, z0 + 2492.0, dark)
    added += 2
  end
end

names = mods ? mods.entities.grep(Sketchup::Group).map(&:name).select { |n| n.to_s.start_with?("GLASS_") } : []
"R5 mat=#{dark.nil? ? 'nil' : dark.display_name} removed=#{removed} added=#{added} " \
"glass_children=#{names.size} total_modules=#{mods ? mods.entities.grep(Sketchup::Group).size : 'n/a'}"
