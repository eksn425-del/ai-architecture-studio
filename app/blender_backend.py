"""Opt-in, project-owned Blender backend. No model-supplied Python is executed."""
from __future__ import annotations
import hashlib
import json
import math
import re
import shutil
import subprocess
import threading
import uuid
from pathlib import Path
from .blender_views import REVIEW_CAMERAS

_LOCK = threading.Lock()
_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')

def enabled(project_dir: Path) -> bool:
    marker = project_dir / 'state/modeling_backend.json'
    return marker.is_file() and json.loads(marker.read_text(encoding="utf-8")).get('backend') == 'blender'

class BlenderBackend:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.root = self.project_dir / 'runtime/blender'
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.resolve() != self.root or self.root.is_symlink():
            raise ValueError('Blender workspace must not be a symlink')
        self.state = self.root / 'scene.json'
        self.executable = shutil.which('blender')
        if not self.executable:
            raise ValueError('Blender executable unavailable')

    def install_edit_contract(self, *, allowed_ids, keep_ids, expected_revision):
        """Host-only explicit scope binding; never exposed in tools()."""
        from .blender_edit_contract import install
        with _LOCK:
            scene = json.loads(self.state.read_text(encoding="utf-8")) if self.state.exists() else {"objects": {}, "revision": 0}
            return install(self.project_dir, scene, allowed_ids=allowed_ids,
                           keep_ids=keep_ids, expected_revision=expected_revision)

    def tools(self):
        number={'type':'number'}
        vector={'type':'array','items':number,'minItems':3,'maxItems':3}
        obj={'type':'object','required':['id','location'],'properties':{'id':{'type':'string','pattern':_NAME.pattern},'location':vector,'dimensions':vector,'vertices':{'type':'array','items':vector,'minItems':3,'maxItems':256},'faces':{'type':'array','items':{'type':'array','items':{'type':'integer'},'minItems':3,'maxItems':64},'maxItems':512},'material':{'type':'object','properties':{'color':{'type':'array','items':number,'minItems':4,'maxItems':4},'roughness':number,'transmission':number},'additionalProperties':False}},'additionalProperties':False}
        return [dict(name='blender_audit_connections',description='Read-only declared connections: connections[{a:existingID,b:existingID,axis:0|1|2,tolerance:metres0..0.1}]. Compare A max bound to B min bound; signed gap, positive AABB overlap and perpendicular alignment. Exact for boxes, conservative for meshes. Contact is not automatically a defect.',inputSchema={'type':'object','required':['connections'],'properties':{'connections':{'type':'array','minItems':1,'maxItems':64,'items':{'type':'object'}}},'additionalProperties':False}),dict(name='blender_prepare_component',description='Prepare bounded parameterized window_wall,sloped_closure,leaf_rosette,floor_opening,furniture,u_staircase geometry. All lengths metres. Parameters: window_wall(name,start,end,plane,thickness,base,height,openings[max8 [horizontal_start,horizontal_end,zbottom,ztop]],wall_material,glass_material,frame_material,axis=0(X) or1(Y)); sloped_closure(name,x0,x1,y0,y1,bottom,top0,top1,material); leaf_rosette(name,location,radius=.3,height=.65,seed=0,material); floor_opening(name,x0,x1,y0,y1,bottom,thickness,opening[x0,x1,y0,y1],material); furniture(name,location,width,depth,height,kind[sofa|bed|table|chair|cabinet|desk],material,quarter_turns=0); u_staircase(name,location,width,depth,height,step_count=18,landing_depth=1,gap=.1,material). Stair/furniture location Z is floor/base; XY centered. Materials use color RGBA,roughness,transmission in0..1. Explicit previous_ids ownership receipt required (empty for new); returns patch,component_ids,writes_performed=0,quality_status=unverified. Preparation is read-only; apply returned patch through blender_apply_objects. Furniture location Z is floor, quarter_turns0..3; interior/hidden design is inferred.',inputSchema={'type':'object','required':['kind','parameters','previous_ids'],'properties':{'kind':{'type':'string','enum':['window_wall','sloped_closure','leaf_rosette','floor_opening','furniture','u_staircase']},'parameters':{'type':'object'},'previous_ids':{'type':'array','items':{'type':'string'},'maxItems':256}},'additionalProperties':False}),dict(name='blender_audit_clearance',description='Read-only rectangular design clearance checks; zones(name,location,dimensions,ignore_ids). Exact positive-volume box blockers and conservative mesh candidates; not navigation/compliance.',inputSchema={'type':'object','required':['zones'],'properties':{'zones':{'type':'array','minItems':1,'maxItems':32,'items':{'type':'object'}}},'additionalProperties':False}),dict(name='blender_apply_objects',description='Create or update named project-owned boxes or bounded indexed meshes in metres, with simple RGBA/PBR materials. Use dimensions OR vertices+faces. Unmentioned objects preserved. Native save/reopen checked. No arbitrary code.',inputSchema={'type':'object','required':['objects'],'properties':{'objects':{'type':'array','minItems':0,'maxItems':256,'items':obj},'delete_ids':{'type':'array','maxItems':256,'items':{'type':'string','pattern':_NAME.pattern}}},'additionalProperties':False}),dict(name='blender_inspect_scene',description='Read current native geometry receipt. Default API context omits native mesh arrays, not exact authored specs. Retrieve full native arrays using include_geometry_detail=true with 1..8 explicit existing object_ids. No source-fidelity claim.',inputSchema={'type':'object','properties':{'object_ids':{'type':'array','minItems':1,'maxItems':8,'uniqueItems':True,'items':{'type':'string','pattern':_NAME.pattern}},'include_geometry_detail':{'type':'boolean'}},'additionalProperties':False}),dict(name='blender_render_scene',description='CPU render saved model from fitted review views or explicit perspective camera. Optional hide_ids creates labeled render-only cutaway; saved geometry unchanged. Square resolution integer 800..1600 (default 800); optional denoise boolean overrides the existing view default. Unsupported requested denoising fails without committing a new receipt. Appearance review required.',inputSchema={'type':'object','properties':{'view':{'type':'string','enum':list(REVIEW_CAMERAS)},'camera':{'type':'object','required':['position','target','lens'],'properties':{'position':vector,'target':vector,'lens':{'type':'number','minimum':12,'maximum':120}},'additionalProperties':False},'hide_ids':{'type':'array','items':{'type':'string'},'maxItems':256},'resolution':{'type':'integer','minimum':800,'maximum':1600,'default':800},'denoise':{'type':'boolean'}},'additionalProperties':False})]

    def dispatch(self, name, arguments):
        with _LOCK:
            if name == 'blender_audit_connections':
                from .blender_connections import audit_connections
                if set(arguments)!={'connections'}:raise ValueError('Invalid connection arguments')
                current=json.loads(self.state.read_text(encoding="utf-8")) if self.state.exists() else {'objects':{}}
                return audit_connections(current['objects'],arguments['connections'])
            if name == 'blender_prepare_component':
                from .declarative_architecture import window_wall,sloped_closure,leaf_rosette,floor_opening,scoped_replacement_patch
                from .declarative_interior import furniture,u_staircase
                if not isinstance(arguments,dict) or set(arguments)!={'kind','parameters','previous_ids'} or not isinstance(arguments['parameters'],dict):raise ValueError('Invalid component arguments')
                helpers={'window_wall':window_wall,'sloped_closure':sloped_closure,'leaf_rosette':leaf_rosette,'floor_opening':floor_opening,'furniture':furniture,'u_staircase':u_staircase}
                if arguments['kind'] not in helpers:raise ValueError('Invalid component kind')
                generated=helpers[arguments['kind']](**arguments['parameters']);objects=generated['objects'] if arguments['kind']=='u_staircase' else (generated if isinstance(generated,list) else [generated])
                current=json.loads(self.state.read_text(encoding="utf-8")) if self.state.exists() else {'objects':{}}
                patch=scoped_replacement_patch(objects,arguments['previous_ids'],current['objects'])
                return {'patch':patch,'component_ids':[o['id'] for o in objects],'writes_performed':0,'quality_status':'unverified'}
            if name == 'blender_audit_clearance':
                from .blender_clearance import audit_clearance
                if set(arguments)!={'zones'}:raise ValueError('Invalid clearance arguments')
                current=json.loads(self.state.read_text(encoding="utf-8")) if self.state.exists() else {'objects':{}}
                return audit_clearance(current['objects'],arguments['zones'])
            if name == 'blender_inspect_scene':
                from .blender_wire_context import inspect_scene_selection
                from .blender_api_readback import _owned_file
                if self.state.exists() or self.state.is_symlink():
                    state = _owned_file(self.project_dir, 'runtime/blender/scene.json')
                    scene = json.loads(state.read_text(encoding='utf-8'))
                else:
                    scene = {'objects':{}, 'revision':0}
                return inspect_scene_selection(scene, arguments)
            if name == 'blender_render_scene':
                from .blender_render_options import render_cache_key,validate_render_options
                current=json.loads(self.state.read_text(encoding="utf-8"))
                options=validate_render_options(arguments,current['objects'])
                model=(self.project_dir/current['model_path']).resolve()
                if not model.is_relative_to(self.root) or not model.is_file():
                    raise ValueError('Invalid saved model path')
                key=render_cache_key(options)
                image=model.parent/('view-'+key+'.png')
                settings_path=model.parent/('render-settings-'+uuid.uuid4().hex+'.json')
                self._run(model.parent,'render',[self.executable,'--background','--disable-autoexec',str(model),'--python-exit-code','1','--python',str(Path(__file__).with_name('blender_worker.py')),'--','render',str(image),options['view'],json.dumps(options),str(settings_path)])
                settings=json.loads(settings_path.read_text(encoding='utf-8'))
                result={'image_path':image.relative_to(self.project_dir).as_posix(),'revision':current['revision'],'cutaway':bool(options['hide_ids']),'hidden_ids':options['hide_ids'],'camera':options['camera'],'resolution':settings['resolution'],'denoise':settings['denoise'],'samples':settings['samples'],'denoise_requested':options.get('denoise')}
                current.setdefault('renders',{})[key]=result
                temporary=self.root/'scene.tmp.json'
                temporary.write_text(json.dumps(current,ensure_ascii=False,indent=2), encoding="utf-8")
                temporary.replace(self.state)
                return result
            if name != 'blender_apply_objects':
                raise ValueError('Unknown Blender tool')
            if set(arguments)-{'objects','delete_ids'} or not isinstance(arguments.get('objects'), list) or not 0 <= len(arguments['objects']) <= 256:
                raise ValueError('Expected up to 256 objects')
            old = json.loads(self.state.read_text(encoding="utf-8")) if self.state.exists() else {'objects':{}, 'revision':0}
            objects = dict(old['objects'])
            deleted=arguments.get('delete_ids',[])
            if not isinstance(deleted,list) or len(deleted)>256 or any(not isinstance(k,str) or not _NAME.fullmatch(k) or k not in objects for k in deleted) or len(set(deleted))!=len(deleted):
                raise ValueError('Invalid delete IDs')
            if not arguments['objects'] and not deleted:
                raise ValueError('Empty update')
            for k in deleted:
                del objects[k]
            seen = set()
            for obj in arguments['objects']:
                if not isinstance(obj,dict) or not {'id','location'}.issubset(obj) or set(obj)-{'id','location','dimensions','vertices','faces','material'} or not isinstance(obj['id'],str) or not _NAME.fullmatch(obj['id']) or obj['id'] in seen or obj['id'] in deleted:
                    raise ValueError('Invalid or duplicate object ID')
                seen.add(obj['id'])
                fields = ('location','dimensions') if 'dimensions' in obj else ('location',)
                if 'dimensions' not in obj:
                    vertices=obj.get('vertices');faces=obj.get('faces')
                    if not isinstance(vertices,list) or not 3<=len(vertices)<=256 or any(not isinstance(v,list) or len(v)!=3 or any(type(n) not in (int,float) or not math.isfinite(n) or abs(n)>10000 for n in v) for v in vertices):
                        raise ValueError('Invalid mesh vertices')
                    if not isinstance(faces,list) or not 1<=len(faces)<=512 or any(not isinstance(f,list) or not 3<=len(f)<=64 or len(set(f))!=len(f) or any(type(i)!=int or not 0<=i<len(vertices) for i in f) for f in faces):
                        raise ValueError('Invalid mesh faces')
                elif 'vertices' in obj or 'faces' in obj:
                    raise ValueError('Use box dimensions or mesh geometry, not both')
                material=obj.get('material',{})
                if not isinstance(material,dict) or set(material)-{'color','roughness','transmission'}:
                    raise ValueError('Invalid material')
                if 'color' in material and (not isinstance(material['color'],list) or len(material['color'])!=4 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in material['color'])):
                    raise ValueError('Invalid RGBA color')
                for k in ('roughness','transmission'):
                    if k in material and (type(material[k]) not in (int,float) or not math.isfinite(material[k]) or not 0<=material[k]<=1):
                        raise ValueError('Invalid material scalar')
                for field in fields:
                    values = obj[field]
                    if not isinstance(values,list) or len(values)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>10000 or (field=='dimensions' and v<=0) for v in values):
                        raise ValueError('Invalid finite metre coordinates')
                objects[obj['id']] = obj
            from .blender_edit_contract import validate, verify_result, advance
            contract = validate(self.project_dir, old, seen | set(deleted))
            if len(objects)>2048 or sum(len(o.get('vertices',[])) or 8 for o in objects.values())>50000:
                raise ValueError('Project object limit reached')
            if objects == old['objects']:
                raise ValueError('No geometry progress: identical object state; prior candidate retained. Inspect remaining issues before retrying.')
            from .stage_quality import geometry_diagnostics
            diagnostics = geometry_diagnostics(objects)
            revision = old['revision']+1
            run = self.root / uuid.uuid4().hex
            run.mkdir()
            spec=run/'input.json'; spec.write_text(json.dumps(objects), encoding="utf-8")
            output=run/'model.blend'; receipt=run/'receipt.json'
            script=Path(__file__).with_name('blender_worker.py')
            self._run(run, 'build', [self.executable,'--background','--factory-startup','--disable-autoexec','--python',str(script),'--',str(spec),str(output),str(receipt)])
            # Independent fresh process reopens the saved native file with autoexec disabled.
            reopen=run/'reopen.json'
            self._run(run, 'reopen', [self.executable,'--background','--disable-autoexec',str(output),'--python',str(script),'--','inspect',str(reopen)])
            before=json.loads(receipt.read_text(encoding="utf-8")); after=json.loads(reopen.read_text(encoding="utf-8"))
            if before != after or set(after) != set(objects):
                raise ValueError('Native save/reopen mismatch; previous revision retained')
            # Native work may take time. Do not commit under superseded intent,
            # host policy, or scene state. The old saved candidate stays intact.
            latest = json.loads(self.state.read_text(encoding="utf-8")) if self.state.exists() else {'objects': {}, 'revision': 0}
            if latest != old:
                raise ValueError('Blender scene changed during native execution; candidate not committed')
            if validate(self.project_dir, latest, seen | set(deleted)) != contract:
                raise ValueError('Blender host edit contract changed during execution')
            verify_result(contract, objects, after)
            result={'geometry_qa':diagnostics,'candidate_status':'saved_candidate','quality_status':'unverified','objects':objects,'revision':revision,'native_reopen':'PASS','geometry':after,'model_path':output.relative_to(self.project_dir).as_posix(), 'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
            temp=self.state.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2), encoding="utf-8");temp.replace(self.state)
            advance(self.project_dir, contract, revision)
            return result

    @staticmethod
    def _run(run_dir, phase, command):
        try:
            result = subprocess.run(command, check=True, timeout=600 if phase == 'render' else 240, capture_output=True, text=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            (run_dir / (phase + '-failure.txt')).write_text(str(error) + '\n' + str(getattr(error,'stdout','')) + '\n' + str(getattr(error,'stderr','')), encoding="utf-8")
            raise
        (run_dir / (phase + '.log')).write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
