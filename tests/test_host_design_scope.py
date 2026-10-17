import hashlib
import json
from tests.test_reconstruction_integration import PlanningAgent,setup_project,send
from app.reference_roles import load_approved_design_scope

class ScopedPlanningAgent(PlanningAgent):
    plans=0
    def respond(self,**kwargs):
        result=super().respond(**kwargs)
        if 'PARAMETER/PLAN turn' in kwargs['prompt']:
            self.plans+=1
            if self.plans>1:
                card=kwargs['project_dir']/'runtime/agent_workspace/notes/reconstruction_card.md'
                text=card.read_text()+'\n<design_scope>'+json.dumps([{'feature_id':'terrace.rails','requested_state':'深灰栏杆，其他构件保持'}],ensure_ascii=False)+'</design_scope>\n'
                card.write_bytes(text.replace('\n','\r\n').encode('utf-8'))
        return result

def prepare(tmp_path):
    client,agent,su,project=setup_project(tmp_path,ScopedPlanningAgent())
    assert send(client,'plan').status_code==200
    assert send(client,'execute').status_code==200
    assert send(client,'plan').status_code==200
    return client,agent,su,project

def execute(client,digest=''):
    return client.post('/api/projects/demo-cultural-center/conversation',json={'message':'确认执行','workflow_mode':'image_reconstruction','agent_action':'execute','approved_plan_sha256':digest})

def test_scoped_followup_requires_displayed_hash_windows_unicode(tmp_path):
    client,agent,su,project=prepare(tmp_path)
    su.calls.clear()
    assert execute(client).status_code==409
    assert not su.calls
    card=project/'runtime/agent_workspace/notes/reconstruction_card.md'
    raw=card.read_bytes().decode('utf-8')
    assert '\r\n' in raw
    digest=hashlib.sha256(raw.replace('\r\n','\n').replace('\r','\n').encode()).hexdigest()
    response=execute(client,digest)
    assert response.status_code==200,response.text
    scope=load_approved_design_scope(project)
    assert scope['features'][0]['feature_id']=='terrace.rails'
    assert response.json()['agent']['geometry_committed'] is False

def test_changed_card_rejected_before_tools(tmp_path):
    client,agent,su,project=prepare(tmp_path)
    card=project/'runtime/agent_workspace/notes/reconstruction_card.md'
    digest=hashlib.sha256(card.read_text().encode()).hexdigest()
    card.write_text(card.read_text()+'changed')
    su.calls.clear()
    assert execute(client,digest).status_code==409
    assert not su.calls
