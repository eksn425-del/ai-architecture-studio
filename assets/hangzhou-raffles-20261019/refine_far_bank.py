"""Approximate layered Qiantang opposite-bank urban scenery, not mapped buildings."""
import bpy,math,random
s=bpy.context.scene;random.seed(301)
for ob in list(bpy.data.objects):
 if ob.name.startswith('Opposite bank |'):bpy.data.objects.remove(ob,do_unlink=True)
fbatches={}
def fcube(name,loc,scale,mat):
 key=mat.name
 if key not in fbatches:fbatches[key]=[[],[],mat]
 vs,fs,_=fbatches[key];n=len(vs);x,y,z=loc;a,b,c=[q/2 for q in scale]
 vs.extend([(x+u*a,y+v*b,z+w*c) for u,v,w in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
 fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
stone=bpy.data.materials['Warm limestone'];grass=bpy.data.materials['Lawn'];paving=bpy.data.materials['Silver granite paving'];asphalt=bpy.data.materials['Fine asphalt'];paint=bpy.data.materials['Ivory road paint'];dark=bpy.data.materials['Graphite metal']
# A continuous landscaped bank, promenade and three parallel urban roads.
fcube('riverfront park',(0,2622,.6),(5200,74,1.2),grass)
fcube('promenade',(0,2585,.75),(5200,18,1.5),paving)
for yy in [2690,3090,3460]:
 fcube('avenue',(0,yy,.50),(5200,28,1),asphalt)
 for off in [-20,20]:fcube('sidewalk',(0,yy+off,.6),(5200,9,1.2),paving)
 for x in range(-2500,2500,30):
  for off in [-7,7]:fcube('lane markings',(x,yy+off,1.02),(13,.20,.03),paint)
for xx in range(-2200,2400,440):fcube('cross street',(xx,3125,.55),(22,1100,1.1),asphalt)
# Two varied-depth back rows make the distant skyline read as a district, not a fence.
for row,yy in enumerate([3210,3620]):
 for x in range(-2300,2400,135):
  if random.random()<.13:continue
  xx=x+random.uniform(-20,20);y=yy+random.uniform(-35,35);w=random.uniform(40,78);d=random.uniform(45,90);h=random.uniform(65,195)
  ma=bpy.data.materials['Context glazing '+str(random.randrange(4))]
  fcube('office/residential body',(xx,y,h/2+1),(w,d,h),ma)
  fcube('podium',(xx,y,5),(w+16,d+13,10),stone)
  if random.random()<.6:fcube('stepped crown',(xx,y,h+5),(w*.65,d*.65,10),ma)
  for z in range(12,int(h),10):fcube('horizontal facade band',(xx,y,z),(w+.3,d+.3,.32),stone)
# Copy only authored procedural tree meshes; no downloaded planting assets.
leafsource=next(o for o in bpy.data.objects if o.name.startswith('Broadleaf canopy') and o.type=='MESH')
for yy in [2609,2648,2717]:
 for xx in range(-2450,2500,27):
  h=random.uniform(7,11);fcube('tree trunk',(xx,yy,h/2),(.5,.5,h),dark)
  o=bpy.data.objects.new('Opposite bank | riverside tree',leafsource.data);s.collection.objects.link(o);o.location=(xx,yy,h);o.scale=(3.5,3.5,4.6);o.rotation_euler.z=random.random()*6.28
for name,(vs,fs,ma) in fbatches.items():
 me=bpy.data.meshes.new(name+' far bank');me.from_pydata(vs,[],fs);me.materials.append(ma);ob=bpy.data.objects.new('Opposite bank | '+name,me);s.collection.objects.link(ob)
s['Opposite bank refinement']='Qiantang/Binjiang and Qianjiang Century City landscape reference; roads, planting and varied skyline are schematic and not GIS positioned.'
print('OPPOSITE_BANK_REFINED',flush=True)
