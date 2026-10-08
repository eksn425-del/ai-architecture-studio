# scripts/build_villa.rb  (r5)
# project: quality-v1-1008  single-image villa reconstruction
# Axes: origin = front-left ground corner; +X along the balcony facade (10.00 m),
#       +Y toward the rear (8.00 m), +Z up.
#       faces: :F front y=0 | :L left x=0 | :R right x=10 | :B rear y=8
#       u = distance along the facade, v = depth inward from the outer face
# Levels: FFL1 0.00, FFL2 3.20, roof slab 6.40-6.60, coping 6.60-6.72
# r5 changes:
#   (1) each facade wall now runs its FULL length (u 0..10 / u 0..8) and the outer
#       face sits 1 mm proud (v -0.001..0.299): the corner solids overlap instead of
#       abutting, so no spurious vertical seam shows at either corner and no two
#       faces are exactly coincident (no z-fighting).
#   (2) timber batten pitch tightened to 45/31 mm so the slat band reads as wood
#       dominated like the reference (was 45/60).
# Retained from r4: full-height wall segments (no seam at the 2F slab level) and
# explicit face/instance materials on component definitions.

M_IN = 39.3700787401575

W_TOT = 10.00
D_TOT =  8.00
H_L1  =  3.20
H_L2  =  6.40
T_W   =  0.30
WW0   = -0.001
WW1   =  0.299

MATS = {
  'STUCCO'  => ['F4F3EE', nil],
  'CONC'    => ['E9E7E2', nil],
  'PLINTH'  => ['D6D4CE', nil],
  'COPING'  => ['C8C6C1', nil],
  'WOOD'    => ['C8803C', nil],
  'WOODB'   => ['9C6029', nil],
  'FRAME'   => ['34322F', nil],
  'GLASS'   => ['AFC3CB', 0.20],
  'RAIL'    => ['C6D8DB', 0.12],
  'METAL'   => ['8E8E8C', nil],
  'PAVING'  => ['C4C2BD', nil],
  'LAWN'    => ['569A3E', nil],
  'FLOOR'   => ['D2CBBE', nil],
  'SOFA'    => ['BDB9B2', nil],
  'CUSH'    => ['D2CEC7', nil],
  'PLANT'   => ['3E7A33', nil],
  'POT'     => ['54504B', nil],
  'TABLE'   => ['6E5A48', nil],
  'CURTAIN' => ['F0EBE1', 0.55],
  'ART'     => ['DCD7CA', nil],
  'ARTF'    => ['4A4744', nil]
}

def m2i(v)
  v.to_f * M_IN
end

def get_mat(model, cache, key)
  cache[:mats] ||= {}
  return cache[:mats][key] if cache[:mats][key]
  spec = MATS[key] || ['CCCCCC', nil]
  m = model.materials[key]
  m = model.materials.add(key) if m.nil?
  m.color = Sketchup::Color.new(spec[0])
  m.alpha = spec[1] if spec[1]
  cache[:mats][key] = m
  m
end

def paint(container, mat)
  container.material = mat
  container.entities.each do |e|
    next unless e.is_a?(Sketchup::Face)
    e.material = mat
  end
end

def build_box(parent, model, cache, name, key, x0, y0, z0, x1, y1, z1)
  dx = x1 - x0
  dy = y1 - y0
  dz = z1 - z0
  return nil if dx <= 0.001 || dy <= 0.001 || dz <= 0.001
  g = parent.entities.add_group
  g.name = name
  pts = [
    Geom::Point3d.new(m2i(x0), m2i(y0), m2i(z0)),
    Geom::Point3d.new(m2i(x1), m2i(y0), m2i(z0)),
    Geom::Point3d.new(m2i(x1), m2i(y1), m2i(z0)),
    Geom::Point3d.new(m2i(x0), m2i(y1), m2i(z0))
  ]
  f = g.entities.add_face(pts)
  if f.nil? || !f.valid?
    g.erase! if g.valid?
    return nil
  end
  f.reverse! if f.normal.z < -0.5
  begin
    f.pushpull(m2i(dz))
  rescue StandardError
    g.erase! if g.valid?
    return nil
  end
  paint(g, get_mat(model, cache, key))
  g
