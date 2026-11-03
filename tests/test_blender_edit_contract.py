import copy
import json
import pytest
from app.blender_edit_contract import install, validate, verify_result, advance

def scene():
    return {'revision': 1, 'objects': {'wall': {'id': 'wall', 'dimensions': [1,2,3]}, 'tree': {'id': 'tree', 'dimensions': [1,1,2]}},
            'geometry': {'wall': {'vertices': [1]}, 'tree': {'vertices': [2]}}}

def bind(p, old=None):
    return install(p, old or scene(), allowed_ids=['wall'], keep_ids=['tree'], expected_revision=1)

def test_scope_rejects_keep_and_undeclared_new_ids(tmp_path):
    c=bind(tmp_path)
    assert validate(tmp_path,scene(),{'wall'})==c
    for ids in ({'tree'},{'new'},{'wall','tree'}):
        with pytest.raises(ValueError, match='scope / KEEP'): validate(tmp_path,scene(),ids)

def test_contract_survives_reload_and_advances_only_explicitly(tmp_path):
    c=bind(tmp_path)
    newer=scene();newer['revision']=2
    with pytest.raises(ValueError, match='stale'):validate(tmp_path,newer,{'wall'})
    advance(tmp_path,c,2)
    assert validate(tmp_path,newer,{'wall'})['revision']==2

def test_new_user_intent_invalidates_contract_without_geometry_change(tmp_path):
    bind(tmp_path)
    p=tmp_path/'state/project_context.json';p.parent.mkdir()
    p.write_text(json.dumps({'conversation':[{'role':'user','content':'change a different wall'}]}))
    with pytest.raises(ValueError, match='stale'):validate(tmp_path,scene(),{'wall'})

def test_native_keep_drift_rejects_commit(tmp_path):
    old=scene();c=bind(tmp_path,old)
    verify_result(c,old['objects'],old['geometry'])
    geometry=copy.deepcopy(old['geometry']);geometry['tree']['vertices']=[3]
    with pytest.raises(ValueError, match='native KEEP'):verify_result(c,old['objects'],geometry)

def test_protected_spec_drift_rejects_preflight(tmp_path):
    c=bind(tmp_path)
    old=scene();old['objects']['tree']['dimensions']=[2,2,2]
    with pytest.raises(ValueError, match='protected scene'):validate(tmp_path,old,{'wall'})
    with pytest.raises(ValueError, match='protected object'):verify_result(c,old['objects'],old['geometry'])

@pytest.mark.parametrize('allowed,keep', [([],[]),(['wall'],['wall']),(['wall'],['missing']),([{}],[]),(['wall','wall'],[])])
def test_invalid_host_scope_rejected(tmp_path,allowed,keep):
    with pytest.raises(ValueError):install(tmp_path,scene(),allowed_ids=allowed,keep_ids=keep,expected_revision=1)

def test_bad_revision_and_symlink_rejected(tmp_path):
    with pytest.raises(ValueError,match='revision'):install(tmp_path,scene(),allowed_ids=['wall'],keep_ids=['tree'],expected_revision=0)
    bind(tmp_path)
    p=tmp_path/'runtime/blender/edit_contract.json';p.unlink();p.symlink_to(tmp_path/'outside')
    with pytest.raises(ValueError,match='Unsafe'):validate(tmp_path,scene(),{'wall'})

def test_malformed_contract_fail_closed(tmp_path):
    bind(tmp_path)
    (tmp_path/'runtime/blender/edit_contract.json').write_text('{}')
    with pytest.raises(ValueError,match='Invalid'):validate(tmp_path,scene(),{'wall'})

@pytest.mark.parametrize('changes', [
    {'allowed_ids':['tree'],'keep_ids':['tree'],'protected_specs':{},'protected_geometry':{}},
    {'protected_specs':{},'protected_geometry':{}},
    {'allowed_ids':'wall'}, {'revision':True}, {'keep_ids':['missing']},
])
def test_corrupted_valid_json_policy_fail_closed(tmp_path,changes):
    c=bind(tmp_path);c.update(changes)
    (tmp_path/'runtime/blender/edit_contract.json').write_text(json.dumps(c))
    with pytest.raises(ValueError,match='Invalid'):validate(tmp_path,scene(),{'tree'})

def test_reference_bytes_change_invalidates_host_contract(tmp_path):
    from PIL import Image
    p=tmp_path/'inputs/reference/source.png';p.parent.mkdir(parents=True)
    Image.new('RGB',(4,4),'white').save(p)
    context=tmp_path/'state/project_context.json';context.parent.mkdir()
    context.write_text(json.dumps({'references':[{'type':'image','source':'inputs/reference/source.png','evidence_role':'target_building'}]}))
    bind(tmp_path)
    Image.new('RGB',(4,4),'black').save(p)
    with pytest.raises(ValueError,match='stale'):validate(tmp_path,scene(),{'wall'})
