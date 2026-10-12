# frozen_string_literal: true
#
# Edit-scope fence inside the EXISTING guarded SketchUp transaction.
# It complements KEEP: declared targets may change; all other direct owned
# groups are protected. It cannot prove that an intended target looks better.
module KStudioEditScopeGuard
  MAX_DIRECT_CHILDREN = 600
  MAX_ALLOWED_TARGETS = 48

  def self.fingerprints(root)
    groups = root.entities.to_a.select do |e|
      e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)
    end
    raise 'Edit scope exceeds maximum direct groups' if groups.length > MAX_DIRECT_CHILDREN
    # Group#to_component may clear the instance name. Preserve unrelated hidden
    # prototypes by stable PID without allowing them to be editable targets.
    names = groups.map do |group|
      name = group.name
      if name == '' && group.is_a?(Sketchup::ComponentInstance) && group.hidden?
        "__PROTECTED_COMPONENT_PID_#{group.persistent_id}"
      else
        name
      end
    end
    raise 'Edit scope requires unambiguous named direct groups' if names.any? { |name| !name.is_a?(String) || name.empty? }
    raise 'Edit scope has duplicate direct group names' unless names.uniq.length == names.length
    result = {}
    groups.zip(names).each do |group, identity|
      items = group.is_a?(Sketchup::Group) ? group.entities : group.definition.entities
      count = items.count { |item| item.is_a?(Sketchup::Group) || item.is_a?(Sketchup::ComponentInstance) }
      result[identity] = {
        'pid' => group.persistent_id,
        'locked' => group.locked?,
        'children' => count,
        'bounds' => KStudioStultusBounds.bounds_mm(group.bounds),
        'hidden' => group.hidden?
      }
    end
    result
  end

  def self.require_bounded_changes!(before, after, allowed_names, tolerance_mm = 0.01)
    raise 'Edit scope baselines must be Hashes' unless before.is_a?(Hash) && after.is_a?(Hash)
    raise 'Edit scope targets must be a nonempty list' unless
      allowed_names.is_a?(Array) && !allowed_names.empty? && allowed_names.length <= MAX_ALLOWED_TARGETS
    raise 'Edit scope target names must be unique' unless allowed_names.uniq.length == allowed_names.length
    allowed_names.each do |name|
      raise 'Edit scope target name is invalid' unless name.is_a?(String) && !name.empty?
      raise 'Anonymous prototype identities are protected, not editable targets' if name.start_with?('__PROTECTED_COMPONENT_PID_')
    end
    protected = before.keys - allowed_names
    protected.each do |name|
      prior = before[name]
      current = after[name]
      raise "Edit scope regression: protected #{name} was removed" if current.nil?
      %w[pid locked children hidden].each do |field|
        raise "Edit scope regression: protected #{name} #{field} changed" unless
          prior[field] == current[field]
      end
      %w[min max].each do |edge|
        a = prior['bounds'][edge.to_sym] || prior['bounds'][edge]
        b = current['bounds'][edge.to_sym] || current['bounds'][edge]
        raise "Edit scope regression: protected #{name} #{edge} missing" unless
          a.is_a?(Array) && b.is_a?(Array) && a.length == 3 && b.length == 3
        a.zip(b).each do |x, y|
          raise "Edit scope regression: protected #{name} bounds changed" unless
            x.is_a?(Numeric) && y.is_a?(Numeric) && (x - y).abs <= tolerance_mm
        end
      end
    end
    (after.keys - before.keys - allowed_names).each do |name|
      raise "Edit scope regression: undeclared new group #{name}"
    end
    {
      'status' => 'passed',
      'allowed_top_level' => allowed_names,
      'protected_top_level_count' => protected.length,
      'unchanged_protected_groups' => protected
    }
  end

  def self.verify!(root, before, allowed_names)
    require_bounded_changes!(before, fingerprints(root), allowed_names)
  end
end