end

def face_rect(face, u0, u1, v0, v1)
  case face
  when :F then [u0, v0, u1, v1]
  when :L then [v0, u0, v1, u1]
  when :R then [W_TOT - v1, u0, W_TOT - v0, u1]
  when :B then [u0, D_TOT - v1, u1, D_TOT - v0]
  else [u0, v0, u1, v1]
  end
end

def fbox(parent, model, cache, name, key, face, u0, u1, z0, z1, v0 = 0.0, v1 = T_W)
  x0, y0, x1, y1 = face_rect(face, u0, u1, v0, v1)
  build_box(parent, model, cache, name, key, x0, y0, z0, x1, y1, z1)
end

def cylinder(parent, model, cache, name, key, cx, cy, z0, r, h, segs = 14)
  g = parent.entities.add_group
  g.name = name
  pts = []
  segs.times do |i|
    a = 2.0 * Math::PI * i / segs
    pts << Geom::Point3d.new(m2i(cx + r * Math.cos(a)), m2i(cy + r * Math.sin(a)), m2i(z0))
  end
  f = g.entities.add_face(pts)
  if f.nil? || !f.valid?
    g.erase! if g.valid?
    return nil
  end
  f.reverse! if f.normal.z < -0.5
  begin
    f.pushpull(m2i(h))
  rescue StandardError
    g.erase! if g.valid?
    return nil
  end
  paint(g, get_mat(model, cache, key))
  g
end

# ---------- shared component definitions (versioned) ----------
def batten_def(model, cache)
  return cache[:batten] if cache[:batten]
  d = model.definitions['WOOD_BATTEN_V4']
  if d.nil?
    d = model.definitions.add('WOOD_BATTEN_V4')
    pts = [
      Geom::Point3d.new(0, 0, 0),
      Geom::Point3d.new(m2i(1.0), 0, 0),
      Geom::Point3d.new(m2i(1.0), m2i(1.0), 0),
      Geom::Point3d.new(0, m2i(1.0), 0)
    ]
    f = d.entities.add_face(pts)
    return nil if f.nil? || !f.valid?
    f.reverse! if f.normal.z < -0.5
    f.pushpull(m2i(1.0))
  end
  b = d.bounds
  return nil if b.min.z < -0.01 || b.max.z < m2i(0.99)
  return nil if b.min.x < -0.01 || b.min.y < -0.01
  paint(d, get_mat(model, cache, 'WOOD'))
  cache[:batten] = d
  d
end

def foliage_def(model, cache)
  return cache[:foliage] if cache[:foliage]
  d = model.definitions['SHRUB_FOLIAGE_V4']
  if d.nil?
    d = model.definitions.add('SHRUB_FOLIAGE_V4')
    segs = 8
    rings = 4
    mesh = Geom::PolygonMesh.new
    top = mesh.add_point(Geom::Point3d.new(0, 0, m2i(1.0)))
    bot = mesh.add_point(Geom::Point3d.new(0, 0, -m2i(1.0)))
    ringpts = []
    (1...rings).each do |k|
      theta = Math::PI * k / rings
      arr = []
      segs.times do |j|
        phi = 2.0 * Math::PI * j / segs
        arr << mesh.add_point(Geom::Point3d.new(
          m2i(Math.sin(theta) * Math.cos(phi)),
          m2i(Math.sin(theta) * Math.sin(phi)),
          m2i(Math.cos(theta))))
      end
      ringpts << arr
    end
    segs.times { |j| mesh.add_polygon(top, ringpts[0][j], ringpts[0][(j + 1) % segs]) }
    (0...(ringpts.size - 1)).each do |i|
      segs.times do |j|
        j2 = (j + 1) % segs
        mesh.add_polygon(ringpts[i][j], ringpts[i + 1][j], ringpts[i + 1][j2], ringpts[i][j2])
      end
    end
    segs.times { |j| mesh.add_polygon(bot, ringpts[-1][(j + 1) % segs], ringpts[-1][j]) }
    d.entities.add_faces_from_mesh(mesh, 0)
    d.entities.each do |e|
      next unless e.is_a?(Sketchup::Face)
      c = e.bounds.center
      v = Geom::Vector3d.new(c.x, c.y, c.z)
      e.reverse! if v.length > 0.001 && e.normal.dot(v) < 0
    end
  end
  b = d.bounds
  return nil if b.min.z > -m2i(0.9) || b.max.z < m2i(0.9)
  paint(d, get_mat(model, cache, 'PLANT'))
  cache[:foliage] = d
  d
