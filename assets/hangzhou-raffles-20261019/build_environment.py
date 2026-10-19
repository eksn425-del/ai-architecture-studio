"""Hangzhou Raffles: presentation environment. Original tower/podium geometry preserved.
Repro: blender -b SOURCE.blend -t 8 --python build_environment.py -- --out OUTPUT [--preview]
All contextual geometry is authored procedural approximation, not surveyed city data.
"""
import bpy,math,random,json,sys,argparse,hashlib
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--out',default=str(Path(__file__).parent));p.add_argument('--preview',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=Path(args.out).resolve();OUT.mkdir(exist_ok=True,parents=True); random.seed(27)
s=bpy.context.scene
# Retain architecture exactly; discard schematic surrounding city.
for o in list(bpy.data.objects):
 if not o.name.startswith(('tower_','podium_')):bpy.data.objects.remove(o,do_unlink=True)
arch=list(bpy.data.objects)
def fingerprint(objects):
 h=hashlib.sha256()
 for o in sorted(objects,key=lambda x:x.name):
  h.update(o.name.encode());h.update(str([tuple(v.co) for v in o.data.vertices]).encode());h.update(str([tuple(f.vertices) for f in o.data.polygons]).encode())
 return h.hexdigest()
original_fingerprint=fingerprint(arch)
def mat(name,col,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*col,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;return m
stone=mat('Warm limestone',(0.56,.53,.46));paving=mat('Silver granite paving',(.43,.46,.45));asphalt=mat('Fine asphalt',(.075,.087,.095),.9);white=mat('Ivory road paint',(.8,.81,.73),.7);yellow=mat('Warm road paint',(.82,.58,.15));glass=mat('Tower blue silver glazing',(.18,.32,.40),.19,.72);silver=mat('Champagne silver mullions',(.66,.69,.68),.27,.65);roof=mat('Pearl roof cladding',(.72,.72,.66),.38,.25);podglass=mat('Retail blue grey glazing',(.105,.19,.22),.23,.5);soil=mat('Mulch',(.12,.085,.045));grass=mat('Lawn',(.19,.28,.095));wood=mat('Oiled timber',(.25,.12,.045));dark=mat('Graphite metal',(.055,.065,.065),.35,.65)
leaves=[mat('Leaf tone '+str(i),c,.8) for i,c in enumerate([(.14,.25,.065),(.22,.32,.10),(.10,.205,.055),(.29,.36,.12)])]
for o in arch:
 m=glass if 'glazing' in o.name else silver
 if o.name.startswith('podium'):m=podglass if 'glazing' in o.name else roof
 if 'roof' in o.name:m=roof
 o.data.materials.clear();o.data.materials.append(m)
 if 'glazing' in o.name:
  for poly in o.data.polygons:poly.use_smooth=True
# Noise is embedded and requires no image resources.
for m,scale,strength in [(asphalt,80,.12),(paving,5,.1),(stone,4,.08),(grass,3,.22)]:
 n=m.node_tree.nodes;l=m.node_tree.links;t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=scale;b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=.12;l.new(t.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
# Batched solid geometry by material keeps performance practical.
batches={}
def box(name,loc,dim,m):
 key=m.name
 if key not in batches:batches[key]=[[],[],m]
 v,f,_=batches[key];i=len(v);x,y,z=loc;a,b,c=[q/2 for q in dim]
 v.extend([(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
 f.extend([tuple(i+j for j in face) for face in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
def flush():
 for key,(v,f,m) in batches.items():
  mesh=bpy.data.meshes.new(key+' geometry');mesh.from_pydata(v,[],f);mesh.materials.append(m);o=bpy.data.objects.new(key+' | authored context',mesh);s.collection.objects.link(o)
 batches.clear()
def curve(name,pts,r,m):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=r;c.bevel_resolution=2;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);s.collection.objects.link(o);c.materials.append(m);return o
# Site and city on one continuous river bank. Shoreline is 560m from origin.
box('Urban ground',(0,-700,-1),(5200,2520,2),stone)
box('Raffles plaza',(0,0,.10),(222,202,.20),paving)
# Continuous avenues with curbs, lanes and central planted medians.
for y in [-120,140,335,510]:
 box('Avenue',(0,y,.035),(2700,27,.07),asphalt)
 for off in [-17,17]:box('Sidewalk',(0,y+off,.15),(2700,7,.3),paving)
 for off in [-.25,.25]:box('Center stripe',(0,y+off,.09),(2700,.11,.02),yellow)
 for x in range(-1300,1300,13):
  for off in [-8,8]:box('Broken lane stripe',(x,y+off,.09),(6,.14,.02),white)
for x in [-335,-125,125,360,650]:
 box('Street',(x,-300,.045),(22,1600,.09),asphalt)
 for off in [-14,14]:box('Pavement',(x+off,-300,.2),(6,1600,.4),paving)
 for y in range(-1000,490,13):
  if min(abs(y-k) for k in [-120,140,335,510])>18:
   box('Center line',(x,y,.11),(.13,7,.02),yellow)
   for off in [-6,6]:box('Lane dashes',(x+off,y,.11),(.13,5,.02),white)
# Zebra crossings on approaches, preserving traffic directions.
for x in [-335,-125,125,360]:
 for y in [-120,140,335]:
  for side in [-1,1]:
   for t in range(-9,11,3):
    box('Crosswalk',(x+t,y+side*20,.105),(1.35,4,.03),white)
    box('Crosswalk',(x+side*17,y+t,.105),(4,1.35,.03),white)
# Furnished public plaza and garden axis (east of site, toward waterfront).
for x in [-94,-70,-46,-22,2,26,50,74,98]:
 for y in [-94,96]:
  box('Planter',(x,y,.5),(11,4,1),stone);box('Planting soil',(x,y,1.02),(10.5,3.5,.08),soil)
for x in [-70,-30,10,50,90]:
 for y in range(-101,102,8):
  if abs(y)>80:box('Plaza inlay',(x,y,.22),(.14,7,.025),white)
box('Civic garden',(238,322,.1),(202,340,.2),grass)
box('Civic promenade',(240,330,.25),(26,358,.5),paving)
for y in [185,240,295,365,420,470]:
 box('Garden cross path',(238,y,.26),(200,7,.52),paving)
 for x in [170,300]:
  box('Garden beds',(x,y+18,.34),(38,22,.25),soil)
  box('Garden groundcover',(x,y+18,.5),(36,20,.22),grass)
# Shallow rectangular reflecting pools, separate from Qiantang River.
water=mat('Qiantang jade water',(.09,.25,.25),.16,.35)
n=water.node_tree.nodes;l=water.node_tree.links;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=1.7;tex.inputs['Detail'].default_value=3;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.35;bump.inputs['Distance'].default_value=.16;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
for y in [215,395]:
 box('Pool coping',(240,y,.45),(19,36,.4),stone);box('Reflecting pool',(240,y,.67),(16,33,.05),water)
# Bank and stepped waterfront; broad river, never a moat around the project.
box('River',(0,1570,-1.25),(6500,2020,.3),water)
box('Waterfront promenade',(0,548,.2),(5000,24,.4),paving)
for j in range(5):box('River embankment steps',(0,563+j*1.6,-j*.25),(5000,1.6,.6),stone)
box('Far bank',(0,3000,-1),(6000,900,3),grass)
for y in [538,556]:
 curve('River balustrade',[(x,y,1.15) for x in [-2450,2450]],.06,dark)
 for x in range(-2400,2400,12):box('Railing post',(x,y,.65),(.09,.09,1.3),dark)
# Layered architectural context with articulated curtain walls, crowns and podiums.
cityglass=[mat('Context glazing '+str(i),c,.31,.5) for i,c in enumerate([(.26,.34,.36),(.32,.39,.40),(.36,.40,.39),(.20,.29,.33)])]
citystone=[mat('Context stone '+str(i),c,.65) for i,c in enumerate([(.46,.46,.42),(.57,.55,.48),(.38,.41,.41)])]
buildings=[]
def building(x,y,w,d,h):
 m=random.choice(cityglass);st=random.choice(citystone);buildings.append((x,y,w,d,h));box('Building podium',(x,y,3),(w+9,d+9,6),st);box('Office volume',(x,y,h/2+6),(w,d,h),m)
 for z in range(9,int(h)+6,4):
  box('Facade slab',(x,y,z),(w+.15,d+.15,.20),st)
 for xx in range(int(x-w/2)+2,int(x+w/2),5):
  for yy in [y-d/2-.1,y+d/2+.1]:box('Facade mullion',(xx,yy,h/2+6),(.16,.15,h),silver)
 for yy in range(int(y-d/2)+2,int(y+d/2),5):
  for xx in [x-w/2-.1,x+w/2+.1]:box('Facade mullion',(xx,yy,h/2+6),(.15,.16,h),silver)
 box('Parapet',(x,y,h+6.4),(w+.7,d+.7,.8),st);box('Plant room',(x,y,h+8),(w*.40,d*.35,3),dark)
# Avoid towers in immediate front: low street wall there, taller city beyond and flanking.
for x in [-540,-430,-240,455,555,755,860]:
 for y in [-360,-235,25,230,425]:
  h=random.uniform(38,126)
  if y<0:h*=.60
  building(x+random.uniform(-12,12),y,random.uniform(34,56),random.uniform(38,63),h)
for x in [-240,-40,45]:building(x,-235,48,52,random.uniform(15,25))
for x in [-240,-45,50]:building(x,235,45,52,random.uniform(45,88))
for x in range(-1500,1800,100):building(x,2830+random.uniform(0,160),random.uniform(38,65),55,random.uniform(40,155))
# Reusable broadleaf geometry with clustered, irregular canopies.
def ico_mesh():
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);o=bpy.context.object;me=o.data.copy();bpy.data.objects.remove(o,do_unlink=True)
 for v in me.vertices:v.co*=random.uniform(.83,1.16)
 for f in me.polygons:f.use_smooth=True
 return me
canopies=[]
for m in leaves:
 me=ico_mesh();me.materials.append(m);canopies.append(me)
def tree(x,y,size=1):
 box('Tree trunk',(x,y,2.5*size),(.35*size,.35*size,5*size),wood)
 for k in range(5):
  a=k*2.4;me=canopies[random.randrange(4)];o=bpy.data.objects.new('Broadleaf canopy',me);s.collection.objects.link(o);o.location=(x+math.cos(a)*1.4*size,y+math.sin(a)*1.4*size,(4.8+random.random()*1.3)*size);o.scale=(2.1*size,2.1*size,2.6*size);o.rotation_euler.z=random.random()*6.28
for x in range(-104,105,16):
 for y in [-94,96]:tree(x,y,random.uniform(.8,1.1))
for y in range(-90,90,18):
 for x in [-107,107]:tree(x,y,.9)
for y in range(170,500,22):
 for x in [145,211,269,331]:tree(x,y,random.uniform(.9,1.35))
for x in range(-880,1000,22):
 for y in [529,552]:tree(x,y,random.uniform(.85,1.25))
for x in [-350,-320,345,375,-140]:
 for y in range(-500,490,28):
  if min(abs(y-k) for k in [-120,140,335,510])>23:tree(x,y,random.uniform(.8,1.1))
# Human-scale furnishings, lamps, benches, bollards and small vehicles.
for y in [-98,99,544]:
 for x in range(-100,101,20):
  box('Bench seat',(x,y,.6),(3,.6,.17),wood)
  for xx in [x-1,x+1]:box('Bench support',(xx,y,.3),(.12,.5,.6),dark)
for x in [-105,105]:
 for y in range(-86,90,7):box('Bollard',(x,y,.48),(.14,.14,.95),dark)
for y in [-103,123,493]:
 for x in range(-500,650,42):
  box('Lamp pole',(x,y,4.7),(.15,.15,9.4),dark);box('Lamp arm',(x+1,y,9.3),(2.2,.12,.12),dark);box('Lamp head',(x+2,y,9.2),(.8,.38,.14),silver)
carcols=[mat('Vehicle '+str(i),c,.25,.4) for i,c in enumerate([(.6,.63,.60),(.05,.10,.14),(.35,.06,.04),(.7,.69,.6),(.02,.14,.20)])]
for i in range(70):
 y=random.choice([-120,140,335,510])+random.choice([-10,-4,4,10]);x=random.uniform(-600,650)
 if min(abs(x-k) for k in [-335,-125,125,360])<22:continue
 m=random.choice(carcols);box('Car body',(x,y,.75),(4.4,1.85,1.05),m);box('Car cabin',(x-.15,y,1.4),(2.3,1.68,.65),podglass)
 for dx in [-1.35,1.35]:
  for dy in [-.92,.92]:box('Vehicle tyre',(x+dx,y+dy,.42),(.64,.16,.65),dark)
# Pedestrians use non-identifiable generic procedural silhouettes.
skin=mat('Pedestrian neutral',(.45,.28,.16));shirts=[mat('Clothing '+str(i),c) for i,c in enumerate([(.10,.19,.25),(.55,.24,.12),(.72,.69,.57),(.22,.30,.22)])]
head=ico_mesh();head.materials.append(skin)
for i in range(100):
 if i<55:x=random.uniform(-99,99);y=random.choice([-88,89])+random.uniform(-3,3)
 else:x=random.choice([228,252])+random.uniform(-3,3);y=random.uniform(165,490)
 box('Pedestrian body',(x,y,1.05),(.40,.24,.65),random.choice(shirts))
 for dx in [-.12,.12]:box('Pedestrian leg',(x+dx,y,.45),(.13,.14,.65),dark)
 o=bpy.data.objects.new('Pedestrian head',head);s.collection.objects.link(o);o.location=(x,y,1.55);o.scale=(.16,.15,.19)
flush()
# Restrained site typography, original geometry not a branding assertion.
def text_obj(body,loc,size,rot):
 c=bpy.data.curves.new(body,'FONT');c.body=body;c.size=size;c.extrude=.015;c.align_x='CENTER';o=bpy.data.objects.new(body,c);s.collection.objects.link(o);o.location=loc;o.rotation_euler=rot;c.materials.append(silver)
text_obj('RAFFLES CITY',(0,-78.2,8.6),2.0,(math.pi/2,0,0))
# Daylight and cinematic views.
world=bpy.data.worlds.new('Clear warm daylight');s.world=world;world.use_nodes=True;n=world.node_tree.nodes;n.clear();sky=n.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=math.radians(31);sky.sun_rotation=math.radians(215);sky.altitude=.1;sky.air_density=1.15;sky.dust_density=.6;bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.45;out=n.new('ShaderNodeOutputWorld');world.node_tree.links.new(sky.outputs['Color'],bg.inputs['Color']);world.node_tree.links.new(bg.outputs[0],out.inputs[0])
def camera(name,pos,target,lens):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=12000;return o
cams=[camera('01 HERO | city to river',(420,-570,355),(15,72,99),47),camera('02 STREET | arrival',(245,-330,26),(0,0,112),28),camera('03 RIVER | promenade to skyline',(440,690,130),(-5,15,100),53)]
# Editable 10-second aerial camera move, no expensive animation render needed.
fly=camera('04 ANIMATION | 250 frame orbit',(420,-570,355),(0,0,110),47)
for fr,pos,target in [(1,(460,-610,340),(0,35,110)),(125,(410,-420,285),(0,35,115)),(250,(360,-260,215),(0,35,120))]:
 fly.location=pos;fly.rotation_euler=(Vector(target)-fly.location).to_track_quat('-Z','Y').to_euler();fly.keyframe_insert('location',frame=fr);fly.keyframe_insert('rotation_euler',frame=fr)
s.frame_end=250;s.render.fps=25;s.frame_set(1)
s.render.engine='CYCLES';s.cycles.samples=24 if args.preview else 64;s.cycles.use_denoising=False;s.cycles.max_bounces=6;s.cycles.transparent_max_bounces=4;s.render.resolution_x=1920;s.render.resolution_y=1440;s.render.resolution_percentage=45 if args.preview else 100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.25
s.camera=cams[0];s['Context disclaimer']='Architectural visualization. Existing tower and podium meshes preserved; streets, landscape, skyline and river alignment are inferred presentation context, not survey data.';s['River shoreline setback_m']=560
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hangzhou-Raffles-Environment.blend'));bpy.ops.file.pack_all()
qa={'architecture_objects':len(arch),'geometry_before':original_fingerprint,'geometry_after':fingerprint(arch),'unchanged_geometry':original_fingerprint==fingerprint(arch),'objects':len(bpy.data.objects),'meshes':len(bpy.data.meshes),'missing_images':[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()],'context_buildings':len(buildings),'river_setback_m':560,'cameras':[c.name for c in cams],'disclaimer':s['Context disclaimer']}
(OUT/'geometry-material-QA.json').write_text(json.dumps(qa,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hangzhou-Raffles-Environment.blend'))
for i,c in enumerate(cams[:1] if args.preview else cams):
 s.camera=c;s.render.filepath=str(OUT/('preview-hero.png' if args.preview else ['01-hero-aerial.png','02-street-arrival.png','03-river-promenade.png'][i]));bpy.ops.render.render(write_still=True)
print('DELIVERY COMPLETE',OUT,flush=True)
