# Dream Coffee r4 局部修正

本次仅替换 revision 4 新增的六个顶层组：独立上层雨棚板、内外梁、两根支柱，以及右侧木墙板缝组。其余 110 个顶层组由 `allowed_mutation_paths` 结构性保护；另外用 `preserve_paths` 复核玻璃屋顶、门窗、入口、楼梯和平台。

雨棚由 2450×3100 mm 缩为 900×1800 mm，移至平台右外缘 X=11100..12000、Y=850..2650 mm，使其与屋顶玻璃及三把伞的平面范围分开，保留两根外侧支柱和局部遮阳。雨棚板、侧梁、立柱均为矩形恒截面实体，选用已启用的 `adai.profile`；在 Ruby 顶层用 lambda 捕获 `adai_geometry` 代理，避免此前方法体内局部变量不可见的问题。若 ledger 未确认真实调用，则不得记作 ADAI 已使用。

右墙原五条竖缝改为十条，间距 560 mm、缝宽 8 mm、浅凸层 6 mm，仍局限于既有木饰面范围 Y=1394..7006、Z=80..3040 mm，不扩成全墙板。该组用 owned Ruby 实体，因为需要在单一受保护顶层组内组织十条独立浅层缝线；墙体、门窗和开口不变。

执行文件：`scripts/dream_coffee_repair04_canopy_timber.rb`（`update_mode=edit`）。完整重建入口 `scripts/dream_coffee_reconstruction.rb` 同步保留同一最终参数，避免后续重放恢复旧版大雨棚与稀疏板缝。
