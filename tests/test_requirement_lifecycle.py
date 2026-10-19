import json
import pytest
from app.reference_roles import (validate_review_requirements, validate_review_resolutions,
    active_requirements, requirement_id, parse_design_scope, record_approved_design_scope,
    load_approved_design_scope)

MANIFEST=[{'source':'target.png','role':'target_building'}, {'source':'defect.png','role':'defect_location'}]
def req(text='remove redundant mullion',rev=1):
    return {'feature_id':'window.mullion','desired_state':text,'source_ref':'target.png',
            'model_revisions':{'villa':rev},'intent':{'property':'presence','value':False}}
def envelope(items):return '<review_requirements>'+json.dumps(items)+'</review_requirements>'
def check(item,history,scope=None):
    return validate_review_requirements(envelope([item]),manifest=MANIFEST,revisions={'villa':2},issue_count=1,history=history,approved_scope=scope)

def test_equivalent_and_refinement_no_longer_false_conflicts():
    old=req();history=[{'requirements':[old]}]
    for relation,text in [('equivalent','delete the unnecessary divider'),('refines','remove only the lower divider; preserve the frame')]:
        new={**req(text,2),'relation':relation,'prior_requirement_id':requirement_id(old),'evidence':'Current front capture and target show the same single opening.'}
        result=check(new,history)
        active=active_requirements(history+[{'requirements':result}])
        assert active['window.mullion']['desired_state']==text
        assert len(active)==1
    missing=req('different wording',2)
    with pytest.raises(ValueError,match='prior identity'):check(missing,history)

def test_true_opposite_intent_cannot_claim_equivalence():
    old=req();new={**req('restore the divider',2),'intent':{'property':'presence','value':True},'relation':'equivalent','prior_requirement_id':requirement_id(old),'evidence':'It should be present.'}
    with pytest.raises(ValueError,match='reverses'):check(new,[{'requirements':[old]}])
    new['relation']='supersedes';new['design_scope_version']=1;new['approved_requested_state']='add divider'
    with pytest.raises(ValueError):check(new,[{'requirements':[old]}])

def test_approved_feature_specific_scope_can_supersede_once(tmp_path):
    features=[{'feature_id':'window.mullion','requested_state':'add divider'}]
    plan='Proposed explicit change\n<design_scope>'+json.dumps(features)+'</design_scope>'
    scope=record_approved_design_scope(tmp_path,'user-approval-1',plan,features)
    assert scope==load_approved_design_scope(tmp_path)
    assert record_approved_design_scope(tmp_path,'user-approval-1',plan,features)==scope
    old=req();new={**req('add vertical divider',2),'intent':{'property':'presence','value':True},'relation':'supersedes','prior_requirement_id':requirement_id(old),'evidence':'User-approved scope changes this feature.', 'design_scope_version':1,'approved_requested_state':'add divider'}
    accepted=check(new,[{'requirements':[old]}],scope)[0]
    assert accepted['design_scope_version']==1
    wrong={**scope,'features':[{'feature_id':'roof','requested_state':'add divider'}]}
    with pytest.raises(ValueError):check(new,[{'requirements':[old]}],wrong)
    reverse={**req('remove divider again',2),'relation':'supersedes','prior_requirement_id':requirement_id(accepted),'evidence':'reverse','design_scope_version':1,'approved_requested_state':'add divider'}
    with pytest.raises(ValueError):check(reverse,[{'requirements':[accepted]}],scope)
    with pytest.raises(ValueError):record_approved_design_scope(tmp_path,'user-approval-1',plan+'changed',features)
    with pytest.raises(ValueError):record_approved_design_scope(tmp_path,'user-approval-2',plan,[])

def test_resolution_requires_explicit_current_evidence_and_never_omission():
    old=req();history=[{'requirements':[old]},{'requirements':[]}]
    assert active_requirements(history)
    resolution={'feature_id':old['feature_id'],'prior_requirement_id':requirement_id(old),'status':'resolved','source_ref':'target.png','model_revisions':{'villa':2},'evidence':'Current front view now shows opening without divider.'}
    def resolve(item):return validate_review_resolutions('<requirement_resolutions>'+json.dumps([item])+'</requirement_resolutions>',manifest=MANIFEST,revisions={'villa':2},history=history)
    checked=resolve(resolution)
    assert active_requirements(history+[{'requirements':[],'resolutions':checked}])=={}
    for mutation in [{'source_ref':'defect.png'},{'model_revisions':{'villa':1}},{'prior_requirement_id':'wrong'},{'evidence':''}]:
        with pytest.raises(ValueError):resolve({**resolution,**mutation})

def test_current_target_and_revision_guards_unchanged():
    old=req();new={**req('same intent, updated wording',2),'relation':'refines','prior_requirement_id':requirement_id(old),'evidence':'Current source/capture comparison.'}
    for mutation in [{'source_ref':'defect.png'},{'model_revisions':{'villa':1}},{'prior_requirement_id':'wrong'}]:
        with pytest.raises(ValueError):check({**new,**mutation},[{'requirements':[old]}])
    assert parse_design_scope('legacy plan')==[]
    with pytest.raises(ValueError):parse_design_scope('<design_scope>[{"feature_id":"*","requested_state":"anything"}]</design_scope>')

def test_new_requirement_binds_current_approval_epoch():
    scope={'version':1,'features':[{'feature_id':'window.mullion','requested_state':'add divider'}]}
    first=check(req(rev=2),[],scope)[0]
    assert first['design_scope_version']==1
    change={**req('add divider',2),'intent':{'property':'presence','value':True},'relation':'supersedes','prior_requirement_id':requirement_id(first),'evidence':'explicit changed plan','design_scope_version':1,'approved_requested_state':'add divider'}
    with pytest.raises(ValueError):check(change,[{'requirements':[first]}],scope)
    change['design_scope_version']=2
    assert check(change,[{'requirements':[first]}],{**scope,'version':2})[0]['design_scope_version']==2

def test_resolved_intent_cannot_be_reopened_as_opposite_new_requirement():
    old=req();resolution={'feature_id':old['feature_id'],'prior_requirement_id':requirement_id(old),'status':'resolved'}
    history=[{'requirements':[old]},{'resolutions':[resolution]}]
    opposite={**req('restore divider',2),'intent':{'property':'presence','value':True},'relation':'new'}
    with pytest.raises(ValueError):check(opposite,history)
    regression={**req(rev=2),'relation':'regression','prior_requirement_id':requirement_id(old),'evidence':'The previously removed divider reappeared in current front view.'}
    assert check(regression,history)[0]['status']=='active'


def test_unchanged_relation_with_changed_prose_reports_exact_conflict_without_accepting():
    old=req();history=[{'requirements':[old]}]
    new={**req('remove only the redundant lower divider',2),'relation':'unchanged',
         'prior_requirement_id':requirement_id(old),'evidence':'Current source shows the same missing divider requirement.'}
    with pytest.raises(ValueError) as caught:check(new,history)
    text=str(caught.value)
    assert 'feature=window.mullion' in text and 'relation=unchanged' in text
    assert 'desired_state_changed=True' in text and 'intent_changed=False' in text
    assert requirement_id(old) in text
    assert active_requirements(history)['window.mullion']['desired_state']==old['desired_state']
    new['relation']='refines'
    assert check(new,history)[0]['relation']=='refines'
