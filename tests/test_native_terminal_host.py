import json
import pytest
from app.native_agent import AgentTurnResult
from app.models import AgentSession
from app.store import ProjectStore
from tests.test_demo import FakeNativeAgent
from tests.test_reconstruction_integration import setup_project

@pytest.mark.parametrize('commit',[False,True])
def test_host_interrupted_is_not_success_or_missing_geometry_error(tmp_path,commit):
    class Interrupted(FakeNativeAgent):
        def respond(self,**kw):
            if commit:
                state={'fixture':{'revision':1,'root_pid':1}}
                p=kw['project_dir']/'runtime/project_ruby_state.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'scripts':state}))
                kw['ruby_state'].update(state)
            return AgentTurnResult(thread_id='t',turn_id='turn',reply='',status='interrupted',cancellation_requested=True)
    client,agent,su,project=setup_project(tmp_path,Interrupted())
    store=ProjectStore(tmp_path/'runtime');session=store.load_state('demo-cultural-center','agent_session.json',AgentSession)
    session.reconstruction_state='planned';store.save_state('demo-cultural-center',session,'agent_session.json')
    response=client.post('/api/projects/demo-cultural-center/conversation',json={'message':'确认执行','agent_action':'execute','workflow_mode':'image_reconstruction'})
    assert response.status_code==200,response.text
    result=response.json()['agent']
    assert result['execution_status']=='interrupted' and result['geometry_committed']==commit
    assert result['checkpoint_saved']==commit


def test_cancel_requires_current_request_identity(tmp_path):
    client,agent,_,project=setup_project(tmp_path)
    called=[];agent.cancel_turn=lambda project:called.append(project) or {'status':'requested'}
    client.app.state.active_turns['demo-cultural-center']={'started':0,'provider':'codex-app-server','request_id':'new'}
    stale=client.post('/api/projects/demo-cultural-center/agent/cancel',json={'expected_request_id':'old'})
    assert stale.status_code==409 and not called
    response=client.post('/api/projects/demo-cultural-center/agent/cancel',json={'expected_request_id':'new'})
    assert response.status_code==200 and len(called)==1
    assert response.json()['terminal_confirmed'] is False and response.json()['rollback_performed'] is False

@pytest.mark.parametrize('commit',[False,True])
def test_blender_host_interrupted_preserves_real_revision_truth(tmp_path,monkeypatch,commit):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.blender_backend import BlenderBackend
    revision=[0]
    def inspect(self,name,args):
        assert name=='blender_inspect_scene'
        return {'revision':revision[0],'objects':{},'native_reopen':'NOT_RUN'}
    monkeypatch.setattr(BlenderBackend,'dispatch',inspect)
    class Interrupted(FakeNativeAgent):
        def respond(self,**kw):
            revision[0]=int(commit)
            return AgentTurnResult(thread_id='t',turn_id='turn',reply='',status='interrupted',cancellation_requested=True)
    app=create_app(runtime_root=tmp_path,native_agent=Interrupted());client=TestClient(app)
    pid=client.post('/api/projects',json={'project_name':'Interrupted fixture'}).json()['project_id']
    base='/api/projects/'+pid
    assert client.post(base+'/blender/session').status_code==200
    session=app.state.store.load_state(pid,'agent_session.json',AgentSession)
    session.reconstruction_state='planned';app.state.store.save_state(pid,session,'agent_session.json')
    response=client.post(base+'/conversation',json={'message':'确认执行','agent_action':'execute'})
    assert response.status_code==200,response.text
    result=response.json()['agent']
    assert result['execution_status']=='interrupted'
    assert result['geometry_committed']==commit and result['checkpoint_saved']==commit
