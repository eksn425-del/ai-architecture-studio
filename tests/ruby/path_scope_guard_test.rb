# frozen_string_literal: true
require_relative '../../app/path_scope_guard'
paths = [['RAMPS', 'RAMP_1'], ['RAMPS', 'RAMP_3']]
baseline = {paths: paths, masked_root: {metadata: {pid: 20606}, loose_sha: 'root-loose',
  children: [{target_path: paths[0], pid: 1}, {target_path: paths[1], pid: 3},
    {name: 'RAMP_2', geometry_material_sha256: 'deep-material-geometry', counts: {faces: 6}}]},
  document_loose_sha: 'doc-loose', external: [{pid: 900, geometry_material_sha256: 'other'}],
  presentation_sha: 'style', model_path: 'same.skp', model_guid: 'same-guid'}
raise 'No native scope receipt' unless KStudioPathScopeGuard.compare!(baseline, Marshal.load(Marshal.dump(baseline)), paths)['guard'] == 'deep_exact_paths_v2'
cases = [
  ->(x) { x[:masked_root][:children][2][:geometry_material_sha256] = 'same-bounds-changed-material-or-vertex' },
  ->(x) { x[:masked_root][:metadata][:pid] = 999 },
  ->(x) { x[:masked_root][:loose_sha] = 'new-root-face' },
  ->(x) { x[:masked_root][:children][0][:pid] = 888 },
  ->(x) { x[:masked_root][:children] << {name: 'undeclared'} },
  ->(x) { x[:document_loose_sha] = 'new-doc-edge' },
  ->(x) { x[:external][0][:geometry_material_sha256] = 'changed-external' },
  ->(x) { x[:presentation_sha] = 'changed-style' },
  ->(x) { x[:model_guid] = 'another-model' }
]
cases.each do |change|
  changed = Marshal.load(Marshal.dump(baseline)); change.call(changed)
  begin
    KStudioPathScopeGuard.compare!(baseline, changed, paths)
  rescue RuntimeError => error
    raise unless error.message.include?('Path scope regression')
    next
  end
  raise 'Protected mutation escaped path guard'
end
[[['RAMPS'], ['RAMPS', 'RAMP_1']], [paths[0], paths[0]], [['']]].each do |bad|
  begin
    KStudioPathScopeGuard.paths!(bad)
  rescue RuntimeError
    next
  end
  raise 'Invalid or broad overlapping scope accepted'
end
puts 'deep exact-path guard contract: positive + 12 negative cases PASS'

policy = {'status' => 'active', 'model_path' => 'same.skp', 'root_pid' => 20606, 'allowed_paths' => paths}
KStudioPathScopeGuard.validate_authorization!(policy, [paths[0]], 'same.skp', 20606)
[
  [policy, [['RAMPS']], 'same.skp', 20606],
  [policy, [['RAMPS', 'RAMP_2']], 'same.skp', 20606],
  [policy.merge('status' => 'closed'), paths, 'same.skp', 20606],
  [policy, paths, 'other.skp', 20606],
  [policy, paths, 'same.skp', 999]
].each do |args|
  begin
    KStudioPathScopeGuard.validate_authorization!(*args)
  rescue RuntimeError
    next
  end
  raise 'Host authorization boundary escaped'
end
puts 'host-approved exact path scope: positive + 5 negatives PASS'

original = {pid: 1, definition_guid: 'old', definition_instances: 2,
  geometry_material_sha256: 'actual-geometry', children: [{pid: 2, definition_instances: 2}]}
unique = Marshal.load(Marshal.dump(original)); unique[:definition_guid] = 'new'; unique[:definition_instances] = 1
unique[:children][0][:definition_instances] = 1
raise 'Definition bookkeeping blocked safe uniqueness' unless KStudioPathScopeGuard.protected_node(original) == KStudioPathScopeGuard.protected_node(unique)
unique[:geometry_material_sha256] = 'illegal-shared-geometry-change'
raise 'Shared geometry escaped normalization' if KStudioPathScopeGuard.protected_node(original) == KStudioPathScopeGuard.protected_node(unique)
puts 'shared definition normalization: bookkeeping-only PASS; geometry still protected'
