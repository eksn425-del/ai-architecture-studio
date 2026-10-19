# frozen_string_literal: true
# Trusted HOST lifecycle only. Never exposed to the modeling Agent.
require 'json'
require 'digest'
require_relative 'native_definition_graph'
module KStudioCopyOwnership
  extend self
  DICT = 'sketchup_architect'
  def guard(model, plan)
    raise 'Active model path changed' unless File.expand_path(model.path) == File.expand_path(plan.fetch('target_path'))
    raise 'Active model GUID changed' unless model.guid == plan.fetch('expected_guid')
    raise 'Exit active edit context' unless model.active_path.nil?
  end
  def roots(model)
    model.entities.grep(Sketchup::Group).select { |e| e.get_attribute(DICT,'role') == 'project_root' }.map { |e|
      {'root_pid'=>e.persistent_id,'revision'=>e.get_attribute(DICT,'revision'),
       'project_id'=>e.get_attribute(DICT,'project_id'),'name'=>e.name}
    }.sort_by { |e| e['root_pid'] }
  end
  def fingerprint(model, ids)
    captures=ids.map { |pid| KStudioNativeDefinitionGraph.capture(model,root_pid:pid) }
    materials=model.materials.map { |mat|
      tex=mat.texture
      [mat.name,mat.color.to_a,mat.alpha,tex && [tex.filename,tex.width.to_f,tex.height.to_f,tex.image_width,tex.image_height]]
    }.sort_by { |entry| entry[0] }
    {'document'=>captures.first.fetch(:document_geometry_material_sha256),
     'roots'=>captures.map { |c| c.fetch(:root_geometry_material_sha256) },
     'hierarchy'=>Digest::SHA256.hexdigest(JSON.generate(captures.first.fetch(:definition_identities))),
     'presentation'=>captures.first.fetch(:presentation_sha256),
     'materials'=>Digest::SHA256.hexdigest(JSON.generate(materials))}
  end
  def inspect(model, plan)
    guard(model,plan)
    owned=roots(model)
    raise 'No owned project root' if owned.empty?
    {'roots'=>owned,'fingerprint'=>fingerprint(model,owned.map { |r| r.fetch('root_pid') }),
     'model_path'=>model.path,'model_guid'=>model.guid}
  end
  def migrate(model, plan)
    guard(model,plan)
    raise 'Source and target projects must differ' if plan.fetch('source_project_id') == plan.fetch('target_project_id')
    raise 'Original model migration is forbidden' if File.expand_path(model.path) == File.expand_path(plan.fetch('source_path'))
    expected=plan.fetch('roots')
    raise 'Owned root identity changed' unless roots(model) == expected
    raise 'Wrong source project identity' unless expected.all? { |r| r.fetch('project_id') == plan.fetch('source_project_id') }
    ids=expected.map { |r| r.fetch('root_pid') }
    before=fingerprint(model,ids)
    raise 'Model changed since preview' unless before == plan.fetch('fingerprint')
    raise 'Cannot preserve native copy' unless model.save_copy(plan.fetch('native_backup_path'))
    guard(model,plan)
    opened=false;committed=false
    begin
      model.start_operation('Adopt independent project copy ownership',true)
      opened=true
      expected.each do |r|
        root=model.find_entity_by_persistent_id(r.fetch('root_pid'))
        raise 'Missing owned root' unless root.is_a?(Sketchup::Group)
        raise 'Copy already adopted' if root.get_attribute(DICT,'copy_ownership_origin')
        root.set_attribute(DICT,'project_id',plan.fetch('target_project_id'))
        root.set_attribute(DICT,'copy_ownership_origin',JSON.generate({source_project_id:plan.fetch('source_project_id'),
          target_project_id:plan.fetch('target_project_id'),receipt_id:plan.fetch('receipt_id'),source_file_sha256:plan.fetch('source_sha256')}))
      end
      after=fingerprint(model,ids)
      raise 'Geometry, hierarchy, material or presentation changed' unless before == after
      model.commit_operation
      opened=false;committed=true
      raise 'Could not save migrated copy' unless model.save
      {'status'=>'saved','geometry_unchanged'=>true,'before'=>before,'after'=>after,
       'roots'=>roots(model),'model_path'=>model.path,'model_guid'=>model.guid,'receipt_id'=>plan.fetch('receipt_id')}
    rescue StandardError => error
      model.abort_operation if opened
      model.undo if committed
      rollback_ok=(roots(model)==expected && fingerprint(model,ids)==before)
      {'status'=>'failed','error'=>error.message,'rollback_verified'=>rollback_ok,
       'recovery_copy'=>plan.fetch('native_backup_path'),'receipt_id'=>plan.fetch('receipt_id')}
    end
  end
end
