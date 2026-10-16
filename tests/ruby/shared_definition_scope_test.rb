# frozen_string_literal: true
require_relative '../../app/shared_definition_scope'
paths = [['FACADE', 'BAY_1', 'GLASS'], ['FACADE', 'BAY_2', 'GLASS']]
rows = paths.map { |p| {root_pid: 20606, path: p, pid: 88, locked: false} }
KStudioSharedDefinitionScope.validate_occurrences!(rows, 20606, paths, paths)
[
  [rows, 20606, [paths.first], paths],
  [rows, 20606, paths, [paths.first]],
  [rows + [{root_pid: 999, path: paths.first, pid: 88, locked: false}], 20606, paths, paths],
  [[rows.first.merge(locked: true)], 20606, paths, paths],
  [[], 20606, paths, paths],
  [rows, 20606, [['FACADE']], paths]
].each do |args|
  begin
    KStudioSharedDefinitionScope.validate_occurrences!(*args)
  rescue RuntimeError
    next
  end
  raise 'Unapproved shared occurrence escaped'
end
puts 'Shared definition exact all-occurrence authorization: positive + six negative cases PASS'
