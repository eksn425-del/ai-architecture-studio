from pathlib import Path
import json,math,html
D=Path(__file__).resolve().parent;x=json.loads((D/'geometry-topology.json').read_text(encoding='utf-8'))
def flatten(nodes):
 for n in nodes:
  yield n
  yield from flatten(n['children'])
nodes=list(flatten(x['groups']));by_path={tuple(n['path']):n for n in nodes}
def node(*p):return by_path[tuple(p)]
def centroid(points):return [sum(p[k] for p in points)/len(points) for k in range(3)]
def inside_convex(n,p,tol=0.1):
 if len(n['vertices_world_mm'])!=8 or len(n['faces'])!=6:return False
 center=centroid(n['vertices_world_mm'])
 for f in n['faces']:
  a=f['loops'][0]['points'][0];normal=f['normal'];side=lambda q:sum(normal[k]*(q[k]-a[k]) for k in range(3))
  if side(center)*side(p)<-tol*max(abs(side(center)),1):return False
 return True
def on_segment(p,a,b):
 cross=(p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0])
 return abs(cross)<0.01 and min(a[0],b[0])-0.01<=p[0]<=max(a[0],b[0])+0.01 and min(a[1],b[1])-0.01<=p[1]<=max(a[1],b[1])+0.01
def inside_polygon(p,poly):
 hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if on_segment(p,a,b):return True
  if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
braces=node('ENVELOPE_OUTER','TENSION_BRACING');roof=[n for n in nodes if n['path'][0]=='ROOF_TIMBER'];galleries=list(flatten([node('CIRCULATION_EXTERNAL','GALLERIES')]))
rods=[]
for n in braces['children']:
 lengths=sorted(set(e['length_mm'] for e in n['edges']));ends=sorted([centroid(f['loops'][0]['points']) for f in n['faces'] if abs(f['area_mm2']-24*24)<0.1],key=lambda p:p[2])
 assert len(ends)==2 and abs(lengths[0]-24)<0.01
 rods.append({'path':n['path'],'pid':n['pid'],'section_mm':[24,24],'long_edge_mm':lengths[-1],'endpoints_world_mm':ends,'roof_endpoint_contacts':[q['path'] for q in roof if inside_convex(q,ends[1])],'lower_endpoint_contacts':[q['path'] for q in galleries if inside_convex(q,ends[0])],'face_count':len(n['faces']),'face_areas_mm2':sorted(f['area_mm2'] for f in n['faces'])})
ramps=[]
for n in node('RAMPS')['children']:
 top=next(f for f in n['faces'] if f['normal'][2]>0.5)
 ps=top['loops'][0]['points'];ys=sorted(set(p[1] for p in ps));ends=sorted([centroid([p for p in ps if p[1]==y]) for y in ys],key=lambda p:p[2]);delta=[ends[1][k]-ends[0][k] for k in range(3)]
 landings=node('CIRCULATION_EXTERNAL','LANDINGS')['children']
 ramps.append({'path':n['path'],'pid':n['pid'],'top_endpoints_world_mm':ends,'ascending_signed_y':'+Y' if delta[1]>0 else '-Y','rise_mm':delta[2],'horizontal_run_mm':math.hypot(delta[0],delta[1]),'source_ramp_end_observation':'+Y up (screen-left) for all three visible flights, SOURCE01','direction_matches_source_projection':delta[1]>0,'endpoint_landing_contacts':[[q['name'] for q in landings if inside_convex(q,p)] for p in ends]})
floors=node('FLOORS');top_faces=[]
for n in floors['children']:
 for f in n['faces']:
  if f['normal'][2]>0.9:top_faces.append({'path':n['path'],'pid':n['pid'],'face_pid':f['pid'],'z_mm':f['loops'][0]['points'][0][2],'loops':f['loops']})
probes=[]
for p in [[10000,16000],[10000,5000],[35000,5000],[37000,6500]]:
 matches=[]
 for f in top_faces:
  if abs(f['z_mm']-7200)>0.1:continue
  outer=next(l['points'] for l in f['loops'] if l['outer']);holes=[l['points'] for l in f['loops'] if not l['outer']]
  if inside_polygon(p,outer) and not any(inside_polygon(p,h) for h in holes):matches.append(f['path'])
 probes.append({'xy_world_mm':p,'z_mm':7200,'native_floor_present':bool(matches),'covering_paths':matches})
envelope_measurements=[]
for path in [('ENVELOPE_OUTER','NORTH_BAY_0','MULLION'),('ENVELOPE_OUTER','NORTH_BAY_0','GLASS'),('ENVELOPE_OUTER','INNER_GLAZING','INNER_GLASS_0_0')]:
 n=node(*path);envelope_measurements.append({'path':n['path'],'pid':n['pid'],'edge_lengths_mm':sorted(set(e['length_mm'] for e in n['edges'])),'material':n['effective_material'],'face_materials':[f['material'] for f in n['faces']],'solid_face_count':len(n['faces'])})
report={'brace_path':braces['path'],'brace_pid':braces['pid'],'brace_geometry_finding':'22 separate 24x24mm rods; no filled triangular web face in this subtree. Source exact diameter unknown; prior thick-solid attribution contradicted by native geometry.','rods':rods,'ramps':ramps,'floor_topology':top_faces,'L2_floor_probes':probes,'envelope_measurements':envelope_measurements,'coordinate_convention':{'view':'Standing -X looking +X','screen_left':'+Y','screen_right':'-Y','up':'+Z'},'root_own_loose_geometry':x['root_own_loose'],'document_own_loose_geometry':x['document_own_loose'],'limitations':['Source dimensions/camera intrinsics unknown; native dimensions are measurements of estimated model, not source survey.','Native endpoint contact is geometric intersection/touch only, not structural-safety certification.','Source long-side gallery return route and concealed connections not fully established.']}
(D/'measured-relations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'rod_count':len(rods),'rod_sections':sorted(set(tuple(r['section_mm']) for r in rods)),'roof_contacts':sum(bool(r['roof_endpoint_contacts']) for r in rods),'gallery_contacts':sum(bool(r['lower_endpoint_contacts']) for r in rods),'ramps':ramps,'floor_probes':probes},ensure_ascii=False))
