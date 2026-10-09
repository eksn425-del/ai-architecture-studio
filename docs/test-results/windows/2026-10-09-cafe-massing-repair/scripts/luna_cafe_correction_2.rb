# Targeted correction 2: add a source-consistent bicycle-side foliage screen.
raise 'Luna correction requires model and root' unless model && root

existing = root.entities.grep(Sketchup::Group).find { |g| g.name == 'BICYCLE_CORNER_PLANT_SCREEN' }
if existing
  {
    'correction' => 2,
    'already_present' => true,
    'bounds_mm' => {
      'min' => [existing.bounds.min.x.to_mm.round(1), existing.bounds.min.y.to_mm.round(1), existing.bounds.min.z.to_mm.round(1)],
      'max' => [existing.bounds.max.x.to_mm.round(1), existing.bounds.max.y.to_mm.round(1), existing.bounds.max.z.to_mm.round(1)]
    }
  }
else
  mm = ->(n) { n.to_f.mm }
  pt = ->(x, y, z) { Geom::Point3d.new(mm.call(x), mm.call(y), mm.call(z)) }
  vec = ->(x, y, z) { Geom::Vector3d.new(x.to_f, y.to_f, z.to_f) }
  pot_mat = model.materials['Luna | Woven planter']
  dark = model.materials['Luna | Espresso brown']
  leaf = model.materials['Luna | Deep green foliage']
  leaf_light = model.materials['Luna | Olive foliage']

  face = lambda do |entities, points, mat|
    f = entities.add_face(points)
    if f
      f.material = mat
      f.back_material = mat
    end
    f
  end

  box = lambda do |entities, name, x1, y1, z1, x2, y2, z2, mat|
    lx, hx = [x1.to_f, x2.to_f].minmax
    ly, hy = [y1.to_f, y2.to_f].minmax
    lz, hz = [z1.to_f, z2.to_f].minmax
    g = entities.add_group
    g.name = name
    f = g.entities.add_face(pt.call(lx, ly, lz), pt.call(hx, ly, lz), pt.call(hx, hy, lz), pt.call(lx, hy, lz))
    raise "Cannot create planter box #{name}" unless f && f.valid?
    h = mm.call(hz - lz)
    f.pushpull(lz.abs < 0.001 ? -h : h)
    g.entities.grep(Sketchup::Face).each do |fc|
      fc.material = mat
      fc.back_material = mat
    end
    g
  end

  ellipsoid = lambda do |entities, name, cx, cy, cz, rx, ry, rz, mat, rings = 7, steps = 10|
    g = entities.add_group
    g.name = name
    ring_pts = []
    (1...rings).each do |r|
      phi = -Math::PI / 2.0 + Math::PI * r / rings.to_f
      ring = []
      steps.times do |i|
        theta = 2.0 * Math::PI * i / steps.to_f
        ring << pt.call(cx + rx * Math.cos(phi) * Math.cos(theta),
                        cy + ry * Math.cos(phi) * Math.sin(theta),
                        cz + rz * Math.sin(phi))
      end
      ring_pts << ring
    end
    bottom = pt.call(cx, cy, cz - rz)
    top = pt.call(cx, cy, cz + rz)
    steps.times do |i|
      j = (i + 1) % steps
      face.call(g.entities, [bottom, ring_pts[0][j], ring_pts[0][i]], mat)
      face.call(g.entities, [ring_pts[-1][i], ring_pts[-1][j], top], mat)
    end
    (0...(ring_pts.length - 1)).each do |r|
      steps.times do |i|
        j = (i + 1) % steps
        face.call(g.entities, [ring_pts[r][i], ring_pts[r][j], ring_pts[r + 1][j], ring_pts[r + 1][i]], mat)
      end
    end
    g
  end

  screen = root.entities.add_group
  screen.name = 'BICYCLE_CORNER_PLANT_SCREEN'
  box.call(screen.entities, 'SCREEN_WICKER_PLANTER', -1000, -1520, 0, 220, -1060, 500, pot_mat)
  box.call(screen.entities, 'SCREEN_PLANTER_SOIL', -960, -1480, 470, 180, -1100, 535, dark)
  ellipsoid.call(screen.entities, 'SCREEN_FOLIAGE_FRONT_LEFT', -650, -1320, 1120, 410, 180, 650, leaf, 7, 10)
  ellipsoid.call(screen.entities, 'SCREEN_FOLIAGE_FRONT_RIGHT', -250, -1330, 1220, 390, 170, 650, leaf_light, 7, 10)
  ellipsoid.call(screen.entities, 'SCREEN_FOLIAGE_CORNER', 120, -650, 1170, 190, 470, 620, leaf, 7, 10)
  ellipsoid.call(screen.entities, 'SCREEN_FOLIAGE_CORNER_HIGHLIGHT', 90, -680, 1420, 170, 400, 480, leaf_light, 7, 10)
  {
    'correction' => 2,
    'already_present' => false,
    'screen_bounds_mm' => {
      'min' => [screen.bounds.min.x.to_mm.round(1), screen.bounds.min.y.to_mm.round(1), screen.bounds.min.z.to_mm.round(1)],
      'max' => [screen.bounds.max.x.to_mm.round(1), screen.bounds.max.y.to_mm.round(1), screen.bounds.max.z.to_mm.round(1)]
    }
  }
end
