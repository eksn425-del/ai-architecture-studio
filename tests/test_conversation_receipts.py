import json
from app.conversation_receipts import begin,finish
from app.models import ConversationRequest
import pytest


def test_receipt_replays_repeatedly(tmp_path):
    r=ConversationRequest(message='讨论',client_request_id='a'*32)
    path,response=begin(tmp_path,r);assert response is None
    finish(path,{'reply':'once'})
    for _ in range(3):
        _,reply=begin(tmp_path,r);assert reply=={'reply':'once'}
    assert json.loads(path.read_text())['status']=='completed'


def test_uncertain_never_reexecuted(tmp_path):
    r=ConversationRequest(message='讨论',client_request_id='a'*32)
    begin(tmp_path,r)
    with pytest.raises(ValueError):begin(tmp_path,r)


def test_reused_id_different_content(tmp_path):
    r=ConversationRequest(message='讨论',client_request_id='a'*32)
    p,_=begin(tmp_path,r);finish(p,{'reply':'once'});r.message='建模'
    with pytest.raises(ValueError):begin(tmp_path,r)


def test_api_duplicate_replay_does_not_corrupt_receipt(tmp_path):
    from tests.test_reconstruction_integration import setup_project
    client,agent,su,project=setup_project(tmp_path)
    body={'message':'先讨论一下','workflow_mode':'image_reconstruction','client_request_id':'b'*32}
    responses=[client.post('/api/projects/demo-cultural-center/conversation',json=body) for _ in range(3)]
    assert [r.status_code for r in responses]==[200,200,200]
    assert responses[0].json()==responses[1].json()==responses[2].json()
    record=json.loads((project/'runtime/conversation_requests'/('b'*32+'.json')).read_text())
    assert record['status']=='completed'
