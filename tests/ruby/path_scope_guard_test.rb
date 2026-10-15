# frozen_string_literal: true
require_relative '../../app/path_scope_guard'
paths = [['RAMPS', 'RAMP_1'], ['RAMPS', 'RAMP_3']]
baseline = {paths: paths, masked_root: {metadata: {pid: 20606}, loose_sha: 'root-loose',
  children: [{target_path: paths[0], pid: 1}, {target_path: paths[1], pid: 3},
    {name: 'RAMP_2', geometry_material_sha256: 'deep-material-geometry', counts: {faces: 6}}]},
  document_loose_sha: 'doc-loose', external: [{pid: 900, geometry_material_sha256: 'other'}],
  presentation_sha: 'style', model_path: 'same.skp', model_guid: 'same-guid'}
raise 'No native scope receipt' unless KStudioPathScopeGuard.compare!(baseline, Marshal.load(Marshal.dump(baseline)), paths)['guard'] == 'deep_exact_paths_v1'
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
