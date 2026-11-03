# frozen_string_literal: true
# Offline contract fixture. No SketchUp process/model or geometry API is used.
require_relative '../../app/path_scope_guard'
module Geom
  class Transformation
    def *(_other); self; end
    def to_a; [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; end
  end
end
module Sketchup
  class Group
    attr_accessor :name, :entities, :persistent_id, :model, :locked, :definition
    def initialize(name, pid, entities = [])
      @name, @persistent_id, @entities = name, pid, entities
      @locked = false
      @definition = Struct.new(:instances).new([self])
    end
    def transformation; Geom::Transformation.new; end
    def locked?; @locked; end
    def hidden?; false; end
    def material; nil; end
  end
  class ComponentInstance < Group; end
end
# Substitute only the SketchUp-dependent collectors, retaining the actual
# capture/creation/authorization/branch/compare implementation under test.
module KStudioNativeDefinitionGraph
  def context; {definitions: [], identities: []}; end
  def scan(items, *_args); items.map { |v| v.is_a?(Sketchup::Group) ? node(v, nil, nil) : v }; end
  def node(v, *_args); {pid: v.persistent_id, name: v.name, contents: scan(v.entities)}; end
  def capture(*_args); {}; end
end
module KStudioNativeDeepFingerprint
  def scan(items, *_args); KStudioNativeDefinitionGraph.scan(items); end
  def inspect_instance(v, *_args); KStudioNativeDefinitionGraph.node(v); end
  def presentation(_model); 'unchanged style'; end
end

def rejected(label)
  begin
    yield
  rescue RuntimeError
    return
  end
  raise "Not rejected: #{label}"
end

def fixture
  roof = Sketchup::Group.new('ROOF', 2, ['roof solid'])
  root = Sketchup::Group.new('BUILDING', 19, [roof, 'root loose'])
  model = Struct.new(:path, :guid, :entities, :active_path).new('/fixture/outputs/model/blank.skp', 'guid', [root, 'document loose'], nil)
  root.model = model
  [root, roof, model]
end

paths = [['RESIDENTIAL_MODULES']]
root, roof, model = fixture
before = KStudioPathScopeGuard.capture(root, paths)
raise 'Not graph guarded' unless before[:contract] == 'deep_exact_paths_graph_v1'
raise 'Missing exact creation' unless before[:creation_paths] == paths
rejected('declared creation not actually made') { KStudioPathScopeGuard.verify!(root, before, paths) }
new_group = Sketchup::Group.new('RESIDENTIAL_MODULES', 3, ['new floor solid'])
root.entities << new_group
receipt = KStudioPathScopeGuard.verify!(root, before, paths)
raise 'No creation receipt' unless receipt['allowed_creation_paths'] == paths
roof.entities << 'changed roof'
rejected('protected roof changed') { KStudioPathScopeGuard.verify!(root, before, paths) }
roof.entities.pop
root.entities << Sketchup::Group.new('UNDECLARED', 4, ['other'])
rejected('undeclared group') { KStudioPathScopeGuard.verify!(root, before, paths) }
root.entities.pop
root.entities << 'new root face'
rejected('root loose geometry') { KStudioPathScopeGuard.verify!(root, before, paths) }
root.entities.pop
model.entities << 'new document face'
rejected('document loose geometry') { KStudioPathScopeGuard.verify!(root, before, paths) }
model.entities.pop
new_group.entities.clear
rejected('empty new target') { KStudioPathScopeGuard.verify!(root, before, paths) }
new_group.entities << 'new floor solid'
new_group.locked = true
rejected('locked new target') { KStudioPathScopeGuard.verify!(root, before, paths) }
new_group.locked = false
new_group.definition.instances << Object.new
rejected('shared new target') { KStudioPathScopeGuard.verify!(root, before, paths) }

root, roof, model = fixture
rejected('missing intermediate ancestor') { KStudioPathScopeGuard.capture(root, [['MISSING', 'LEAF']]) }
root.locked = true
rejected('locked creation ancestor') { KStudioPathScopeGuard.capture(root, paths) }
root.locked = false
root.definition.instances << Object.new
rejected('shared creation ancestor') { KStudioPathScopeGuard.capture(root, paths) }
root.definition.instances.pop
root.entities << Sketchup::Group.new('ROOF', 55, ['duplicate'])
rejected('ambiguous ancestor children') { KStudioPathScopeGuard.capture(root, paths) }

# Existing narrower host policy is not broadened by the new default path.
policy = {'status' => 'active', 'model_path' => model.path, 'root_pid' => 19,
  'allowed_paths' => [['ROOF']], 'scope_contract' => KStudioPathScopeGraphGuard::CONTRACT}
rejected('scope expansion under host policy') { KStudioPathScopeGuard.validate_authorization!(policy, paths, model.path, 19) }

root, roof, model = fixture
host_policy_path = '/fixture/runtime/active_edit_scope.json'
class << File
  alias_method :creation_test_original_file?, :file?
  alias_method :creation_test_original_read, :read
end
File.define_singleton_method(:file?) { |path| path == host_policy_path || creation_test_original_file?(path) }
File.define_singleton_method(:read) { |path, **options|
  path == host_policy_path ? JSON.generate(policy) : creation_test_original_read(path, **options)
}
rejected('narrower policy through real capture dispatch') { KStudioPathScopeGuard.capture(root, paths) }
class << File
  alias_method :file?, :creation_test_original_file?
  alias_method :read, :creation_test_original_read
end

# An existing declared target must retain its container identity.
root, roof, model = fixture
existing = KStudioPathScopeGuard.capture(root, [['ROOF']])
roof.persistent_id = 999
rejected('replacement of existing target') { KStudioPathScopeGuard.verify!(root, existing, [['ROOF']]) }
puts 'PASS: exact absent leaf creation + 15 negative scope checks (offline collector fixture)'
