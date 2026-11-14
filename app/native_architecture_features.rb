# frozen_string_literal: true
# Fixed HOST read-only audit. No geometry operations, camera edits, or saves.
require_relative 'native_deep_fingerprint'
module KStudioNativeArchitectureFeatures
  extend self
  def walk(entities, world, inherited, path, rows, counter, depth)
    raise 'Feature depth limit' if depth > 24
    entities.each do |e|
      counter[0] += 1
      raise 'Feature entity limit' if counter[0] > 250_000
      if e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)
        walk(e.definition.entities, world * e.transformation, e.material || inherited,
             path + [KStudioNativeDeepFingerprint.entity_name(e)], rows, counter, depth + 1)
      elsif e.is_a?(Sketchup::Face)
        mesh = e.mesh(0)
        triangles = mesh.polygons.map { |poly|
          poly.map { |i| KStudioNativeDeepFingerprint.point(mesh.point_at(i.abs), world) }
        }
        rows << {path: path, pid: e.persistent_id, triangles_mm: triangles,
                 front: KStudioNativeDeepFingerprint.material(e.material || inherited),
                 back: KStudioNativeDeepFingerprint.material(e.back_material || inherited),
                 hidden: e.hidden?, visible_edges: e.edges.count { |edge| !edge.hidden? && !edge.soft? }}
      end
    end
  end
  def capture(model, root_pid:)
    deep = KStudioNativeDeepFingerprint.capture(model, root_pid: root_pid)
    root = model.find_entity_by_persistent_id(root_pid)
    rows = []
    walk(root.definition.entities, root.transformation, root.material, [], rows, [0], 0)
    options = {}
    %w[RenderMode DrawEdges DrawProfiles EdgeDisplayMode DrawSilhouettes ModelTransparency].each do |key|
      options[key] = model.rendering_options[key] rescue nil
    end
    deep.merge(collector: 'KStudioNativeArchitectureFeatures/1', faces: rows,
               rendering_options: options, quality_verdict: 'NOT_ASSESSED')
  end

  # Bounded, fixed host query against two explicit named subtrees. Reuse the
  # native triangulated world-space feature representation used for deep QA.
  def joint_triangles(root, path, axis, position, span, tolerance)
    world = Geom::Transformation.new
    ancestry = (0..path.length).map { |depth| KStudioProfessionalHelpers.named_owned_group(root, path.take(depth)) }
    ancestry.each do |group|
      return [] if group.hidden? || !group.layer.visible?
      world *= group.transformation
    end
    section_triangles(ancestry.last.definition.entities, world, axis, position, span, tolerance, [0], 0)
  end

  def section_triangles(entities, world, axis, position, span, tolerance, counter, depth)
    raise 'Level joint exceeded native traversal depth' if depth > 24
    across = 1 - axis
    entities.each_with_object([]) do |entity, rows|
      counter[0] += 1
      raise 'Level joint exceeded native entity cap; select narrower part paths' if counter[0] > 50_000
      if entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
        next if entity.hidden? || !entity.layer.visible?
        rows.concat(section_triangles(entity.definition.entities, world * entity.transformation,
                                      axis, position, span, tolerance, counter, depth + 1))
      elsif entity.is_a?(Sketchup::Face)
        next if entity.hidden? || !entity.layer.visible?
        vertices = entity.vertices.map { |v| KStudioNativeDeepFingerprint.point(v.position, world) }
        z_min, z_max = vertices.map { |p| p[2] }.minmax
        near_min, near_max = vertices.map { |p| p[axis] }.minmax
        lo, hi = vertices.map { |p| p[across] }.minmax
        next if z_max - z_min > tolerance || position < near_min - tolerance || position > near_max + tolerance
        next if lo > span[1] || hi < span[0]
        mesh = entity.mesh(0)
        mesh.polygons.each do |poly|
          rows << poly.map { |i| KStudioNativeDeepFingerprint.point(mesh.point_at(i.abs), world) }
        end
      end
      raise 'Level joint exceeded native face cap; select narrower part paths' if rows.size > 8_192
    end
  end
end
