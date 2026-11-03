"""Opt-in assistant-mediated local API probe, NOT autonomous/provider billing evidence.
A supervising assistant reads queued requests and writes each reply after inspection.
"""
import sys,os,json,copy,shutil,argparse,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.benchmark_simulated_api_usage import ScriptedServer,file_reply,summarize
from scripts.verify_cloud_blender_contracts import bind_instruction,dump
from app.blender_backend import BlenderBackend
from app.litellm_runtime import LiteLLMRuntime
from app.model_router import DeterministicModelRouter

def run(source,out):
 if out.exists():raise ValueError('Fresh output required')
 out.mkdir(parents=True);project=out/'project';shutil.copytree(source,project)
 backend=BlenderBackend(project);before=backend.dispatch('blender_inspect_scene',{})
 prompt='仅测试任务：把第一层左侧两列栏板改为深蓝色，高度改成0.5米，底边不动，其他构件保持不变。先读取当前场景，再修改，最后查看新渲染。'
 ids=['bay_0_0_rail','bay_0_1_rail']
 bind_instruction(project,prompt,'assistant-mediated-test')
 backend.install_edit_contract(allowed_ids=ids,keep_ids=sorted(set(before['objects'])-set(ids)),expected_revision=before['revision'])
 os.environ['ARCH_STUDIO_ECONOMY_PROVIDER']='litellm';os.environ['ARCH_STUDIO_STANDALONE']='1';os.environ['LITELLM_LOCAL_MODEL_COST_MAP']='True'
 relay=file_reply(out/'queue',timeout_seconds=600)
 with ScriptedServer([relay]*8) as server:
  runtime=LiteLLMRuntime(out/'runtime',model='openai/assistant-mediated-fixture')
  runtime.custom_api_base=server.base_url;runtime.session_api_key='nonsecret-loopback-fixture'
  class NoCodex:available=False
  router=DeterministicModelRouter(NoCodex(),china_runtime=runtime,runtime_root=out/'runtime')
  result=router.respond(tier='economy',project_dir=project,thread_id=None,prompt=prompt,mcp_enabled=True,ruby_enabled=False,tool_profile='full',workflow_mode='architecture_design',developer_instructions='Cloud experiment only. Exact host scope is authoritative. Read scene, preserve all non-target objects and use rendered image feedback. Do not infer engineering or source-photo certification.')
  after=backend.dispatch('blender_inspect_scene',{})
  dump(out/'evidence.json',{'mode':'assistant-mediated API; not autonomous LLM','paid_calls':0,'requests':summarize(server.requests),'result':result.__dict__,'before_revision':before['revision'],'after_revision':after['revision'],'untargeted_native_equal':all(before['geometry'][k]==after['geometry'][k] for k in set(before['objects'])-set(ids)),'changed_ids':ids,'target_geometry':{k:after['geometry'][k] for k in ids},'source_photo_quality':'NOT_RUN','usage_is_mock_proxy':True})
  dump(out/'http-requests.json',server.requests)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.source,a.output)
