import json
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.copy_ownership import CopyOwnership, read, sha
from app.models import AgentSession
from app.sketchup_mcp import MCPCallError

SOURCE='original-theatre'
TARGET='independent-copy'
FP={'document':'geometry','roots':['root-geometry'],'hierarchy':'component-pids','materials':'materials','presentation':'view'}

class Store:
    def __init__(self,root): self.root=root
    def project_dir(self,p): return self.root/'projects'/p
    def load_state(self,p,name,kind): return kind(**read(self.project_dir(p)/'state'/name))
    def save_state(self,p,value,name): (self.project_dir(p)/'state'/name).write_text(value.model_dump_json())
    def load_context(self,p): return SimpleNamespace(project_name=p)

class Adapter:
    def __init__(self,path): self.identity={'model_path':str(path),'model_guid':'expected-guid','main_thread':True,'active_context':False}
    def get_active_model_identity(self): return self.identity.copy()

class Native(CopyOwnership):
    def __init__(self,store,adapter):
        super().__init__(store,adapter);self.owner=SOURCE;self.calls=[];self.fail=False;self.geometry=FP.copy()
    def native(self,action,plan):
        self.calls.append(action)
        roots=[{'root_pid':19,'revision':3,'project_id':self.owner,'name':'Original theatre'}]
        if action=='inspect': return {'roots':roots,'fingerprint':self.geometry.copy()}
        assert plan['expected_guid']==self.adapter.identity['model_guid']
        assert roots==plan['roots']
        if plan['source_project_id']!=self.owner: raise MCPCallError('Wrong source project identity')
        if plan['fingerprint']!=self.geometry: return {'status':'failed','error':'Model changed since preview','rollback_verified':True}
        if self.fail: return {'status':'failed','error':'Native save failed','rollback_verified':True}
        self.owner=TARGET
        self.adapter.identity['model_guid']='saved-guid'
        Path(plan['target_path']).write_bytes(b'migrated-native-metadata-only')
        return {'status':'saved','geometry_unchanged':True,'before':self.geometry.copy(),'after':self.geometry.copy(),
            'model_guid':'saved-guid','roots':[dict(roots[0],project_id=TARGET)]}

@pytest.fixture
def setup(tmp_path):
    store=Store(tmp_path)
    for p in (SOURCE,TARGET):
        project=store.project_dir(p)
        for d in ('state','runtime','outputs/model'): (project/d).mkdir(parents=True)
        path=project/'outputs/model/blank-disposable-test.skp';path.write_bytes(b'original-skp')
        session=AgentSession(project_id=p,status='ready',model_path='outputs/model/blank-disposable-test.skp',model_guid='expected-guid',ruby_state={'theatre':{'root_pid':19,'revision':3}})
        store.save_state(p,session,'agent_session.json')
        (project/'runtime/project_ruby_state.json').write_text(json.dumps({'model_path':str(path),'scripts':{'theatre':{'root_pid':19,'revision':3,'model_guid':'stale-guid'}}}))
    adapter=Adapter(store.project_dir(TARGET)/'outputs/model/blank-disposable-test.skp')
    return Native(store,adapter),store,adapter

def test_preview_read_only_and_confirm_updates_only_copy(setup):
    service,store,adapter=setup
    source=store.project_dir(SOURCE)/'outputs/model/blank-disposable-test.skp';baseline=sha(source)
    target=store.project_dir(TARGET)/'outputs/model/blank-disposable-test.skp';before=sha(target)
    plan=service.prepare(TARGET)
    assert sha(target)==before and service.calls==['inspect']
    assert plan['source_project_id']==SOURCE and plan['target_project_id']==TARGET
    receipt=service.apply(TARGET,plan['receipt_id'])
    assert receipt['geometry_unchanged'] and receipt['source_unchanged'] and sha(source)==baseline
    assert store.load_state(TARGET,'agent_session.json',AgentSession).model_guid=='saved-guid'
    assert read(store.project_dir(TARGET)/'runtime/project_ruby_state.json')['scripts']['theatre']['model_guid']=='saved-guid'
    assert store.load_state(SOURCE,'agent_session.json',AgentSession).model_guid=='expected-guid'

@pytest.mark.parametrize('field,value',[('model_path','outside.skp'),('model_guid','wrong-guid'),('active_context',True),('main_thread',False)])
def test_wrong_active_binding_rejected_before_native(setup,field,value):
    service,_,adapter=setup;adapter.identity[field]=value
    with pytest.raises(ValueError,match='does not match'): service.prepare(TARGET)
    assert service.calls==[]

def test_original_cannot_be_adopted(setup):
    service,store,adapter=setup
    adapter.identity['model_path']=str(store.project_dir(SOURCE)/'outputs/model/blank-disposable-test.skp')
    with pytest.raises(ValueError,match='distinct'): service.prepare(SOURCE)

