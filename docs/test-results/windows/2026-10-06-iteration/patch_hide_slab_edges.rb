# ============================================================
# patch_hide_slab_edges.rb —— 隐藏室内楼板 / 屋面结构板边线（edit 模式，同一 root）
# 目的：消除斜视中楼板与外墙共面处的残余横线；这些边线对外观无贡献
#      （室内楼板被外墙包住；屋面结构板被女儿墙包住，屋顶外轮廓由 PARAPET/COPING 表达）
# 只改 SHELL_主体 内三个 slab 的边线可见性；不改几何、尺寸、ID
# ============================================================
def find_group(host, name)
  host.entities.each { |e| return e if e.is_a?(Sketchup::Group) && e.name == name }
  nil
end

def hide_edges(grp)
  n = 0
  grp.entities.each do |e|
    if e.is_a?(Sketchup::Group)
      n += hide_edges(e)
    elsif e.is_a?(Sketchup::Edge)
      e.hidden = true unless e.hidden?
      n += 1
    end
  end
  n
end

shell = find_group(root, "SHELL_主体")
total = 0
done = []
if shell
  ["FLOOR_GF", "FLOOR_2F", "ROOF_SLAB"].each do |nm|
    g = shell.entities.grep(Sketchup::Group).find { |c| c.name == nm }
    next if g.nil?
    k = hide_edges(g)
    total += k
    done << "#{nm}:#{k}"
  end
end
"SLAB_EDGES_HIDDEN=#{total} (#{done.join(',')})"
