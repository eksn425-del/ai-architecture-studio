# frozen_string_literal: true
# Adapts the explicit opening-boundary shell method from Local MCP for SketchUp
# Copyright 2026 zhanglinqi and contributors.
# (Apache-2.0, see vendor/local_mcp_sketchup). Geometry only, under the owned writer.

module KStudioWindowBay
  module_function

  def rectangle(x, z, width, height)
    [[x, z], [x + width, z], [x + width, z + height], [x, z + height]]
  end

  def points(loop, y)
    loop.map { |x, z| Geom::Point3d.new(x.mm, y.mm, z.mm) }
  end

  def material(model, rgb, alpha)
    name = "KStudioBay_#{rgb.join('_')}_#{alpha}"
    material = model.materials[name]
    return material if material

    material = model.materials.add(name)
    material.color = Sketchup::Color.new(*rgb)
    material.alpha = alpha
    material
  end

  def solid(entities, name, exterior, interior, front_y, depth, area, finish)
    group = entities.add_group
    group.name = name
    front = points(exterior, front_y)
    back = points(exterior.reverse, front_y + depth)
    front_holes = interior ? [points(interior.reverse, front_y)] : []
    back_holes = interior ? [points(interior, front_y + depth)] : []
    loops = [front, *front_holes]
    front_face = back_face = nil
    group.entities.build do |builder|
      front_face = builder.add_face(front, holes: front_holes)
      back_face = builder.add_face(back, holes: back_holes)
      loops.each do |loop|
        loop.each_index do |i|
          a = loop[i]
          b = loop[(i + 1) % loop.length]
          builder.add_face([b, a, Geom::Point3d.new(a.x, (front_y + depth).mm, a.z),
                            Geom::Point3d.new(b.x, (front_y + depth).mm, b.z)])
        end
      end
    end
    unless front_face.loops.size == loops.size && back_face.loops.size == loops.size
      raise "#{name}: native opening loops did not match the specification"
    end
    expected_volume_mm3 = area * depth
    actual_volume_mm3 = group.volume * 25.4**3
    unless group.manifold? && (actual_volume_mm3 - expected_volume_mm3).abs <= [0.1, expected_volume_mm3 * 1e-6].max
      raise "#{name}: native solid volume or edge closure did not match the specification"
    end
    group.entities.grep(Sketchup::Face).each do |face|
      face.material = finish
      face.back_material = finish
    end
    group
  end

  def build(model, part, piece, instance_name)
    unless part.entities.respond_to?(:build)
      raise 'Window bays need the SketchUp 2022+ EntitiesBuilder API; use the established wall/opening workflow on this host.'
    end

    definition = model.definitions.add("WindowBay_#{part.name}_#{instance_name}")
    width, thickness, height = piece.fetch('size')
    offset, sill, opening_width, opening_height = piece.fetch('opening')
    frame_width = piece.fetch('frame_width_mm')
    frame_depth = piece.fetch('frame_depth_mm')
    glass_depth = piece.fetch('glass_thickness_mm', 6)
    frame_y = piece.fetch('recess_mm')
    glass_width = opening_width - 2 * frame_width
    glass_height = opening_height - 2 * frame_width
    pane_area = glass_width * glass_height
    opening_area = opening_width * opening_height
    opening = rectangle(offset, sill, opening_width, opening_height)
    pane = rectangle(offset + frame_width, sill + frame_width, glass_width, glass_height)

    solid(definition.entities, 'Wall', rectangle(0, 0, width, height), opening, 0, thickness,
          width * height - opening_area, material(model, piece.fetch('color', [190, 180, 160]), 1))
    solid(definition.entities, 'Frame', opening, pane, frame_y, frame_depth,
          opening_area - pane_area, material(model, piece.fetch('frame_color', [52, 57, 61]), 1))
    solid(definition.entities, 'Glass', pane, nil, frame_y + (frame_depth - glass_depth) / 2.0, glass_depth,
          pane_area, material(model, piece.fetch('glass_color', [146, 182, 195]), piece.fetch('glass_alpha', 0.45)))
    instance = part.entities.add_instance(definition, Geom::Transformation.new)
    instance.name = instance_name
    instance
  end
end
