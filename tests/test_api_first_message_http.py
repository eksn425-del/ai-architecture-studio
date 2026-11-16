"""Real HTTP entrypoint with offline provider response, no native or paid calls."""
import io
from types import SimpleNamespace
import pytest
from PIL import Image
from tests.test_novice_flow import workspace
from app.litellm_runtime import LiteLLMRuntime

@pytest.mark.parametrize('mode,base,model', [('bai','https://api.b.ai/v1','deepseek-v4.1-flash'),('compatible','https://example.invalid/v1','fixture-model')])
def test_first_uploaded_image_crosses_real_conversation_entry(tmp_path,monkeypatch,mode,base,model):
    app,client,project,_,su=workspace(tmp_path)
    monkeypatch.setattr(LiteLLMRuntime,'available',property(lambda _:True))
    configured=client.post('/api/model-settings',json={'mode':mode,'model':model,'api_base':base,'api_key':'offline-fixture','reasoning_effort':'high'})
    assert configured.status_code==200
    provider=app.state.model_router.china_runtime
    calls=[]
    def completion(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(model=model,usage={'prompt_tokens':42,'completion_tokens':8},choices=[SimpleNamespace(finish_reason='stop',message={'content':'已收到图片，请确认层数。'})])
    monkeypatch.setattr(provider,'completion_callable',lambda:completion)
    monkeypatch.setattr('app.bai_transport.complete_bai',lambda kwargs,**_:completion(**kwargs))
    def no_intent(**kwargs):raise AssertionError('first turn must not call extra intent inference')
    monkeypatch.setattr(provider,'read_only_intent',no_intent)
    image=io.BytesIO();Image.new('RGB',(32,32),'white').save(image,format='PNG')
    upload=client.post(f'/api/projects/{project}/inputs/reference?filename=source.png',content=image.getvalue(),headers={'Content-Type':'image/png'})
    assert upload.status_code==200,upload.text
    request={'message':'帮我还原这个建筑模型，侧面和背面合理推测','workflow_mode':'image_reconstruction','client_request_id':'d'*32}
    response=client.post(f'/api/projects/{project}/conversation',json=request)
    assert response.status_code==200,response.text
    history=response.json()['project']['context']['conversation']
    user=next(item for item in history if item['role']=='user')
    assert user['metadata']['evidence_turn_id'].startswith('message:')
    assert len(calls)==1
    assert client.post(f'/api/projects/{project}/conversation',json=request).json()==response.json()
    assert len(calls)==1
