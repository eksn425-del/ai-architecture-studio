# frozen_string_literal: true
# Host opt-in only. A prototype may change only when EVERY physical document
# occurrence is explicitly authorized; no ancestor widening or uniqueness guess.
module KStudioSharedDefinitionScope
  extend self
  MAX_DEFINITIONS = 250_000
  MAX_OCCURRENCES = 50_000
  MAX_DEPTH = 24

  def validate_occurrences!(rows, root_pid, declared, approved_shared)
    raise 'Shared definition has no proven document occurrences' if rows.empty?
    rows.each do |row|
      raise 'Shared definition occurs outside owned root' unless row[:root_pid] == root_pid
      raise 'Shared definition has locked occurrence/ancestor' if row[:locked]
      raise 'Shared definition occurrence lacks exact approval: ' + row[:path].join('/') unless
        declared.include?(row[:path]) && approved_shared.include?(row[:path])
    end
    rows
  end

  def entities(instance)
    instance.is_a?(Sketchup::Group) ? instance.entities : instance.definition.entities
  end

  def instances(items)
    items.select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
  end

  def contains_target?(definition, target, memo, stack = [])
    return true if definition == target
    key = definition.object_id
    raise 'Recursive or too deep shared-definition graph' if stack.include?(key) || stack.length > MAX_DEPTH
    return memo[key] if memo.key?(key)
    raise 'Shared-definition traversal exceeded complete definition cap' if memo.length >= MAX_DEFINITIONS
    memo[key] = instances(definition.entities).any? do |child|
      contains_target?(child.definition, target, memo, stack + [key])
    end
  end

  def walk(instance, target, root_pid, path, locked, memo, rows, depth = 0)
    raise 'Shared occurrence traversal too deep' if depth > MAX_DEPTH
    return unless contains_target?(instance.definition, target, memo)
    locked ||= instance.locked?
    if instance.definition == target
      raise 'Shared occurrence traversal exceeded cap' if rows.length >= MAX_OCCURRENCES
      rows << {root_pid: root_pid, path: path, pid: instance.persistent_id, locked: locked}
      return
    end
    children = instances(entities(instance))
    names = children.map(&:name)
    raise 'Ambiguous shared-definition occurrence path' unless names.uniq.length == names.length
    children.each do |child|
      walk(child, target, root_pid, path + [child.name], locked, memo, rows, depth + 1)
    end
  end

  def prove!(root, leaf, declared, approved_shared)
    rows = []; memo = {}
    instances(root.model.entities).each do |document_root|
      walk(document_root, leaf.definition, document_root.persistent_id, [], false, memo, rows)
    end
    validate_occurrences!(rows, root.persistent_id, declared, approved_shared)
    {contract: 'all_document_definition_occurrences_v1', target_definition: leaf.definition.name,
     occurrences: rows.sort_by { |r| [r[:root_pid], r[:path].join('/')] }}
  end
end
