"""File-based assistant-in-loop seam using real K Studio schema/parser/dispatch.
This is NOT a model endpoint or the complete K Studio Agent runtime.
Exports original product instructions unchanged for compatibility inspection.
A future backend port must reconcile the SketchUp/Ruby instructions before modeling.
"""
import sys,os,json,hashlib
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(REPO))
from app.sketchup_mcp import ConfiguredSketchUpMCP
from app.agent_tools import AgentToolSurface
from app.litellm_runtime import _to_litellm_tool,_tool_call_parts
from backend_contract import ADAPTED_INSTRUCTIONS
from app.workflow_context import workflow_developer_instructions,load_workflow_skill_context

def context(root):
    config=root/'connector.json'
    if not config.exists(): raise ValueError('Run checks/bootstrap first to produce explicit isolated connector config')
    os.environ['ARCH_STUDIO_MCP_CONFIG']=str(config)
    return AgentToolSurface(root,ConfiguredSketchUpMCP(timeout_seconds=150),oss_backends={}).prepare(project_dir=root/'project',mcp_enabled=True,model_path=None,model_guid='',ruby_enabled=False,ruby_state=None,tool_profile='full')
def export(root,prompt):
    ctx=context(root)
    packet={'kind':'MANUAL_ASSISTANT_RELAY_NOT_API','user_prompt':prompt,'original_kstudio_developer_instructions':workflow_developer_instructions('architecture_design',mcp_enabled=True,action='execute'),'original_kstudio_skill':load_workflow_skill_context('architecture_design',mcp_enabled=True),'tools':[_to_litellm_tool(t) for t in ctx.dynamic_tools if t['name'].startswith('blender_')],'adapted_developer_instructions':ADAPTED_INSTRUCTIONS,'blockers':['Supervised file relay; no live API','Bounded box-part backend only; original Ruby geometry/independent Critic not ported'],'allowed_now':[t['name'] for t in ctx.dynamic_tools if t['name'].startswith('blender_')]}
    packet['request_sha256']=hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()
    (root/'assistant_request.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)); print(packet['request_sha256'])
def consume(root,response_path):
    req=json.loads((root/'assistant_request.json').read_text()); response=json.loads(Path(response_path).read_text())
    if response.get('request_sha256')!=req['request_sha256']: raise ValueError('Stale request digest')
    calls=response.get('tool_calls',[])
    if not isinstance(calls,list) or len(calls)>8: raise ValueError('Maximum eight calls')
    parsed=[_tool_call_parts(c) for c in calls]
    if any(name not in req['allowed_now'] for _,name,_ in parsed): raise ValueError('Modeling blocked until original backend contracts are ported')
    ctx=context(root); outputs=[]
    for ident,name,args in parsed: outputs.append({'call_id':ident,'name':name,'result':ctx.dispatch(name,args)})
    journal=root/'relay_history.jsonl'
    with journal.open('a') as f: f.write(json.dumps({'request':req,'response':response,'outputs':outputs},ensure_ascii=False)+'\n')
    (root/'assistant_tool_results.json').write_text(json.dumps({'kind':'MANUAL_ASSISTANT_RELAY_NOT_API','outputs':outputs},indent=2))
if __name__=='__main__':
    action,folder=sys.argv[1:3]; root=Path(folder).resolve()
    if action=='export': export(root,sys.argv[3])
    elif action=='consume': consume(root,sys.argv[3])
    else: raise ValueError('export or consume required')
