"""Trusted Blender entrypoint. Declarative geometry only, never supplied source code."""
import bpy
import json
import sys
import math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
def snapshot():
    return {o.name:{'location':list(o.location),'dimensions':list(o.dimensions),'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'material':[{'color':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'transmission':m.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value} for m in o.data.materials]} for o in bpy.data.objects if o.type=='MESH'}
if args[0]=='inspect':
    Path(args[1]).write_text(json.dumps(snapshot(),sort_keys=True))
elif args[0]=='render':
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False
    scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(0.82,0.82,0.82,1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0.8
    scene.view_settings.exposure=0.6
    area_data=bpy.data.lights.new('ReviewFill','AREA');area_data.energy=1600;area_data.shape='DISK';area_data.size=8
    area=bpy.data.objects.new('ReviewFill',area_data);scene.collection.objects.link(area);area.location=(1,-8,12)
    area.rotation_euler=(Vector((0,0,3))-area.location).to_track_quat('-Z','Y').to_euler()
    camera_data=bpy.data.cameras.new('ReviewCamera');camera=bpy.data.objects.new('ReviewCamera',camera_data);scene.collection.objects.link(camera)
    camera.location=(17,-23,18) if args[2]=='front' else (-17,23,18)
    camera.rotation_euler=(Vector((0,0,2.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=21;scene.camera=camera
    light_data=bpy.data.lights.new('ReviewSun','SUN');light_data.energy=3
    light=bpy.data.objects.new('ReviewSun',light_data);scene.collection.objects.link(light);light.rotation_euler=(0.5,-0.4,-0.5)
    scene.render.image_settings.file_format='PNG';scene.render.filepath=args[1]
    bpy.ops.render.render(write_still=True)
else:
    spec,output,receipt=map(Path,args)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for name,obj in json.loads(spec.read_text()).items():
        if 'dimensions' in obj:
            bpy.ops.mesh.primitive_cube_add(size=1,location=obj['location'])
            item=bpy.context.object;item.name=name;item.dimensions=obj['dimensions']
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        else:
            mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(obj['vertices'],[],obj['faces']);mesh.update()
            item=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(item);item.location=obj['location']
        if obj.get('material'):
            specmat=obj['material'];mat=bpy.data.materials.new(name+'Material');mat.diffuse_color=specmat.get('color',[0.7,0.7,0.7,1]);mat.use_nodes=True
            bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=mat.diffuse_color
            bsdf.inputs['Roughness'].default_value=specmat.get('roughness',0.5);bsdf.inputs['Transmission Weight'].default_value=specmat.get('transmission',0)
            item.data.materials.append(mat)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.ops.wm.save_as_mainfile(filepath=str(output));receipt.write_text(json.dumps(snapshot(),sort_keys=True))
