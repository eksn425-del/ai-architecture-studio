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

_LOCK = threading.Lock()
_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')

def enabled(project_dir: Path) -> bool:
    marker = project_dir / 'state/modeling_backend.json'
    return marker.is_file() and json.loads(marker.read_text()).get('backend') == 'blender'

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

    def tools(self):
        number={'type':'number'}
        vector={'type':'array','items':number,'minItems':3,'maxItems':3}
        obj={'type':'object','required':['id','location'],'properties':{'id':{'type':'string','pattern':_NAME.pattern},'location':vector,'dimensions':vector,'vertices':{'type':'array','items':vector,'minItems':3,'maxItems':256},'faces':{'type':'array','items':{'type':'array','items':{'type':'integer'},'minItems':3,'maxItems':64},'maxItems':512},'material':{'type':'object','properties':{'color':{'type':'array','items':number,'minItems':4,'maxItems':4},'roughness':number,'transmission':number},'additionalProperties':False}},'additionalProperties':False}
        return [dict(name='blender_apply_objects',description='Create or update named project-owned boxes or bounded indexed meshes in metres, with simple RGBA/PBR materials. Use dimensions OR vertices+faces. Unmentioned objects preserved. Native save/reopen checked. No arbitrary code.',inputSchema={'type':'object','required':['objects'],'properties':{'objects':{'type':'array','minItems':0,'maxItems':256,'items':obj},'delete_ids':{'type':'array','maxItems':256,'items':{'type':'string','pattern':_NAME.pattern}}},'additionalProperties':False}),dict(name='blender_inspect_scene',description='Read current native geometry receipt.',inputSchema={'type':'object','properties':{},'additionalProperties':False}),dict(name='blender_render_scene',description='CPU render saved model from fixed front or rear camera. Appearance review still required.',inputSchema={'type':'object','properties':{'view':{'type':'string','enum':['front','rear']}},'additionalProperties':False})]

    def dispatch(self, name, arguments):
        with _LOCK:
            if name == 'blender_inspect_scene':
                return json.loads(self.state.read_text()) if self.state.exists() else {'objects':{}, 'revision':0}
            if name == 'blender_render_scene':
                if set(arguments)-{'view'} or arguments.get('view','front') not in ('front','rear'):
                    raise ValueError('Invalid render view')
                current=json.loads(self.state.read_text())
                model=(self.project_dir/current['model_path']).resolve()
                if not model.is_relative_to(self.root) or not model.is_file():
                    raise ValueError('Invalid saved model path')
                image=model.parent/('view-'+arguments.get('view','front')+'.png')
                self._run(model.parent,'render',[self.executable,'--background','--disable-autoexec',str(model),'--python',str(Path(__file__).with_name('blender_worker.py')),'--','render',str(image),arguments.get('view','front')])
                result={'image_path':str(image.relative_to(self.project_dir)),'revision':current['revision']}
                current.setdefault('renders',{})[arguments.get('view','front')]=result
                temporary=self.root/'scene.tmp.json'
                temporary.write_text(json.dumps(current,ensure_ascii=False,indent=2))
                temporary.replace(self.state)
                return result
            if name != 'blender_apply_objects':
                raise ValueError('Unknown Blender tool')
            if set(arguments)-{'objects','delete_ids'} or not isinstance(arguments.get('objects'), list) or not 0 <= len(arguments['objects']) <= 256:
                raise ValueError('Expected up to 256 objects')
            old = json.loads(self.state.read_text()) if self.state.exists() else {'objects':{}, 'revision':0}
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
            if len(objects)>2048 or sum(len(o.get('vertices',[])) or 8 for o in objects.values())>50000:
                raise ValueError('Project object limit reached')
            revision = old['revision']+1
            run = self.root / uuid.uuid4().hex
            run.mkdir()
            spec=run/'input.json'; spec.write_text(json.dumps(objects))
            output=run/'model.blend'; receipt=run/'receipt.json'
            script=Path(__file__).with_name('blender_worker.py')
            self._run(run, 'build', [self.executable,'--background','--factory-startup','--disable-autoexec','--python',str(script),'--',str(spec),str(output),str(receipt)])
            # Independent fresh process reopens the saved native file with autoexec disabled.
            reopen=run/'reopen.json'
            self._run(run, 'reopen', [self.executable,'--background','--disable-autoexec',str(output),'--python',str(script),'--','inspect',str(reopen)])
            before=json.loads(receipt.read_text()); after=json.loads(reopen.read_text())
            if before != after or set(after) != set(objects):
                raise ValueError('Native save/reopen mismatch; previous revision retained')
            result={'objects':objects,'revision':revision,'native_reopen':'PASS','geometry':after,'model_path':str(output.relative_to(self.project_dir)), 'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
            temp=self.state.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2));temp.replace(self.state)
            return result

    @staticmethod
    def _run(run_dir, phase, command):
        try:
            result = subprocess.run(command, check=True, timeout=240, capture_output=True, text=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            (run_dir / (phase + '-failure.txt')).write_text(str(error) + '\n' + str(getattr(error,'stdout','')) + '\n' + str(getattr(error,'stderr','')))
            raise
        (run_dir / (phase + '.log')).write_text(result.stdout + "\n" + result.stderr)
