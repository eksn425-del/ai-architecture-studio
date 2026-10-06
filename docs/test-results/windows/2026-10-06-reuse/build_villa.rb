# build_villa.rb — 参考图别墅整体重建基线（可重跑入口）v2
# 依据 notes/reconstruction_card.md v1.0 + 首轮同角度校对修正（2026-10-06）
# 坐标：原点=正面(阳台面)左外角、室外铺装面；+X 沿正向右(0-10000)，+Y 向背面(0-8000)，+Z 向上
# 全部参数以 mm 输入，统一 .mm 转换；所有几何建在注入的 root 之下。
# v2 修正：1F 左墙垛 1200→500、门洞 1200-6600→500-6900(3 扇 2 中梃)；
#          2F 左窗 700-3300→400-3300、右窗 5700-8200→5500-8000；
#          铺装提亮+缝变细(12mm)、草坪提亮。

module VillaBuild
  W    = 10000
  D    = 8000
  WT   = 200
  S2   = 220
  Z_1F = 2980
  Z_2F = 6180
  Z_RS = 6400
  Z_PT = 6650
  Z_CT = 6700
  FW   = 60

  # 正面洞口定位（v2）
  D1_X0 = 500    # 一层门洞左
  D1_X1 = 6900   # 一层门洞右
  W2_X0 = 400    # 二层左窗左
  W2_X1 = 3300   # 二层左窗右
  W2_M  = 1850   # 二层左窗中梃
  W3_X0 = 5500   # 二层右窗左
  W3_X1 = 8000   # 二层右窗右
  W3_M  = 6750   # 二层右窗中梃
  GR_X0 = 8600   # 木格栅带起点

  def self.material(model, name, rgb, alpha = 1.0)
    m = model.materials[name]
    m = model.materials.add(name) if m.nil?
    m.color = Sketchup::Color.new(rgb[0], rgb[1], rgb[2])
    m.alpha = alpha
    m
  end

  def self.paint(g, mat)
    return if g.nil? || mat.nil?
    g.material = mat
    g.entities.grep(Sketchup::Face).each { |f| f.material = mat; f.back_material = mat }
    g.entities.grep(Sketchup::Group).each { |s| paint(s, mat) }
  end

  def self.box(parent, name, x0, y0, z0, x1, y1, z1, mat)
    return nil if x1 <= x0 || y1 <= y0 || z1 <= z0
    g = parent.entities.add_group
    g.name = name
    f = g.entities.add_face(
      Geom::Point3d.new(x0.mm, y0.mm, z0.mm),
      Geom::Point3d.new(x1.mm, y0.mm, z0.mm),
      Geom::Point3d.new(x1.mm, y1.mm, z0.mm),
      Geom::Point3d.new(x0.mm, y1.mm, z0.mm)
    )
    if f.nil?
      g.erase!
      return nil
    end
    f.reverse! if f.normal.z < 0
    f.pushpull((z1 - z0).mm)
    paint(g, mat)
    g
  end

  def self.sbox(ents, x0, y0, z0, x1, y1, z1, mat)
    return nil if x1 <= x0 || y1 <= y0 || z1 <= z0
    f = ents.add_face(
      Geom::Point3d.new(x0.mm, y0.mm, z0.mm),
      Geom::Point3d.new(x1.mm, y0.mm, z0.mm),
      Geom::Point3d.new(x1.mm, y1.mm, z0.mm),
      Geom::Point3d.new(x0.mm, y1.mm, z0.mm)
    )
    return nil if f.nil?
    f.reverse! if f.normal.z < 0
    f.pushpull((z1 - z0).mm)
    f
  end

  def self.cyl(parent, name, cx, cy, z_top, dia, h, mat)
    g = parent.entities.add_group
    g.name = name
    edge = g.entities.add_circle(Geom::Point3d.new(cx.mm, cy.mm, z_top.mm),
                                 Geom::Vector3d.new(0, 0, -1), (dia / 2.0).mm, 24)
    f = g.entities.add_face(edge)
    if f.nil?
      g.erase!
      return nil
    end
    f.pushpull(h.mm)
    paint(g, mat)
    g
  end

  # 沿 Y 法线的洞口（正面/背面）
  def self.win_y(parent, name, x0, x1, z0, z1, fy0, fy1, mullions, mat, glass)
    return nil if x1 - x0 < 3 * FW + 40 || z1 - z0 < 2 * FW + 40
    grp = parent.entities.add_group
    grp.name = name
    box(grp, name + '_Sill', x0, fy0, z0, x1, fy1, z0 + FW, mat)
    box(grp, name + '_Head', x0, fy0, z1 - FW, x1, fy1, z1, mat)
    box(grp, name + '_JambL', x0, fy0, z0, x0 + FW, fy1, z1, mat)
    box(grp, name + '_JambR', x1 - FW, fy0, z0, x1, fy1, z1, mat)
    gz0 = z0 + FW
    gz1 = z1 - FW
    gy0 = (fy0 + fy1) / 2.0 - 7
    gy1 = (fy0 + fy1) / 2.0 + 7
    ms = Array(mullions)
    ms.each_with_index { |mx, i| box(grp, format('%s_Mullion%d', name, i + 1), mx - FW / 2, fy0, z0, mx + FW / 2, fy1, z1, mat) }
    xs = [x0 + FW] + ms + [x1 - FW]
    (0...(xs.size - 1)).each do |i|
      a = xs[i] + (i.zero? ? 0 : FW / 2)
      b = xs[i + 1] - (i == xs.size - 2 ? 0 : FW / 2)
      box(grp, format('%s_Glass%d', name, i + 1), a, gy0, gz0, b, gy1, gz1, glass)
    end
    grp
  end

  # 沿 X 法线的洞口（左右侧墙）
  def self.win_x(parent, name, y0, y1, z0, z1, fx0, fx1, mullions, mat, glass)
    return nil if y1 - y0 < 3 * FW + 40 || z1 - z0 < 2 * FW + 40
    grp = parent.entities.add_group
    grp.name = name
    box(grp, name + '_Sill', fx0, y0, z0, fx1, y1, z0 + FW, mat)
    box(grp, name + '_Head', fx0, y0, z1 - FW, fx1, y1, z1, mat)
    box(grp, name + '_JambL', fx0, y0, z0, fx1, y0 + FW, z1, mat)
    box(grp, name + '_JambR', fx0, y1 - FW, z0, fx1, y1, z1, mat)
    gz0 = z0 + FW
    gz1 = z1 - FW
    gx0 = (fx0 + fx1) / 2.0 - 7
    gx1 = (fx0 + fx1) / 2.0 + 7
    ms = Array(mullions)
    ms.each_with_index { |my, i| box(grp, format('%s_Mullion%d', name, i + 1), fx0, my - FW / 2, z0, fx1, my + FW / 2, z1, mat) }
    ys = [y0 + FW] + ms + [y1 - FW]
    (0...(ys.size - 1)).each do |i|
      a = ys[i] + (i.zero? ? 0 : FW / 2)
      b = ys[i + 1] - (i == ys.size - 2 ? 0 : FW / 2)
      box(grp, format('%s_Glass%d', name, i + 1), gx0, a, gz0, gx1, b, gz1, glass)
    end
    grp
  end

  def self.run(model, root)
    m_white   = material(model, 'WHITE_STUCCO', [238, 236, 231])
    m_frame   = material(model, 'ALU_FRAME',    [ 58,  61,  64])
    m_glass   = material(model, 'GLASS_LIGHT',  [168, 203, 208], 0.35)
    m_wood    = material(model, 'TIMBER_SLAT',  [197, 126,  58])
    m_paving  = material(model, 'PAVING_GREY',  [196, 196, 194])
    m_joint   = material(model, 'PAVING_JOINT', [168, 168, 166])
    m_lawn    = material(model, 'LAWN',         [118, 172,  80])
    m_conc    = material(model, 'CONCRETE',     [203, 201, 197])
    m_floorin = material(model, 'FLOOR_IN',     [217, 210, 199])
    m_sofa    = material(model, 'FABRIC',       [206, 200, 189])
    m_furn    = material(model, 'FURN_WOOD',    [152, 112,  72])
    m_plant   = material(model, 'PLANT',        [ 62, 112,  56])
    m_pot     = material(model, 'POT',          [ 86,  86,  88])
    m_curtain = material(model, 'CURTAIN',      [240, 238, 234])
    m_light   = material(model, 'LIGHT_FIX',    [252, 244, 226])
    m_rooftop = material(model, 'ROOF_TOP',     [214, 212, 208])

    # ===== 场地 =====
    box(root, 'Site_Lawn',    -9500, -9500, -150, 19500, 17500, -40, m_lawn)
    box(root, 'Site_Paving',  -1800, -2500, -150, 11800,  9900, -10, m_paving)
    jg = root.entities.add_group
    jg.name = 'Site_Paving_Joints'
    xs = -1800
    while xs <= 11800
      sbox(jg.entities, xs, -2500, -9, xs + 12, 9900, -7, m_joint)
      xs += 600
    end
    ys = -2500
    while ys <= 9900
      sbox(jg.entities, -1800, ys, -9, 11800, ys + 12, -7, m_joint)
      ys += 600
    end
    paint(jg, m_joint)

    # ===== 一层结构 =====
    box(root, 'Slab_Ground',       0, 0, -200, W, D, 0, m_conc)
    box(root, 'Floor_1F_Finish',  WT, WT, 0, W - WT, D - WT, 20, m_floorin)

    # ===== 一层外墙 =====
    box(root, 'Wall_Front_1F_PierL',     0, 0, 0, D1_X0, WT, Z_1F, m_white)
    box(root, 'Wall_Front_1F_DoorHead',  D1_X0, 0, 2400, D1_X1, WT, Z_1F, m_white)
    box(root, 'Wall_Front_1F_PierR',     D1_X1, 0, 0, GR_X0, WT, Z_1F, m_white)
    box(root, 'Wall_Front_1F_GrilleZone', GR_X0, 0, 0, W, WT, Z_1F, m_white)
    box(root, 'Wall_Back_1F_A',     0, D - WT, 0, 2050, D, Z_1F, m_white)
    box(root, 'Wall_Back_1F_B_low', 2050, D - WT, 0, 3550, D, 900, m_white)
    box(root, 'Wall_Back_1F_B_high', 2050, D - WT, 2400, 3550, D, Z_1F, m_white)
    box(root, 'Wall_Back_1F_C',     3550, D - WT, 0, 6450, D, Z_1F, m_white)
    box(root, 'Wall_Back_1F_D_low', 6450, D - WT, 0, 7950, D, 900, m_white)
    box(root, 'Wall_Back_1F_D_high', 6450, D - WT, 2400, 7950, D, Z_1F, m_white)
    box(root, 'Wall_Back_1F_E',     7950, D - WT, 0, W, D, Z_1F, m_white)
    box(root, 'Wall_Left_1F_A',      0, 0, 0, WT, 5050, Z_1F, m_white)
    box(root, 'Wall_Left_1F_B_low',  0, 5050, 0, WT, 5750, 600, m_white)
    box(root, 'Wall_Left_1F_B_high', 0, 5050, 1950, WT, 5750, Z_1F, m_white)
    box(root, 'Wall_Left_1F_C',      0, 5750, 0, WT, D, Z_1F, m_white)
    box(root, 'Wall_Right_1F', W - WT, 0, 0, W, D, Z_1F, m_white)

    # ===== 二层结构 =====
    box(root, 'Slab_2F',        0, 0, Z_1F, W, D, 3200, m_conc)
    box(root, 'Floor_2F_Finish', WT, WT, 3200, W - WT, D - WT, 3220, m_floorin)
    box(root, 'Balcony_Slab',    300, -1000, 2950, 9700, 100, 3200, m_white)

    # ===== 二层外墙 =====
    box(root, 'Wall_Front_2F_PierL',      0, 0, 3200, W2_X0, WT, Z_2F, m_white)
    box(root, 'Wall_Front_2F_WinA_low',   W2_X0, 0, 3200, W2_X1, WT, 3950, m_white)
    box(root, 'Wall_Front_2F_WinA_high',  W2_X0, 0, 5650, W2_X1, WT, Z_2F, m_white)
    box(root, 'Wall_Front_2F_PierM',      W2_X1, 0, 3200, W3_X0, WT, Z_2F, m_white)
    box(root, 'Wall_Front_2F_WinB_low',   W3_X0, 0, 3200, W3_X1, WT, 3950, m_white)
    box(root, 'Wall_Front_2F_WinB_high',  W3_X0, 0, 5650, W3_X1, WT, Z_2F, m_white)
    box(root, 'Wall_Front_2F_PierR',      W3_X1, 0, 3200, GR_X0, WT, Z_2F, m_white)
    box(root, 'Wall_Front_2F_GrilleZone', GR_X0, 0, 3200, W, WT, Z_2F, m_white)
    box(root, 'Wall_Back_2F_A',     0, D - WT, 3200, 2050, D, Z_2F, m_white)
    box(root, 'Wall_Back_2F_B_low', 2050, D - WT, 3200, 3550, D, 4100, m_white)
    box(root, 'Wall_Back_2F_B_high', 2050, D - WT, 5600, 3550, D, Z_2F, m_white)
    box(root, 'Wall_Back_2F_C',     3550, D - WT, 3200, 6450, D, Z_2F, m_white)
    box(root, 'Wall_Back_2F_D_low', 6450, D - WT, 3200, 7950, D, 4100, m_white)
    box(root, 'Wall_Back_2F_D_high', 6450, D - WT, 5600, 7950, D, Z_2F, m_white)
    box(root, 'Wall_Back_2F_E',     7950, D - WT, 3200, W, D, Z_2F, m_white)
    box(root, 'Wall_Left_2F_A',      0, 0, 3200, WT, 5050, Z_2F, m_white)
    box(root, 'Wall_Left_2F_B_low',  0, 5050, 3200, WT, 5750, 3800, m_white)
    box(root, 'Wall_Left_2F_B_high', 0, 5050, 5150, WT, 5750, Z_2F, m_white)
    box(root, 'Wall_Left_2F_C',      0, 5750, 3200, WT, D, Z_2F, m_white)
    box(root, 'Wall_Right_2F', W - WT, 0, 3200, W, D, Z_2F, m_white)

    # ===== 屋面 =====
    box(root, 'Roof_Slab', 0, 0, Z_2F, W, D, Z_RS, m_rooftop)
    box(root, 'Roof_Parapet_Front', 0, 0, Z_RS, W, WT, Z_PT, m_white)
    box(root, 'Roof_Parapet_Back',  0, D - WT, Z_RS, W, D, Z_PT, m_white)
    box(root, 'Roof_Parapet_Left',  0, 0, Z_RS, WT, D, Z_PT, m_white)
    box(root, 'Roof_Parapet_Right', W - WT, 0, Z_RS, W, D, Z_PT, m_white)
    box(root, 'Roof_Coping_Front', -30, -30, Z_PT, W + 30, WT + 30, Z_CT, m_white)
    box(root, 'Roof_Coping_Back',  -30, D - WT - 30, Z_PT, W + 30, D + 30, Z_CT, m_white)
    box(root, 'Roof_Coping_Left',  -30, -30, Z_PT, WT + 30, D + 30, Z_CT, m_white)
    box(root, 'Roof_Coping_Right', W - WT - 30, -30, Z_PT, W + 30, D + 30, Z_CT, m_white)

    # ===== 一层大面玻璃推拉门（3 扇 2 中梃）=====
    d = root.entities.add_group
    d.name = 'F1_SlidingDoor'
    fx0 = 70; fx1 = 130
    box(d, 'F1_SlidingDoor_Track', D1_X0, fx0, 0, D1_X1, fx1, 60, m_frame)
    box(d, 'F1_SlidingDoor_Head',  D1_X0, fx0, 2340, D1_X1, fx1, 2400, m_frame)
    box(d, 'F1_SlidingDoor_JambL', D1_X0, fx0, 0, D1_X0 + FW, fx1, 2400, m_frame)
    box(d, 'F1_SlidingDoor_JambR', D1_X1 - FW, fx0, 0, D1_X1, fx1, 2400, m_frame)
    span = (D1_X1 - FW) - (D1_X0 + FW)   # 玻璃总宽 6280
    pw = (span - 2 * FW) / 3.0           # 单扇玻璃宽 2053.3
    m1 = D1_X0 + FW + pw + FW / 2.0
    m2 = m1 + FW / 2.0 + FW + pw + FW / 2.0
    box(d, 'F1_SlidingDoor_Mullion1', m1 - FW / 2, fx0, 0, m1 + FW / 2, fx1, 2400, m_frame)
    box(d, 'F1_SlidingDoor_Mullion2', m2 - FW / 2, fx0, 0, m2 + FW / 2, fx1, 2400, m_frame)
    box(d, 'F1_SlidingDoor_Glass1', D1_X0 + FW, 93, 60, m1 - FW / 2, 107, 2340, m_glass)
    box(d, 'F1_SlidingDoor_Glass2', m1 + FW / 2, 93, 60, m2 - FW / 2, 107, 2340, m_glass)
    box(d, 'F1_SlidingDoor_Glass3', m2 + FW / 2, 93, 60, D1_X1 - FW, 107, 2340, m_glass)

    # ===== 二层正面两樘窗 =====
    win_y(root, 'F2_Window_Left',  W2_X0, W2_X1, 3950, 5650, 60, 140, [W2_M], m_frame, m_glass)
    win_y(root, 'F2_Window_Right', W3_X0, W3_X1, 3950, 5650, 60, 140, [W3_M], m_frame, m_glass)

    # ===== 左面窄窗 =====
    win_x(root, 'F1_Window_Left', 5050, 5750, 600, 1950, 40, 160, [], m_frame, m_glass)
    win_x(root, 'F2_Window_LeftSide', 5050, 5750, 3800, 5150, 40, 160, [], m_frame, m_glass)

    # ===== 背面窗（推断）=====
    win_y(root, 'B1_Window_Left',  2050, 3550, 900, 2400, D - 140, D - 60, [2800], m_frame, m_glass)
    win_y(root, 'B1_Window_Right', 6450, 7950, 900, 2400, D - 140, D - 60, [7200], m_frame, m_glass)
    win_y(root, 'B2_Window_Left',  2050, 3550, 4100, 5600, D - 140, D - 60, [2800], m_frame, m_glass)
    win_y(root, 'B2_Window_Right', 6450, 7950, 4100, 5600, D - 140, D - 60, [7200], m_frame, m_glass)

    # ===== 木格栅 =====
    slat_h = 6400
    n_f = 13
    span_f = (n_f - 1) * 105 + 60
    start_f = GR_X0 + (1400 - span_f) / 2
    (0...n_f).each do |i|
      x = start_f + i * 105
      box(root, format('Slat_Front_%03d', i + 1), x, -30, 0, x + 60, 0, slat_h, m_wood)
    end
    n_r = 76
    span_r = (n_r - 1) * 105 + 60
    start_r = (D - span_r) / 2
    (0...n_r).each do |i|
      y = start_r + i * 105
      box(root, format('Slat_Right_%03d', i + 1), W, y, 0, W + 30, y + 60, slat_h, m_wood)
    end

    # ===== 阳台玻璃栏板 =====
    rx0 = 400; rx1 = 9600; ry0 = -950; ry1 = -890
    posts = 5
    pw = 50
    gap = (rx1 - rx0 - posts * pw) / 4.0
    box(root, 'Balcony_Railing_Channel', rx0, ry0, 3200, rx1, ry1, 3250, m_frame)
    box(root, 'Balcony_Railing_TopRail', rx0, ry0, 4150, rx1, ry1, 4200, m_frame)
    (0...posts).each do |i|
      px = rx0 + i * (pw + gap)
      box(root, format('Balcony_Railing_Post_%02d', i + 1), px, ry0, 3200, px + pw, ry1, 4200, m_frame)
    end
    (0...4).each do |i|
      gx0 = rx0 + i * (pw + gap) + pw
      gx1 = gx0 + gap
      box(root, format('Balcony_Railing_Glass_%02d', i + 1), gx0, -928, 3250, gx1, -912, 4150, m_glass)
    end

    # ===== 阳台挑板底面筒灯 =====
    [1500, 3833, 6167, 8400].each_with_index do |lx, i|
      cyl(root, format('Balcony_Downlight_%02d', i + 1), lx, -600, 2950, 100, 30, m_light)
    end

    # ===== 一层可见室内家具（示意）=====
    zf = 20
    box(root, 'Int_Sofa_Seat', 3400, 3100, zf, 5600, 4000, zf + 420, m_sofa)
    box(root, 'Int_Sofa_Back', 3400, 3900, zf, 5600, 4120, zf + 860, m_sofa)
    box(root, 'Int_Sofa_ArmL', 3300, 3100, zf, 3400, 4120, zf + 600, m_sofa)
    box(root, 'Int_Sofa_ArmR', 5600, 3100, zf, 5700, 4120, zf + 600, m_sofa)
    box(root, 'Int_Armchair_Seat', 2300, 2900, zf, 3100, 3600, zf + 420, m_sofa)
    box(root, 'Int_Armchair_Back', 2300, 3520, zf, 3100, 3660, zf + 780, m_sofa)
    box(root, 'Int_Ottoman', 2500, 1950, zf, 3200, 2650, zf + 380, m_sofa)
    box(root, 'Int_CoffeeTable', 4200, 1850, zf, 5200, 2550, zf + 380, m_furn)
    box(root, 'Int_Plant_01_Pot', 1400, 700, zf, 1750, 1050, zf + 400, m_pot)
    box(root, 'Int_Plant_01_Leaf', 1330, 630, zf + 400, 1820, 1120, zf + 1250, m_plant)
    box(root, 'Int_Plant_02_Pot', 6000, 800, zf, 6350, 1150, zf + 400, m_pot)
    box(root, 'Int_Plant_02_Leaf', 5930, 730, zf + 400, 6420, 1220, zf + 1250, m_plant)
    box(root, 'Int_Curtain', 6150, 230, zf, 6550, 330, 2380, m_curtain)
    box(root, 'Int_Wall_Art', 4000, 7760, 1200, 4900, 7795, 1900, m_frame)

    true
  end
end

VillaBuild.run(model, root)