end

def plant(model, parent, cache, name, x, y, z, pot_r, pot_h, fol_r, fol_h)
  g = parent.entities.add_group
  g.name = name
  cylinder(g, model, cache, 'POT', 'POT', x, y, z, pot_r, pot_h, 14)
  d = foliage_def(model, cache)
  if d
    tr = Geom::Transformation.new(Geom::Point3d.new(m2i(x), m2i(y), m2i(z + pot_h + fol_h * 0.55))) *
         Geom::Transformation.scaling(fol_r, fol_r, fol_h)
    inst = g.entities.add_instance(d, tr)
    if inst
      inst.name = 'FOLIAGE'
      inst.material = get_mat(model, cache, 'PLANT')
    end
  end
  g
end

def glazing(parent, model, cache, name, face, u0, u1, z0, z1, ndiv, opts = {})
  fw = opts[:frame_w] || 0.055
  bw = opts[:bottom_w] || fw
  dw = opts[:div_w] || 0.050
  v0 = opts[:v0] || 0.060
  v1 = opts[:v1] || 0.180
  gv0 = v0 + 0.040
  gv1 = gv0 + 0.012
  g = parent.entities.add_group
  g.name = name
  fbox(g, model, cache, 'FRAME_SILL', 'FRAME', face, u0, u1, z0, z0 + bw, v0, v1)
  fbox(g, model, cache, 'FRAME_HEAD', 'FRAME', face, u0, u1, z1 - fw, z1, v0, v1)
  fbox(g, model, cache, 'FRAME_LEFT', 'FRAME', face, u0, u0 + fw, z0, z1, v0, v1)
  fbox(g, model, cache, 'FRAME_RIGHT', 'FRAME', face, u1 - fw, u1, z0, z1, v0, v1)
  inner = (u1 - fw) - (u0 + fw)
  return g if inner <= 0.08 || ndiv < 1
  step = inner / ndiv
  (1...ndiv).each do |k|
    uc = u0 + fw + step * k
    fbox(g, model, cache, "MULLION_#{k}", 'FRAME', face, uc - dw / 2.0, uc + dw / 2.0, z0, z1, v0, v1)
  end
  ndiv.times do |k|
    a = u0 + fw + step * k + 0.006
    b = u0 + fw + step * (k + 1) - 0.006
    fbox(g, model, cache, "GLASS_#{k}", 'GLASS', face, a, b, z0 + bw + 0.006, z1 - fw - 0.006, gv0, gv1)
  end
  g
end

def add_wall(g, model, cache, cnt, face, u0, u1, z0, z1)
  cnt[:n] += 1
  fbox(g, model, cache, format('WALL_%s_%02d', face, cnt[:n]), 'STUCCO',
       face, u0, u1, z0, z1, WW0, WW1)
end

