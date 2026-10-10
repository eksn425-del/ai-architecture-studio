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
