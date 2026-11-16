"""Explicit pairwise connection diagnostics. Mesh bounds remain conservative."""
import math

def audit_connections(objects,connections):
 if not isinstance(connections,list) or not 1<=len(connections)<=64:raise ValueError('Expected1to64 connections')
 results=[]
 def bounds(o):
  return [(x-d/2,x+d/2) for x,d in zip(o['location'],o['dimensions'])] if 'dimensions' in o else [(min(v[i] for v in o['vertices'])+o['location'][i],max(v[i] for v in o['vertices'])+o['location'][i]) for i in range(3)]
 for c in connections:
  if not isinstance(c,dict) or set(c)!={'a','b','axis','tolerance'} or not isinstance(c['a'],str) or not isinstance(c['b'],str) or c['a']==c['b'] or c['a'] not in objects or c['b'] not in objects or type(c['axis'])!=int or c['axis'] not in(0,1,2) or type(c['tolerance']) not in(int,float) or not math.isfinite(c['tolerance']) or not 0<=c['tolerance']<=.1:raise ValueError('Invalid declared connection')
  a,b=objects[c['a']],objects[c['b']];aa,bb=bounds(a),bounds(b);axis=c['axis'];tol=c['tolerance'];gap=bb[axis][0]-aa[axis][1];overlaps=[min(x[1],y[1])-max(x[0],y[0]) for x,y in zip(aa,bb)];aligned=all(overlaps[i]>tol for i in range(3) if i!=axis)
  if not aligned:status='misaligned'
  elif gap>tol:status='gap'
  elif gap>=-tol:status='contact'
  elif overlaps[axis]>tol:status='penetration'
  elif overlaps[axis]>=-tol:status='reversed_contact'
  else:status='reversed_disjoint'
  results.append({'a':c['a'],'b':c['b'],'axis':axis,'signed_gap_m':gap,'aabb_overlap_volume_m3':math.prod(max(0,v) for v in overlaps),'bounds_status':status,'exact_for_boxes':'dimensions' in a and 'dimensions' in b,'mesh_surface_verification_required':'dimensions' not in a or 'dimensions' not in b})
 return {'connections':results,'note':'A max bound to B min bound on declared axis. Intentional contact is not a defect. Mesh bounds do not establish exact surface intersection.','automatic_geometry_changes':False}
