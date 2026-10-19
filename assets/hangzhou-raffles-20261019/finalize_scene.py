"""Polish, render, and save a self-contained presentation scene. No external assets."""
import bpy, math, json, sys, argparse, random
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=Path(__file__).parent;s=bpy.context.scene
s.view_settings.exposure=-2.1;s.cycles.use_denoising=False;s.cycles.samples=64 if a.preview else 256
s.cycles.adaptive_threshold=.03;s.render.resolution_percentage=40 if a.preview else 100
# Reuse authored material-only resources; no external image references.
green=bpy.data.materials.get('Lawn');path=bpy.data.materials.get('Silver granite paving')
def cube(name,loc,scale,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat);return o
# Continuous landscaped buffer, small campus greens and forecourt details.
for x,y,w,d in [(-240,-360,130,96),(-240,25,136,155),(455,25,150,150),(-240,425,130,120),(455,425,150,125),(-40,-235,80,65),(45,-235,65,65)]:
 cube('Urban planted parcel',(x,y,.20),(w,d,.12),green)
 # Architectural podiums rise above this groundcover. An axial path keeps entrances clear.
 cube('Parcel walking connection',(x,y,.29),(6,d,.10),path)
for x in [-88,88]:
 for y in range(-65,70,16):cube('Site green verge',(x,y,.32),(5,11,.12),green)
# Broader context surfaces remove abrupt model edges in wide camera views.
cube('Distant urban terrain',(0,-5500,-2),(20000,12110,1),bpy.data.materials.get('Warm limestone'))
cube('Distant opposite bank',(0,8000,-2),(20000,10840,1),green)
# Park / campus parcels complete the otherwise empty large urban blocks.
for x,y,w,d in [(235,-235,195,160),(235,30,195,150),(-40,420,175,120),(-40,235,175,140),(-430,425,150,120),(560,230,150,150)]:
 cube('Inferred park ground',(x,y,.18),(w,d,.12),green)
 cube('Park pedestrian axis',(x,y,.28),(8,d,.10),path)
 cube('Park crosswalk',(x,y,.28),(w,5,.10),path)
# A few colored city blocks establish neutral, non-identifiable infill.
# Distant urban massing fills the inland horizon; approximate, not surveyed.
random.seed(104)
citymat=bpy.data.materials.get('Context glazing 1')
for row,y in enumerate([-650,-850,-1080,-1320,-1600,-1900]):
 for x in range(-1500,1550,110):
  xx=x+random.uniform(-20,20); yy=y+random.uniform(-22,22); h=random.uniform(35,120)
  cube('Distant city silhouette',(xx,yy,h/2),(random.uniform(40,65),random.uniform(45,80),h),citymat)
# Strip unused image datablocks so no private source photograph is distributed.
for im in list(bpy.data.images):
 if im.users==0:bpy.data.images.remove(im)
# Reproducible native cameras; separate curated views.
cameras=[bpy.data.objects[n] for n in ['01 HERO | city to river','02 STREET | arrival','03 RIVER | promenade to skyline']]
cameras[2].location=(-500,1400,320); cameras[2].rotation_euler=(Vector((0,180,80))-cameras[2].location).to_track_quat('-Z','Y').to_euler(); cameras[2].data.lens=45
s.camera=cameras[0];s.frame_set(1);s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s['Presentation purpose']='Promotional architectural visualization; inferred city context, not georeferenced survey or K Studio user-flow benchmark.'
s['Coordinate convention']='Local scene coordinates only. +Y is artistically assigned riverward; not surveyed true north.'
s['Source architecture']='R3-final-Hangzhou-Raffles.blend, SHA256 2b4748ab881a5fe45efa814ad1e24a80ccaf3f72f474e0bd9ceeea6473eb6fc8'
exec(compile((out/'refine_atrium.py').read_text(),str(out/'refine_atrium.py'),'exec'), {'__name__':'__main__','__file__':str(out/'refine_atrium.py')})
exec(compile((out/'refine_far_bank.py').read_text(),str(out/'refine_far_bank.py'),'exec'), {'__name__':'__main__','__file__':str(out/'refine_far_bank.py')})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'Hangzhou-Raffles-Environment-Final.blend'),compress=True)
for i,c in enumerate(cameras):
 s.camera=c;s.render.filepath=str(out/(('preview-' if a.preview else '')+['01-hero-aerial.png','02-street-arrival.png','03-river-promenade.png'][i]));bpy.ops.render.render(write_still=True)
s.camera=cameras[0]
print('FINAL_RENDERS_COMPLETE',flush=True)
