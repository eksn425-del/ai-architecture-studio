import json,types
import pytest
from app.conversation_receipts import begin,finish,abort_before_dispatch
from app.cloud_account import CloudAccount,CloudAccountError

def test_authorization_failure_retry_retains_evidence_but_uncertain_never_replays(tmp_path):
    class Request:
        client_request_id='a'*32
        def model_dump(self):return {'client_request_id':self.client_request_id,'message':'test'}
    request=Request();path,replay=begin(tmp_path,request);assert replay is None
    abort_before_dispatch(path,'fixture cloud offline before any provider/native call')
    path,replay=begin(tmp_path,request);assert replay is None
    assert len(json.loads(path.read_text())['preflight_failures'])==1
    finish(path)
    with pytest.raises(ValueError,match='unfinished or failed'):begin(tmp_path,request)

def test_platform_never_falls_back_to_local_provider(tmp_path):
    account=CloudAccount(tmp_path,'https://cloud.example.test');account.state['source_mode']='platform'
    app=types.SimpleNamespace(state=types.SimpleNamespace(model_router=types.SimpleNamespace()))
    with pytest.raises(CloudAccountError,match='未恢复'):account.authorize_turn(app,'turn','project',None)
    router=types.SimpleNamespace(cloud_model_id='platform-model',providers={'deepseek-harness':types.SimpleNamespace(api_provider=types.SimpleNamespace(api_base='https://other.example/v1'))})
    app.state.model_router=router
    route=types.SimpleNamespace(tier='economy',model='platform-model',provider='deepseek-harness')
    with pytest.raises(CloudAccountError,match='账本'):account.authorize_turn(app,'turn','project',route)
