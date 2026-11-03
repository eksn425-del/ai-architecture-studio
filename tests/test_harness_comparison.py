import json
import pytest
from app.su_harness_tools import SUHarnessTools,tool_specs
from app.dsh_runtime import reported_usage
from app.model_router import ModelRoute

def test_frozen_edit_allows_product_plan_approval_without_expanding_scope():
    from app.harness_comparison import frozen_edit_requested
    edit='屋顶向前增加600毫米，其他不变。'
    user=lambda text:{'role':'user','content':text}
    approval=user('确认，按当前计划开始建模。')
    assert frozen_edit_requested([user(edit)],edit)
    assert frozen_edit_requested([user(edit),{'role':'assistant','content':'计划'},approval],edit)
    assert not frozen_edit_requested([{'role':'assistant','content':edit},approval],edit)
    assert not frozen_edit_requested([user(edit),user('同时重建幕墙'),approval],edit)
    assert not frozen_edit_requested([approval],edit)
    assert not frozen_edit_requested([user(edit),user('随便修改整栋')],edit)

def test_plan_never_grants_native_execution(tmp_path):
    project=tmp_path/'projects'/'test';project.mkdir(parents=True)
    surface=SUHarnessTools(tmp_path,None).prepare(project_dir=project,mcp_enabled=False,allow_plan=True)
    plan='按用户估计尺寸建模，侧后面注明推定，主体和屋面独立分组，保留所有其他对象，等待用户确认后才开始。'
    result=surface.dispatch('sketchup_save_plan',{'text':plan})
    assert result['approval_granted'] is False
    assert (project/'runtime/agent_workspace/notes/reconstruction_card.md').read_text(encoding='utf-8')==plan
    for name,args in [('sketchup_apply_parts',{'parts':[]}),('sketchup_view',{'view':'front'}),('sketchup_model_state',{})]:
        with pytest.raises(ValueError,match='require host-confirmed'):surface.dispatch(name,args)
    discussion=SUHarnessTools(tmp_path,None).prepare(project_dir=project,mcp_enabled=False)
    with pytest.raises(ValueError,match='planning stage'):discussion.dispatch('sketchup_save_plan',{'text':plan})
    assert discussion.dynamic_tools==surface.dynamic_tools==tool_specs(planning=True)

def test_local_edit_cannot_expand_to_other_parts(tmp_path,monkeypatch):
    class Executor:
        ruby_state={'harness_building':{'root_pid':4,'revision':1}}
        def __init__(self,*a,**kw):pass
        def verify_active_model(self):return {}
        def run(self,_):pytest.fail('Out-of-scope native writer must never run')
    monkeypatch.setattr('app.su_harness_tools.ProjectRubyExecutor',Executor)
    surface=SUHarnessTools(tmp_path,None).prepare(project_dir=tmp_path/'p',mcp_enabled=True,model_path=tmp_path/'blank.skp',model_guid='g',allowed_parts={'Roof'})
    with pytest.raises(ValueError,match='outside the approved'):
        surface.dispatch('sketchup_apply_parts',{'parts':[{'name':'Walls','pieces':[]}]})


def test_corrections_stop_without_blocking_other_initial_parts(tmp_path,monkeypatch):
    from app.project_ruby import ProjectRubyExecutor
    calls=[]
    class Executor:
        _ruby_string=staticmethod(ProjectRubyExecutor._ruby_string)
        ruby_state={'harness_building':{'root_pid':4,'revision':1}}
        def __init__(self,*a,**kw):pass
        def verify_active_model(self):return {}
        def run(self,args):calls.append(args);return {'success':True}
    monkeypatch.setattr('app.su_harness_tools.ProjectRubyExecutor',Executor)
    project=tmp_path/'p';(project/'runtime').mkdir(parents=True)
    surface=SUHarnessTools(tmp_path,None).prepare(project_dir=project,mcp_enabled=True,model_path=tmp_path/'blank.skp',model_guid='g')
    args=lambda name:{'parts':[{'name':name,'pieces':[{'kind':'box','origin':[0,0,0],'size':[100,200,30]}]}]}
    for _ in range(3):surface.dispatch('sketchup_apply_parts',args('Roof'))
    with pytest.raises(ValueError,match='Correction limit'):surface.dispatch('sketchup_apply_parts',args('Roof'))
    surface.dispatch('sketchup_apply_parts',args('Glass'))
    assert len(calls)==4

def test_usage_keeps_cached_prompt_and_unknowns_distinct():
    def event(usage):return {'type':'assistant/message','data':{'usage':usage}}
    assert reported_usage([event({'inputTokens':736,'outputTokens':109,'totalTokens':2381,'cacheReadTokens':1536})])==(2272,109)
    assert reported_usage([event({'inputTokens':2272,'outputTokens':109,'totalTokens':2381,'cacheReadTokens':1536})])==(2272,109)
    assert reported_usage([event(None)])==(None,None)
    assert ModelRoute('economy','deepseek-harness','deepseek-v4.1-flash','high','local').as_dict()['agent_engine']=='deepseek-harness'

