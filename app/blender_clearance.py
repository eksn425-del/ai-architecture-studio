"""Declared clearance-zone checks, not navigation or building-code approval."""
import math

def audit_clearance(objects,zones):
    if not isinstance(zones,list) or not 1<=len(zones)<=32:raise ValueError('Invalid clearance zones')
    results=[]
    for z in zones:
        if not isinstance(z,dict) or set(z)!={'name','location','dimensions','ignore_ids'} or not isinstance(z['name'],str) or not 1<=len(z['name'])<=80:raise ValueError('Invalid zone')
        for k in ('location','dimensions'):
            v=z[k]
            if not isinstance(v,list) or len(v)!=3 or any(type(n) not in(int,float) or not math.isfinite(n) or abs(n)>10000 or(k=='dimensions' and n<=0) for n in v):raise ValueError('Invalid zone bounds')
        ignore=z['ignore_ids']
        if not isinstance(ignore,list) or len(ignore)>256 or any(not isinstance(n,str) or n not in objects for n in ignore) or len(set(ignore))!=len(ignore):raise ValueError('Invalid ignore IDs')
        lo=[x-d/2 for x,d in zip(z['location'],z['dimensions'])];hi=[x+d/2 for x,d in zip(z['location'],z['dimensions'])];blocked=[];potential=[]
        for name,o in objects.items():
            if name in ignore:continue
            bounds=[(x-d/2,x+d/2) for x,d in zip(o['location'],o['dimensions'])] if 'dimensions' in o else [(min(v[i] for v in o['vertices'])+o['location'][i],max(v[i] for v in o['vertices'])+o['location'][i]) for i in range(3)]
            if all(min(hi[i],b)-max(lo[i],a)>1e-6 for i,(a,b) in enumerate(bounds)):(blocked if 'dimensions' in o else potential).append(name)
        results.append({'name':z['name'],'box_blockers':blocked,'mesh_bounds_candidates':potential,'status':'blocked' if blocked else('needs_mesh_review' if potential else 'clear'),'ignored_ids':ignore})
    return {'zones':results,'method':'positive-volume box AABB; conservative mesh bounds','navigation_verified':False,'building_code_compliance':False}
