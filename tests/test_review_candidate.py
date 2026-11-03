from fastapi.testclient import TestClient
from tests.test_novice_flow import workspace
from app.review_candidate import create_review_app


def test_review_entry_blocks_paid_and_mutating_routes(tmp_path):
    app,_,project,*_=workspace(tmp_path)
    client=TestClient(create_review_app(app))
    before=app.state.model_router.route('economy').as_dict()
    for path,body in [('/api/model-settings',{'mode':'bai'}),
                      (f'/api/projects/{project}/conversation',{'message':'build'}),
                      (f'/api/projects/{project}/agent/recover',{})]:
        response=client.post(path,json=body)
        assert response.status_code==409
    assert app.state.model_router.route('economy').as_dict()==before
    status=client.get('/api/candidate-review').json()
    assert not status['model_calls_enabled'] and not status['python_bridge_enabled']
    assert status['configured_route']['agent_engine']==before['agent_engine']
    assert 'native_execution_safety' in status
    html = client.get('/').text
    assert 'candidate-review-banner' in html
    assert 'Windows 原生执行未通过隔离验证' in html
