from pathlib import Path
import json,sys,time,hashlib
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP,_generated_script_dir
P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/exterior-completion-20261016';O=D/'interior-finish-preparation';O.mkdir(exist_ok=True)
finish=[['FLOORS',n] for n in ['L0','L1','L2_PARTIAL_SOUTH','L2_PARTIAL_EAST','L3']]+[['ROOF_TIMBER','CURVED_SHELL']]+[['INTERIOR','FURNITURE_SIMPLIFIED',f'TABLE_Z{z}_{n}'] for z in [0,3600,10800] for n in range(6)]
geo=[['CIRCULATION_INTERNAL',f'SPIRAL_L{k}_L{k+1}',f'S{k}_{n}'] for k in range(3) for n in ['CONTINUOUS_CORE','CORE_BASE_COLLAR']];new=['INTERIOR','CEILING_TENSION_MEMBERS'];paths=geo+finish+[new]
keep=[[n] for n in ['STRUCTURE_EXISTING','ENVELOPE_OUTER','CIRCULATION_EXTERNAL','RAMPS','SITE_GROUND']]+[['ROOF_TIMBER','ROOF_SUPPORTS'],['CIRCULATION_INTERNAL','SMALL_CIRCULAR_VOID_GUARDS'],['CIRCULATION_INTERNAL','LARGE_CIRCULAR_VOID_MESH'],['INTERIOR','HALL_CURTAINS'],['INTERIOR','ROOM_FRONT_COMPLETION'],['INTERIOR','CORE_EAST'],['INTERIOR','GREEN_PANEL_SOUTH']]
a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=180));i=a.get_active_model_identity();assert Path(i['model_path']).name=='blank-disposable-customer-readiness-r4-20261015.skp'
source='''# ARCHFLOW_GENERATED_SCRIPT
load HELPER
m=Sketchup.active_model;raise 'GUID' unless m.guid==GUID
r=m.entities.find{|e|e.respond_to?(:persistent_id)&&e.persistent_id==20606};raise 'Revision' unless r.get_attribute('sketchup_architect','revision')==18
paths=JSON.parse(FINISH);geo=JSON.parse(GEO);faces=[];seams=[];rows=[]
paths.each do |p|
 g=KStudioProfessionalHelpers.named_owned_group(r,p,true);direct=g.entities.grep(Sketchup::Face)
 allowed=if p[0]=='FLOORS'
  direct.select{|f|p[1]=='L3' ? f.normal.z< -0.99 : (f.normal.z>0.99||p[1].start_with?('L2_')&&f.normal.z< -0.99)}
 elsif p[0]=='INTERIOR'
  direct.select{|f|f.normal.z>0.99}
 else
  []
 end
 faces+=allowed.map(&:persistent_id)
 if p[0]=='ROOF_TIMBER'
  seams=g.entities.grep(Sketchup::Edge).select{|e|e.faces.length==2&&e.faces[0].normal.angle_between(e.faces[1].normal)<5*Math::PI/180}.map(&:persistent_id)
 end
 rows<<{path:p,pid:g.persistent_id,allowed_material_faces:allowed.map{|f|{pid:f.persistent_id,normal:f.normal.to_a,actual_z_mm:f.vertices.map{|v|v.position.z.to_mm}.minmax}},direct_faces:direct.length}
end
raise 'Surface masks unexpected' unless faces.length==25&&faces.uniq.length==25&&seams.length==158
geo_rows=geo.map{|p|g=KStudioProfessionalHelpers.named_owned_group(r,p,true);{path:p,pid:g.persistent_id,actual_bounds_mm:[g.bounds.min.to_a.map(&:to_mm),g.bounds.max.to_a.map(&:to_mm)]}}
interior=KStudioProfessionalHelpers.named_owned_group(r,['INTERIOR']);raise 'New leaf exists' if interior.entities.any?{|e|e.respond_to?(:name)&&e.name=='CEILING_TENSION_MEMBERS'}
slab=KStudioProfessionalHelpers.named_owned_group(r,['FLOORS','L3']);face=slab.entities.grep(Sketchup::Face).find{|f|f.normal.z< -0.99};holes=face.loops.reject(&:outer?).map{|l|l.vertices.map{|v|v.position.to_a.map(&:to_mm)}}
members=[];omitted=[]
10.times do |n|
 x=2500+n*5000
 [[150,9850],[10150,19850]].each do |ya,yb|
  intersects=holes.any? do |poly|
   [x-20,x,x+20].any? do |xx|
    ys=[];poly.each_with_index do |p,j|
     q=poly[(j+1)%poly.length];next if (q[0]-p[0]).abs<0.00001
     tt=(xx-p[0])/(q[0]-p[0]);ys<<p[1]+tt*(q[1]-p[1]) if tt>=0&&tt<=1
    end
    ys.length>=2&&ys.min-20<yb&&ys.max+20>ya
   end
  end
  row={x_mm:x,y0_mm:ya,y1_mm:yb,middle_y_mm:(ya+yb)/2.0,attach_z_mm:10330,middle_z_mm:10050,width_mm:35}
  (intersects ? omitted : members)<<row
 end
end
raise 'Expected source-consistent hole-safe V layout' unless members.length==15&&omitted.length==5
frame=KStudioProfessionalHelpers.named_owned_group(r,['STRUCTURE_EXISTING']);beam_bases=(0..2).map{|n|g=frame.entities.find{|e|e.respond_to?(:name)&&e.name=="LONG_BEAM_Z10800_Y#{n}"};raise 'Actual beam missing' unless g;g.bounds.min.z.to_mm};raise 'Actual beam supports differ' unless beam_bases.all?{|z|(z-10320).abs<0.1}
cir=KStudioProfessionalHelpers.named_owned_group(r,['CIRCULATION_INTERNAL']);gaps=3.times.flat_map do |k|
 st=cir.entities.find{|g|g.respond_to?(:name)&&g.name=="SPIRAL_L#{k}_L#{k+1}"};landing=st.entities.find{|g|g.respond_to?(:name)&&g.name=="S#{k}_TOP_LANDING"}
 2.times.map{|j|sp=st.entities.find{|g|g.respond_to?(:name)&&g.name=="S#{k}_LANDING_SUPPORT_#{j}"};{spiral:k,support:j,actual_support_top_mm:sp.bounds.max.z.to_mm,actual_landing_bottom_mm:landing.bounds.min.z.to_mm,gap_mm:landing.bounds.min.z.to_mm-sp.bounds.max.z.to_mm}}
end
{geometry_writes:0,revision:18,root_pid:20606,finish_targets:rows,geometry_targets:geo_rows,face_material_pids:faces,soft_smooth_edge_pids:seams,actual_approved_v_members:members,omitted_v_members_above_actual_holes:omitted,actual_old_upper_beam_soffits_mm:beam_bases,actual_old_landing_support_gaps:gaps,new_leaf_absent:true,display_diagnosis:'Native neutralDark80/Light15/UseSunForAllShadingtrue controls reveal existing pale roof/L3; original settings restored. Geometry/material unchanged in tests. Not actual source-quality PASS.'}
'''
for k,v in [('HELPER',(R/'app/adopted_sketchup_helpers.rb').as_posix()),('GUID',i['model_guid']),('FINISH',json.dumps(finish)),('GEO',json.dumps(geo))]:source=source.replace(k,json.dumps(v,ensure_ascii=False))
f=_generated_script_dir()/('studio-interior-finish-preparation-'+str(time.time_ns())+'.rb');f.write_text(source,encoding='utf8');(O/'native-preparation-source.rb').write_text(source,encoding='utf8');v=a.client.call('sketchup_eval_project_file',{'script_path':str(f),'operation_name':'Read only exact core/finish IDs, roof seams and ceiling V layout excluding real holes'});v=v.get('result',v);v=json.loads(v) if isinstance(v,str) else v;(O/'native-targets-and-finish-masks-r18.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
policy={'status':'prepared','phase':'Source4 interior ceiling members/finishes and slender supported spiral shafts','model_path':str(Path(i['model_path'])),'root_pid':20606,'scope_contract':'deep_exact_paths_graph_v1','allowed_paths':paths,'allowed_creation_paths':[new],'required_preserve_paths':keep,'verified_start_revision':18,'owner_inference_authorized':True,'constrained_surface_edits':{'contract':'native_constrained_surface_edits_v1','paths':finish,'face_material_pids':v['face_material_pids'],'soft_smooth_edge_pids':v['soft_smooth_edge_pids']},'source_registration':'notes/interior-finish-registration.json'}
accept=[
 'Six exact existing core/collar containers keepPIDs. Slender shaft estimated diameter300mm and base450mm; keep original center37000,6500 and level heights. New brackets inside core target connect to actual unchanged24radial supports perflight, preserve all72treads/guards/meshes/landing geometry. Two actual landing support upper gaps17.5mm each flight need core-root connector overlap at original bar and true plate underside, not moving old bars/plates.',
 'Surface targets constrained by native primitiveID/vertex/loop/normal/transform/material guard: only25listed Face front/back materials and158listed low-angle roof Edge.soft/smooth may change. No floor/roof/table geometry, holes or IDs change; all other face/group/component materials and seam/hidden flags fixed. Keep actual already-pale roof material, fix roof facet joins only. Lower floor tops pale mineral; L2partial/L3undersides light timber ceiling finish; table top faces pale white, supports unchanged.',
 'New INTERIOR/CEILING_TENSION_MEMBERS holds15source4shallow V members under actual upper existing beam grid, 35mm rods and coherent attachment details inferred. Native-approved layout excludes5Vspans over actual circular openings; do not close holes or cross stairs. Endpoints at10330embed10mm into actual10320beam soffits, midpoint10050 leaves2850clear abovepartial7200floor. Use actual native geometry for contact/headroom checks, no slab/beam cutting.',
 'Native viewport lighting diagnosis proves defaultDark45/Light80/UseSunfalse makes already-pale material dark. Adopt neutralDark80/Light15/UseSuntrue with DisplayShadowsfalse, preserve all other display state; this is native view setting, not a new renderer or a material/geometry repair. Reject initial85/90overexposure, retain both actual experiments. Record style separately and verify saved/reopened view settings.',
 'Complete graph protection outside31paths, transactional surface guard beforecommit, originalr4/r18immutable; independent all8source current6+matched interiors, native216headroom/support/landing/ceiling beam contacts/surface material flags. Real website save/download/native3stage including actual presave ordering; strict rawdouble/strictblankreplay kept separate.'
]
g=json.loads((D/'outer-vents-preparation/design_graph.json').read_text(encoding='utf8'));g['objects']=[{'id':'complete_interior_ceiling_and_finish','provenance':'observed','source_refs':['ref_04','ref_05','ref_06','ref_07','ref_08'],'allowed_paths':paths,'inferred_details':['Slender shaft300mm/base450mm, bracket details, ceiling V positions35mm/280mm sag and light wood soffit finish inferred consistently from source04 and real beam/slab/opening geometry; no measured source dimensions.']}];g['constraints']={'allowed_paths':paths,'required_preserve_paths':keep,'acceptance':accept}
plan=json.loads((D/'outer-vents-preparation/buildplan.json').read_text(encoding='utf8'));plan.update(run_id='20261016-interior-ceiling-and-finish',design_graph_digest='sha256:'+hashlib.sha256(json.dumps(g,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest());plan['steps'][0].update(id='complete_interior_ceiling_and_finish',object='complete_interior_ceiling_and_finish',parameters={'allowed_mutation_paths':paths,'preserve_paths':keep},tag='interior_finish',component_strategy='Six precise core/collar replacements,24strict surface-only leaves and one new semantic ceiling leaf; reused rod prototypes',risk='Detached thin core/landing supports, V crossing holes, forbidden floor/roof geometry/material changes or overexposed view hiding mesh',evidence_refs=['ref_04','ref_05','ref_06','ref_07','ref_08'],preconditions=['Actual18immutable native/browser proof','Complete native primitive masks and15hole-safe V footprints captured','Native constrained-surface positive/negative safety fixturePASS beforelive activation'],postconditions=accept,rollback_group='preserved_r18',qa_view=['six canonical','all8whole originals','source4wide lower/upper same cameras','thin core radial/landing bracket roots','ceiling V end solid contacts','native material and curve-seam checks'])
for n,x in [('authorization-prepared.json',policy),('registration.json',{'status':'PREPARED_NOT_ACTIVE','revision':18,'native_verification':v,'acceptance':accept}),('design_graph.json',g),('buildplan.json',plan)]:(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
print('Prepared31exact targets:6core/collar +24surface-only +1new15Vceiling group;25Face/158EdgeIDs native-bound')
