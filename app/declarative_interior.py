"""Parameterized schematic furniture and stairs; inferred design, not compliance."""
import math,re
from copy import deepcopy

def _builder(name,location,width,depth,height,material):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}',name):raise ValueError('Invalid component name')
    if not isinstance(location,list) or len(location)!=3 or any(type(v) not in(int,float) or not math.isfinite(v) for v in location+[width,depth,height]) or min(width,depth,height)<.01 or max(width,depth,height)>100:raise ValueError('Invalid component envelope')
    if any(abs(location[i])+[width/2,depth/2,height][i]>10000 for i in range(3)):raise ValueError('Component outside coordinate bounds')
    if material is None:material={'color':[.58,.49,.37,1],'roughness':.7}
    if not isinstance(material,dict) or set(material)-{'color','roughness','transmission'}:raise ValueError('Invalid material')
    for k,v in material.items():
        values=v if k=='color' else [v]
        if not isinstance(values,list) or (k=='color' and len(values)!=4) or any(type(n) not in(int,float) or not math.isfinite(n) or not 0<=n<=1 for n in values):raise ValueError('Invalid material values')
    out=[];origin=[location[0]-width/2,location[1]-depth/2,location[2]];size=[width,depth,height]
    def box(s,a,b,c,d,e,f):
        intervals=[(a,b),(c,d),(e,f)]
        if any(not 0<=l<h<=1 for l,h in intervals):raise ValueError('Invalid internal box')
        out.append(dict(id=name+'_'+s,location=[origin[i]+(l+h)*size[i]/2 for i,(l,h) in enumerate(intervals)],dimensions=[(h-l)*size[i] for i,(l,h) in enumerate(intervals)],material=deepcopy(material)))
    return out,box

def furniture(name,location,width,depth,height,kind,material=None,quarter_turns=0):
    if kind not in('sofa','bed','table','chair','cabinet','desk') or type(quarter_turns)!=int or not 0<=quarter_turns<=3:raise ValueError('Invalid furniture kind/orientation')
    out,box=_builder(name,location,width,depth,height,material)
    def legs(top):
        for i,x in enumerate((.06,.86)):
            for j,y in enumerate((.06,.86)):box(f'leg_{i}_{j}',x,x+.08,y,y+.08,0,top)
    if kind=='sofa':
        legs(.16);box('base',.04,.96,.04,.96,.16,.32);box('back',0,1,.84,1,.32,1);box('arm_left',0,.09,0,.84,.32,.73);box('arm_right',.91,1,0,.84,.32,.73)
        for i,(a,b) in enumerate(((.09,.497),(.503,.91))):box(f'seat_{i}',a,b,.04,.84,.32,.51);box(f'cushion_{i}',a,b,.78,.84,.51,.9)
    elif kind=='bed':
        legs(.16);box('platform',0,1,0,1,.16,.35);box('headboard',0,1,.92,1,.35,1);box('mattress',.02,.98,.01,.92,.35,.61)
        for i,(a,b) in enumerate(((.08,.47),(.53,.92))):box(f'pillow_{i}',a,b,.68,.88,.61,.73)
    elif kind in('table','desk'):
        legs(.9);box('top',0,1,0,1,.9,1)
        if kind=='desk':
            out[:]=[o for o in out if not o['id'].startswith(name+'_leg_1_')]
            box('pedestal_left',.68,.74,.05,.95,0,.9);box('pedestal_right',.92,.98,.05,.95,0,.9)
            for i,z in enumerate((.04,.35,.66)):box(f'shelf_{i}',.74,.92,.05,.95,z,z+.04)
    elif kind=='chair':
        legs(.43);box('seat',0,1,0,1,.43,.53);box('back',.04,.94,.88,1,.53,1)
    else:
        box('side_left',0,.08,0,1,0,1);box('side_right',.92,1,0,1,0,1);box('bottom',.08,.92,0,1,0,.08);box('top',.08,.92,0,1,.92,1);box('rear',.08,.92,.94,1,.08,.92)
        for i,z in enumerate((.31,.62)):box(f'shelf_{i}',.08,.92,0,.94,z,z+.04)
    if quarter_turns:
        for o in out:
            x,y=o['location'][0]-location[0],o['location'][1]-location[1];x,y=[(x,y),(-y,x),(-x,-y),(y,-x)][quarter_turns];o['location'][:2]=[location[0]+x,location[1]+y]
            if quarter_turns%2:o['dimensions'][0],o['dimensions'][1]=o['dimensions'][1],o['dimensions'][0]
    return out

def u_staircase(name,location,width,depth,height,step_count=18,landing_depth=1,gap=.1,material=None):
    out,box=_builder(name,location,width,depth,height,material)
    if type(step_count)!=int or not 4<=step_count<=128 or step_count%2 or type(landing_depth) not in(int,float) or type(gap) not in(int,float) or not math.isfinite(landing_depth+gap) or not 0<landing_depth<depth or not 0<=gap<width:raise ValueError('Invalid stair parameters')
    n=step_count//2;fw=(width-gap)/2;run=(depth-landing_depth)/n
    if min(fw,run)<.01:raise ValueError('Invalid stair width/run')
    a=fw/width;b=(fw+gap)/width;end=1-landing_depth/depth
    for i in range(n):
        y0,y1=end*i/n,end*(i+1)/n
        box(f'lower_{i}',0,a,y0,y1,0,(i+1)/step_count);box(f'upper_{i}',b,1,end-y1,end-y0,0,(n+i+1)/step_count)
    box('landing',0,1,end,1,0,.5)
    return {'objects':out,'component_ids':[o['id'] for o in out],'receipt':{'rise':height/step_count,'tread_depth':run,'flight_width':fw,'top_z':location[2]+height,'landing_top_z':location[2]+height/2,'solid_to_base':True,'compliance':'not_assessed'}}
