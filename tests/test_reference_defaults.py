import io,json
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import create_app
from app.models import Reference,ProjectContext,AgentSession
from app.reference_defaults import infer_reference_role,resolve_pending_reference_defaults
from app.design_scope_approval import capture_pending_design_plan,approve_pending_design_plan
from app.reference_roles import load_approved_design_scope

def image(color='white'):
 b=io.BytesIO();Image.new('RGB',(12,12),color).save(b,'PNG');return b.getvalue()

def ref(root,role,content=None):
 p=root/'inputs/reference/photo.png';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content or image())
 return Reference(type='image',source='inputs/reference/photo.png',evidence_role=role)

@pytest.mark.parametrize('has_model,context,count,expected',[
 (False,'',1,'target_building'),(False,'',2,'unknown'),(True,'',1,'unknown'),
 (True,'这里有缝，帮我修一下',1,'defect_location'),(False,'这里有缝',1,'unknown'),
 (True,'补充同一栋建筑的背面视角',1,'target_building'),
 (True,'第一张原图，第二张问题截图',2,'unknown'),
 (True,'不是问题截图，这是新视角',1,'unknown'),
 (False,'这几张是同一栋建筑的多视角参考图',3,'target_building')])
def test_context_defaults(tmp_path,has_model,context,count,expected):
 assert infer_reference_role(tmp_path,image(),[],has_model=has_model,context=context,batch_count=count)[0]==expected

@pytest.mark.parametrize('prior_role,text,expected',[
 ('target_building','','target_building'),('defect_location','','defect_location'),
 ('defect_location','补充目标建筑图','unknown'),('target_building','这里有缝','unknown'),
 ('unknown','','unknown')])
def test_identical_image_preserves_role_or_asks(tmp_path,prior_role,text,expected):
 r=ref(tmp_path,prior_role)
 assert infer_reference_role(tmp_path,image(),[r],has_model=True,context=text)[0]==expected

def test_filename_is_not_evidence_and_legacy_is_not_upgraded(tmp_path):
 r=ref(tmp_path,'unknown');r.source='inputs/reference/target_gap_original.png'
 (tmp_path/r.source).write_bytes(image('red'))
 context=ProjectContext(project_name='test',references=[r])
 assert not resolve_pending_reference_defaults(tmp_path,context,'这是目标建筑图',{'main':3})
 assert r.evidence_role=='unknown'

def test_pending_problem_keeps_upload_version(tmp_path):
 r=ref(tmp_path,'unknown');r.role_origin='awaiting_context';r.evidence_model_revisions={'main':2}
 context=ProjectContext(project_name='test',references=[r])
 assert resolve_pending_reference_defaults(tmp_path,context,'这里有缝',{'main':3})
 resolved=context.references[0]
 assert resolved.evidence_role=='defect_location' and resolved.evidence_model_revisions=={'main':2}
 resolved.evidence_role='unknown';resolved.role_origin='awaiting_context';resolved.submitted_at='already'
 assert not resolve_pending_reference_defaults(tmp_path,context,'原图',{'main':3})

def client_project(tmp_path):
 app=create_app(runtime_root=tmp_path);client=TestClient(app)
 pid=client.post('/api/projects',json={'project_name':'Role defaults'}).json()['project_id']
 return app,client,pid

def upload(client,pid,query='',color='white'):
 return client.post(f'/api/projects/{pid}/inputs/reference?filename=anything.png'+query,content=image(color))

def test_upload_default_correctable_and_correction_invalidates_plan(tmp_path):
 app,client,pid=client_project(tmp_path)
 response=upload(client,pid);assert response.status_code==200,response.text
 context=client.get('/api/projects/'+pid).json()['context'];r=context['references'][0]
 assert r['evidence_role']=='target_building' and r['role_origin']=='context_default'
 project=app.state.store.project_dir(pid);plan='<design_scope>[{"feature_id":"window","requested_state":"lower"}]</design_scope>'
 snapshot=capture_pending_design_plan(project,plan,is_followup=True)
 approve_pending_design_plan(project,'approved',plan,snapshot['plan_sha256'])
 session=app.state.store.load_state(pid,'agent_session.json',AgentSession);session.reconstruction_state='planned';app.state.store.save_state(pid,session,'agent_session.json')
 corrected=client.patch(f'/api/projects/{pid}/reference-role',json={'source':r['source'],'evidence_role':'defect_location'})
 assert corrected.status_code==200
 after=client.get('/api/projects/'+pid).json()
 assert after['context']['references'][0]['role_origin']=='user'
 assert after['agent_session']['reconstruction_state']=='clarifying'
 assert not load_approved_design_scope(project)['features']

def test_mixed_uploads_wait_and_existing_problem_binds_revision(tmp_path):
 app,client,pid=client_project(tmp_path)
 r=upload(client,pid,'&evidence_role=auto&batch_image_count=2')
 assert r.status_code==200
 assert client.get('/api/projects/'+pid).json()['context']['references'][0]['evidence_role']=='unknown'
 session=app.state.store.load_state(pid,'agent_session.json',AgentSession);session.ruby_state={'main':{'revision':7}};app.state.store.save_state(pid,session,'agent_session.json')
 r=upload(client,pid,'&evidence_role=auto&role_context=这里有缝',color='red');assert r.status_code==200,r.text
 last=client.get('/api/projects/'+pid).json()['context']['references'][-1]
 assert last['evidence_role']=='defect_location' and last['evidence_model_revisions']=={'main':7}

