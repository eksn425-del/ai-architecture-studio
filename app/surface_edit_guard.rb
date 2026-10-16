# frozen_string_literal: true
# Host opt-in: surface finishes may change only listed face materials and
# listed curved-seam edge soft/smooth flags. Every primitive ID/vertex and all
# other geometry, materials, transforms and flags remain exact before commit.
require_relative 'native_deep_fingerprint'
module KStudioSurfaceEditGuard
  extend self
  CONTRACT = 'native_constrained_surface_edits_v1'
  MAX_ENTITIES = 100_000

  def ids!(values, maximum)
    raise 'Invalid surface primitive whitelist' unless values.is_a?(Array) && values.length <= maximum &&
      values.uniq.length == values.length && values.all? { |v| v.is_a?(Integer) && v > 0 }
    values
  end

  def vertex(v)
    {pid: v.persistent_id, point_mm: v.position.to_a.map(&:to_mm)}
  end

  def node(g, materials, seams, visited)
    c = KStudioNativeDeepFingerprint
    es = g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities
    records = es.map do |e|
      visited[:count] += 1
      raise 'Constrained surface capture exceeded complete entity cap' if visited[:count] > MAX_ENTITIES
      if e.is_a?(Sketchup::Face)
        visited[:faces] << e.persistent_id
        loops = e.loops.map do |l|
          points = l.vertices.map { |v| vertex(v) }
          {outer: l.outer?, vertices: points.each_index.map { |j| points.rotate(j) }.min_by { |p| JSON.generate(p) }}
        end
        {type: 'Face', pid: e.persistent_id, loops: loops.sort_by { |v| JSON.generate(v) }, normal: e.normal.to_a,
         front: materials.include?(e.persistent_id) ? :approved_material : c.material(e.material),
         back: materials.include?(e.persistent_id) ? :approved_material : c.material(e.back_material),
         hidden: e.hidden?, tag: c.tag(e)}
      elsif e.is_a?(Sketchup::Edge)
        visited[:edges] << e.persistent_id
        {type: 'Edge', pid: e.persistent_id, vertices: e.vertices.map { |v| vertex(v) }.sort_by { |v| v[:pid] },
         soft: seams.include?(e.persistent_id) ? :approved_seam : e.soft?,
         smooth: seams.include?(e.persistent_id) ? :approved_seam : e.smooth?, hidden: e.hidden?, tag: c.tag(e)}
      elsif e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)
        node(e, materials, seams, visited)
      else
        raise 'Unsupported entity in constrained surface target: ' + e.typename
      end
    end
    {type: g.typename, pid: g.persistent_id, name: g.name, definition_name: g.definition.name,
     transform: g.transformation.to_a, material: c.material(g.material), tag: c.tag(g), hidden: g.hidden?, locked: g.locked?,
     entities: records.sort_by { |v| [v[:type], v[:pid]] }}
  end

  def capture(root, policy)
    rule = policy['constrained_surface_edits']
    return nil unless rule
    raise 'Wrong surface-edit contract' unless rule['contract'] == CONTRACT
    paths = rule['paths']; KStudioPathScopeGuard.paths!(paths)
    raise 'Surface targets must be existing exact HOST-approved leaves' unless paths.all? { |p|
      policy['allowed_paths'].include?(p) && !policy.fetch('allowed_creation_paths', []).include?(p)
    }
    materials = ids!(rule.fetch('face_material_pids'), 1024)
    seams = ids!(rule.fetch('soft_smooth_edge_pids'), 4096)
    seen = {count: 0, faces: [], edges: []}
    shapes = paths.map { |p| {path: p, shape: node(KStudioProfessionalHelpers.named_owned_group(root, p), materials, seams, seen)} }
    raise 'Unknown or out-of-target surface face ID' unless (materials - seen[:faces]).empty?
    raise 'Unknown or out-of-target surface seam edge ID' unless (seams - seen[:edges]).empty?
    canonical = JSON.generate(shapes)
    {contract: CONTRACT, paths: paths, face_material_pids: materials, soft_smooth_edge_pids: seams,
     canonical_shape_json: canonical, shape_sha256: Digest::SHA256.hexdigest(canonical), captured_entities: seen[:count]}
  end
end
