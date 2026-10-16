# frozen_string_literal: true
require_relative '../../app/path_scope_guard'
root = Struct.new(:model, :persistent_id).new(:test_document, 20606)
original = KStudioNativeDefinitionGraph.method(:capture)
calls = []
begin
  KStudioNativeDefinitionGraph.define_singleton_method(:capture) do |model, root_pid:|
    calls << [model, root_pid]
    {complete_reference_graph: true}
  end
  KStudioPathScopeGraphGuard.validate_complete_document!(root, :before)
  raise 'Unnecessary before traversal' unless calls.empty?
  KStudioPathScopeGraphGuard.validate_complete_document!(root, :after)
  raise 'Missing complete edited-document check' unless calls == [[:test_document, 20606]]
  KStudioNativeDefinitionGraph.define_singleton_method(:capture) do |*args, **kwargs|
    raise 'Definition graph exceeded unique-entity cap'
  end
  begin
    KStudioPathScopeGraphGuard.validate_complete_document!(root, :after)
    raise 'Invalid native delivery escaped precommit'
  rescue RuntimeError => error
    raise unless error.message.include?('complete native delivery preflight') && error.message.include?('reuse geometry definitions')
  end
ensure
  KStudioNativeDefinitionGraph.define_singleton_method(:capture, original)
end
puts 'Complete native precommit: before skip, after full validation, unchanged collector failure propagated PASS'
