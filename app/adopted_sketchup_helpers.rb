# frozen_string_literal: true
# Thin owned-root glue around licensed SAIE and Stultus code, not a new engine.
require_relative 'vendor/saie/wall_geometry'
require_relative 'vendor/saie/opening_geometry'
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

  def wall_with_openings(root, params)
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
    KStudioSAIEOpening.build(root, params)
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

  # Named-path glue over owned groups; no model-global entity lookup or eval.
  def named_owned_group(root, path, mutation = false)
    raise 'Expected at most eight exact child names' unless path.is_a?(Array) && path.length <= 8 && path.all? { |n| n.is_a?(String) && !n.empty? && n.length <= 200 }
    current = root
    ([root] + path).each_with_index do |part, i|
      if i > 0
        entities = current.is_a?(Sketchup::Group) ? current.entities : current.definition.entities
        matches = entities.select { |e| (e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)) && e.name == part }
        raise 'Owned child name must match exactly one group or component' unless matches.length == 1
        current = matches.first
      end
      if mutation
        raise 'Owned child or ancestor is locked' if current.locked?
        raise 'Shared definition requires an explicit unique-instance edit first' if current.definition.instances.length > 1
      end
    end
    current
  end

  def remove_named_owned_group(root, name)
    path = name.is_a?(String) ? [name] : name
    raise 'Root removal is forbidden' unless path.is_a?(Array) && !path.empty?
    child = named_owned_group(root, path, true)
    removed_pid = child.persistent_id
    child.erase!
    removed_pid
  end

  def inspect_named_owned_group(root, path, offset, limit)
    group = named_owned_group(root, path)
    entities = group.is_a?(Sketchup::Group) ? group.entities : group.definition.entities
    objects = entities.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    page = objects.drop(offset).first(limit)
    {
      path: path, persistent_id: group.persistent_id, locked: group.locked?,
      bounds_units: 'mm', bounds_frame: 'parent-local',
      bounds_mm: KStudioStultusBounds.bounds_mm(group.bounds),
      object_bounds_frame: 'selected-group-local',
      objects_total: objects.length, offset: offset,
      next_offset: offset + page.length < objects.length ? offset + page.length : nil,
      truncated: offset > 0 || offset + page.length < objects.length,
      objects: page.map { |e| {name: e.name, persistent_id: e.persistent_id, locked: e.locked?, bounds_mm: KStudioStultusBounds.bounds_mm(e.bounds)} }
    }
  end
end
