# frozen_string_literal: true
# Host-only precommit fence. Reuses the native deep geometry collector, masking
# ONLY exact declared subtree paths; ancestor geometry and siblings stay fixed.
require_relative 'native_deep_fingerprint'
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

  def branch(instance, parent_world, path, paths, counter)
    c = KStudioNativeDeepFingerprint
    world = parent_world * instance.transformation
    if paths.include?(path)
      # Replacing a declared existing group still loses its stable identity.
      raise 'Shared definition cannot be an editable path target' if instance.definition.instances.length != 1
      return {target_path: path, pid: instance.persistent_id, name: c.entity_name(instance), locked: instance.locked?}
    end
    unless paths.any? { |p| p.take(path.length) == path }
      return c.inspect_instance(instance, parent_world, [], path.length, counter)
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
    raise 'Exit edit context before path scope capture' unless model.active_path.nil?
    c = KStudioNativeDeepFingerprint
    groups = model.entities.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    raise 'Owned root must be at document top level' unless groups.include?(root)
    loose = c.scan(model.entities.reject { |e| groups.include?(e) }, Geom::Transformation.new, [], 0, {count: 0})
    masked = branch(root, Geom::Transformation.new, [], paths, {count: 0})
    external = groups.reject { |e| e == root }.map { |e| c.inspect_instance(e, Geom::Transformation.new, [], 0, {count: 0}) }.sort_by { |n| n[:pid] }
    {paths: paths, masked_root: masked, document_loose_sha: c.sha(loose), external: external,
     presentation_sha: c.sha(c.presentation(model)), model_path: model.path, model_guid: model.guid}
  end

  def compare!(before, after, paths)
    paths!(paths)
    raise 'Path scope declaration changed' unless before[:paths] == paths && after[:paths] == paths
    raise 'Path scope regression: protected geometry/identity/presentation changed' unless before == after
    {'status' => 'passed', 'guard' => 'deep_exact_paths_v1', 'allowed_paths' => paths,
     'allowed_top_level' => paths.map(&:first).uniq,
     'protected_deep_geometry_and_loose_entities' => true}
  end

  def verify!(root, before, paths)
    compare!(before, capture(root, paths), paths)
  end
end
