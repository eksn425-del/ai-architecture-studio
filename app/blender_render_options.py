"""Validated render-only perspective and explicitly labeled cutaway options."""
import math
from .blender_views import REVIEW_CAMERAS

def validate_render_options(args,ids):
    if not isinstance(args,dict) or set(args)-{'view','camera','hide_ids'} or args.get('view','front') not in REVIEW_CAMERAS:raise ValueError('Invalid render options')
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
    return {'view':args.get('view','front'),'camera':camera,'hide_ids':hidden}
