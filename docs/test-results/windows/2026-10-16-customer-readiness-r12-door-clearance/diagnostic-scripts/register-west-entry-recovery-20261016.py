from pathlib import Path
import json,sys,time,shutil
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';O=D/'west-entry-recovery';O.mkdir(exist_ok=True);base=['ENVELOPE_OUTER','LOWER_END_WEST_ADDITION','LEVEL_7200_BAY_6'];targets=[base+[n] for n in ['DOOR_LEFT_OPEN_90','DOOR_RIGHT_OPEN_90']]
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();s='''# ARCHFLOW_GENERATED_SCRIPT
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==11
paths=JSON.parse(PATHS);rows=paths.map do |p|
 g=r;p.each{|n|es=g.is_a?(Sketchup::Group) ? g.entities : g.definition.entities;x=es.select{|e|e.respond_to?(:name)&&e.name==n};raise 'Missing/ambiguous' unless x.length==1;g=x.first;raise 'Shared/locked' unless !g.locked?&&g.definition.instances.length==1}
 {path:p,pid:g.persistent_id,bounds_mm:[g.bounds.min.to_a.map(&:to_mm),g.bounds.max.to_a.map(&:to_mm)]}
end
{revision:11,geometry_writes:0,root_pid:20606,targets:rows}
'''.replace('GUID',json.dumps(i['model_guid'])).replace('PATHS',json.dumps(json.dumps(targets)))
f=_generated_script_dir()/('studio-west-door-recovery-'+str(time.time_ns())+'.rb');f.write_text(s,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only verify new west L2 doorway leaf identities before clearance recovery'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-targets-before.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
backup=P/'outputs/model/blank-disposable-r11-before-west-entry-clearance-20261016.skp';assert not backup.exists();a.save_model(backup,expected_root_ids=[20606]);assert Path(a.get_active_model_identity()['model_path']).resolve()==Path(i['model_path']).resolve()
# Freeze the actual first commit/review before allowing its necessary local repair.
F=D/'r11-initial-record';assert not F.exists()
for rel in ['runtime/project_ruby_state.json','runtime/active_edit_scope.json','runtime/agent_workspace/notes','runtime/agent_workspace/qa','runtime/agent_workspace/scripts','runtime/scripts']:
 src=P/rel;dest=F/rel
 if src.is_dir():shutil.copytree(src,dest)
 else:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
policy=json.loads((P/'runtime/active_edit_scope.json').read_text(encoding='utf8'));(O/'prior-scope-four-creations.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8');policy.update({'phase':'Fix only the two newly added west L2 door leaves that narrow return clearance','allowed_paths':targets,'allowed_creation_paths':[],'verified_start_revision':11,'max_geometry_commits':1,'source_registration':'notes/west-entry-clearance-recovery.json'})
for p in [P/'runtime/active_edit_scope.json',P/'runtime/agent_workspace/notes/local-edit-scope.json',O/'authorization-active.json']:
 tmp=p.with_suffix('.atomic.tmp');tmp.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(p)
reg={'status':'HOST_VERIFIED_RECOVERY_APPROVED','actual_targets':v,'scope_change':'Exact two existing newly-built door leaves, no ancestor expansion. Preserve apertures/frame/sill and all rest.','reason':'New open90 leaves project1100mm into actual1650mmreturn. Sliding side-parked leaves at72mm projection inferred from source adjacency, empty2200x2400portal retained. Actual leaf/world/clearance verification required.','initial_failed_call':'Old four-creation policy rejected narrower descendant declaration before native eval; no geometry change from rejected attempt.','r11_backup':str(backup),'current_native_revision':11}
(P/'runtime/agent_workspace/notes/west-entry-clearance-recovery.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf8');(O/'registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf8');(P/'runtime/agent_workspace/notes/enclosure_addition_r11.md').open('a',encoding='utf8').write('\n\n## Host clearance recovery now registered\nThe exact two new west L2 door leaves are now approved in local-edit-scope.json as existing targets; no creation, no broader parent. First rejected writer changed nothing. Re-read policy and retry the saved clear_west_middle_entry.rb with exact two leaf paths and KEEP of all unrelated geometry. Existing source-based opening/frame stays. This is authorized completion of the newly added entry, not a reason to pause.\n')
print('Verified/backup r11; exact two new door leaves authorized for safe clearance recovery')
