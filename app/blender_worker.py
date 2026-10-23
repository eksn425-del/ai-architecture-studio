"""Trusted Blender entrypoint. Declarative geometry only, never supplied source code."""
import bpy
import json
import sys
import math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_views import fitted_axis_camera
args=sys.argv[sys.argv.index('--')+1:]
def snapshot():
    return {o.name:{'location':list(o.location),'dimensions':list(o.dimensions),'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'material':[{'color':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'transmission':m.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value} for m in o.data.materials]} for o in bpy.data.objects if o.type=='MESH'}
if args[0]=='inspect':
    Path(args[1]).write_text(json.dumps(snapshot(),sort_keys=True))
elif args[0]=='render':
    scene=bpy.context.scene
    options=json.loads(args[3]) if len(args)>3 else {}
    # Bound resources again at the trusted worker boundary, including direct invocations.
    resolution=options.get('resolution',800)
    if type(resolution) is not int or not 800<=resolution<=1600:raise ValueError('Resolution must be an integer from 800 to 1600')
    if 'denoise' in options and type(options['denoise']) is not bool:raise ValueError('Denoise must be a boolean')
    for name in options.get("hide_ids",[]):bpy.data.objects[name].hide_render=True
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=128;scene.cycles.use_denoising=False
    scene.render.resolution_x=resolution;scene.render.resolution_y=resolution;scene.render.resolution_percentage=100
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(0.82,0.82,0.82,1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0.8
    scene.view_settings.exposure=0.6
    area_data=bpy.data.lights.new('ReviewFill','AREA');area_data.energy=1600;area_data.shape='DISK';area_data.size=8
    area=bpy.data.objects.new('ReviewFill',area_data);scene.collection.objects.link(area);area.location=(1,-8,12)
    area.rotation_euler=(Vector((0,0,3))-area.location).to_track_quat('-Z','Y').to_euler()
    camera_data=bpy.data.cameras.new('ReviewCamera');camera=bpy.data.objects.new('ReviewCamera',camera_data);scene.collection.objects.link(camera)
    points=[o.matrix_world @ Vector(corner) for o in scene.objects if o.type=='MESH' for corner in o.bound_box]
    if not points:raise ValueError('No mesh geometry')
    bounds=[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(3)]
    position,target,scale,clip=fitted_axis_camera(args[2],bounds)
    camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=scale;camera_data.clip_end=clip;scene.camera=camera
    if options.get('camera'):
        config=options['camera'];camera.location=config['position'];camera.rotation_euler=(Vector(config['target'])-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='PERSP';camera_data.lens=config['lens'];camera_data.clip_start=.02;camera_data.clip_end=max(1000,(Vector(config['target'])-camera.location).length+2*max(b-a for a,b in bounds))
        scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False));scene.cycles.samples=256;area.location=camera.location;area.rotation_euler=camera.rotation_euler;area_data.energy=140;area_data.size=3
    # Omission preserves each view's historical default; explicit true may fail if
    # the installed Cycles build lacks a denoiser, rather than silently downgrade.
    if 'denoise' in options:scene.cycles.use_denoising=options['denoise']
    light_data=bpy.data.lights.new('ReviewSun','SUN');light_data.energy=3
    light=bpy.data.objects.new('ReviewSun',light_data);scene.collection.objects.link(light);light.rotation_euler=(0.5,-0.4,-0.5)
    scene.render.image_settings.file_format='PNG';scene.render.filepath=args[1]
    bpy.ops.render.render(write_still=True)
    if len(args)>4:
        Path(args[4]).write_text(json.dumps({'resolution':scene.render.resolution_x,'denoise':scene.cycles.use_denoising,'samples':scene.cycles.samples}),encoding='utf-8')
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
