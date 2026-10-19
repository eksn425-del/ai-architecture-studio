import bpy,json,hashlib,math,sys
from pathlib import Path
root=Path(__file__).parent
source=root/'R3-final-Hangzhou-Raffles.blend'
def geom():
 d={}
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith(('tower_','podium_')):
   x={'matrix':[list(row) for row in o.matrix_world],'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]}
   d[o.name]=hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
 return d
bpy.ops.wm.open_mainfile(filepath=str(source));old=geom()
bpy.ops.wm.open_mainfile(filepath=str(root/'Hangzhou-Raffles-Environment-Final.blend'));new=geom();s=bpy.context.scene
missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
q={'blender_version':bpy.app.version_string,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_architecture_mesh_count':len(old),'final_architecture_mesh_count':len(new),'architecture_geometry_and_world_transform_identical':old==new,'all_objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA'],'external_image_dependencies':missing,'image_datablocks':[im.name for im in bpy.data.images],'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'render_engine':s.render.engine,'samples':s.cycles.samples,'denoising':s.cycles.use_denoising,'animation':[s.frame_start,s.frame_end,s.render.fps],'riverward_axis':'+Y artistic local axis, not true north','river_setback_metres':560,'publication_excludes':['user reference photograph','private account data','old product traces'],'status':'PASS' if old==new and not missing and s.render.resolution_percentage==100 else 'FAIL'}
(root/'QA_FINAL.json').write_text(json.dumps(q,indent=2));print(json.dumps(q,indent=2))
