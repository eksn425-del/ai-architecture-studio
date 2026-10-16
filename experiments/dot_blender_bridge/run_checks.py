"""Actual K Studio tool discovery/dispatch -> MCP -> Blender regression, not AI inference."""
import sys,os,json,tempfile,time,hashlib
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(REPO))
from app.sketchup_mcp import ConfiguredSketchUpMCP, MCPCallError
from app.agent_tools import AgentToolSurface
from app.litellm_runtime import _to_litellm_tool, _tool_call_parts, _tool_result_parts
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(tempfile.mkdtemp(prefix='dot-blender-proof-'))
out.mkdir(parents=True,exist_ok=True)
if (out/'scene'/'scene.blend').exists(): raise ValueError('Use a fresh evidence directory; preserve earlier runs')
config=out/'connector.json'; config.write_text(json.dumps({'command':sys.executable,'args':[str(Path(__file__).with_name('server.py'))],'env':{'DOT_BLENDER_LAB_ROOT':str(out/'scene')},'cwd':str(REPO)}))
os.environ['ARCH_STUDIO_MCP_CONFIG']=str(config)
mcp=ConfiguredSketchUpMCP(timeout_seconds=150)
surface=AgentToolSurface(out,mcp,oss_backends={})
ctx=surface.prepare(project_dir=out/'project',mcp_enabled=True,model_path=None,model_guid='',ruby_enabled=False,ruby_state=None,tool_profile='full')
checks=[]; traces=[]
def check(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    if not ok: raise AssertionError(name)
def dispatch(name,args):
    t=time.monotonic(); result=ctx.dispatch(name,args)
    traces.append({'tool':name,'arguments':args,'duration_seconds':time.monotonic()-t,'result':result})
    return json.loads(result['contentItems'][0]['text'])
check('actual_K_Studio_discovers_Blender_tools',len([t for t in ctx.dynamic_tools if t['name'].startswith('blender_')])==7)
check('real_Blender_version',dispatch('blender_health',{})['version'].startswith('Blender 4.3.2'))
# Fixed deterministic fixture, never presented as natural-language generation.
a=dispatch('blender_create_box',{'name':'FixtureSlab','dimensions':[6,4,.2],'location':[0,0,.1]})
b=dispatch('blender_create_box',{'name':'FixtureColumn','dimensions':[.3,.3,3],'location':[-2,-1,1.7]})
check('actual_mesh_objects',len(b['meshes'])==2)
check('slab_unchanged_after_second_write',a['meshes'][0]==next(x for x in b['meshes'] if x['name']=='FixtureSlab'))
c=dispatch('blender_inspect',{})
check('native_save_reopen_geometry_equal',b['geometry_sha256']==c['geometry_sha256'])
d=dispatch('blender_render',{})
check('render_does_not_change_mesh_geometry',c['geometry_sha256']==d['geometry_sha256'])
from PIL import Image
with Image.open(d['render_file']) as im: check('actual_render_480x360',im.size==(480,360)); im.verify()
for label,name,args in [('reject_arbitrary_code','execute_python',{'code':'pass'}),('reject_negative_size','blender_create_box',{'name':'Bad','dimensions':[-1,1,1],'location':[0,0,0]}),('reject_path_argument','blender_inspect',{'path':'/tmp/other.blend'}),('reject_duplicate_name','blender_create_box',{'name':'FixtureSlab','dimensions':[1,1,1],'location':[0,0,0]})]:
    try: dispatch(name,args)
    except MCPCallError: check(label,True)
    else: check(label,False)
e=dispatch('blender_inspect',{})
check('rejected_calls_preserve_geometry',d['geometry_sha256']==e['geometry_sha256'])
# Product's actual provider-schema conversion and call parser, no model invocation.
tool=next(x for x in ctx.dynamic_tools if x['name']=='blender_inspect')
check('provider_tool_schema_conversion',_to_litellm_tool(tool)['function']['name']=='blender_inspect')
callid,name,args=_tool_call_parts({'id':'contract-only','function':{'name':'blender_inspect','arguments':'{}'}})
check('provider_tool_call_parser',name=='blender_inspect' and args=={})
summary={'scope':'K_STUDIO_TOOL_SURFACE_MCP_BLENDER_INTEGRATION_ONLY','inference':'NOT_RUN','website_end_to_end':'NOT_RUN','production_su':'UNTOUCHED','checks':checks,'base_commit':'59fa229b5ae8873d05d42aafadfbc61c7af7ec41','output':str(out),'geometry_sha256':e['geometry_sha256']}
(out/'results.json').write_text(json.dumps(summary,indent=2)); (out/'trace.json').write_text(json.dumps(traces,indent=2)); print(json.dumps(summary,indent=2))
