"""Read-only native triangle contact measurements; not a visual/code-compliance PASS.

Input comes from the fixed architecture_features collector. Bounding boxes are
only a pruning optimization; final distance uses actual native triangles.
"""
import argparse
import json
import math
from pathlib import Path


def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))


def point_triangle(p,t):
    a,b,c=t;ab=sub(b,a);ac=sub(c,a);ap=sub(p,a);d1=dot(ab,ap);d2=dot(ac,ap)
    if d1<=0 and d2<=0:return norm(ap)
    bp=sub(p,b);d3=dot(ab,bp);d4=dot(ac,bp)
    if d3>=0 and d4<=d3:return norm(bp)
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:return norm(sub(p,add(a,mul(ab,d1/(d1-d3)))))
    cp=sub(p,c);d5=dot(ab,cp);d6=dot(ac,cp)
    if d6>=0 and d5<=d6:return norm(cp)
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:return norm(sub(p,add(a,mul(ac,d2/(d2-d6)))))
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:
        return norm(sub(p,add(b,mul(sub(c,b),(d4-d3)/((d4-d3)+(d5-d6))))))
    n=cross(ab,ac)
    if norm(n)<1e-12:return min(norm(sub(p,q)) for q in t)
    return abs(dot(ap,n))/norm(n)


def segment_distance(p1,q1,p2,q2):
    d1=sub(q1,p1);d2=sub(q2,p2);r=sub(p1,p2);a=dot(d1,d1);e=dot(d2,d2);f=dot(d2,r)
    clamp=lambda v:max(0,min(1,v))
    if a<1e-12 and e<1e-12:return norm(r)
    if a<1e-12:s=0;t=clamp(f/e)
    else:
        c=dot(d1,r)
        if e<1e-12:t=0;s=clamp(-c/a)
        else:
            b=dot(d1,d2);den=a*e-b*b;s=clamp((b*f-c*e)/den) if abs(den)>1e-12 else 0
            t=(b*s+f)/e
            if t<0:t=0;s=clamp(-c/a)
            elif t>1:t=1;s=clamp((b-c)/a)
    return norm(sub(add(p1,mul(d1,s)),add(p2,mul(d2,t))))


def pierces(p,q,t):
    a,b,c=t;d=sub(q,p);e1=sub(b,a);e2=sub(c,a);h=cross(d,e2);det=dot(e1,h)
    if abs(det)<1e-10:return False
    s=sub(p,a);u=dot(s,h)/det;v=dot(d,cross(s,e1))/det;w=dot(e2,cross(s,e1))/det
    return -1e-9<=u<=1+1e-9 and -1e-9<=v and u+v<=1+1e-9 and -1e-9<=w<=1+1e-9


def triangle_distance(a,b):
    ae=list(zip(a,a[1:]+a[:1]));be=list(zip(b,b[1:]+b[:1]))
    if any(pierces(p,q,b) for p,q in ae) or any(pierces(p,q,a) for p,q in be):return 0.0
    return min([point_triangle(p,b) for p in a]+[point_triangle(p,a) for p in b]+
               [segment_distance(p,q,r,s) for p,q in ae for r,s in be])


def bounds(t):return ([min(p[i] for p in t) for i in range(3)],[max(p[i] for p in t) for i in range(3)])
def box_gap(a,b):return math.sqrt(sum(max(0,a[0][i]-b[1][i],b[0][i]-a[1][i])**2 for i in range(3)))


def measure(faces,left,right):
    def triangles(prefix):
        return [(tri,bounds(tri),face['pid']) for face in faces if face['path'][:len(prefix)]==prefix
                for tri in face['triangles_mm'] if len(tri)==3]
    a=triangles(left);b=triangles(right)
    if not a or not b:return {'status':'MISSING_GEOMETRY','left':left,'right':right}
    best=float('inf');pair=None
    for at,ab,ap in a:
        for bt,bb,bp in b:
            if box_gap(ab,bb)>best:continue
            value=triangle_distance(at,bt)
            if value<best:best=value;pair=[ap,bp]
            if best<1e-7:break
        if best<1e-7:break
    return {'left':left,'right':right,'minimum_surface_distance_mm':round(best,4),'nearest_face_pids':pair,
            'status':'CONTACT_OR_INTERSECTION' if best<=0.1 else 'GAP',
            'limitation':'Minimum contact alone does not prove a full-width seam or a traversable stair connection.'}


def audit(data,pairs):
    if data.get('collector')!='KStudioNativeArchitectureFeatures/1':raise ValueError('Native feature evidence required')
    return {'schema_version':1,'root_pid':data['root_pid'],'identity':data['owned_identity'],
        'geometry_sha256':data['root_geometry_material_sha256'],
        'contacts':[measure(data['faces'],*pair) for pair in pairs],
        'visual_verdict':'NOT_ASSESSED','regulatory_verdict':'NOT_ASSESSED'}


def stair_terminals(data,pairs):
    """Measure each flight's highest horizontal tread against its landing.

    This deliberately does not use the whole-flight minimum, which may be zero
    at the bottom even when the upper exit is disconnected. A contact result
    still requires full-width and walkable-path review.
    """
    faces=list(data['faces']);terminal_pairs=[]
    for flight,landing in pairs:
        rows=[r for r in faces if r['path'][:len(flight)]==flight]
        points=[p for r in rows for t in r['triangles_mm'] for p in t]
        terminal=flight+['__highest_horizontal_tread__']
        if points:
            z=max(p[2] for p in points)
            for row in rows:
                triangles=[t for t in row['triangles_mm'] if all(abs(p[2]-z)<0.01 for p in t)]
                if triangles:faces.append({**row,'path':terminal,'triangles_mm':triangles})
        terminal_pairs.append((terminal,landing))
    return audit({**data,'faces':faces},terminal_pairs)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('pairs',type=Path)
    p.add_argument('--stair-terminals',action='store_true')
    a=p.parse_args();print(json.dumps((stair_terminals if a.stair_terminals else audit)(json.loads(a.capture.read_text(encoding='utf8')),
        json.loads(a.pairs.read_text(encoding='utf8'))),ensure_ascii=False,indent=2))
