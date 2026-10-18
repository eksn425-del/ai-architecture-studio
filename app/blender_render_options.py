"""Validated render-only camera, cutaway, and bounded image-quality options."""
import hashlib
import json
import math
from .blender_views import REVIEW_CAMERAS

DEFAULT_RESOLUTION = 800
MAX_RESOLUTION = 1600

def validate_render_options(args,ids):
    if not isinstance(args,dict) or set(args)-{'view','camera','hide_ids','resolution','denoise'} or args.get('view','front') not in REVIEW_CAMERAS:raise ValueError('Invalid render options')
    resolution=args.get('resolution',DEFAULT_RESOLUTION)
    if type(resolution) is not int or not DEFAULT_RESOLUTION<=resolution<=MAX_RESOLUTION:raise ValueError('Resolution must be an integer from 800 to 1600')
    if 'denoise' in args and type(args['denoise']) is not bool:raise ValueError('Denoise must be a boolean')
    camera=args.get('camera')
    if camera is not None:
        if not isinstance(camera,dict) or set(camera)!={'position','target','lens'}:raise ValueError('Invalid camera')
        for k in ('position','target'):
            v=camera[k]
            if not isinstance(v,list) or len(v)!=3 or any(type(n) not in(int,float) or not math.isfinite(n) or abs(n)>10000 for n in v):raise ValueError('Invalid camera coordinates')
        n=camera['lens']
        if type(n) not in(int,float) or not math.isfinite(n) or not 12<=n<=120 or sum((a-b)**2 for a,b in zip(camera['position'],camera['target']))<.0001:raise ValueError('Invalid camera lens/target')
    hidden=args.get('hide_ids',[])
    if not isinstance(hidden,list) or len(hidden)>256 or any(not isinstance(n,str) or n not in ids for n in hidden) or len(set(hidden))!=len(hidden):raise ValueError('Invalid cutaway IDs')
    options={'view':args.get('view','front'),'camera':camera,'hide_ids':hidden,'resolution':resolution}
    if 'denoise' in args:options['denoise']=args['denoise']
    return options


def render_cache_key(options):
    """Retain legacy default filenames; separate every explicit quality variant."""
    identity={k:v for k,v in options.items() if k!='resolution' or v!=DEFAULT_RESOLUTION}
    key=options['view']
    if options['camera'] or options['hide_ids'] or options['resolution']!=DEFAULT_RESOLUTION or 'denoise' in options:
        key+='-'+hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:12]
    return key
