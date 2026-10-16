"""Replay the saved assistant decisions for reproducibility; no new inference."""
import sys,json,shutil
from pathlib import Path
from interactive_seam import export,consume
root=Path(sys.argv[1]).resolve();root.mkdir(parents=True,exist_ok=True)
if (root/'scene'/'scene.blend').exists():raise ValueError('Use a new evidence directory')
repo=Path(__file__).resolve().parents[2]
(root/'connector.json').write_text(json.dumps({'command':sys.executable,'args':[str(Path(__file__).with_name('server.py'))],'env':{'DOT_BLENDER_LAB_ROOT':str(root/'scene'),'DOT_BLENDER_ALLOWED_EDIT_NAMES':'["pavilion_roof"]'},'cwd':str(repo)}))
def run(prompt,calls):
    export(root,prompt);q=json.loads((root/'assistant_request.json').read_text());r={'request_sha256':q['request_sha256'],'provenance':'REPLAY of saved assistant decisions, not fresh inference','tool_calls':[{'id':str(i),'function':{'name':name,'arguments':json.dumps(args)}} for i,(name,args) in enumerate(calls)]};p=root/'assistant_response.json';p.write_text(json.dumps(r));consume(root,p)
parts=[{'name':'pavilion_slab','dimensions':[6,4,.2],'location':[0,0,.1]}]
for name,x,y in [('sw',-2.7,-1.7),('se',2.7,-1.7),('nw',-2.7,1.7),('ne',2.7,1.7)]:parts.append({'name':'column_'+name,'dimensions':[.25,.25,2.8],'location':[x,y,1.6]})
parts.append({'name':'pavilion_roof','dimensions':[6,4,.25],'location':[0,0,3.125]})
run('Replay initial synthetic pavilion decision',[('blender_create_assembly',{'expected_geometry_sha256':'','parts':parts}),('blender_inspect',{}),('blender_render_views',{})])
data=json.loads((root/'assistant_tool_results.json').read_text());before=json.loads(data['outputs'][-1]['result']['contentItems'][0]['text']);(root/'before_edit.json').write_text(json.dumps(before));shutil.copytree(root/'scene',root/'before_scene')
run('Replay roof-only overhang edit',[('blender_edit_parts',{'expected_geometry_sha256':before['geometry_sha256'],'parts':[{'name':'pavilion_roof','dimensions':[6.8,4.8,.25],'location':[0,0,3.125]}]}),('blender_inspect',{}),('blender_render_views',{})])
print('Replay complete; run verify_pavilion.py and check_guards.py against this directory')
