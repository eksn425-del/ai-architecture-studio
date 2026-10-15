# frozen_string_literal: true
# Host-only precommit fence. Reuses the native deep geometry collector, masking
# ONLY exact declared subtree paths; ancestor geometry and siblings stay fixed.
require_relative 'native_deep_fingerprint'
require_relative 'adopted_sketchup_helpers'
module KStudioPathScopeGuard
  extend self

  def paths!(paths)
    raise 'Path scope requires 1..48 exact paths' unless paths.is_a?(Array) && (1..48).cover?(paths.length)
    paths.each do |path|
      raise 'Invalid path scope' unless path.is_a?(Array) && (1..8).cover?(path.length) &&
        path.all? { |s| s.is_a?(String) && !s.strip.empty? && s.length <= 200 }
    end
    raise 'Duplicate path scope' unless paths.uniq.length == paths.length
    paths.combination(2).each do |a, b|
      raise 'Overlapping ancestor/child scope' if a.take(b.length) == b || b.take(a.length) == a
    end
    paths
  end

  def metadata(instance, world)
    c = KStudioNativeDeepFingerprint
    {pid: instance.persistent_id, name: c.entity_name(instance),
     local_transform: c.matrix(instance.transformation), world_transform: c.matrix(world),
     hidden: instance.hidden?, locked: instance.locked?, tag: c.tag(instance), material: c.material(instance.material)}
  end

  # Making one approved shared instance unique changes the remaining
  # definition's reference count/GUID, without changing its geometry or IDs.
  # Keep the collector's full geometry/material hash and identity tree.
  def protected_node(value)
    case value
    when Hash
      value.each_with_object({}) do |(key, item), out|
        next if [:definition_guid, :definition_instances].include?(key)
        out[key] = protected_node(item)
      end
    when Array then value.map { |item| protected_node(item) }
    else value
    end
  end

  def branch(instance, parent_world, path, paths, counter)
    c = KStudioNativeDeepFingerprint
    world = parent_world * instance.transformation
    if paths.include?(path)
      # Replacing a declared existing group still loses its stable identity.
      return {target_path: path, pid: instance.persistent_id, name: c.entity_name(instance), locked: instance.locked?}
    end
    unless paths.any? { |p| p.take(path.length) == path }
      return protected_node(c.inspect_instance(instance, parent_world, [], path.length, counter))
    end
    items = instance.is_a?(Sketchup::Group) ? instance.entities : instance.definition.entities
    children = items.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    names = children.map { |e| c.entity_name(e) }
    raise 'Ambiguous path ancestor children' unless names.uniq.length == names.length
    paths.select { |p| p.take(path.length) == path && p.length > path.length }.each do |p|
      raise "Missing scope path #{p.join('/')}" unless names.include?(p[path.length])
    end
    loose = c.scan(items.reject { |e| children.include?(e) }, world, [], path.length, counter)
    {metadata: metadata(instance, world), loose_sha: c.sha(loose),
     children: children.sort_by { |e| c.entity_name(e) }.map { |e| branch(e, world, path + [c.entity_name(e)], paths, counter) }}
  end

  def capture(root, paths)
    paths!(paths)
    model = root.model
    # Optional HOST-owned per-project authorization. A Builder declaration must
    # not enlarge an approved nested scope to its ancestor. Absent policy keeps
    # existing projects' explicit-path behavior unchanged.
    policy_file = File.join(File.dirname(File.dirname(File.dirname(model.path))), 'runtime', 'active_edit_scope.json')
    required_keep = []
    if File.file?(policy_file)
      policy = JSON.parse(File.read(policy_file, encoding: 'UTF-8'))
      validate_authorization!(policy, paths, model.path, root.persistent_id)
      keep_paths = policy.fetch('required_preserve_paths', [])
      paths!(keep_paths) unless keep_paths.empty?
      required_keep = keep_paths.map do |path|
        protected_node(KStudioProfessionalHelpers.inspect_named_owned_group(root, path, 0, 1, true))
      end
    end
    raise 'Exit edit context before path scope capture' unless model.active_path.nil?
    c = KStudioNativeDeepFingerprint
    groups = model.entities.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    raise 'Owned root must be at document top level' unless groups.include?(root)
    loose = c.scan(model.entities.reject { |e| groups.include?(e) }, Geom::Transformation.new, [], 0, {count: 0})
    masked = branch(root, Geom::Transformation.new, [], paths, {count: 0})
    external = groups.reject { |e| e == root }.map { |e| protected_node(c.inspect_instance(e, Geom::Transformation.new, [], 0, {count: 0})) }.sort_by { |n| n[:pid] }
    {paths: paths, masked_root: masked, required_deep_keep: required_keep,
     document_loose_sha: c.sha(loose), external: external,
     presentation_sha: c.sha(c.presentation(model)), model_path: model.path, model_guid: model.guid}
  end

  def validate_authorization!(policy, declared, model_path, root_pid)
    approved = policy['allowed_paths']
    paths!(approved)
    raise 'Host edit authorization is inactive' unless policy['status'] == 'active'
    raise 'Host edit authorization identity mismatch' unless policy['root_pid'] == root_pid &&
      File.expand_path(policy['model_path']) == File.expand_path(model_path)
    raise 'Declared scope exceeds exact HOST-approved paths; do not widen to an ancestor' unless
      declared.all? { |path| approved.include?(path) }
    true
  end

  def compare!(before, after, paths)
    paths!(paths)
    raise 'Path scope declaration changed' unless before[:paths] == paths && after[:paths] == paths
    raise 'Path scope regression: protected geometry/identity/presentation changed' unless before == after
    {'status' => 'passed', 'guard' => 'deep_exact_paths_v2', 'allowed_paths' => paths,
     'required_deep_keep_paths' => (before[:required_deep_keep] || []).map { |item| item[:path] },
     'allowed_top_level' => paths.map(&:first).uniq,
     'protected_deep_geometry_and_loose_entities' => true}
  end

  def verify!(root, before, paths)
    compare!(before, capture(root, paths), paths)
  end
end
