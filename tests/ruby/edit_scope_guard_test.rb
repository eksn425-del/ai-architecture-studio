# frozen_string_literal: true
require_relative '../../app/edit_scope_guard'

def group(pid, children = 1, low = [0, 0, 0], high = [10, 10, 10])
  {'pid' => pid, 'locked' => false, 'children' => children,
   'bounds' => {'min' => low, 'max' => high}}
end

original = {'FRONT_GLAZING' => group(101), 'RIGHT_WOOD_CLADDING' => group(102, 20),
            'ROOF_GLASS' => group(103, 25)}
good = Marshal.load(Marshal.dump(original))
good['FRONT_GLAZING'] = group(109, 2)
receipt = KStudioEditScopeGuard.require_bounded_changes!(original, good, ['FRONT_GLAZING'])
raise 'Not an actual guard pass' unless receipt['status'] == 'passed' &&
                                        receipt['protected_top_level_count'] == 2

def expect_scope_abort(original, changed, allowed)
  begin
    KStudioEditScopeGuard.require_bounded_changes!(original, changed, allowed)
  rescue RuntimeError => error
    raise 'Wrong failure' unless error.message.include?('Edit scope regression')
    return
  end
  raise 'Unexpected edit escaped precommit scope verification'
end

changed_wood = Marshal.load(Marshal.dump(good))
changed_wood['RIGHT_WOOD_CLADDING']['children'] = 3
expect_scope_abort(original, changed_wood, ['FRONT_GLAZING'])

changed_roof = Marshal.load(Marshal.dump(good))
changed_roof['ROOF_GLASS']['bounds']['max'][2] = 100
expect_scope_abort(original, changed_roof, ['FRONT_GLAZING'])

added_obstruction = Marshal.load(Marshal.dump(good))
added_obstruction['NEW_OBSTRUCTION'] = group(200)
expect_scope_abort(original, added_obstruction, ['FRONT_GLAZING'])

puts 'K AI Studio precommit edit-scope guard contract PASS'

# Reproduce Group#to_component's empty instance name without native geometry.
module Sketchup
  class Group; end unless const_defined?(:Group)
  class ComponentInstance; end unless const_defined?(:ComponentInstance)
end
module KStudioStultusBounds
  def self.bounds_mm(value); value; end
end
PrototypeStub = Struct.new(:name, :persistent_id, :hidden, :locked, :definition, :bounds) do
  def is_a?(klass); klass == Sketchup::ComponentInstance || super; end
  def hidden?; hidden; end
  def locked?; locked; end
end
RootStub = Struct.new(:entities)
DefinitionStub = Struct.new(:entities)
prototype = PrototypeStub.new('', 77, true, false, DefinitionStub.new([]), {'min'=>[0,0,0], 'max'=>[1,1,1]})
baseline = KStudioEditScopeGuard.fingerprints(RootStub.new([prototype]))
raise 'Missing protected anonymous prototype' unless baseline.key?('__PROTECTED_COMPONENT_PID_77')
current = Marshal.load(Marshal.dump(baseline))
current['SCREEN_FRONT'] = group(88)
KStudioEditScopeGuard.require_bounded_changes!(baseline, current, ['SCREEN_FRONT'])
lost = {'SCREEN_FRONT'=>group(88)}
expect_scope_abort(baseline, lost, ['SCREEN_FRONT'])
visible = Marshal.load(Marshal.dump(current))
visible['__PROTECTED_COMPONENT_PID_77']['hidden'] = false
expect_scope_abort(baseline, visible, ['SCREEN_FRONT'])
begin
  KStudioEditScopeGuard.require_bounded_changes!(baseline, current, ['__PROTECTED_COMPONENT_PID_77'])
  raise 'Reserved prototype identity was editable'
rescue RuntimeError => error
  raise unless error.message.include?('protected, not editable')
end
prototype.hidden = false
begin
  KStudioEditScopeGuard.fingerprints(RootStub.new([prototype]))
  raise 'Visible anonymous geometry escaped naming requirement'
rescue RuntimeError => error
  raise unless error.message.include?('unambiguous named')
end
puts 'Hidden unnamed prototype stays protected; visible unnamed geometry still blocked PASS'