@pytest.mark.parametrize('query',['&batch_image_count=0','&batch_image_count=9','&batch_image_count=no','&evidence_role=pretend'])
def test_invalid_hints_rejected(tmp_path,query):
 _,client,pid=client_project(tmp_path);assert upload(client,pid,query).status_code==400


def test_non_target_first_image_and_later_correction_of_fresh_default(tmp_path):
 text='这是操作界面截图，不是我要建的建筑。'
 assert infer_reference_role(tmp_path,image(),[],has_model=False,context=text)[0]=='unknown'
 r=ref(tmp_path,'target_building');r.role_origin='context_default';r.role_reason='first_image_new_project'
 context=ProjectContext(project_name='test',references=[r])
 assert resolve_pending_reference_defaults(tmp_path,context,text,{})
 assert context.references[0].evidence_role=='unknown'
 r=context.references[0];r.evidence_role='target_building';r.role_origin='user'
 assert not resolve_pending_reference_defaults(tmp_path,context,text,{})
 assert r.evidence_role=='target_building'


def test_duplicate_defect_upload_keeps_historical_revision(tmp_path):
 app,client,pid=client_project(tmp_path)
 session=app.state.store.load_state(pid,'agent_session.json',AgentSession);session.ruby_state={'main':{'revision':2}};app.state.store.save_state(pid,session,'agent_session.json')
 assert upload(client,pid,'&evidence_role=defect_location').status_code==200
 session.ruby_state={'main':{'revision':3}};app.state.store.save_state(pid,session,'agent_session.json')
 assert upload(client,pid).status_code==200
 refs=client.get('/api/projects/'+pid).json()['context']['references']
 assert refs[-1]['evidence_role']=='defect_location' and refs[-1]['evidence_model_revisions']=={'main':2}

def test_conflicting_duplicate_defect_versions_ask(tmp_path):
 a=ref(tmp_path,'defect_location');a.evidence_model_revisions={'main':2}
 b=a.model_copy(deep=True);b.evidence_model_revisions={'main':3}
 assert infer_reference_role(tmp_path,image(),[a,b],has_model=True)[0]=='unknown'


@pytest.mark.parametrize('role,reason',[('target_building','explicit_current_target_context'),('defect_location','current_problem_context')])
def test_later_generic_message_keeps_reliable_upload_default(tmp_path,role,reason):
 r=ref(tmp_path,role);r.role_origin='context_default';r.role_reason=reason;r.evidence_model_revisions={'main':2}
 context=ProjectContext(project_name='test',references=[r])
 assert not resolve_pending_reference_defaults(tmp_path,context,'按这个完善模型。',{'main':2})
 assert context.references[0].evidence_role==role and context.references[0].role_reason==reason


@pytest.mark.parametrize('text,expected',[('按这张照片修复外墙。','unknown'),('这是模型截图，这里有缝，帮我修一下。','defect_location'),('按这张目标建筑图修复外墙。','target_building')])
def test_repair_verb_alone_is_not_evidence_role(tmp_path,text,expected):
 assert infer_reference_role(tmp_path,image(),[],has_model=True,context=text)[0]==expected


def test_duplicate_conflicting_description_then_defect_keeps_old_version(tmp_path):
 app,client,pid=client_project(tmp_path)
 session=app.state.store.load_state(pid,'agent_session.json',AgentSession);session.ruby_state={'main':{'revision':2}};app.state.store.save_state(pid,session,'agent_session.json')
 assert upload(client,pid,'&evidence_role=defect_location').status_code==200
 session.ruby_state={'main':{'revision':3}};app.state.store.save_state(pid,session,'agent_session.json')
 assert upload(client,pid,'&role_context=补充目标建筑图').status_code==200
 context=app.state.store.load_context(pid);latest=context.references[-1]
 assert latest.evidence_role=='unknown' and latest.evidence_model_revisions=={'main':2}
 assert resolve_pending_reference_defaults(app.state.store.project_dir(pid),context,'这是问题截图',{'main':3})
 assert context.references[-1].evidence_role=='defect_location' and context.references[-1].evidence_model_revisions=={'main':2}


def test_ambiguous_image_blocks_formal_plan_before_provider(tmp_path):
 _,client,pid=client_project(tmp_path)
 assert upload(client,pid,'&batch_image_count=2').status_code==200
 result=client.post('/api/projects/'+pid+'/conversation',json={'message':'请制定计划','workflow_mode':'image_reconstruction','agent_action':'plan'})
 assert result.status_code==409 and '用途' in result.text


def test_unknown_reference_blocks_default_ready_auto_before_provider(tmp_path):
 app,client,pid=client_project(tmp_path)
 assert upload(client,pid,'&batch_image_count=2').status_code==200
 session=app.state.store.load_state(pid,'agent_session.json',AgentSession);session.status='ready';session.model_path='outputs/model/fixture.skp';app.state.store.save_state(pid,session,'agent_session.json')
 result=client.post('/api/projects/'+pid+'/conversation',json={'message':'继续'})
 assert result.status_code==409 and '用途' in result.text