def test_hardlinked_original_rejected(setup):
    service,store,_=setup
    target=store.project_dir(TARGET)/'outputs/model/blank-disposable-test.skp'
    target.unlink();os.link(store.project_dir(SOURCE)/'outputs/model/blank-disposable-test.skp',target)
    with pytest.raises(ValueError,match='independent target'): service.prepare(TARGET)

def test_unknown_source_rejected(setup):
    service,_,_=setup;service.owner='wrong-source'
    with pytest.raises((ValueError,FileNotFoundError)): service.prepare(TARGET)
    assert service.calls==['inspect']

def test_wrong_source_native_guard_preserved(setup):
    service,store,_=setup;preview=service.prepare(TARGET)
    planpath=store.project_dir(TARGET)/'runtime/copy_ownership_preview.json'
    plan=read(planpath);plan['source_project_id']='wrong-source';planpath.write_text(json.dumps(plan))
    with pytest.raises(MCPCallError,match='Wrong source'): service.apply(TARGET,preview['receipt_id'])
    assert service.owner==SOURCE

def test_running_project_blocks_prepare_and_apply(setup):
    service,store,_=setup;preview=service.prepare(TARGET)
    sessionpath=store.project_dir(SOURCE)/'state/agent_session.json';session=read(sessionpath);session['status']='running';sessionpath.write_text(json.dumps(session))
    with pytest.raises(ValueError,match='running'): service.apply(TARGET,preview['receipt_id'])
    with pytest.raises(ValueError,match='running'): service.prepare(TARGET)
    assert service.calls==['inspect']

@pytest.mark.parametrize('target',['source','target'])
def test_changed_file_requires_fresh_preview(setup,target):
    service,store,_=setup;preview=service.prepare(TARGET)
    p=SOURCE if target=='source' else TARGET
    (store.project_dir(p)/'outputs/model/blank-disposable-test.skp').write_bytes(b'changed externally')
    with pytest.raises(ValueError,match='changed since preview'): service.apply(TARGET,preview['receipt_id'])

def test_changed_geometry_rejected_without_receipt(setup):
    service,store,_=setup;preview=service.prepare(TARGET);service.geometry=dict(FP,document='changed')
    with pytest.raises(MCPCallError,match='changed since preview'): service.apply(TARGET,preview['receipt_id'])
    assert service.owner==SOURCE
    assert not (store.project_dir(TARGET)/'runtime/copy_ownership_receipt.json').exists()

def test_native_failure_retains_error_and_no_success_receipt(setup):
    service,store,_=setup;preview=service.prepare(TARGET);service.fail=True
    with pytest.raises(MCPCallError,match='save failed'): service.apply(TARGET,preview['receipt_id'])
    attempt=read(store.project_dir(TARGET)/f"runtime/copy_ownership_attempt-{preview['receipt_id']}.json")
    assert attempt['rollback_verified'] and service.owner==SOURCE
    assert not (store.project_dir(TARGET)/'runtime/copy_ownership_receipt.json').exists()

def test_repeated_migration_rejected(setup):
    service,_,_=setup;preview=service.prepare(TARGET);service.apply(TARGET,preview['receipt_id'])
    with pytest.raises(ValueError,match='already'): service.prepare(TARGET)
    with pytest.raises(ValueError,match='already'): service.apply(TARGET,preview['receipt_id'])

def test_root_revision_mismatch_rejected(setup):
    service,store,_=setup;p=store.project_dir(TARGET)/'runtime/project_ruby_state.json'
    state=read(p);state['scripts']['theatre']['revision']=4;p.write_text(json.dumps(state))
    with pytest.raises(ValueError,match='revision'): service.prepare(TARGET)

def test_wrong_confirmation_token_rejected(setup):
    service,_,_=setup;service.prepare(TARGET)
    with pytest.raises(ValueError,match='preview expired'): service.apply(TARGET,'not-approved')

def test_expired_preview_rejected(setup):
    service,store,_=setup;preview=service.prepare(TARGET)
    p=store.project_dir(TARGET)/'runtime/copy_ownership_preview.json'
    plan=read(p);plan['created_at']=0;p.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='expired'): service.apply(TARGET,preview['receipt_id'])

def test_endpoint_refuses_busy_cross_origin_and_unconfirmed(tmp_path,fake_components):
    from fastapi.testclient import TestClient
    from app.main import create_app
    brain,sketchup=fake_components
    app=create_app(tmp_path/'service',brain=brain,sketchup=sketchup)
    client=TestClient(app)
    url=f'/api/projects/{TARGET}/model-copy-ownership'
    assert client.post(url,json={'action':'preview'},headers={'origin':'https://unrelated.invalid'}).status_code==403
    app.state.agent_lock.acquire()
    try:
        assert client.post(url,json={'action':'preview'}).status_code==409
    finally:app.state.agent_lock.release()
    app.state.active_turns[SOURCE]={'action':'execute'}
    assert client.post(url,json={'action':'preview'}).status_code==409
    app.state.active_turns.clear()
    assert client.post(url,json={'action':'confirm'}).status_code==400
