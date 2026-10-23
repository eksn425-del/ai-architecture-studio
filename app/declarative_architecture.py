"""Explicit bounded assemblies. Does not infer source truth or certify safety."""
import math,re

def finite(*values):
    if any(type(v) not in(int,float) or not math.isfinite(v) or abs(v)>10000 for v in values):raise ValueError('Expected finite bounded coordinates')

def sloped_closure(name,x0,x1,y0,y1,bottom,top0,top1,material):
    finite(x0,x1,y0,y1,bottom,top0,top1)
    if not(x0<x1 and y0<y1 and bottom<min(top0,top1)):raise ValueError('Invalid closure')
    return dict(id=name,location=[0,0,0],vertices=[[x0,y0,bottom],[x1,y0,bottom],[x1,y1,bottom],[x0,y1,bottom],[x0,y0,top0],[x1,y0,top1],[x1,y1,top1],[x0,y1,top0]],faces=[[3,2,1,0],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]],material=material)

def window_wall(name,start,end,plane,thickness,base,height,openings,wall_material,glass_material,frame_material,axis=0):
    if type(axis)!=int or axis not in(0,1) or not isinstance(openings,list) or len(openings)>8 or any(not isinstance(o,(list,tuple)) or len(o)!=4 for o in openings):raise ValueError('Invalid openings')
    finite(start,end,plane,thickness,base,height,*[v for o in openings for v in o])
    if not(start<end and thickness>0 and height>0):raise ValueError('Invalid wall')
    for a,b,c,d in openings:
        if not(start<a<b<end and base<c<d<base+height):raise ValueError('Opening outside wall')
    for i,(a,b,c,d) in enumerate(openings):
        for e,f,g,h in openings[i+1:]:
            if min(b,f)>max(a,e) and min(d,h)>max(c,g):raise ValueError('Overlapping openings')
    xs=sorted({start,end,*[v for a,b,c,d in openings for v in(a,b)]});zs=sorted({base,base+height,*[v for a,b,c,d in openings for v in(c,d)]});out=[]
    def box(s,a,b,c,d,depth,mat):
        loc=[(a+b)/2,plane,(c+d)/2];dims=[b-a,depth,d-c]
        if axis:loc[0],loc[1]=loc[1],loc[0];dims[0],dims[1]=dims[1],dims[0]
        out.append(dict(id=name+'_'+s,location=loc,dimensions=dims,material=mat))
    for i,(a,b) in enumerate(zip(xs,xs[1:])):
        for j,(c,d) in enumerate(zip(zs,zs[1:])):
            if not any(e<=(a+b)/2<=f and g<=(c+d)/2<=h for e,f,g,h in openings):box(f'wall_{i}_{j}',a,b,c,d,thickness,wall_material)
    for i,(a,b,c,d) in enumerate(openings):
        t=min(.055,(b-a)/5,(d-c)/5);box(f'glass_{i}',a+t,b-t,c+t,d-t,.035,glass_material)
        for key,x0,x1,z0,z1 in [('left',a,a+t,c,d),('right',b-t,b,c,d),('bottom',a+t,b-t,c,c+t),('top',a+t,b-t,d-t,d)]:box(f'frame_{i}_{key}',x0,x1,z0,z1,thickness*.8,frame_material)
    return out

def floor_opening(name,x0,x1,y0,y1,bottom,thickness,opening,material):
    if not isinstance(opening,(list,tuple)) or len(opening)!=4:raise ValueError('Invalid opening')
    finite(x0,x1,y0,y1,bottom,thickness,*opening);a,b,c,d=opening
    if not(x0<a<b<x1 and y0<c<d<y1 and thickness>0):raise ValueError('Opening outside slab')
    return [dict(id=name+'_'+str(i),location=[(l+r)/2,(f+t)/2,bottom+thickness/2],dimensions=[r-l,t-f,thickness],material=material) for i,(l,r,f,t) in enumerate([(x0,a,y0,y1),(b,x1,y0,y1),(a,b,y0,c),(a,b,d,y1)])]

def leaf_rosette(name,location,radius=.3,height=.65,seed=0,material=None):
    import random
    if not isinstance(location,list) or len(location)!=3 or type(seed)!=int:raise ValueError('Invalid plant')
    finite(*location,radius,height)
    if radius<=0 or height<=0:raise ValueError('Invalid plant extent')
    rng=random.Random(seed);vertices=[];faces=[]
    for i in range(36):
        a=i*2.399963+rng.uniform(-.15,.15);length=radius*rng.uniform(.55,1);z=height*(.3+.3*(i%3));w=radius*.11;u,v=math.cos(a),math.sin(a);n=len(vertices)
        vertices.extend([[0,0,height*.05],[u*length*.5-v*w,v*length*.5+u*w,z],[u*length,v*length,z*.65],[u*length*.5+v*w,v*length*.5-u*w,z+height*.035]])
        faces.extend([[n,n+2,n+1],[n,n+1,n+3],[n+1,n+2,n+3],[n+2,n,n+3]])
    return dict(id=name,location=location,vertices=vertices,faces=faces,material=material or {'color':[.19,.32,.07,1],'roughness':.85})

def scoped_replacement_patch(objects,previous_ids,current_ids=None):
    ids=[o.get('id') for o in objects];pattern=re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')
    if not isinstance(previous_ids,list) or len(ids)>256 or len(previous_ids)>256 or any(not isinstance(n,str) or not pattern.fullmatch(n) for n in ids+previous_ids) or len(set(ids))!=len(ids) or len(set(previous_ids))!=len(previous_ids):raise ValueError('Invalid component receipt')
    if current_ids is not None:
        current=set(current_ids)
        if set(previous_ids)-current:raise ValueError('Missing prior owned objects')
        if set(ids)&(current-set(previous_ids)):raise ValueError('Unrelated object ID collision')
    return dict(objects=objects,delete_ids=sorted(set(previous_ids)-set(ids)))
