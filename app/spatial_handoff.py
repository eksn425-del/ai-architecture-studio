"""Small durable project handoff. This is context, never native authorization."""
from pathlib import Path
import hashlib
import json


def load(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def bounded_conversation(conversation, *, max_chars=12000, max_messages=16):
    """Keep recent dialogue verbatim; the full source remains in project_context.

    Never silently truncate an individual current message. Oversize input asks
    for a smaller request before any provider/model call.
    """
    selected=[]; used=0
    for item in reversed(conversation):
        if item.get('role') not in ('user','assistant'):
            continue
        text=str(item.get('content',''))
        if not selected and len(text)>max_chars:
            raise ValueError('当前消息超过上下文安全长度，请缩短当前消息；原始对话已保留。')
        if len(selected)>=max_messages or used+len(text)>max_chars:
            break
        selected.append({'role':item['role'],'content':text}); used+=len(text)
    return list(reversed(selected))


def handoff(project, *, graph, state, binding, sources):
    root=Path(project)
    runtime=root/'runtime'
    # Only host-created state is read; no model supplied path controls this read.
    quality=load(runtime/'harness-quality.json',{})
    if not quality:
        quality=load(runtime/'k-harness/latest-review.json',{})
    native=state.get('harness_building',{})
    coordinate=(graph or {}).get('spatial',{}).get('coordinate_frame',{
        'units':'mm','x':'right','front':'-Y','up':'+Z','origin':'unspecified; do not relocate existing geometry'})
    scripts=[]
    directory=runtime/'agent_workspace/scripts'
    if directory.is_dir():
        for path in sorted(directory.glob('*.rb'))[:64]:
            if path.is_symlink():continue
            scripts.append({'path':path.relative_to(root).as_posix(),
                            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    parts=(graph or {}).get('parts',[]); edited=(graph or {}).get('edit_parts',[])
    return {'schema_version':1,'sources':sources,'coordinate_frame':coordinate,
            'spatial_facts':(graph or {}).get('spatial',{}),
            'levels':(graph or {}).get('levels',[]),
            'relationships':(graph or {}).get('relationships',[]),
            'facts':(graph or {}).get('facts',[]),
            'plan_binding':binding,'approval_is_host_stage_only':True,
            'keep_parts':[part for part in parts if part not in edited],
            'native_identity_and_revision':native,
            'current_views':quality.get('views',{}),
            'last_recorded_writes':quality.get('writes',[])[-4:],
            'remaining_work':(graph or {}).get('spatial',{}).get('remaining_work',[]),
            'last_interruption':load(runtime/'k-harness/last-interruption.json',None),
            'scripts':scripts,
            'invariant':'Facade unification does not authorize changing approved levels, cantilevers, voids or mass relationships. Planned facts are not verified geometry.'}


def validate_spatial(value, parts, source_ids):
    if not isinstance(value,dict) or set(value)-{'coordinate_frame','scale_anchors','critical_features','remaining_work','change_rationale'}:
        raise ValueError('Invalid spatial handoff fields.')
    coordinate=value.get('coordinate_frame',{})
    if coordinate:
        if (not isinstance(coordinate,dict) or set(coordinate)!={'units','x','front','up','origin'}
            or any(coordinate[k]!=v for k,v in {'units':'mm','x':'right','front':'-Y','up':'+Z'}.items())
            or not isinstance(coordinate['origin'],str) or not 1<=len(coordinate['origin'])<=400):
            raise ValueError('Coordinate frame must preserve mm, X right, front -Y, Z up and an explicit origin.')
    for key in ('scale_anchors','remaining_work'):
        values=value.get(key,[])
        if not isinstance(values,list) or len(values)>32 or any(not isinstance(v,str) or not 1<=len(v)<=600 for v in values):
            raise ValueError('Spatial notes must be bounded strings.')
    rationale=value.get('change_rationale','')
    if not isinstance(rationale,str) or len(rationale)>1200:raise ValueError('Invalid spatial change rationale.')
    features=value.get('critical_features',[])
    if not isinstance(features,list) or len(features)>40:raise ValueError('Invalid critical spatial features.')
    ids=set()
    for feature in features:
        if not isinstance(feature,dict) or set(feature)!={'id','kind','parts','description','basis','source'}:
            raise ValueError('Critical feature requires id/kind/parts/description/basis/source.')
        if (not isinstance(feature['id'],str) or not 1<=len(feature['id'])<=80 or feature['id'] in ids
            or feature['kind'] not in {'split_level','cantilever','setback','void','stair_landing','ramp','mass_relation','uncertain_back'}
            or not isinstance(feature['parts'],list) or not feature['parts'] or any(p not in parts for p in feature['parts'])
            or feature['basis'] not in {'observed','user','inferred'}
            or not isinstance(feature['source'],str) or (feature['basis']=='observed' and feature['source'] not in source_ids)
            or not isinstance(feature['description'],str) or not 1<=len(feature['description'])<=1200):
            raise ValueError('Invalid critical spatial feature evidence or part scope.')
        ids.add(feature['id'])


def spatial_schema():
    text={'type':'string'}
    strings={'type':'array','items':text}
    coordinate={'type':'object','properties':{key:text for key in ('units','x','front','up','origin')},
                'required':['units','x','front','up','origin'],'additionalProperties':False}
    feature={'type':'object','properties':{'id':text,'kind':{'type':'string','enum':[
        'split_level','cantilever','setback','void','stair_landing','ramp','mass_relation','uncertain_back']},
        'parts':strings,'description':text,'basis':{'type':'string','enum':['observed','user','inferred']},'source':text},
        'required':['id','kind','parts','description','basis','source'],'additionalProperties':False}
    return {'type':'object','properties':{'coordinate_frame':coordinate,'scale_anchors':strings,
        'critical_features':{'type':'array','items':feature},'remaining_work':strings,'change_rationale':text},
        'additionalProperties':False}