# ============================================================
def build_site(model, root, cache)
  g = root.entities.add_group
  g.name = 'SITE'
  build_box(g, model, cache, 'LAWN', 'LAWN', -7.00, -8.00, -0.22, 17.00, 16.00, -0.12)
  build_box(g, model, cache, 'PAVING_FRONT', 'PAVING', -2.20, -2.20, -0.20, 12.20, 0.00, -0.05)
  build_box(g, model, cache, 'PAVING_REAR',  'PAVING', -2.20,  8.00, -0.20, 12.20, 10.20, -0.05)
  build_box(g, model, cache, 'PAVING_LEFT',  'PAVING', -2.20,  0.00, -0.20,  0.00,  8.00, -0.05)
  build_box(g, model, cache, 'PAVING_RIGHT', 'PAVING', 10.00,  0.00, -0.20, 12.20,  8.00, -0.05)
  fbox(g, model, cache, 'PLINTH_F', 'PLINTH', :F, 0.00, 10.00, 0.00, 0.15, -0.030, 0.290)
  fbox(g, model, cache, 'PLINTH_B', 'PLINTH', :B, 0.00, 10.00, 0.00, 0.15, -0.030, 0.290)
  fbox(g, model, cache, 'PLINTH_L', 'PLINTH', :L, 0.00,  8.00, 0.00, 0.15, -0.030, 0.290)
  fbox(g, model, cache, 'PLINTH_R', 'PLINTH', :R, 0.00,  8.00, 0.00, 0.15, -0.030, 0.290)
  g
end

def build_shell(model, root, cache)
  g = root.entities.add_group
  g.name = 'SHELL'
  cnt = { n: 0 }
  zi = 0.00
  zt = H_L2

  # FRONT facade: full u 0..10. Openings: glass slider 1.90-6.50 z0-2.60,
  # windows A 2.30-4.70 and B 6.30-8.10 (z 4.10-5.60)
  add_wall(g, model, cache, cnt, :F, 0.00, 1.90, zi, zt)
  add_wall(g, model, cache, cnt, :F, 1.90, 2.30, 2.60, zt)
  add_wall(g, model, cache, cnt, :F, 2.30, 4.70, 2.60, 4.10)
  add_wall(g, model, cache, cnt, :F, 2.30, 4.70, 5.60, zt)
  add_wall(g, model, cache, cnt, :F, 4.70, 6.30, 2.60, zt)
  add_wall(g, model, cache, cnt, :F, 6.30, 6.50, 2.60, 4.10)
  add_wall(g, model, cache, cnt, :F, 6.30, 8.10, 5.60, zt)
  add_wall(g, model, cache, cnt, :F, 6.50, 8.10, zi, 4.10)
  add_wall(g, model, cache, cnt, :F, 8.10, 10.00, zi, zt)

  # LEFT facade: full u 0..8, window 0.90x1.50 at y 3.15-4.05
  add_wall(g, model, cache, cnt, :L, 0.00, 3.15, zi, zt)
  add_wall(g, model, cache, cnt, :L, 3.15, 4.05, zi, 0.90)
  add_wall(g, model, cache, cnt, :L, 3.15, 4.05, 2.40, 4.10)
  add_wall(g, model, cache, cnt, :L, 3.15, 4.05, 5.60, zt)
  add_wall(g, model, cache, cnt, :L, 4.05, 8.00, zi, zt)

  # RIGHT facade: full u 0..8, inferred window 1.20x1.50 at y 3.00-4.20
  add_wall(g, model, cache, cnt, :R, 0.00, 3.00, zi, zt)
  add_wall(g, model, cache, cnt, :R, 3.00, 4.20, zi, 0.90)
  add_wall(g, model, cache, cnt, :R, 3.00, 4.20, 2.40, 4.10)
  add_wall(g, model, cache, cnt, :R, 3.00, 4.20, 5.60, zt)
  add_wall(g, model, cache, cnt, :R, 4.20, 8.00, zi, zt)

  # REAR facade: full u 0..10 [ASSUMED] door 2.50-3.40, window 6.00-7.50,
  # 2F windows 2.30-3.80 and 6.30-7.80
  add_wall(g, model, cache, cnt, :B, 0.00, 2.30, zi, zt)
  add_wall(g, model, cache, cnt, :B, 2.30, 2.50, zi, 4.10)
  add_wall(g, model, cache, cnt, :B, 2.30, 2.50, 5.60, zt)
  add_wall(g, model, cache, cnt, :B, 2.50, 3.40, 2.10, 4.10)
  add_wall(g, model, cache, cnt, :B, 2.50, 3.40, 5.60, zt)
  add_wall(g, model, cache, cnt, :B, 3.40, 3.80, zi, 4.10)
  add_wall(g, model, cache, cnt, :B, 3.40, 3.80, 5.60, zt)
  add_wall(g, model, cache, cnt, :B, 3.80, 6.00, zi, zt)
  add_wall(g, model, cache, cnt, :B, 6.00, 6.30, zi, 0.90)
  add_wall(g, model, cache, cnt, :B, 6.00, 6.30, 2.40, zt)
  add_wall(g, model, cache, cnt, :B, 6.30, 7.50, zi, 0.90)
  add_wall(g, model, cache, cnt, :B, 6.30, 7.50, 2.40, 4.10)
  add_wall(g, model, cache, cnt, :B, 6.30, 7.50, 5.60, zt)
  add_wall(g, model, cache, cnt, :B, 7.50, 7.80, zi, 4.10)
  add_wall(g, model, cache, cnt, :B, 7.50, 7.80, 5.60, zt)
  add_wall(g, model, cache, cnt, :B, 7.80, 10.00, zi, zt)

  build_box(g, model, cache, 'SLAB_GF', 'CONC', 0.32, 0.32, -0.15, 9.68, 7.68, 0.00)
  build_box(g, model, cache, 'SLAB_2F', 'CONC', 0.32, 0.32, 2.95, 9.68, 7.68, H_L1)

  build_box(g, model, cache, 'ROOF_SLAB', 'CONC', -0.05, -0.05, H_L2, 10.05, 8.05, 6.60)
  build_box(g, model, cache, 'COPING_F', 'COPING', -0.05, -0.05, 6.60, 10.05, 0.13, 6.72)
  build_box(g, model, cache, 'COPING_B', 'COPING', -0.05, 7.87, 6.60, 10.05, 8.05, 6.72)
  build_box(g, model, cache, 'COPING_L', 'COPING', -0.05, 0.13, 6.60, 0.13, 7.87, 6.72)
  build_box(g, model, cache, 'COPING_R', 'COPING', 9.87, 0.13, 6.60, 10.05, 7.87, 6.72)
  g
