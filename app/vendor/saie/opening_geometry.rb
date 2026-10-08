# frozen_string_literal: true
# Adapted from SAIE eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f,
# ruby_plugin/su_mcp_bridge/ops/opening.rb (MIT; see LICENSE).
#
# K Studio keeps only the geometry pattern: derive one wall-local frame, build
# ONE combined cutter for all rectangular openings, then perform ONE subtract.
# No Sketchup.active_model, AI_ID registry, transaction, save or bridge code is
# retained; the K Studio host owns those boundaries.

module KStudioSAIEOpening
  MM_TO_IN = 1.0 / 25.4

  module_function

  def validate_openings!(wall, openings)
    raise 'openings must be a nonempty Array' unless openings.is_a?(Array) && !openings.empty?
    length_mm = wall[:len] / MM_TO_IN
    height_mm = wall[:height] / MM_TO_IN
    intervals = []

    openings.each_with_index do |opening, index|
      raise "opening #{index} must be a Hash" unless opening.is_a?(Hash)
      offset = opening['offset_mm']
      width = opening['width_mm']
      height = opening['height_mm']
      sill = opening.fetch('sill_mm', 0)
      [offset, width, height, sill].each do |value|
        raise "opening #{index} values must be finite numbers" unless value.is_a?(Numeric) && value.finite?
      end
      raise "opening #{index} width/height must be positive" unless width > 0 && height > 0
      raise "opening #{index} offset/sill must be nonnegative" unless offset >= 0 && sill >= 0
      raise "opening #{index} exceeds wall length" unless offset + width <= length_mm + 0.01
      raise "opening #{index} exceeds wall height" unless sill + height <= height_mm + 0.01
      intervals << [offset, offset + width, sill, sill + height]
    end

    intervals.each_with_index do |a, i|
      intervals[(i + 1)..].to_a.each do |b|
        x_overlap = [a[1], b[1]].min - [a[0], b[0]].max
        z_overlap = [a[3], b[3]].min - [a[2], b[2]].max
        raise 'openings may not overlap' if x_overlap > 0.01 && z_overlap > 0.01
      end
    end
    true
  end

  def build(root, params)
    raise 'Wall parameters must be a Hash' unless params.is_a?(Hash)
    wall = KStudioSAIE._read_centerline(params)
    raise 'Wall centerline is zero length' if wall[:len] < 0.001
    openings = params['openings']
    validate_openings!(wall, openings)

    wall_group = KStudioSAIE._build_wall_group(root.entities, wall)
    cutter = root.entities.add_group
    cutter_entities = cutter.entities

    # SAIE uses one combined cutter to avoid progressive corruption from
    # sequential boolean subtracts. Keep the cutter slightly oversized across
    # wall thickness and Z so coplanar faces are not the cutting boundary.
    oversize = 10.0 * MM_TO_IN
    openings.each do |opening|
      x0 = opening['offset_mm'].to_f * MM_TO_IN
      x1 = (opening['offset_mm'].to_f + opening['width_mm'].to_f) * MM_TO_IN
      y0 = -(wall[:thick] / 2.0 + oversize)
      y1 = wall[:thick] / 2.0 + oversize
      z0 = opening.fetch('sill_mm', 0).to_f * MM_TO_IN - oversize
      z1 = (opening.fetch('sill_mm', 0).to_f + opening['height_mm'].to_f) * MM_TO_IN + oversize

      sub = cutter_entities.add_group
      points = [
        Geom::Point3d.new(x0, y0, z0),
        Geom::Point3d.new(x1, y0, z0),
        Geom::Point3d.new(x1, y1, z0),
        Geom::Point3d.new(x0, y1, z0)
      ]
      face = sub.entities.add_face(points)
      raise 'Could not create opening cutter face' unless face
      face.reverse! if face.normal.z < 0
      face.pushpull(z1 - z0)
      sub.explode
    end

    x_axis = Geom::Vector3d.new(wall[:dx] / wall[:len], wall[:dy] / wall[:len], 0)
    y_axis = Geom::Vector3d.new(-wall[:dy] / wall[:len], wall[:dx] / wall[:len], 0)
    z_axis = Geom::Vector3d.new(0, 0, 1)
    origin = Geom::Point3d.new(wall[:x1], wall[:y1], 0)
    cutter.transform!(Geom::Transformation.axes(origin, x_axis, y_axis, z_axis))

    result = cutter.subtract(wall_group)
    raise 'Combined opening subtract failed' unless result.is_a?(Sketchup::Group)
    result.name = params['name']
    elevation = params.fetch('elevation_mm', 0)
    result.transform!(Geom::Transformation.translation([0, 0, elevation.to_f * MM_TO_IN])) unless elevation.to_f.zero?
    result
  rescue StandardError
    cutter.erase! if defined?(cutter) && cutter && cutter.valid?
    wall_group.erase! if defined?(wall_group) && wall_group && wall_group.valid?
    raise
  end
end
