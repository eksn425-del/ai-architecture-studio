# ARCHFLOW_GENERATED_SCRIPT
load "E:/K AI 产品建模网站/app/adopted_sketchup_helpers.rb"
load "E:/K AI 产品建模网站/app/surface_edit_guard.rb"
load "E:/K AI 产品建模网站/app/path_scope_graph_guard.rb"
load "E:/K AI 产品建模网站/app/path_scope_guard.rb"
m=Sketchup.active_model;raise 'Wrong safe copy' unless File.expand_path(m.path)==File.expand_path("E:\\K AI 产品建模网站\\runtime\\projects\\architecture-project-4f0e4\\outputs\\model\\blank-disposable-r18-surface-guard2-20261016.skp")
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==18
policy=JSON.parse("{\"status\": \"active\", \"phase\": \"Source4 interior ceiling members/finishes and slender supported spiral shafts\", \"model_path\": \"E:\\\\K AI 产品建模网站\\\\runtime\\\\projects\\\\architecture-project-4f0e4\\\\outputs\\\\model\\\\blank-disposable-r18-surface-guard2-20261016.skp\", \"root_pid\": 20606, \"scope_contract\": \"deep_exact_paths_graph_v1\", \"allowed_paths\": [[\"CIRCULATION_INTERNAL\", \"SPIRAL_L0_L1\", \"S0_CONTINUOUS_CORE\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L0_L1\", \"S0_CORE_BASE_COLLAR\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L1_L2\", \"S1_CONTINUOUS_CORE\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L1_L2\", \"S1_CORE_BASE_COLLAR\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L2_L3\", \"S2_CONTINUOUS_CORE\"], [\"CIRCULATION_INTERNAL\", \"SPIRAL_L2_L3\", \"S2_CORE_BASE_COLLAR\"], [\"FLOORS\", \"L0\"], [\"FLOORS\", \"L1\"], [\"FLOORS\", \"L2_PARTIAL_SOUTH\"], [\"FLOORS\", \"L2_PARTIAL_EAST\"], [\"FLOORS\", \"L3\"], [\"ROOF_TIMBER\", \"CURVED_SHELL\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_5\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_5\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_5\"], [\"INTERIOR\", \"CEILING_TENSION_MEMBERS\"]], \"allowed_creation_paths\": [[\"INTERIOR\", \"CEILING_TENSION_MEMBERS\"]], \"required_preserve_paths\": [[\"STRUCTURE_EXISTING\"], [\"ENVELOPE_OUTER\"], [\"CIRCULATION_EXTERNAL\"], [\"RAMPS\"], [\"SITE_GROUND\"], [\"ROOF_TIMBER\", \"ROOF_SUPPORTS\"], [\"CIRCULATION_INTERNAL\", \"SMALL_CIRCULAR_VOID_GUARDS\"], [\"CIRCULATION_INTERNAL\", \"LARGE_CIRCULAR_VOID_MESH\"], [\"INTERIOR\", \"HALL_CURTAINS\"], [\"INTERIOR\", \"ROOM_FRONT_COMPLETION\"], [\"INTERIOR\", \"CORE_EAST\"], [\"INTERIOR\", \"GREEN_PANEL_SOUTH\"]], \"verified_start_revision\": 18, \"owner_inference_authorized\": true, \"constrained_surface_edits\": {\"contract\": \"native_constrained_surface_edits_v1\", \"paths\": [[\"FLOORS\", \"L0\"], [\"FLOORS\", \"L1\"], [\"FLOORS\", \"L2_PARTIAL_SOUTH\"], [\"FLOORS\", \"L2_PARTIAL_EAST\"], [\"FLOORS\", \"L3\"], [\"ROOF_TIMBER\", \"CURVED_SHELL\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z0_5\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z3600_5\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_0\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_1\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_2\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_3\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_4\"], [\"INTERIOR\", \"FURNITURE_SIMPLIFIED\", \"TABLE_Z10800_5\"]], \"face_material_pids\": [76310, 76530, 76645, 76654, 76673, 76874, 76989, 75702, 75734, 75766, 75798, 75830, 75862, 75894, 75926, 75958, 75990, 76022, 76054, 76086, 76118, 76150, 76182, 76214, 76246], \"soft_smooth_edge_pids\": [78525, 78528, 78530, 78532, 78534, 78536, 78538, 78540, 78542, 78544, 78546, 78548, 78550, 78552, 78554, 78556, 78558, 78560, 78562, 78564, 78566, 78568, 78570, 78572, 78574, 78576, 78578, 78580, 78582, 78584, 78586, 78588, 78590, 78592, 78594, 78596, 78598, 78600, 78602, 78604, 78606, 78608, 78610, 78612, 78614, 78616, 78618, 78620, 78622, 78624, 78626, 78628, 78630, 78632, 78634, 78636, 78638, 78640, 78642, 78644, 78646, 78648, 78650, 78652, 78654, 78656, 78658, 78660, 78662, 78664, 78666, 78668, 78670, 78672, 78674, 78676, 78678, 78680, 78682, 78688, 78690, 78692, 78694, 78696, 78698, 78700, 78702, 78704, 78706, 78708, 78710, 78712, 78714, 78716, 78718, 78720, 78722, 78724, 78726, 78728, 78730, 78732, 78734, 78736, 78738, 78740, 78742, 78744, 78746, 78748, 78750, 78752, 78754, 78756, 78758, 78760, 78762, 78764, 78766, 78768, 78770, 78772, 78774, 78776, 78778, 78780, 78782, 78784, 78786, 78788, 78790, 78792, 78794, 78796, 78798, 78800, 78802, 78804, 78806, 78808, 78810, 78812, 78814, 78816, 78818, 78820, 78822, 78824, 78826, 78828, 78830, 78832, 78834, 78836, 78838, 78840, 78842, 78844]}, \"source_registration\": \"notes/interior-finish-registration.json\"}");paths=policy['constrained_surface_edits']['paths'];before=KStudioPathScopeGuard.capture(r,paths)
floor=KStudioProfessionalHelpers.named_owned_group(r,['FLOORS','L0']);roof=KStudioProfessionalHelpers.named_owned_group(r,['ROOF_TIMBER','CURVED_SHELL']);top=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z>0.99};steel=m.materials['KS_White_Steel']
m.start_operation('Surface positive: only approved material and seams',true)
begin
 top.material=steel;top.back_material=steel
 roof.entities.grep(Sketchup::Edge).select{|e|policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)}.each{|e|e.soft=true;e.smooth=true}
 positive=KStudioPathScopeGuard.verify!(r,before,paths);raise 'Surface guard not proven' unless positive['constrained_surface_edits']
 m.commit_operation
