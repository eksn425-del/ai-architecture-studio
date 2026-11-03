import pytest
from app.dsh_interactions import Interactions


def test_approval_is_one_shot_and_cancel_never_grants():
    bridge=Interactions()
    first=bridge.create({'kind':'approval','tool':'pwsh','reason':'review'})
    assert bridge.pending()[0]['status']=='pending'
    with pytest.raises(ValueError):bridge.answer(first['id'], 'always')
    bridge.answer(first['id'],'allowed-once')
    assert bridge.get(first['id'])['answer']=='allowed-once'
    with pytest.raises(ValueError):bridge.answer(first['id'],'allowed-once')
    second=bridge.create({'kind':'approval'})
    bridge.cancel()
    assert bridge.get(second['id'])['status']=='cancelled'
    with pytest.raises(ValueError):bridge.answer(second['id'],'allowed-once')


def test_questions_validate_options_and_preserve_text():
    bridge=Interactions()
    question=bridge.create({'kind':'question','questions':[{'id':'a','question':'楼高？','options':[{'label':'三米'}]}]})
    with pytest.raises(ValueError):bridge.answer(question['id'],{'answers':[{'id':'a','selected':['未知']}]})
    bridge.answer(question['id'],{'answers':[{'id':'a','selected':[],'custom':'四米'}]})
    assert bridge.get(question['id'])['answer']['answers'][0]['custom']=='四米'


def test_interactions_are_not_shared_between_turns():
    first,second=Interactions(),Interactions()
    row=first.create({'kind':'approval'})
    with pytest.raises(ValueError):second.answer(row['id'],'allowed-once')
    copy=first.pending();copy[0]['status']='answered'
    assert first.get(row['id'])['status']=='pending'
