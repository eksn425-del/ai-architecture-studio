# 已真实执行的 Agent Ruby 片段

来源：本轮网页 DeepSeek 在公开六视图测试项目中生成的持久补丁；只摘录无个人路径/输入的片段供云端审查。不是新增通用几何库，不可脱离宿主的 disposable-model / owned-root 保护任意执行。完整生成工作区仍留在忽略的 runtime。

## 米坐标与挤出法线（patch_fix_down.rb）

```ruby
def mp(x, y, z)
  Geom::Point3d.new(x.m, y.m, z.m)
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
```

本项目参数为米，p0 是已换成内部长度的 Point3d；offset 长度另由米转换，不能给 p0 原点传未换算的建筑米数。后墙/侧墙负方向基面先前令法线向下；此处翻面后正高度挤出回到正确标高。该帮助函数限水平基面，不是所有曲面/复杂屋顶的通用法线方案。实际范围参见 [rev13 回读](objects-final-r13.json)，并非只用 Ruby 替身推测成功。

## 单件位移（patch_move_bal_table.rb）

Agent 递归找到 owned-root 内目标 ID，校验名称后执行的关键片段：

```ruby
TARGET_PID = 52717
DX_MM = 50.0

# tbl = find_by_pid(root, TARGET_PID)
if tbl.name.to_s == "BAL_TABLE"
  tbl.transform!(Geom::Transformation.translation(
    Geom::Vector3d.new(DX_MM.mm, 0, 0)
  ))
end
```

完整补丁还生成一个诊断组，再用下一补丁删除；独立回读确认最终只有原六个顶层组/249 个子组，目标移 +50 mm，其他子组边界/ID 不变。见 [完整网页前后证据](web-single-child-edit-readback.json)。这段是增量位移，**重复运行会继续移动**；不能当作幂等基线，下一轮应明确已应用状态或目标绝对位置。没有把诊断标记当作用户最终几何。

## 独立 QA 对 Agent 记录的纠正

Agent 原文声称“格1侧墙↔左面图：每层2樘小窗…✓”，但源图左上侧面可见的是每层1樘窄窗；这个 ✓ 不成立。旧参数卡的2樘为低置信默认值，应经网页修订确认。Agent 交付文本里的 blank 文件名也不等于网页下载 export；验收下载 fast-assembly-agent.skp 并核对原字节后重开。

因此脚本执行成功、六视角文件存在和 Agent 自评均不能替代本轮 [独立质量报告](README.md)。