end

def build_glazing(model, root, cache)
  g = root.entities.add_group
  g.name = 'GLAZING'
  glazing(g, model, cache, 'DOOR_F_1F', :F, 1.90, 6.50, 0.00, 2.60, 4,
          frame_w: 0.060, bottom_w: 0.030, div_w: 0.055, v0: 0.045, v1: 0.165)
  glazing(g, model, cache, 'WIN_F_2F_A', :F, 2.30, 4.70, 4.10, 5.60, 2)
  glazing(g, model, cache, 'WIN_F_2F_B', :F, 6.30, 8.10, 4.10, 5.60, 2)
  glazing(g, model, cache, 'WIN_L_1F', :L, 3.15, 4.05, 0.90, 2.40, 1)
  glazing(g, model, cache, 'WIN_L_2F', :L, 3.15, 4.05, 4.10, 5.60, 1)
  glazing(g, model, cache, 'WIN_R_1F', :R, 3.00, 4.20, 0.90, 2.40, 2)
  glazing(g, model, cache, 'WIN_R_2F', :R, 3.00, 4.20, 4.10, 5.60, 2)
  fbox(g, model, cache, 'DOOR_B_1F_LEAF', 'FRAME', :B, 2.53, 3.37, 0.02, 2.08, 0.060, 0.140)
  fbox(g, model, cache, 'DOOR_B_1F_FRAME_L', 'FRAME', :B, 2.50, 2.56, 0.00, 2.10, 0.050, 0.160)
  fbox(g, model, cache, 'DOOR_B_1F_FRAME_R', 'FRAME', :B, 3.34, 3.40, 0.00, 2.10, 0.050, 0.160)
  fbox(g, model, cache, 'DOOR_B_1F_FRAME_H', 'FRAME', :B, 2.50, 3.40, 2.04, 2.10, 0.050, 0.160)
  glazing(g, model, cache, 'WIN_B_1F', :B, 6.00, 7.50, 0.90, 2.40, 2)
  glazing(g, model, cache, 'WIN_B_2F_A', :B, 2.30, 3.80, 4.10, 5.60, 2)
  glazing(g, model, cache, 'WIN_B_2F_B', :B, 6.30, 7.80, 4.10, 5.60, 2)
  g
