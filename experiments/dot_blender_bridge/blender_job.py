"""Native atomic backend. No arbitrary Python/Ruby input accepted."""
import bpy, json, sys, hashlib, uuid
from pathlib import Path
from mathutils import Vector
job_path=Path(sys.argv[sys.argv.index('--')+1]);j=json.loads(job_path.read_text());root=job_path.parent
scene_file=root/'scene.blend'
if scene_file.exists(): bpy.ops.wm.open_mainfile(filepath=str(scene_file))
else:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
method,a=j['method'],j['arguments']
def snapshot():
    bpy.context.view_layer.update();result=[]
    for o in sorted(bpy.data.objects,key=lambda o:o.name):
        if o.type!='MESH': continue
        result.append({'name':o.name,'id':o.get('dot_id','legacy-'+o.name),'dimensions':list(o.dimensions),'location':list(o.location),'matrix':[list(row) for row in o.matrix_world],'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'materials':[m.name if m else None for m in o.data.materials]})
    return result
def digest(data): return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
before=snapshot();before_hash=digest(before);targets=set();revision=int(bpy.context.scene.get('dot_revision',0));mutating=False
if method in ('blender_create_box','blender_create_assembly','blender_edit_parts'):
    parts=[a] if method=='blender_create_box' else a['parts'];targets={p['name'] for p in parts}
    if method!='blender_create_box':
        expected=a['expected_geometry_sha256']
        if expected!=before_hash and not (not before and expected==''): raise ValueError('Stale geometry digest')
    for part in parts:
        o=bpy.data.objects.get(part['name'])
        if method=='blender_edit_parts':
            if o is None or o.type!='MESH' or not o.get('dot_owned'): raise ValueError('Edit target absent or not owned')
            o.location=part['location'];o.dimensions=part['dimensions'];bpy.context.view_layer.objects.active=o
            bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        else:
            if o is not None: raise ValueError('Duplicate name')
            bpy.ops.mesh.primitive_cube_add(size=1,location=part['location']);o=bpy.context.object;o.name=part['name'];o.dimensions=part['dimensions'];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            o['dot_id']=str(uuid.uuid4());o['dot_owned']=True
    after=snapshot();protected_before=[x for x in before if x['name'] not in targets];protected_after=[x for x in after if x['name'] not in targets]
    if protected_before!=protected_after: raise ValueError('KEEP violation: no commit')
    if method=='blender_edit_parts':
        old={x['name']:x['id'] for x in before};new={x['name']:x['id'] for x in after}
        if old!=new: raise ValueError('Object identity changed')
    revision+=1;bpy.context.scene['dot_revision']=revision;mutating=True
views=[]
if method in ('blender_render','blender_render_views'):
    scene=bpy.context.scene
    if not scene.camera:
        bpy.ops.object.camera_add();scene.camera=bpy.context.object
        bpy.ops.object.light_add(type='AREA',location=(1,-4,9));bpy.context.object.data.energy=1800;bpy.context.object.data.size=8
    camera=scene.camera;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.device='CPU';scene.cycles.use_denoising=False
    scene.render.resolution_x=480;scene.render.resolution_y=360;scene.render.resolution_percentage=100
    cameras={'front':(0,-14,2),'rear':(0,14,2),'left':(-14,0,2),'right':(14,0,2),'roof':(0,0,16),'oblique':(10,-13,9)}
    for name,eye in cameras.items():
        if method=='blender_render' and name!='oblique':continue
        camera.location=eye;camera.rotation_euler=(Vector((0,0,1.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=12
        path=root/('preview.png' if method=='blender_render' else name+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        views.append({'name':name,'eye':list(eye),'target':[0,0,1.5],'orthographic_scale':12,'file':str(path)})
    if snapshot()!=before: raise ValueError('Render changed mesh geometry')
    mutating=True
meshes=snapshot()
if mutating: bpy.ops.wm.save_as_mainfile(filepath=str(root/'candidate.blend'))
result={'blender':bpy.app.version_string,'meshes':meshes,'geometry_sha256':digest(meshes),'before_geometry_sha256':before_hash,'revision':revision,'keep_verified':True,'protected_names':[m['name'] for m in before if m['name'] not in targets],'blend_file':str(scene_file),'render_file':str(root/'preview.png') if (root/'preview.png').exists() else None,'views':views}
(root/'job_result.json').write_text(json.dumps(result,indent=2))
