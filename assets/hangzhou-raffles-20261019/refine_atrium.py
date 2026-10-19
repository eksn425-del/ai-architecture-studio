"""Reference-informed atrium skylight, framed glazing and visible gallery layers.
Uses official UNStudio atrium photograph as a construction-type reference.
Exact panel sizes and internal galleries remain inferred, not surveyed.
Run within finalize_scene.py before saving. Existing roof/tower meshes untouched.
"""
import bpy,math
from mathutils import Vector
s=bpy.context.scene
# Remove only a previous instance of this explicit refinement if rerun.
for ob in list(bpy.data.objects):
 if ob.name.startswith('Atrium |'):bpy.data.objects.remove(ob,do_unlink=True)
def amaterial(name,color,rough=.4,metal=0,trans=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;bs.inputs['Transmission Weight'].default_value=trans
 return m
steel=amaterial('Atrium silver frame',(.62,.68,.68),.27,.65)
glazing=amaterial('Atrium pale blue skylight',(.30,.51,.57),.22,.25,.20)
inner=amaterial('Atrium ivory gallery',(.72,.68,.57),.6)
floor=amaterial('Atrium limestone floor',(.42,.36,.25),.65)
bs=floor.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(.23,.18,.10,1);bs.inputs['Emission Strength'].default_value=.18
rim=[]
for k in range(4):
 ob=bpy.data.objects['podium_roof_segment_'+str(k)]
 rim.extend([ob.matrix_world@ob.data.vertices[i*5+4].co for i in range(12)])
cx,cy=-8.,0.;rx,ry=18.,34.
def height(x,y):
 u=(x-cx)/rx;v=y/ry;r=min(1,math.hypot(u,v));a=(math.atan2(v,u)%(2*math.pi))*48/(2*math.pi);i=int(a);f=a-i
 edge=rim[i].z*(1-f)+rim[(i+1)%48].z*f
 return 39.4*(1-r*r)+(edge+.28)*r*r

def meshobj(name,vs,fs,ma):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(ma);ob=bpy.data.objects.new('Atrium | '+name,me);s.collection.objects.link(ob);return ob

def line(name,pts,r=.10,ma=steel):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 ob=bpy.data.objects.new('Atrium | '+name,c);s.collection.objects.link(ob);c.materials.append(ma);return ob
# Connected glass surface: concentric tessellation follows the preserved rim exactly.
vs=[(cx,cy,height(cx,cy))];rings=14;seg=96
for j in range(1,rings+1):
 r=j/rings
 for i in range(seg):
  t=2*math.pi*i/seg;x=cx+rx*r*math.cos(t);y=ry*r*math.sin(t);vs.append((x,y,height(x,y)))
fs=[(0,1+i,1+(i+1)%seg) for i in range(seg)]
for j in range(1,rings):
 a=1+(j-1)*seg;b=a+seg
 for i in range(seg):k=(i+1)%seg;fs.extend([(a+i,b+i,b+k),(a+i,b+k,a+k)])
ob=meshobj('continuous glazed skylight',vs,fs,glazing)
for p in ob.data.polygons:p.use_smooth=True
mod=ob.modifiers.new('Glazing thickness','SOLIDIFY');mod.thickness=.08
# Orthogonal steel members are clipped to the elliptical opening, like the photographed grid.
for j in range(-6,7):
 x=cx+j*2.6;lim=ry*math.sqrt(max(0,1-((x-cx)/rx)**2));pts=[]
 for i in range(35):y=-lim+2*lim*i/34;pts.append((x,y,height(x,y)+.14))
 line('longitudinal steel %02d'%j,pts,.105)
for j in range(-12,13):
 y=j*2.6;lim=rx*math.sqrt(max(0,1-(y/ry)**2));pts=[]
 for i in range(21):x=cx-lim+2*lim*i/20;pts.append((x,y,height(x,y)+.16))
 line('cross steel %02d'%j,pts,.085)
line('continuous perimeter closure',[(v.x,v.y,v.z+.28) for v in rim]+[(rim[0].x,rim[0].y,rim[0].z+.28)],.22)
# Visible inner wall lining, floor and stepped gallery rings remove the empty black shaft.
wallvs=[]
for zmode in [0,1]:
 for v in rim:wallvs.append((v.x,v.y,2.8 if zmode==0 else v.z-.12))
meshobj('internal light lining',wallvs,[(i,(i+1)%48,(i+1)%48+48,i+48) for i in range(48)],inner)
meshobj('ground floor',[(cx,cy,2.9)]+[(v.x,v.y,2.9) for v in rim],[(0,1+i,1+(i+1)%48) for i in range(48)],floor)
for level,z in enumerate([8,14,20,26,31]):
 vv=[]
 for rr in [1,.82]:
  for i in range(96):
   t=2*math.pi*i/96;vv.append((cx+rx*rr*math.cos(t),ry*rr*math.sin(t),z))
 meshobj('gallery ledge '+str(level),vv,[(i,(i+1)%96,(i+1)%96+96,i+96) for i in range(96)],inner)
 line('gallery rail '+str(level),[(cx+rx*.82*math.cos(2*math.pi*i/96),ry*.82*math.sin(2*math.pi*i/96),z+1.05) for i in range(97)],.045)
s['Atrium refinement']='Official UNStudio imagery shows glazed steel-grid atrium roof; added reference-informed curved skylight, perimeter frame, light lining and gallery levels. Exact dimensions inferred.'
print('ATRIUM_SKYLIGHT_ADDED',flush=True)
