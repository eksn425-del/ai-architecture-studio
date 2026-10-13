# frozen_string_literal: true
# K Studio owned-root deep fingerprint, READ ONLY against SketchUp geometry.
# This file is loaded by the HOST via a verified fixed eval script, not exposed
# as user-generated Ruby. Only JSON values are returned; the plugin never saves,
# opens, transforms, selects, creates, erases or writes a model/entity.
require 'json'
require 'digest'

module KStudioNativeDeepFingerprint
  extend self
  MM_PER_INCH = 25.4
  MAX_ENTITIES = 250_000
  MAX_DEPTH = 24

  def mm(value)
    (value.to_f * MM_PER_INCH * 100.0).round / 100.0
  end

  def num(value)
    (value.to_f * 1_000_000.0).round / 1_000_000.0
  end

  def point(point, transform)
    p = transform * point
    [mm(p.x), mm(p.y), mm(p.z)]
  end

  def matrix(transform)
    transform.to_a.each_with_index.map { |v, i| i >= 12 && i <= 14 ? mm(v) : num(v) }
  end

  def material(mat)
    return nil if mat.nil?
    color = mat.color
    {name: mat.name.to_s, rgba: [color.red, color.green, color.blue, num(mat.alpha)]}
  end

  def tag(entity)
    layer = entity.respond_to?(:layer) ? entity.layer : nil
    layer && {name: layer.name.to_s, visible: layer.visible?}
  end

  def sha(value)
    Digest::SHA256.hexdigest(JSON.generate(value))
  end

  def entity_name(entity)
    name = entity.name.to_s
    return name unless name.empty?
    definition = entity.respond_to?(:definition) ? entity.definition : nil
    label = definition && definition.name.to_s
    label && !label.empty? ? "__UNNAMED_DEFINITION__#{label}" : '__UNNAMED__'
  end

  def scan(entities, world, stack, depth, counter)
    raise 'Deep native fingerprint exceeded recursion limit' if depth > MAX_DEPTH
    faces = []
    edges = []
    nodes = []
    entities.each do |entity|
      counter[:count] += 1
      raise 'Deep native fingerprint exceeded entity cap' if counter[:count] > MAX_ENTITIES
      if entity.is_a?(Sketchup::Face)
        pts = entity.vertices.map { |v| point(v.position, world) }.sort
        normal = entity.normal.transform(world)
        faces << {
          vertices_world_mm: pts, normal: [num(normal.x), num(normal.y), num(normal.z)],
          front: material(entity.material), back: material(entity.back_material),
          hidden: entity.hidden?, tag: tag(entity)
        }
      elsif entity.is_a?(Sketchup::Edge)
        edges << {endpoints_world_mm: entity.vertices.map { |v| point(v.position, world) }.sort,
                  hidden: entity.hidden?, soft: entity.soft?, smooth: entity.smooth?, tag: tag(entity)}
      elsif entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
        nodes << inspect_instance(entity, world, stack, depth + 1, counter)
      end
    end
    faces.sort_by! { |x| JSON.generate(x) }
    edges.sort_by! { |x| JSON.generate(x) }
    nodes.sort_by! { |x| [x[:name], x[:geometry_material_sha256]] }
    {faces: faces, edges: edges, nodes: nodes}
  end

  def inspect_instance(instance, parent_world, stack, depth, counter)
    definition = instance.definition
    key = definition.object_id
    raise 'Recursive component definition encountered' if stack.include?(key)
    local = instance.transformation
    world = parent_world * local
    contents = instance.is_a?(Sketchup::Group) ? instance.entities : definition.entities
    scanned = scan(contents, world, stack + [key], depth, counter)
    children = scanned[:nodes]
    own_faces = scanned[:faces].length
    own_edges = scanned[:edges].length
    counts = {
      faces: own_faces + children.sum { |node| node[:counts][:faces] },
      edges: own_edges + children.sum { |node| node[:counts][:edges] },
      instances: children.length + children.sum { |node| node[:counts][:instances] }
    }
    payload = {
      name: entity_name(instance),
      local_transform: matrix(local), world_transform: matrix(world),
      definition_name: definition.name.to_s, material: material(instance.material),
      hidden: instance.hidden?, locked: instance.locked?, tag: tag(instance),
      faces: scanned[:faces], edges: scanned[:edges],
      children: children.map { |node| [node[:name], node[:geometry_material_sha256]] }
    }
    {
      name: entity_name(instance), pid: instance.persistent_id,
      definition_name: definition.name.to_s, definition_guid: definition.guid.to_s,
      local_transform: payload[:local_transform], world_transform: payload[:world_transform],
      hidden: instance.hidden?, tag: tag(instance), counts: counts,
      geometry_material_sha256: sha(payload),
      children: children.map { |node|
        node.slice(:name, :local_transform, :world_transform, :definition_name,
                   :hidden, :tag, :counts, :geometry_material_sha256)
      }
    }
  end

  def presentation(model)
    path = model.active_path
    page = model.pages.selected_page
    {
      active_path: path.nil? ? nil : path.map { |entity| entity_name(entity) },
      selected_page: page.nil? ? nil : page.name.to_s,
      tags: model.layers.map { |layer| [layer.name.to_s, layer.visible?] }.sort,
      section_planes: model.entities.grep(Sketchup::SectionPlane).map { |section|
        [section.name.to_s, section.active?, section.hidden?, tag(section)]
      }.sort_by { |entry| JSON.generate(entry) }
    }
  end

  def capture(model, root_pid:)
    raise 'Active model is not saved' if model.path.to_s.empty?
    raise 'Exit current group/component edit context first' unless model.active_path.nil?
    root = model.entities.find { |e|
      (e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance)) &&
        e.persistent_id == root_pid
    }
    raise 'Expected owned root not found at model top level' if root.nil?
    raise 'Owned root has no unique name' if root.name.to_s.empty?
    counter = {count: 0}
    base = Geom::Transformation.new
    groups = inspect_instance(root, base, [], 0, counter)
    direct = (root.is_a?(Sketchup::Group) ? root.entities : root.definition.entities)
      .select { |e| e.is_a?(Sketchup::Group) || e.is_a?(Sketchup::ComponentInstance) }
    # The established Python comparator indexes top-level named groups. The
    # traversals share one world frame, not merely parent-local bounding boxes.
    child_counter = {count: 0}
    nodes = direct.map { |e|
      inspect_instance(e, root.transformation, [root.definition.object_id], 1, child_counter)
    }.sort_by { |e| [e[:name], e[:geometry_material_sha256]] }
    names = nodes.map { |e| e[:name] }
    raise 'Ambiguous named direct groups; cannot establish stable comparison' if names.uniq.length != names.length
    visible = presentation(model)
    {
      schema_version: 2, collector: 'KStudioNativeDeepFingerprint/1',
      model_path: model.path, model_guid: model.guid, root_pid: root_pid,
      root_name: root.name, counts: groups[:counts],
      root_geometry_material_sha256: groups[:geometry_material_sha256],
      groups: nodes, presentation: visible, presentation_sha256: sha(visible),
      visited_entities: counter[:count] + child_counter[:count],
      evidence_status: 'NATIVE_READ_ONLY_NOT_A_SAVE_OR_DELIVERY_PASS'
    }
  end
end
