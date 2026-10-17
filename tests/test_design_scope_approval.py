import json
import pytest
from app.design_scope_approval import (capture_pending_design_plan, approve_pending_design_plan,
    invalidate_stale_design_scope)
from app.reference_roles import load_approved_design_scope

PLAN='<design_scope>[{"feature_id":"window.mullion","requested_state":"remove divider"}]</design_scope>'
def project(tmp_path):
    p=tmp_path/'inputs/reference/a.png';p.parent.mkdir(parents=True);p.write_bytes(b'original')
    (tmp_path/'state').mkdir();(tmp_path/'state/project_context.json').write_text(json.dumps({'references':[{'type':'image','source':'inputs/reference/a.png','evidence_role':'target_building'}]}))
    return p

def test_exact_displayed_followup_approval(tmp_path):
    project(tmp_path);snapshot=capture_pending_design_plan(tmp_path,PLAN,is_followup=True)
    assert snapshot['features']
    scope=approve_pending_design_plan(tmp_path,'message:approval',PLAN,snapshot['plan_sha256'])
    assert scope['valid'] and scope['features']==snapshot['features']
    assert not invalidate_stale_design_scope(tmp_path)

def test_initial_and_unscoped_plans_never_grant_override(tmp_path):
    project(tmp_path)
    for text,followup in [(PLAN,False),('ordinary plan',True)]:
        snapshot=capture_pending_design_plan(tmp_path,text,is_followup=followup)
        assert not snapshot['features']
        assert approve_pending_design_plan(tmp_path,'message:approval',text,snapshot['plan_sha256'])=={}

def test_changed_card_missing_hash_changed_image_and_role_rejected(tmp_path):
    image=project(tmp_path);snapshot=capture_pending_design_plan(tmp_path,PLAN,is_followup=True)
    for text,digest in [(PLAN,'wrong'),(PLAN+'modified',snapshot['plan_sha256'])]:
        with pytest.raises(ValueError):approve_pending_design_plan(tmp_path,'message:approval',text,digest)
    image.write_bytes(b'changed')
    with pytest.raises(ValueError):approve_pending_design_plan(tmp_path,'message:approval',PLAN,snapshot['plan_sha256'])
    snapshot=capture_pending_design_plan(tmp_path,PLAN,is_followup=True)
    context=tmp_path/'state/project_context.json';data=json.loads(context.read_text());data['references'][0]['evidence_role']='defect_location';context.write_text(json.dumps(data))
    with pytest.raises(ValueError):approve_pending_design_plan(tmp_path,'message:approval',PLAN,snapshot['plan_sha256'])

def test_new_unscoped_plan_and_later_source_change_invalidate_existing_scope(tmp_path):
    image=project(tmp_path);snapshot=capture_pending_design_plan(tmp_path,PLAN,is_followup=True)
    approve_pending_design_plan(tmp_path,'message:1',PLAN,snapshot['plan_sha256'])
    capture_pending_design_plan(tmp_path,'unscoped updated plan',is_followup=True)
    assert load_approved_design_scope(tmp_path)['features']==[]
    snapshot=capture_pending_design_plan(tmp_path,PLAN,is_followup=True)
    with pytest.raises(ValueError):approve_pending_design_plan(tmp_path,'message:1',PLAN,snapshot['plan_sha256'])
    scope=approve_pending_design_plan(tmp_path,'message:2',PLAN,snapshot['plan_sha256'])
    assert scope['version']==2
    image.write_bytes(b'later changed')
    assert invalidate_stale_design_scope(tmp_path)
    assert not load_approved_design_scope(tmp_path)['features']
    assert (tmp_path/'runtime/design_scope_invalidations.jsonl').exists()

def test_chinese_plan_newline_hash_interoperability(tmp_path):
    import hashlib
    from app.reference_roles import record_approved_design_scope, parse_design_scope
    project(tmp_path)
    lf='中文方案：保留墙体。\n'+PLAN+'\n请确认。\n'
    crlf=lf.replace('\n','\r\n');cr=lf.replace('\n','\r')
    snapshot=capture_pending_design_plan(tmp_path,crlf,is_followup=True)
    expected=hashlib.sha256(lf.encode('utf-8')).hexdigest()
    assert snapshot['plan_sha256']==expected
    scope=approve_pending_design_plan(tmp_path,'message:newlines',cr,expected)
    assert scope['plan_sha256']==expected and scope['plan_text']==lf
    assert record_approved_design_scope(tmp_path,'message:newlines',crlf,parse_design_scope(lf))['version']==scope['version']
    assert capture_pending_design_plan(tmp_path,lf,is_followup=True)['plan_sha256']==expected