end

def build_cladding(model, root, cache)
  g = root.entities.add_group
  g.name = 'CLADDING'
  d = batten_def(model, cache)
  wood = get_mat(model, cache, 'WOOD')
  build_box(g, model, cache, 'BACK_F', 'WOODB', 8.50, -0.015, 0.15, 10.00, 0.00, 6.60)
  build_box(g, model, cache, 'BACK_R', 'WOODB', 10.00, 0.00, 0.15, 10.015, 3.00, 6.60)
  # front band 1.50 m: 20 battens, 45 slat / 31 gap
  n = 20
  pitch = (1.50 - 0.045) / (n - 1)
  n.times do |k|
    x = 8.50 + k * pitch
    nm = format('BATTEN_F_%02d', k)
    if d
      tr = Geom::Transformation.new(Geom::Point3d.new(m2i(x), m2i(-0.09), m2i(0.15))) *
           Geom::Transformation.scaling(0.045, 0.075, 6.45)
      inst = g.entities.add_instance(d, tr)
      if inst
        inst.name = nm
        inst.material = wood
      end
    else
      build_box(g, model, cache, nm, 'WOOD', x, -0.09, 0.15, x + 0.045, -0.015, 6.60)
    end
  end
  # right band 3.00 m: 40 battens
  n2 = 40
  pitch2 = (3.00 - 0.045) / (n2 - 1)
  n2.times do |k|
    y = k * pitch2
    nm = format('BATTEN_R_%02d', k)
    if d
      tr = Geom::Transformation.new(Geom::Point3d.new(m2i(10.015), m2i(y), m2i(0.15))) *
           Geom::Transformation.scaling(0.075, 0.045, 6.45)
      inst = g.entities.add_instance(d, tr)
      if inst
        inst.name = nm
        inst.material = wood
      end
    else
      build_box(g, model, cache, nm, 'WOOD', 10.015, y, 0.15, 10.09, y + 0.045, 6.60)
    end
  end
  g
end

