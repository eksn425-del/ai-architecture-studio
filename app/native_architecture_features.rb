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
end