def test_deepseek_host_tools_feed_real_product_progress(tmp_path,monkeypatch):
    import sys
    import urllib.request
    from types import SimpleNamespace
    from app.dsh_runtime import DSHHostSession
    from app.agent_progress import ProgressLogReader
    from app.progress_activity import public_events
    sdk_config={}
    def create_sdk(**kw):
        sdk_config.update(kw)
        return SimpleNamespace(close=lambda:None)
    monkeypatch.setitem(sys.modules,'deepseek_harness',SimpleNamespace(DeepSeekHarness=create_sdk))
    received=[]
    def dispatch(name,args):
        if args.get('fail'):raise ValueError('test tool failure')
        return {'success':True}
    log=tmp_path/'events.jsonl'
    host=DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base='https://example.invalid',api_key='test-secret',model='test',
        specs=[{'name':'sketchup_apply_parts'}],dispatch=dispatch,trace_path=log,sdk_site=tmp_path,dsh_bin='unused',progress=received.append,max_tokens=32768)
    try:
        profile=json.loads((tmp_path/'home/kstudio.patch.yml').read_text())
        llm=next(row for row in profile if row['id']=='llm-pi-ai')
        assert llm['config']['providers']['kstudio-bai']['models'][0]['maxTokens']==sdk_config['max_tokens']==32768
        for fail in (False,True):
            request=urllib.request.Request(f'http://127.0.0.1:{host.server.server_port}/call',
                data=json.dumps({'name':'sketchup_apply_parts','arguments':{'fail':fail}}).encode(),
                headers={'Authorization':'Bearer '+host.token,'Content-Type':'application/json'})
            with urllib.request.urlopen(request) as response:
                assert json.load(response)['success'] is not fail
        stats=ProgressLogReader().read(log)
        assert (stats['calls'],stats['failures'])==(2,1)
        assert len(public_events(log))==4
        assert [e['event'] for e in received]==['tool_started','tool_completed']*2
        assert received[-1]['success'] is False
        host.progress=lambda event:(_ for _ in ()).throw(RuntimeError('subscriber unavailable'))
        host.emit_progress({'event':'tool_result','tool':'sketchup_apply_parts','success':True})
        assert 'test-secret' not in log.read_text()
    finally:host.close()

def test_deepseek_readiness_does_not_require_codex(tmp_path,monkeypatch):
    from app.harness_comparison import ComparisonRuntime
    from app.native_agent import CodexAppServerRuntime
    runtime=ComparisonRuntime.__new__(ComparisonRuntime)
    runtime.arm='B';runtime.comparison_root=tmp_path/'comparison'
    runtime.codex_executable=str(tmp_path/'missing-codex.exe')
    sdk,entry=runtime._dsh_paths()
    (sdk/'deepseek_harness').mkdir(parents=True)
    (sdk/'deepseek_harness/__init__.py').write_text('')
    entry.parent.mkdir(parents=True);entry.write_text('')
    monkeypatch.setattr('app.harness_comparison.shutil.which',lambda name: 'node.exe' if name=='node' else None)
    def forbidden(*a,**kw):pytest.fail('DeepSeek must not check Codex identity')
    monkeypatch.setattr(CodexAppServerRuntime,'execution_readiness',forbidden)
    assert runtime.available
    runtime._assert_execution_ready()
    entry.unlink()
    assert not runtime.available
    assert runtime.execution_readiness()['status']=='blocked_missing_deepseek_dependency'

def test_codex_arm_preserves_original_readiness_gate(monkeypatch):
    from app.harness_comparison import ComparisonRuntime
    from app.native_agent import CodexAppServerRuntime
    runtime=ComparisonRuntime.__new__(ComparisonRuntime);runtime.arm='A'
    sentinel={'execution_allowed':False,'status':'blocked_unsupported_host_tools_runtime'}
    monkeypatch.setattr(CodexAppServerRuntime,'execution_readiness',lambda self:sentinel)
    assert runtime.execution_readiness()==sentinel

def test_deepseek_route_exposes_its_own_ui_readiness(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from app.model_router import DeterministicModelRouter
    monkeypatch.setenv('ARCH_STUDIO_STANDALONE','1')
    router=DeterministicModelRouter(SimpleNamespace(available=False,model='test',runtime_root=tmp_path),runtime_root=tmp_path)
    provider=SimpleNamespace(available=True,binary_available=True,model='deepseek-v4.1-flash',
        execution_readiness=lambda:{'execution_allowed':True,'status':'ready_host_tools'})
    router.providers['deepseek-harness']=provider
    router.economy_route=ModelRoute('economy','deepseek-harness',provider.model,'high','local')
    assert router.available
    assert router.status()['providers']['deepseek-harness']['available']
    provider.available=False
    assert not router.available
    assert not router.status()['providers']['deepseek-harness']['available']

def test_deepseek_receipt_cannot_be_mislabeled_by_inheritance(tmp_path):
    from types import SimpleNamespace
    from app.contextual_turn import interpret_turn
    from app.design_scope_approval import capture_pending_design_plan
    from app.models import AgentSession,ConversationRequest,ProjectContext
    card=tmp_path/'runtime/agent_workspace/notes/reconstruction_card.md'
    card.parent.mkdir(parents=True);card.write_text('按图建两层，其他物体保持不变。',encoding='utf-8')
    pending=capture_pending_design_plan(tmp_path,card.read_text(encoding='utf-8'),is_followup=False)
    import hashlib
    request=ConversationRequest(message='确认，按当前计划开始建模。',workflow_mode='image_reconstruction',
        approval_gesture='plan_button',approved_pending_plan_id=pending['pending_plan_id'],
        approved_plan_sha256=hashlib.sha256(card.read_bytes()).hexdigest())
    runtime=SimpleNamespace(provider_name='deepseek-harness',_run_turn=lambda **kw:pytest.fail('Explicit approval requires no model call'))
    action,receipt=interpret_turn(runtime,project=tmp_path,session=AgentSession(project_id='test',reconstruction_state='planned'),
        request=request,context=ProjectContext(),model='test',reasoning_effort='high')
    assert action=='execute'
    assert receipt['agent_engine']=='deepseek-harness'