def build_balcony(model, root, cache)
  g = root.entities.add_group
  g.name = 'BALCONY'
  build_box(g, model, cache, 'BALCONY_SLAB', 'CONC', 0.20, -1.40, 2.95, 8.40, 0.20, H_L1)
  build_box(g, model, cache, 'BALCONY_FASCIA', 'CONC', 0.20, -1.42, 2.95, 8.40, -1.36, 3.16)
  cylinder(g, model, cache, 'DOWNLIGHT_1', 'METAL', 3.90, -0.75, 2.930, 0.045, 0.020, 14)
  cylinder(g, model, cache, 'DOWNLIGHT_2', 'METAL', 5.90, -0.75, 2.930, 0.045, 0.020, 14)

  rail = g.entities.add_group
  rail.name = 'GLASS_RAIL'
  build_box(rail, model, cache, 'SHOE_FRONT', 'METAL', 0.20, -1.375, 3.20, 8.40, -1.30, 3.32)
  build_box(rail, model, cache, 'SHOE_LEFT', 'METAL', 0.20, -1.38, 3.20, 0.28, -0.02, 3.32)
  build_box(rail, model, cache, 'SHOE_RIGHT', 'METAL', 8.32, -1.38, 3.20, 8.40, -0.02, 3.32)
  np = 8
  pw = (8.40 - 0.20) / np
  np.times do |k|
    x0 = 0.20 + k * pw
    x1 = x0 + pw - 0.008
    build_box(rail, model, cache, format('RAIL_GLASS_F_%02d', k), 'RAIL',
              x0, -1.352, 3.30, x1, -1.338, 4.25)
  end
  build_box(rail, model, cache, 'RAIL_GLASS_L', 'RAIL', 0.250, -1.352, 3.30, 0.264, -0.020, 4.25)
  build_box(rail, model, cache, 'RAIL_GLASS_R', 'RAIL', 8.336, -1.352, 3.30, 8.350, -0.020, 4.25)
  (np + 1).times do |k|
    x = 0.20 + k * pw
    build_box(rail, model, cache, format('RAIL_CLAMP_%02d', k), 'METAL',
              x - 0.025, -1.365, 3.20, x + 0.025, -1.305, 3.44)
  end
  build_box(rail, model, cache, 'RAIL_CLAMP_L', 'METAL', 0.255, -1.36, 3.20, 0.300, -1.30, 3.44)
  build_box(rail, model, cache, 'RAIL_CLAMP_R', 'METAL', 8.300, -1.36, 3.20, 8.345, -1.30, 3.44)
  g
end

def sofa_fy(model, parent, cache, name, x0, x1, y_front, y_back, z0)
  g = parent.entities.add_group
  g.name = name
  build_box(g, model, cache, 'BASE', 'SOFA', x0, y_front, z0, x1, y_back, z0 + 0.20)
  build_box(g, model, cache, 'SEAT', 'CUSH', x0 + 0.16, y_front + 0.05, z0 + 0.20, x1 - 0.16, y_back - 0.24, z0 + 0.44)
  build_box(g, model, cache, 'BACK', 'SOFA', x0 + 0.16, y_back - 0.22, z0 + 0.20, x1 - 0.16, y_back, z0 + 0.84)
  build_box(g, model, cache, 'ARM_L', 'SOFA', x0, y_front, z0 + 0.20, x0 + 0.16, y_back, z0 + 0.64)
  build_box(g, model, cache, 'ARM_R', 'SOFA', x1 - 0.16, y_front, z0 + 0.20, x1, y_back, z0 + 0.64)
  g
end

