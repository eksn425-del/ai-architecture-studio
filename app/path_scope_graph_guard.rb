# frozen_string_literal: true
# Host-only full definition graph fence; enabled by explicit host policy only.
require 'json'
require_relative 'native_definition_graph'
module KStudioPathScopeGraphGuard
  extend self
  CONTRACT = 'deep_exact_paths_graph_v1'

  def paths!(paths)
    KStudioPathScopeGuard.paths!(paths)
  end

  def placeholder(path)
    {target_path: path, approved_absent_leaf_creation: true}
  end

  def branch(instance, parent_world, path, paths, creations, phase, counter)
    c = KStudioNativeDeepFingerprint
    world = parent_world * instance.transformation
    if paths.include?(path)
      if creations.include?(path)
        raise 'Approved creation path already exists before operation' if phase == :before
        raise 'New target must be an unlocked unique nonempty group' unless instance.is_a?(Sketchup::Group) &&
          !instance.locked? && instance.definition.instances.length == 1 && instance.entities.length > 0
        return placeholder(path)
      end
      return {target_path: path, pid: instance.persistent_id, name: c.entity_name(instance), locked: instance.locked?}
    end
    unless paths.any? { |p| p.take(path.length) == path }
      return KStudioNativeDefinitionGraph.node(instance, parent_world, counter[:graph])
    end
    if creations.any? { |p| p.take(path.length) == path }
      raise 'Creation requires existing unlocked unique ancestors' if instance.locked? || instance.definition.instances.length != 1
    end
    items = instance.is_a?(Sketchup::Group) ? instance.entities : instance.definition.entities
    children = items.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    names = children.map { |e| c.entity_name(e) }
    raise 'Ambiguous path ancestor children' unless names.uniq.length == names.length
    pending = []
    paths.select { |p| p.take(path.length) == path && p.length > path.length }.each do |p|
      next if names.include?(p[path.length])
      if phase == :before && creations.include?(p) && p.length == path.length + 1
        pending << placeholder(p)
      else
        raise "Missing scope path #{p.join('/')}"
      end
    end
    loose = KStudioNativeDefinitionGraph.scan(items.reject { |e| children.include?(e) }, [], 0, counter[:graph])
    values = children.map { |e| [c.entity_name(e), branch(e, world, path + [c.entity_name(e)], paths, creations, phase, counter)] }
    pending.each { |v| values << [v[:target_path].last, v] }
    meta = KStudioPathScopeGuard.metadata(instance, world)
    meta[:local_transform] = KStudioNativeDefinitionGraph.matrix(instance.transformation)
    meta[:world_transform] = KStudioNativeDefinitionGraph.matrix(world)
    {metadata: meta, loose_sha: c.sha(loose), children: values.sort_by(&:first).map(&:last)}
  end

  def keep_node(root, path, graph)
    current = root
    parent_world = Geom::Transformation.new
    path.each do |name|
      parent_world *= current.transformation
      entities = current.is_a?(Sketchup::Group) ? current.entities : current.definition.entities
      matches = entities.select { |e| (e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)) && e.name == name }
      raise 'Mandatory graph KEEP path must be unambiguous and existing' unless matches.length == 1
      current = matches.first
    end
    {path: path, node: KStudioNativeDefinitionGraph.node(current, parent_world, graph)}
  end

  def capture(root, paths, policy, phase: :before)
    raise 'Invalid capture phase' unless [:before, :after].include?(phase)
    paths!(paths)
    KStudioPathScopeGuard.validate_authorization!(policy, paths, root.model.path, root.persistent_id)
    raise 'Wrong host scope contract' unless policy['scope_contract'] == CONTRACT
    approved = policy.fetch('allowed_creation_paths', [])
    paths!(approved) unless approved.empty?
    raise 'Creation approval must name exact HOST-approved leaves' unless approved.all? { |p| policy['allowed_paths'].include?(p) }
    creations = paths.select { |p| approved.include?(p) }
    model = root.model
    raise 'Exit active edit context' unless model.active_path.nil?
    c = KStudioNativeDeepFingerprint
    groups = model.entities.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    raise 'Root must be document owned group' unless groups.include?(root)
    graph = KStudioNativeDefinitionGraph.context
    keep_paths = policy.fetch('required_preserve_paths', [])
    paths!(keep_paths) unless keep_paths.empty?
    keeps = keep_paths.map { |p| keep_node(root, p, graph) }
    loose = KStudioNativeDefinitionGraph.scan(model.entities.reject { |e| groups.include?(e) }, [], 0, graph)
    external = groups.reject { |e| e == root }.map { |e| KStudioNativeDefinitionGraph.node(e, Geom::Transformation.new, graph) }.sort_by { |n| n[:pid] }
    masked = branch(root, Geom::Transformation.new, [], paths, creations, phase, {graph: graph})
    {contract: CONTRACT, paths: paths, creation_paths: creations, masked_root: masked,
     protected_definition_graph: {definitions: graph[:definitions], identities: KStudioNativeDefinitionGraph.sorted(graph[:identities])},
     required_deep_keep: keeps, document_loose_sha: c.sha(loose), external: external,
     presentation_sha: c.sha(c.presentation(model)), model_path: model.path, model_guid: model.guid}
  end

  def compare!(before, after, paths)
    paths!(paths)
    raise 'Path scope contract changed' unless before[:contract] == CONTRACT && after[:contract] == CONTRACT
    raise 'Path scope declaration changed' unless before[:paths] == paths && after[:paths] == paths &&
      before[:creation_paths].is_a?(Array) && before[:creation_paths] == after[:creation_paths]
    raise 'Protected geometry changed outside approved exact paths' unless before == after
    {'status' => 'passed', 'guard' => CONTRACT, 'allowed_paths' => paths,
     'allowed_creation_paths' => before[:creation_paths],
     'allowed_top_level' => paths.map(&:first).uniq,
     'required_deep_keep_paths' => before[:required_deep_keep].map { |v| v[:path] },
     'protected_deep_geometry_and_loose_entities' => true}
  end
end
