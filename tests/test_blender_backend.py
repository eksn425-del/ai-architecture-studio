import json
import shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.blender_backend import BlenderBackend
from app.agent_tools import AgentToolSurface
from app.main import create_app
from app.native_agent import AgentTurnResult

@pytest.mark.skipif(not shutil.which('blender'),reason='real Blender required')
def test_real_conversation_plan_execute_edit_download_reopen(tmp_path):
    class AssistantSimulation:
        available=True
        model='assistant-test-simulation'
        reasoning_effort='low'
        def respond(self, **kw):
            # Deterministic assistant tool fixture, not a paid model or visual-quality test.
            surface=AgentToolSurface(tmp_path,None,oss_backends={})
            tools=surface.prepare(project_dir=kw['project_dir'],mcp_enabled=kw['mcp_enabled'],model_path=None,model_guid='',ruby_enabled=False,ruby_state={})
            if not kw['mcp_enabled']:
                assert not tools.dynamic_tools
                return AgentTurnResult(thread_id='fixture',reply='计划：创建墙和柱，保留其他对象。',provider_name='assistant-test-simulation',model_name=self.model)
            previous=tools.dispatch('blender_inspect_scene',{})
            objs=[{'id':'wall','location':[0,0,1.5],'dimensions':[4,0.2,3]},{'id':'column','location':[2,0,1.5],'dimensions':[0.3,0.3,3]}] if not previous['revision'] else [{'id':'wall','location':[0,0,1.5],'dimensions':[5,0.2,3]}]
            tools.dispatch('blender_apply_objects',{'objects':objs})
            return AgentTurnResult(thread_id='fixture',reply='有限体块已保存并真实重开核验。',provider_name='assistant-test-simulation',model_name=self.model)
    app=create_app(runtime_root=tmp_path,native_agent=AssistantSimulation())
    client=TestClient(app)
    pid=client.post('/api/projects',json={'project_name':'Blender integration test'}).json()['project_id']
    base=f'/api/projects/{pid}'
    assert client.post(base+'/blender/session').status_code==200
    assert client.post(base+'/conversation',json={'message':'执行','agent_action':'execute'}).status_code==409
    r=client.post(base+'/conversation',json={'message':'先制定墙柱计划','agent_action':'plan'})
    assert r.status_code==200,r.text
    r=client.post(base+'/conversation',json={'message':'按计划建模','agent_action':'execute'})
    assert r.status_code==200,r.text
    first=r.json()['agent']['model_info']
    r=client.post(base+'/conversation',json={'message':'只把墙改为五米，柱不变','agent_action':'execute'})
    assert r.status_code==200,r.text
    second=r.json()['agent']['model_info']
    assert second['revision']==2 and second['native_reopen']=='PASS'
    assert first['geometry']['column']==second['geometry']['column']
    assert second['geometry']['wall']['dimensions'][0]==5
    f=client.get(base+'/files/'+second['model_path'])
    assert f.status_code==200 and len(f.content)>1000
    assert client.get(base).status_code==200
    (tmp_path/'blender_test_evidence.json').write_text(json.dumps({'first':first,'second':second},indent=2))

@pytest.mark.parametrize('objects',[[{'id':'../bad','location':[0,0,0],'dimensions':[1,1,1]}],[{'id':'good','location':[float('nan'),0,0],'dimensions':[1,1,1]}],[{'id':'good','location':[0,0,0],'dimensions':[0,1,1]}]])
def test_reject_unsafe_input(tmp_path,objects):
    if not shutil.which('blender'): pytest.skip('Blender unavailable')
    with pytest.raises(ValueError): BlenderBackend(tmp_path).dispatch('blender_apply_objects',{'objects':objects})
    assert not (tmp_path/'runtime/blender/scene.json').exists()

