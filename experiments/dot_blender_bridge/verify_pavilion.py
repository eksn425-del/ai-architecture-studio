"""Verify real before/after native data and on-disk six-view deliverables."""
import json,sys,hashlib
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent));from interactive_seam import context
root=Path(sys.argv[1]);before=json.loads((root/'before_edit.json').read_text());ctx=context(root)
after=json.loads(ctx.dispatch('blender_inspect',{})['contentItems'][0]['text']);old={m['name']:m for m in before['meshes']};new={m['name']:m for m in after['meshes']}
checks=[]
def ck(name,passed):checks.append({'name':name,'passed':bool(passed)});assert passed,name
ck('six_meshes_and_same_stable_id_set',len(new)==6 and {x['id'] for x in old.values()}=={x['id'] for x in new.values()})
for name in sorted(old):
    if name!='pavilion_roof':ck('KEEP_'+name,old[name]==new[name])
roof=new['pavilion_roof'];M=roof['matrix'];verts=[[sum(M[i][j]*v[j] for j in range(3))+M[i][3] for i in range(3)] for v in roof['vertices']];bounds={'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)]};tolerance_m=1e-6
ck('roof_actual_world_bounds',all(abs(a-b)<=tolerance_m for a,b in zip(bounds['min']+bounds['max'],[-3.4,-2.4,3,3.4,2.4,3.25])))
ck('roof_geometry_changed',before['geometry_sha256']!=after['geometry_sha256'])
ck('native_revision_two',after['revision']==2)
last=json.loads((root/'assistant_tool_results.json').read_text());render=json.loads(last['outputs'][-1]['result']['contentItems'][0]['text']);ck('render_then_native_reopen_identical',render['geometry_sha256']==after['geometry_sha256'])
views=[]
for name in ['front','rear','left','right','roof','oblique']:
    p=root/'scene'/(name+'.png')
    with Image.open(p) as im:ck(name+'_real_png',im.size==(480,360));im.verify()
    views.append({'name':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
result={'scope':'SUPERVISED_CHAT_DRIVEN_ADAPTED_K_STUDIO_TOOL_PIPELINE','live_model_api':'NOT_RUN','website_ui':'NOT_RUN','source_reconstruction':'NOT_RUN','independent_product_critic':'NOT_PORTED','structural_certification':'NOT_CLAIMED','before_geometry_sha256':before['geometry_sha256'],'after_geometry_sha256':after['geometry_sha256'],'float_coordinate_tolerance_m':tolerance_m,'roof_world_bounds':bounds,'checks':checks,'views':views,'assistant_decisions':[{'stage':'plan_create','decision':'6x4 slab, four corner columns, flat roof; parent selected actual tool calls'},{'stage':'review_edit','decision':'After viewing native oblique render parent requested only roof6.8x4.8, giving0.4m slab-relative overhang per side'}]}
(root/'supervised_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