def build_interior(model, root, cache)
  g = root.entities.add_group
  g.name = 'INTERIOR_1F'
  build_box(g, model, cache, 'FLOOR_1F', 'FLOOR', 0.32, 0.32, -0.15, 9.68, 7.68, 0.00)
  sofa_fy(model, g, cache, 'SOFA_1F', 3.20, 5.40, 1.95, 2.90, 0.00)
  ott = g.entities.add_group
  ott.name = 'OTTOMAN_1F'
  build_box(ott, model, cache, 'BODY', 'SOFA', 4.00, 1.20, 0.00, 4.80, 1.90, 0.38)
  build_box(ott, model, cache, 'TOP', 'CUSH', 4.02, 1.22, 0.38, 4.78, 1.88, 0.46)
  ac = g.entities.add_group
  ac.name = 'ARMCHAIR_1F'
  build_box(ac, model, cache, 'BASE', 'SOFA', 5.90, 1.70, 0.00, 6.70, 2.50, 0.20)
  build_box(ac, model, cache, 'SEAT', 'CUSH', 5.96, 1.76, 0.20, 6.64, 2.44, 0.44)
  build_box(ac, model, cache, 'BACK', 'SOFA', 6.48, 1.76, 0.20, 6.70, 2.44, 0.82)
  tb = g.entities.add_group
  tb.name = 'TABLE_1F'
  build_box(tb, model, cache, 'TOP', 'TABLE', 3.85, 0.95, 0.33, 5.15, 1.55, 0.38)
  build_box(tb, model, cache, 'LEG_1', 'TABLE', 3.90, 1.00, 0.00, 3.95, 1.05, 0.33)
  build_box(tb, model, cache, 'LEG_2', 'TABLE', 5.05, 1.00, 0.00, 5.10, 1.05, 0.33)
  build_box(tb, model, cache, 'LEG_3', 'TABLE', 3.90, 1.45, 0.00, 3.95, 1.50, 0.33)
  build_box(tb, model, cache, 'LEG_4', 'TABLE', 5.05, 1.45, 0.00, 5.10, 1.50, 0.33)
  build_box(g, model, cache, 'CURTAIN_1F', 'CURTAIN', 5.72, 0.44, 0.05, 6.42, 0.48, 2.55)
  fr1 = g.entities.add_group
  fr1.name = 'ART_1F_1'
  build_box(fr1, model, cache, 'FRAME', 'ARTF', 0.32, 1.60, 1.35, 0.345, 2.20, 2.15)
  build_box(fr1, model, cache, 'CANVAS', 'ART', 0.345, 1.63, 1.38, 0.352, 2.17, 2.12)
  fr2 = g.entities.add_group
  fr2.name = 'ART_1F_2'
  build_box(fr2, model, cache, 'FRAME', 'ARTF', 0.32, 2.50, 1.35, 0.345, 3.10, 2.15)
  build_box(fr2, model, cache, 'CANVAS', 'ART', 0.345, 2.53, 1.38, 0.352, 3.07, 2.12)
  plant(model, g, cache, 'PLANT_1F_A', 2.35, 0.75, 0.00, 0.15, 0.32, 0.26, 0.60)
  plant(model, g, cache, 'PLANT_1F_B', 6.25, 0.70, 0.00, 0.15, 0.32, 0.28, 0.66)
  plant(model, g, cache, 'PLANT_1F_C', 5.95, 2.90, 0.00, 0.15, 0.30, 0.24, 0.55)
  g
end

def build_balcony_furniture(model, root, cache)
  g = root.entities.add_group
  g.name = 'BALCONY_FURN'
  sofa_fy(model, g, cache, 'SOFA_BAL', 5.00, 7.00, 0.10, 1.05, H_L1)
  tb = g.entities.add_group
  tb.name = 'TABLE_BAL'
  build_box(tb, model, cache, 'TOP', 'TABLE', 3.95, -0.50, 3.42, 4.55, 0.10, 3.47)
  build_box(tb, model, cache, 'LEG_1', 'TABLE', 4.00, -0.45, H_L1, 4.05, -0.40, 3.42)
  build_box(tb, model, cache, 'LEG_2', 'TABLE', 4.45, -0.45, H_L1, 4.50, -0.40, 3.42)
  build_box(tb, model, cache, 'LEG_3', 'TABLE', 4.00, 0.05, H_L1, 4.05, 0.10, 3.42)
  build_box(tb, model, cache, 'LEG_4', 'TABLE', 4.45, 0.05, H_L1, 4.50, 0.10, 3.42)
  plant(model, g, cache, 'PLANT_BAL_A', 1.05, -0.55, H_L1, 0.18, 0.38, 0.30, 0.80)
  plant(model, g, cache, 'PLANT_BAL_B', 7.55, -0.45, H_L1, 0.17, 0.34, 0.28, 0.72)
  plant(model, g, cache, 'PLANT_BAL_C', 8.10, -1.05, H_L1, 0.15, 0.30, 0.24, 0.58)
  plant(model, g, cache, 'PLANT_BAL_D', 4.25, -1.05, H_L1, 0.15, 0.30, 0.22, 0.52)
  g
end

# ============================================================
def build_all(model, root)
  cache = {}
  build_site(model, root, cache)
  build_shell(model, root, cache)
  build_glazing(model, root, cache)
  build_cladding(model, root, cache)
  build_balcony(model, root, cache)
  build_interior(model, root, cache)
  build_balcony_furniture(model, root, cache)
  root
end

build_all(model, root)
puts "build_villa r5: children=#{root.entities.count}"
