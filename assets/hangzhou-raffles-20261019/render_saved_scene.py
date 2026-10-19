"""Render packaged scene cameras with Blender 4.3+. No network or external assets."""
import bpy
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;out=Path(bpy.data.filepath).parent
s.render.engine='CYCLES';s.cycles.use_denoising=False;s.cycles.samples=256;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
name='05 ATRIUM | glazed roof detail'
c=bpy.data.objects.get(name)
if not c:
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);s.collection.objects.link(c)
c.location=(76,-110,120);c.rotation_euler=(Vector((-8,0,35))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=52;c.data.clip_end=12000
s.camera=bpy.data.objects['01 HERO | city to river']
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
for name,filename in [('01 HERO | city to river','01-hero-aerial.png'),('02 STREET | arrival','02-street-arrival.png'),('03 RIVER | promenade to skyline','03-river-promenade.png'),('05 ATRIUM | glazed roof detail','04-atrium-skylight.png')]:
 s.camera=bpy.data.objects[name];s.render.filepath=str(out/filename);bpy.ops.render.render(write_still=True)
print('FINAL_RENDERS_COMPLETE',flush=True)