rescue
 m.abort_operation;raise
end
baseline=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];results=[]
['vertex_shift','face_reverse','new_edge','unapproved_material','hidden_seam','unapproved_soft_edge','unknown_mask_id'].each do |label|
 b=KStudioPathScopeGuard.capture(r,paths);m.start_operation('Expected constrained-surface abort '+label,true);error=nil
 begin
  case label
  when 'vertex_shift'
   floor.entities.transform_entities(Geom::Transformation.translation([1.mm,0,0]),floor.entities.to_a)
  when 'face_reverse'
   top.reverse!
  when 'new_edge'
   floor.entities.add_line([1000.mm,1000.mm,0],[1001.mm,1000.mm,0])
  when 'unapproved_material'
   bottom=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z< -0.99};bottom.material=steel
  when 'hidden_seam'
   edge=roof.entities.grep(Sketchup::Edge).find{|e|policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)};edge.hidden=true
  when 'unapproved_soft_edge'
   edge=roof.entities.grep(Sketchup::Edge).find{|e|!policy['constrained_surface_edits']['soft_smooth_edge_pids'].include?(e.persistent_id)};edge.soft=true
  when 'unknown_mask_id'
   wrong=Marshal.load(Marshal.dump(policy));wrong['constrained_surface_edits']['face_material_pids']<<9999999999;KStudioPathScopeGraphGuard.capture(r,paths,wrong)
  end
  KStudioPathScopeGuard.verify!(r,b,paths)
 rescue=>e
  error=e.message
 ensure
  m.abort_operation
 end
 raise 'Expected surface protection did not reject '+label+'; actual='+error.inspect unless error&&(error.include?('Protected geometry changed outside approved exact paths')||label=='unknown_mask_id'&&error.include?('Unknown or out-of-target surface face ID'))
 after=KStudioNativeDefinitionGraph.capture(m,root_pid:20606)[:document_geometry_material_sha256];raise 'Whole-document rollback failed '+label unless after==baseline
 results<<{case:label,status:'PASS',native_rejection:error,complete_document_rollback_equal:true}
 top=floor.entities.grep(Sketchup::Face).find{|f|f.normal.z>0.99}
end
{status:'PASS_NATIVE_CONSTRAINED_SURFACE_GUARD',native_version:Sketchup.version,root_pid:20606,revision:18,production_geometry_writes:0,disposable_committed_operations:1,actual_positive_receipt:positive,negative_cases:results,original_source_masks:{face_material_count:policy['constrained_surface_edits']['face_material_pids'].length,soft_smooth_edge_count:policy['constrained_surface_edits']['soft_smooth_edge_pids'].length},scope:'Safety-copy guard test; no live website geometry/finish modification or source-quality PASS'}
