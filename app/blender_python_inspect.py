"""Trusted Blender data collector; never execute project scripts in this process."""
import hashlib
import json
from pathlib import Path
import sys
import bpy


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def vector(value):
    return [float(x) for x in value]


def properties(rna):
    result = {}
    for prop in rna.bl_rna.properties:
        key = prop.identifier
        if key in {'rna_type', 'name', 'session_uid', 'users', 'is_updated', 'is_updated_data', 'is_runtime_data'} or prop.type in {'COLLECTION'}:
            continue
        value = getattr(rna, key, None)
        if prop.type == 'POINTER':
            result[key] = getattr(value, 'name', None)
        elif getattr(prop, "is_array", False):
            result[key] = list(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = value
    return result


def material(mat):
    if mat is None:return None
    result = {'name':mat.name, 'properties':properties(mat)}
    if mat.use_nodes and mat.node_tree:
        result['nodes'] = sorted([
            {'name':n.name, 'type':n.bl_idname, 'properties':properties(n),
             'inputs':[[s.identifier, list(s.default_value) if hasattr(s.default_value, '__len__') and not isinstance(s.default_value,str) else s.default_value]
                       for s in n.inputs if hasattr(s,'default_value') and not isinstance(s.default_value,bpy.types.ID)]}
            for n in mat.node_tree.nodes], key=lambda n:n['name'])
        result['links'] = sorted([l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in mat.node_tree.links)
    return result


def inspect():
    if bpy.data.libraries:raise ValueError('Linked libraries are outside the candidate contract')
    if any(i.source not in {'GENERATED','VIEWER'} and not i.packed_file for i in bpy.data.images):
        raise ValueError('Candidate textures must be packed; external file reads are not accepted')
    if bpy.data.texts or bpy.data.sounds:raise ValueError('Embedded scripts/sounds are not accepted in this candidate')
    if any(x.animation_data for x in [*bpy.data.objects,*bpy.data.scenes,*bpy.data.materials]):
        raise ValueError('Animation/drivers require a separate validated contract')
    graph=bpy.context.evaluated_depsgraph_get()
    result={}
    for obj in bpy.data.objects:
        if obj.type not in {'MESH','CURVE','EMPTY','CAMERA','LIGHT'}:raise ValueError('Unsupported data type: '+obj.type)
        entry={'type':obj.type,'matrix':list(sum((vector(v) for v in obj.matrix_world),[])),
            'parent':obj.parent.name if obj.parent else None,
            'hide_render':obj.hide_render,'hide_viewport':obj.hide_viewport,
            'materials':[material(m) for m in obj.data.materials] if hasattr(obj.data,'materials') else [],
            'modifiers':[properties(m) for m in obj.modifiers]}
        if obj.type in {'MESH','CURVE'}:
            evaluated=obj.evaluated_get(graph); mesh=evaluated.to_mesh()
            try:
                if len(mesh.vertices)>500000:raise ValueError('Candidate mesh exceeds the local limit')
                entry['mesh']={'vertices':[vector(v.co) for v in mesh.vertices],
                    'polygons':[[list(p.vertices),p.material_index,p.use_smooth] for p in mesh.polygons]}
            finally:evaluated.to_mesh_clear()
        elif obj.data:entry['data']=properties(obj.data)
        result[obj.name]={'sha256':digest(entry),'type':obj.type,'dimensions':vector(obj.dimensions)}
    return {'objects':result,'world':material(bpy.context.scene.world) if bpy.context.scene.world else None}


args=sys.argv[sys.argv.index('--')+1:]
if args[0]=='bootstrap':
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.context.scene['kstudio_project']=args[2]
    bpy.ops.wm.save_as_mainfile(filepath=args[1])
elif args[0]=='inspect':
    bpy.ops.wm.open_mainfile(filepath=args[1],load_ui=False,use_scripts=False)
    Path(args[2]).write_text(json.dumps(inspect(),sort_keys=True,allow_nan=False),encoding='utf-8')
elif args[0]=='render':
    bpy.ops.wm.open_mainfile(filepath=args[1],load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    if scene.camera is None:raise ValueError('Candidate has no source-matched camera')
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False
    scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.filepath=args[2];scene.render.image_settings.file_format='PNG'
    bpy.ops.render.render(write_still=True)
else:raise ValueError('Unknown trusted operation')
