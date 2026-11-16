# frozen_string_literal: true
# Thin owned-root glue around licensed SAIE and Stultus code, not a new engine.
require_relative 'vendor/saie/wall_geometry'
require_relative 'vendor/saie/opening_geometry'
require_relative 'vendor/stultus/bounds'
require_relative 'native_deep_fingerprint'
require_relative 'native_definition_graph'
require_relative 'shared_definition_scope'

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
        unless matches.length == 1
          # Keep the exact failing prefix; a generic error caused repeated blind
          # KEEP retries on a nonexistent leaf in the real apartment trial.
          raise "Owned child name must match exactly one group or component: path=#{JSON.generate(path.first(i))}, matches=#{matches.length}; inspect this parent before retrying"
        end
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

  # Preserve the declared container and only replace its owned contents.
  # Reuse the existing exact-path resolver and its locked/shared checks.
  def owned_contents_target(root, path, approved_paths)
    raise 'Root contents clearing is forbidden' unless path.is_a?(Array) && !path.empty?
    raise 'Contents clearing requires declared edit scope' unless approved_paths.is_a?(Array) &&
      approved_paths.any? { |approved| path.take(approved.length) == approved }
    # Shared prototype edits require an additional exact HOST whitelist and a
    # complete document occurrence proof. The default unique-instance rule is
    # unchanged, including callers that provide only a Builder declaration.
    policy_file = File.join(File.dirname(File.dirname(File.dirname(root.model.path))), 'runtime', 'active_edit_scope.json')
    policy = File.file?(policy_file) ? JSON.parse(File.read(policy_file, encoding: 'UTF-8')) : {}
    shared = policy.fetch('shared_definition_edit_paths', [])
    if shared.include?(path)
      raise 'Shared edit requires complete graph fence' unless policy['scope_contract'] == 'deep_exact_paths_graph_v1'
      KStudioPathScopeGuard.validate_authorization!(policy, approved_paths, root.model.path, root.persistent_id)
      child = named_owned_group(root, path)
      KStudioSharedDefinitionScope.prove!(root, child, approved_paths, shared)
    else
      child = named_owned_group(root, path, true)
    end
    child
  end

  def clear_named_owned_contents(root, path, approved_paths)
    child = owned_contents_target(root, path, approved_paths)
    entities = child.is_a?(Sketchup::Group) ? child.entities : child.definition.entities
    count = entities.length
    entities.erase_entities(entities.to_a) unless count.zero?
    {persistent_id: child.persistent_id, removed_entities: count}
  end

  # Cut a real aperture without exposing arbitrary entity/root deletion. Face
  # IDs must resolve directly inside the approved leaf; shared leaves retain
  # the same all-document exact occurrence proof as contents replacement.
  def erase_named_owned_faces(root, path, face_pids, approved_paths)
    raise 'Provide 1..256 distinct owned face IDs' unless face_pids.is_a?(Array) &&
      (1..256).cover?(face_pids.length) && face_pids.uniq.length == face_pids.length &&
      face_pids.all? { |pid| pid.is_a?(Integer) && pid > 0 }
    child = owned_contents_target(root, path, approved_paths)
    entities = child.is_a?(Sketchup::Group) ? child.entities : child.definition.entities
    faces = entities.grep(Sketchup::Face).select { |face| face_pids.include?(face.persistent_id) }
    raise 'Face IDs must belong directly to the approved owned leaf' unless faces.length == face_pids.length
    entities.erase_entities(faces)
    {persistent_id: child.persistent_id, removed_face_ids: face_pids}
  end

  def inspect_named_owned_group(root, path, offset, limit, deep = false)
    group = named_owned_group(root, path)
    entities = group.is_a?(Sketchup::Group) ? group.entities : group.definition.entities
    objects = entities.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    page = objects.drop(offset).first(limit)
    snapshot = {
      path: path, persistent_id: group.persistent_id, locked: group.locked?,
      definition_instances: group.definition.instances.length, definition_name: group.definition.name.to_s,
      bounds_units: 'mm', bounds_frame: 'parent-local',
      bounds_mm: KStudioStultusBounds.bounds_mm(group.bounds),
      object_bounds_frame: 'selected-group-local',
      objects_total: objects.length, offset: offset,
      next_offset: offset + page.length < objects.length ? offset + page.length : nil,
      truncated: offset > 0 || offset + page.length < objects.length,
      objects: page.map { |e| {name: e.name, persistent_id: e.persistent_id, locked: e.locked?, bounds_mm: KStudioStultusBounds.bounds_mm(e.bounds)} }
    }
    if deep
      parent_world = Geom::Transformation.new
      (0...path.length).each do |depth|
        parent_world *= named_owned_group(root, path.take(depth)).transformation
      end
      policy_file = File.join(File.dirname(File.dirname(File.dirname(root.model.path))), 'runtime', 'active_edit_scope.json')
      graph_mode = false
      if File.file?(policy_file)
        policy = JSON.parse(File.read(policy_file, encoding: 'UTF-8'))
        graph_mode = policy['scope_contract'] == 'deep_exact_paths_graph_v1' && policy['status'] == 'active' &&
          policy['root_pid'] == root.persistent_id && File.expand_path(policy['model_path']) == File.expand_path(root.model.path)
      end
      if graph_mode
        node = KStudioNativeDefinitionGraph.node(group, parent_world, KStudioNativeDefinitionGraph.context)
        snapshot[:deep_fingerprint_collector] = 'KStudioNativeDefinitionGraph/1'
      else
        node = KStudioNativeDeepFingerprint.inspect_instance(group, parent_world, [], 0, {count: 0})
        snapshot[:deep_fingerprint_collector] = 'KStudioNativeDeepFingerprint/1'
      end
      snapshot[:deep_geometry_material_sha256] = node[:geometry_material_sha256]
    end
    snapshot
  end

  # Transaction-local KEEP guard. This deliberately runs inside the same
  # SketchUp operation as the candidate edit, so a regression raises before
  # commit and model_session.rb aborts the whole operation. The contract mirrors
  # K Studio's post-write fingerprint: persistent identity, direct child count
  # and parent-local millimeter bounds.
  def verify_owned_fingerprints!(root, expectations, tolerance_mm = 0.01)
    raise 'KEEP expectations must be a nonempty Array' unless expectations.is_a?(Array) && !expectations.empty?
    raise 'Too many KEEP expectations' if expectations.length > 256
    raise 'KEEP tolerance must be a positive number' unless tolerance_mm.is_a?(Numeric) && tolerance_mm.finite? && tolerance_mm > 0

    checks = []
    expectations.each_with_index do |expected, index|
      raise "KEEP expectation #{index} must be a Hash" unless expected.is_a?(Hash)
      path = expected['path']
      raise "KEEP expectation #{index} path is invalid" unless path.is_a?(Array) && !path.empty? && path.length <= 8

      snapshot = inspect_named_owned_group(root, path, 0, 1, expected.key?('deep_geometry_material_sha256'))
      label = path.join('/')
      expected_pid = expected['persistent_id']
      expected_count = expected['objects_total']
      expected_bounds = expected['bounds_mm']

      raise "KEEP regression #{label}: persistent_id changed" unless snapshot[:persistent_id] == expected_pid
      raise "KEEP regression #{label}: objects_total changed" unless snapshot[:objects_total] == expected_count
      raise "KEEP regression #{label}: bounds_mm missing" unless expected_bounds.is_a?(Hash)
      if expected.key?('deep_geometry_material_sha256')
        raise "KEEP regression #{label}: deep fingerprint contract changed" unless
          snapshot[:deep_fingerprint_collector] == expected.fetch('deep_fingerprint_collector', 'KStudioNativeDeepFingerprint/1')
        raise "KEEP regression #{label}: deep geometry/material changed" unless
          snapshot[:deep_geometry_material_sha256] == expected['deep_geometry_material_sha256']
      end

      actual_bounds = snapshot[:bounds_mm]
      %w[min max].each do |edge|
        wanted = expected_bounds[edge]
        actual = actual_bounds[edge.to_sym] || actual_bounds[edge]
        raise "KEEP regression #{label}: bounds_mm.#{edge} missing" unless wanted.is_a?(Array) && actual.is_a?(Array) && wanted.length == 3 && actual.length == 3
        wanted.zip(actual).each_with_index do |(a, b), axis|
          raise "KEEP regression #{label}: bounds_mm.#{edge}[#{axis}] changed" unless a.is_a?(Numeric) && b.is_a?(Numeric) && (a.to_f - b.to_f).abs <= tolerance_mm
        end
      end

      checks << {
        path: path,
        persistent_id: snapshot[:persistent_id],
        objects_total: snapshot[:objects_total],
        bounds_mm: snapshot[:bounds_mm]
      }
    end
    {verified: true, source: 'precommit_owned_keep_guard', checks: checks}
  end
end
