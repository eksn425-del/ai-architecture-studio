# frozen_string_literal: true
# Read-only factored native geometry. Every referenced definition is scanned
# once, while every instance and local transform remains in the Merkle graph.
# This is a DIFFERENT fingerprint contract from the expanded legacy collector.
require_relative 'native_deep_fingerprint'
module KStudioNativeDefinitionGraph
  extend self
  C = KStudioNativeDeepFingerprint
  SCHEME = 'KStudioNativeDefinitionGraph/1'
  MAX_UNIQUE_ENTITIES = 250_000
  MAX_DEPTH = 24

  def number(value)
    f = value.to_f
    raise 'Nonfinite native coordinate' unless f.finite?
    f.zero? ? 0.0 : f
  end

  def point(p)
    [p.x, p.y, p.z].map { |v| number(v * 25.4) }
  end

  def matrix(t)
    t.to_a.each_with_index.map { |v, i| number(i >= 12 && i <= 14 ? v * 25.4 : v) }
  end

  def loop_points(loop)
    points = loop.vertices.map { |v| point(v.position) }
    return points if points.empty?
    # Preserve winding and hole topology, ignoring only a cyclic start vertex.
    points.each_index.map { |i| points.rotate(i) }.min
  end

  def sorted(values)
    values.sort_by { |v| JSON.generate(v) }
  end

  def tick(ctx)
    ctx[:visited] += 1
    raise 'Definition graph exceeded unique-entity cap' if ctx[:visited] > MAX_UNIQUE_ENTITIES
  end

  def prototype(definition, stack, depth, ctx)
    key = definition.object_id
    raise 'Recursive component definition' if stack.include?(key)
    if ctx[:memo].key?(key)
      result = ctx[:memo][key]
      raise 'Definition graph exceeded depth cap' if depth + result[:depth] > MAX_DEPTH
      return result
    end
    raise 'Definition graph exceeded depth cap' if depth > MAX_DEPTH
    scanned = scan(definition.entities, stack + [key], depth, ctx)
    faces = scanned[:faces];edges = scanned[:edges];children = scanned[:nodes]
    counts = {faces: faces.length, edges: edges.length, instances: children.length}
    child_depth = 0
    children.each do |child|
      child[:counts].each { |name, value| counts[name] += value }
      child_depth = [child_depth, 1 + child[:definition_depth]].max
    end
    payload = {definition_name: definition.name.to_s, faces_local_mm: faces,
               edges_local_mm: edges, sections:scanned[:sections], instances: children.map { |n| n[:geometry] }}
    canonical = JSON.generate(payload)
    digest = Digest::SHA256.hexdigest(canonical)
    record = {canonical_payload_json: canonical, counts: counts, depth: child_depth}
    # Geometry deduplication never drops an instance: its full descriptor is
    # retained in its parent. Native identity is a separate compact table.
    if ctx[:definitions].key?(digest) && ctx[:definitions][digest] != record
      raise 'Ambiguous content-addressed native definition'
    end
    ctx[:definitions][digest] = record
    ctx[:identities] << {name:definition.name.to_s,definition_ref:digest,
                        child_instance_pids:children.map { |n| n[:pid] }}
    result = {sha: digest, counts: counts, depth: child_depth}
    ctx[:memo][key] = result
    result
  end

  def instance(entity, stack, depth, ctx)
    proto = prototype(entity.definition, stack, depth, ctx)
    geo = {type: entity.typename, name: C.entity_name(entity),
           definition_name: entity.definition.name.to_s, definition_ref: proto[:sha],
           local_transform: matrix(entity.transformation), material: C.material(entity.material),
           hidden: entity.hidden?, locked: entity.locked?, tag: C.tag(entity)}
    {pid: entity.persistent_id, name: geo[:name], geometry: geo,
     counts: proto[:counts], definition_depth: proto[:depth]}
  end

  def scan(entities, stack, depth, ctx)
    faces=[];edges=[];nodes=[];sections=[]
    entities.each do |e|
      tick(ctx)
      if e.is_a?(Sketchup::Face)
        faces << {loops: sorted(e.loops.map { |l| {outer: l.outer?, points: loop_points(l)} }),
                  normal: e.normal.to_a.map { |v| number(v) }, front: C.material(e.material),
                  back: C.material(e.back_material), hidden: e.hidden?, tag: C.tag(e)}
      elsif e.is_a?(Sketchup::Edge)
        edges << {endpoints: e.vertices.map { |v| point(v.position) }.sort,
                  hidden: e.hidden?, soft: e.soft?, smooth: e.smooth?, tag: C.tag(e)}
      elsif e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)
        nodes << instance(e, stack, depth + 1, ctx)
      elsif e.is_a?(Sketchup::SectionPlane)
        sections << {name:e.name.to_s, plane:e.get_plane.map { |v| number(v) }, active:e.active?, hidden:e.hidden?, tag:C.tag(e)}
      else
        raise "Unsupported native entity for complete definition graph: #{e.typename}"
      end
    end
    {faces:sorted(faces),edges:sorted(edges),sections:sorted(sections),nodes:nodes.sort_by { |n| [n[:name],C.sha(n[:geometry])] }}
  end

  def context
    {visited:0,memo:{},definitions:{},identities:[]}
  end

  def node(entity, parent_world, ctx)
    descriptor = instance(entity, [], 0, ctx)
    world = parent_world * entity.transformation
    canonical = JSON.generate({instance:descriptor[:geometry],world_transform:matrix(world)})
    {name:descriptor[:name],pid:descriptor[:pid],definition_name:entity.definition.name.to_s,
     definition_ref:descriptor[:geometry][:definition_ref],
     local_transform:matrix(entity.transformation),world_transform:matrix(world),
     counts:descriptor[:counts],
     canonical_geometry_json:canonical,geometry_material_sha256:Digest::SHA256.hexdigest(canonical)}
  end

  def capture(model, root_pid:)
    raise 'Native document must be saved and outside edit context' if model.path.to_s.empty? || !model.active_path.nil?
    roots=model.entities.select { |e| (e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance)) && e.persistent_id==root_pid }
    raise 'Owned document root must be unique' unless roots.length==1
    root=roots.first;ctx=context
    doc=scan(model.entities,[],0,ctx)
    top=node(root,Geom::Transformation.new,ctx)
    contents=root.is_a?(Sketchup::Group) ? root.entities : root.definition.entities
    groups=contents.select { |e| e.is_a?(Sketchup::Group)||e.is_a?(Sketchup::ComponentInstance) }.map { |e| node(e,root.transformation,ctx) }.sort_by { |n| n[:name] }
    raise 'Ambiguous direct owned names' unless groups.map { |n| n[:name] }.uniq.length==groups.length
    visible=C.presentation(model)
    document_canonical=JSON.generate({faces:doc[:faces],edges:doc[:edges],sections:doc[:sections],nodes:doc[:nodes].map { |n| n[:geometry] }})
    {schema_version:3,collector:SCHEME,model_path:model.path,model_guid:model.guid,root_pid:root_pid,
     root_name:root.name.to_s,counts:top[:counts],root_geometry_material_sha256:top[:geometry_material_sha256],
     root_instance:top,document_canonical_json:document_canonical,
     document_geometry_material_sha256:Digest::SHA256.hexdigest(document_canonical),
     groups:groups,presentation:visible,presentation_sha256:C.sha(visible),
     definitions:ctx[:definitions],definition_identities:sorted(ctx[:identities]),document_loose:{faces:doc[:faces],edges:doc[:edges],sections:doc[:sections]},
     document_instances:doc[:nodes].map { |n| {pid:n[:pid],geometry:n[:geometry]} },
     unique_entities_visited:ctx[:visited],definition_count:ctx[:definitions].length,
     complete_reference_graph:true,coordinate_contract:'Full finite native doubles in local mm plus every local transform; no world-instance expansion or count-only equality',
     evidence_status:'NATIVE_READ_ONLY_NOT_A_SAVE_OR_DELIVERY_PASS'}
  end
end