def test_timeout_preserves_last_committed_state(tmp_path,monkeypatch):
    import subprocess
    backend=BlenderBackend(tmp_path)
    prior={'objects':{},'revision':4,'native_reopen':'PASS'}
    backend.state.write_text(json.dumps(prior))
    def timeout(*a,**kw):
        assert kw['timeout']==240
        assert '--disable-autoexec' in a[0]
        assert '--factory-startup' in a[0]
        raise subprocess.TimeoutExpired(a[0],120)
    monkeypatch.setattr(subprocess,'run',timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        backend.dispatch('blender_apply_objects',{'objects':[{'id':'wall','location':[0,0,1],'dimensions':[1,1,2]}]})
    assert json.loads(backend.state.read_text())==prior

def test_symlink_workspace_rejected(tmp_path):
    (tmp_path/'runtime').mkdir()
    target=tmp_path/'outside';target.mkdir()
    (tmp_path/'runtime/blender').symlink_to(target,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):
        BlenderBackend(tmp_path)

def test_plan_failure_invalidates_old_plan_and_reconnect_is_idempotent(tmp_path):
    class FailedProvider:
        available=True
        model='fixture'
        reasoning_effort='low'
        def respond(self,**kw): raise ValueError('fixture provider failure')
    app=create_app(runtime_root=tmp_path,native_agent=FailedProvider())
    client=TestClient(app)
    pid=client.post('/api/projects',json={'project_name':'Failure handling'}).json()['project_id']
    base=f'/api/projects/{pid}'
    assert client.post(base+'/blender/session').status_code==200
    from app.models import AgentSession
    session=app.state.store.load_state(pid,'agent_session.json',AgentSession)
    session.reconstruction_state='planned'
    app.state.store.save_state(pid,session,'agent_session.json')
    assert client.post(base+'/blender/session').json()['project']['agent_session']['reconstruction_state']=='planned'
    assert client.post(base+'/agent/session',json={'confirm_disposable_model':True}).status_code==409
    assert client.post(base+'/conversation',json={'message':'修改计划','agent_action':'plan'}).status_code==502
    assert client.post(base+'/conversation',json={'message':'执行','agent_action':'execute'}).status_code==409
    assert not app.state.agent_lock.locked()

def test_ui_blender_is_explicit_and_does_not_open_su_dialog():
    root=Path(__file__).resolve().parents[1]
    html=(root/'app/static/index.html').read_text()
    js=(root/'app/static/studio.js').read_text()
    assert 'start-blender-session' in html
    assert 'state.project?.agent_session?.modeling_backend !== "blender"' in js
    assert '外观质量尚未验收' in js

def test_readonly_turn_cannot_dispatch_blender_write(tmp_path):
    (tmp_path/'state').mkdir()
    (tmp_path/'state/modeling_backend.json').write_text('{"backend":"blender"}')
    tools=AgentToolSurface(tmp_path,None,oss_backends={}).prepare(project_dir=tmp_path,mcp_enabled=False,model_path=None,model_guid='',ruby_enabled=False,ruby_state={})
    assert tools.dynamic_tools==[]
    with pytest.raises(ValueError,match='approved execution'):
        tools.dispatch('blender_apply_objects',{'objects':[]})

def test_failed_provider_after_commit_recovers_native_artifact(tmp_path):
    class FailedAfterCommit:
        available=True
        model='fixture'
        reasoning_effort='low'
        def respond(self,**kw):
            backend=BlenderBackend(kw['project_dir'])
            # State fixture isolates interruption recovery; native build is tested separately.
            backend.state.write_text(json.dumps({'revision':1,'objects':{},'geometry':{},'model_path':'runtime/blender/fixture.blend','native_reopen':'PASS'}))
            raise ValueError('fixture interruption after commit')
    app=create_app(runtime_root=tmp_path,native_agent=FailedAfterCommit())
    client=TestClient(app)
    pid=client.post('/api/projects',json={'project_name':'Interrupted turn'}).json()['project_id']
    base=f'/api/projects/{pid}'
    client.post(base+'/blender/session')
    from app.models import AgentSession
    session=app.state.store.load_state(pid,'agent_session.json',AgentSession)
    session.reconstruction_state='planned';app.state.store.save_state(pid,session,'agent_session.json')
    assert client.post(base+'/conversation',json={'message':'执行','agent_action':'execute'}).status_code==502
    recovered=app.state.store.load_state(pid,'agent_session.json',AgentSession)
    assert recovered.model_path=='runtime/blender/fixture.blend'
    assert recovered.reconstruction_state=='building'
    assert 'interruption' in recovered.error

@pytest.mark.parametrize('extra',[{'vertices':[[0,0,0],[1,0,0],[0,1,0]],'faces':[[0,1,9]]},{'vertices':[[0,0,0],[1,0,0],[0,1,0]],'faces':[[0,1,1]]},{'dimensions':[1,1,1],'material':{'transmission':2}},{'dimensions':[1,1,1],'material':{'color':[0,0,0,float('nan')]}}])
def test_reject_unsafe_mesh_and_material(tmp_path,extra):
    with pytest.raises(ValueError):
        BlenderBackend(tmp_path).dispatch('blender_apply_objects',{'objects':[{'id':'roof','location':[0,0,0],**extra}]})

def test_real_mesh_material_edit_preserves_roof(tmp_path):
    backend=BlenderBackend(tmp_path)
    roof={'id':'roof','location':[0,0,0],'vertices':[[0,0,2],[2,0,1],[2,2,1],[0,2,2]],'faces':[[0,1,2,3]],'material':{'color':[.2,.2,.2,1],'roughness':.6}}
    glass={'id':'glass','location':[0,0,1],'dimensions':[1,.04,2],'material':{'color':[.5,.6,.6,1],'transmission':.8,'roughness':.1}}
    first=backend.dispatch('blender_apply_objects',{'objects':[roof,glass]})
    glass['dimensions']=[1.2,.04,2]
    second=backend.dispatch('blender_apply_objects',{'objects':[glass]})
    assert first['geometry']['roof']==second['geometry']['roof']
    assert second['native_reopen']=='PASS'
    assert second['geometry']['glass']['material'][0]['transmission']==pytest.approx(.8)

def test_blender_progress_reports_committed_geometry_without_claiming_quality(tmp_path):
    import time
    app=create_app(runtime_root=tmp_path)
    client=TestClient(app)
    pid=client.post('/api/projects',json={'project_name':'progress test'}).json()['project_id']
    assert client.post(f'/api/projects/{pid}/blender/session').status_code==200
    project=app.state.store.project_dir(pid)
    (project/'runtime/blender/scene.json').write_text(json.dumps({'revision':2}))
    app.state.active_turns[pid]={'started':time.time(),'action':'execute','baseline':{},'blender_baseline':1}
    result=client.get(f'/api/projects/{pid}/agent/progress').json()
    assert result['running'] and result['backend']=='blender'
    assert result['committed_revisions']==[2] and result['tool_calls'] is None
    assert 'quality_pass' not in result

def test_safe_named_delete_preserves_other_objects_and_history(tmp_path):
    backend=BlenderBackend(tmp_path)
    first=backend.dispatch('blender_apply_objects',{'objects':[{'id':n,'location':[0,0,0],'dimensions':[1,1,1]} for n in ['keep','duplicate']]})
    for ids in [['missing'],['../bad'],['keep','keep']]:
        with pytest.raises(ValueError):backend.dispatch('blender_apply_objects',{'objects':[],'delete_ids':ids})
    second=backend.dispatch('blender_apply_objects',{'objects':[],'delete_ids':['duplicate']})
    assert second['geometry']=={'keep':first['geometry']['keep']}
    assert (tmp_path/first['model_path']).is_file() and second['native_reopen']=='PASS'
