from pathlib import Path
import sys,json,hashlib,shutil
R=Path.cwd();P=R/'runtime/projects/architecture-project-4f0e4';D=R/'runtime/customer-readiness-20261015';O=D/'r10-small-guards-preparation';O.mkdir(exist_ok=True)
g=json.loads((D/'grating-design-graph.json').read_text(encoding='utf8'))
for src in g['sources']:
 assert hashlib.sha256((P/src['path']).read_bytes()).hexdigest()==src['sha256'],src['id']
native=json.loads((D/'r9-graph-bound-reopened.json').read_text(encoding='utf8'));pool=native['definitions'];root=json.loads(native['root_instance']['canonical_geometry_json'])['instance'];cur=root
for name in ['FLOORS','L3']:
 cur=next(i for i in json.loads(pool[cur['definition_ref']]['canonical_payload_json'])['instances'] if i['name']==name)
 assert cur['local_transform']==[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
floor=json.loads(pool[cur['definition_ref']]['canonical_payload_json']);holes=[]
for f in floor['faces_local_mm']:
 if f['normal']!=[0.,0.,1.]:continue
 for loop in f['loops']:
  if loop['outer']:continue
  pts=loop['points'];bounds=[[min(v[k] for v in pts),max(v[k] for v in pts)] for k in range(3)]
  holes.append({'vertex_count':len(pts),'boundary_vertices_mm':pts,'bounds_mm':bounds,'center_mm':[(v[0]+v[1])/2 for v in bounds]})
small=[h for h in holes if abs(h['bounds_mm'][0][1]-h['bounds_mm'][0][0]-2200)<1e-8]
assert len(small)==2 and all(h['vertex_count']==48 and h['center_mm'][2]==10800 for h in small)
internal=next(i for i in json.loads(pool[root['definition_ref']]['canonical_payload_json'])['instances'] if i['name']=='CIRCULATION_INTERNAL');children=json.loads(pool[internal['definition_ref']]['canonical_payload_json'])['instances'];target=['CIRCULATION_INTERNAL','SMALL_CIRCULAR_VOID_GUARDS'];assert not any(c['name']==target[-1] for c in children)
registration={'status':'NATIVE_EXISTING_HOLES_REGISTERED','revision':9,'root_pid':20606,'actual_floor_path':['FLOORS','L3'],'incorrect_historical_label':'L3_DECK is NOT an existing exact floor path; do not use it','source':'ref_04 full original upper panel shows thin white cylindrical mesh guards','source_metric_dimensions':'not measured; existing-model hole coordinates retained, not proof of surveyed source dimensions','top_holes':holes,'two_small_missing_guard_holes':small,'new_exact_leaf':target,'parent_pid_source':'complete raw native definition graph identities','existing_internal_child_names':[c['name'] for c in children]}
(O/'registration.json').write_text(json.dumps(registration,ensure_ascii=False,indent=2),encoding='utf8')
g['objects']=[{'id':'two_small_circular_guards','provenance':'inferred','allowed_paths':[target],'dimensions':{'guard_height':{'value':1.1,'unit':'m','provenance':'inferred','confidence':0.5,'evidence_refs':['ref_04']}}}]
g['constraints']={'status':'PREPARED_NOT_ACTIVE','observed':'Source04 shows slender white cylindrical open wire mesh around small circular voids. Actual native L3 has two48segment holes centered12000,10500 and22500,10500mm, radius1100mm, top10800mm. Existing 42large VOID_RAIL segments surround only the stair opening at37000,6500mm.','inferred':'Retain existing hole locations, construct mesh guard just outside each boundary, estimated1100mmheight; wire pitch/diameter and attachment detail not measured. No opaque transparent-cylinder shortcut.','allowed_creation_paths':[target],'mandatory_preserve_paths':[['RAMPS'],['CIRCULATION_EXTERNAL'],['ROOF_TIMBER'],['ENVELOPE_OUTER'],['FLOORS'],['INTERIOR']],'preserve':'All actual existing geometry including all floors, existing large spiral guard, ramps, glass, grating and roof. No parent expansion, cutting slab, whole rebuild or other material change.','acceptance':['exact host-approved absent-leaf creation only','two genuinely open mesh guards at actual two existing small holes','native boundary/contact/open-cell controls','deep graph protection, legacy KEEP and current independent eight-source review','real website save/download/native reopen with raw and declared precision verdicts separate'],'limitations':'Not guard safety/load/code certification. Source interior overall registration remains unresolved; this addition follows two already-existing model holes.'}
(O/'design_graph.json').write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf8')
digest='sha256:'+hashlib.sha256(json.dumps(g,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
plan={'schema_version':1,'project_id':'architecture-project-4f0e4','run_id':'20261016-r9-two-small-circle-guards','design_graph_digest':digest,'steps':[{'id':'two_small_circular_guards','object':'two_small_circular_guards','action':'existing_guarded_workspace_ruby_edit','parameters':{'allowed_mutation_paths':[target],'allowed_creation_paths':[target],'scope_contract':'deep_exact_paths_graph_v1','actual_model':'gpt-6.1-sol','reasoning_effort':'medium'},'depends_on':[],'tag':'interior_circulation','component_strategy':'One exact new owned leaf containing two named editable guard assemblies; reuse slender mesh members and rings; existing model immutable','risk':'Wrong hole/level, opaque filled skin, over-heavy wires, altered floor or neighboring geometry','evidence_refs':['ref_04'],'preconditions':['same actual r9/root20606','production dispatcher native positive/7negative tests','explicit absent-leaf host scope; parent remains protected','same eight source SHA/order'],'postconditions':g['constraints']['acceptance'],'rollback_group':'preserved_r9','qa_view':['source04 upper circular guard view','both circles closeup','six canonical','eight originals/12pairs']}]}
(O/'buildplan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
session=json.loads((P/'state/agent_session.json').read_text(encoding='utf8'));assert session['ruby_state']['glass_curved_roof']['revision']==9
policy={'status':'prepared','phase':'Add only two missing small circle mesh guards at same r9 holes','model_path':str((P/session['model_path']).resolve()),'root_pid':20606,'scope_contract':'deep_exact_paths_graph_v1','allowed_paths':[target],'allowed_creation_paths':[target],'required_preserve_paths':g['constraints']['mandatory_preserve_paths'],'max_geometry_commits':1,'source_registration':'notes/small-circle-registration.json','source_quality_before':'FAIL; no implicit completion claim'}
(O/'authorization-prepared.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf8')
backup=P/'outputs/model/blank-disposable-r9-before-small-guards-20261016.skp'
if not backup.exists():shutil.copy2(Path.home()/'Downloads/agent-checkpoint-5374ca398451.skp',backup)
assert hashlib.sha256(backup.read_bytes()).hexdigest()=='70f103cac7cdeed87fe4dd7e70b5d67ed747f18f748c0d41d53e7cf48423f67c'
print('Eight source hashes unchanged; two actual L3 holes registered; exact absent-leaf plan prepared, not activated')
