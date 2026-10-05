# frozen_string_literal: true
# Thin owned-root glue around licensed SAIE and Stultus code, not a new engine.
require_relative 'vendor/saie/wall_geometry'
require_relative 'vendor/stultus/bounds'

module KStudioProfessionalHelpers
  module_function

  def wall(root, params)
    raise 'Wall parameters must be a Hash' unless params.is_a?(Hash)
    cl = params['centerline']
    raise 'centerline must contain exactly two [x,y] points in mm' unless cl.is_a?(Array) && cl.length == 2 && cl.all? { |p| p.is_a?(Array) && p.length == 2 && p.all? { |v| v.is_a?(Numeric) && v.finite? } }
    %w[thickness_mm height_mm].each do |key|
      value = params[key]
      raise "#{key} must be a positive finite number in mm" unless value.is_a?(Numeric) && value.finite? && value > 0
    end
    elevation = params.fetch('elevation_mm', 0)
    raise 'elevation_mm must be finite' unless elevation.is_a?(Numeric) && elevation.finite?
    name = params['name']
    raise 'Provide a unique nonempty wall name' unless name.is_a?(String) && !name.strip.empty? && name.length <= 200
    raise 'Wall name already exists; edit/remove only the affected child first' if root.entities.any? { |e| e.respond_to?(:name) && e.name == name }
    coordinates = KStudioSAIE._read_centerline(params)
    raise 'Wall centerline is zero length' if coordinates[:len] < 0.001
    group = KStudioSAIE._build_wall_group(root.entities, coordinates)
    group.name = name
    group.transform!(Geom::Transformation.translation([0, 0, elevation * KStudioSAIE::MM_TO_IN])) unless elevation.zero?
    group
  end

  def owned_snapshot(root, limit = 200)
    objects = root.entities.to_a.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    {
      api_units: 'inch', bounds_units: 'mm', axes: %w[x y z],
      root_bounds_frame: 'model', object_bounds_frame: 'owned-root-local',
      bounds_mm: KStudioStultusBounds.bounds_mm(root.bounds),
      objects_total: objects.length, truncated: objects.length > limit,
      objects: objects.first(limit).map do |e|
        { persistent_id: e.persistent_id, name: e.name,
          locked: e.locked?, bounds_mm: KStudioStultusBounds.bounds_mm(e.bounds) }
      end
    }
  end
end
