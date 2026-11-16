from tests.test_reconstruction_integration import setup_project,send

def test_existing_revision_does_not_make_noop_a_new_delivery(tmp_path):
 client,agent,su,project=setup_project(tmp_path)
 assert send(client,'plan').status_code==200
 first=send(client,'execute');assert first.status_code==200
 assert first.json()['agent']['geometry_committed'] is True
 before=client.get('/api/projects/demo-cultural-center').json()['model_state']['model_path']
 su.calls.clear()
 second=send(client,'execute');assert second.status_code==200
 assert second.json()['agent']['geometry_committed'] is False
 assert second.json()['agent']['checkpoint_saved'] is False
 assert second.json()['agent']['execution_status']=='no_geometry_committed'
 assert second.json()['project']['model_state']['model_path']==before
 saves=[args['operation_name'] for name,args in su.calls if name=='save_model']
 assert 'Fast Assembly v1 agent checkpoint' not in saves
 assert '没有新的几何提交' in second.json()['reply']
