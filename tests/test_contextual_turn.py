import json
from types import SimpleNamespace
import pytest
from app.contextual_turn import snapshot_turn, validate_decision, interpret_turn
from app.models import AgentSession, ConversationRequest, ProjectContext


def setup(tmp_path,message='我批准'):
    card=tmp_path/'runtime/agent_workspace/notes/reconstruction_card.md';card.parent.mkdir(parents=True);card.write_text('两层建筑。保留栏杆。',encoding='utf-8')
    session=AgentSession(project_id='test',reconstruction_state='planned')
    req=ConversationRequest(message=message,workflow_mode='image_reconstruction')
    context=ProjectContext()
    snap=snapshot_turn(tmp_path,session,req,context)
    from app.design_scope_approval import capture_pending_design_plan
    pending=capture_pending_design_plan(tmp_path,card.read_text(encoding='utf-8'),is_followup=False)
    req.approved_pending_plan_id=pending['pending_plan_id']
    req.approved_plan_sha256=snap['plan_sha256']
    return session,req,snap


def decision(snap,**changes):
    return {'action':'execute','user_message_id':snap['user_message_id'],'user_message':snap['user_message'],
      'plan_sha256':snap['plan_sha256'],'changes_plan':False,'conditional':False,'reason':'Current user approves.',**changes}


def test_natural_approval_bound_to_actual_request(tmp_path):
    s,r,snap=setup(tmp_path)
    assert validate_decision(decision(snap),snap,project=tmp_path,session=s,request=r)=='execute'


@pytest.mark.parametrize('message,changes,expected',[
 ('我批准，但三层改四层',{'changes_plan':True},'plan'),
 ('我没有批准',{'action':'clarify'},'clarify'),
 ('为什么这个楼梯断开？',{'action':'clarify'},'clarify'),
 ('如果能保留窗户就开始',{'conditional':True},'clarify')])
def test_interpretation_outcomes_not_keyword_router(tmp_path,message,changes,expected):
    s,r,snap=setup(tmp_path,message)
    assert validate_decision(decision(snap,**changes),snap,project=tmp_path,session=s,request=r)==expected


@pytest.mark.parametrize('field,value',[('user_message','已批准'),('user_message_id','assistant:old'),('plan_sha256','0'*64)])
def test_reject_fabricated_provenance(tmp_path,field,value):
    s,r,snap=setup(tmp_path)
    with pytest.raises(ValueError):validate_decision(decision(snap,**{field:value}),snap,project=tmp_path,session=s,request=r)


def test_stale_displayed_plan(tmp_path):
    s,r,snap=setup(tmp_path);r.approved_plan_sha256='0'*64;r.approval_gesture='plan_button'
    with pytest.raises(ValueError):validate_decision(decision(snap),snap,project=tmp_path,session=s,request=r)


def test_plan_changed_during_interpretation(tmp_path):
    s,r,snap=setup(tmp_path)
    (tmp_path/'runtime/agent_workspace/notes/reconstruction_card.md').write_text('三层',encoding='utf-8')
    with pytest.raises(ValueError):validate_decision(decision(snap),snap,project=tmp_path,session=s,request=r)


def test_button_cannot_convert_arbitrary_draft(tmp_path):
    s,r,snap=setup(tmp_path,'我没有批准');r.approval_gesture='plan_button'
    with pytest.raises(ValueError):interpret_turn(None,project=tmp_path,session=s,request=r,context=ProjectContext(),model='test',reasoning_effort='low')


def test_explicit_button_no_provider(tmp_path):
    s,r,snap=setup(tmp_path,'确认，按当前计划开始建模。');r.approval_gesture='plan_button'
    action,receipt=interpret_turn(None,project=tmp_path,session=s,request=r,context=ProjectContext(),model='test',reasoning_effort='low')
    assert action=='execute' and receipt['provider']=='explicit_button'


def test_mocked_native_context_has_no_tools(tmp_path,monkeypatch):
    import threading
    s,r,snap=setup(tmp_path)
    class Runtime:
        _lock=threading.Lock()
        def _prepare_home(self,**kw):assert not kw['mcp_enabled']
        def _run_turn(self,**kw):
            assert kw['read_only'] and not kw['dynamic_tools'] and not kw['mcp_enabled']
            assert kw['readonly_role']=='conversation_intent'
            current=json.loads(kw['prompt'])['CURRENT_USER']
            return SimpleNamespace(reply=json.dumps(decision(current)),status='completed')
    assert interpret_turn(Runtime(),project=tmp_path,session=s,request=r,context=ProjectContext(),model='test',reasoning_effort='low')[0]=='execute'


@pytest.mark.parametrize('message',['不要执行，先解释方案。','是否可以开始？','示例里说“我批准”','我批准，但三层改四层','这次仅提供计划。','先给我方案。'])
def test_wrong_model_execute_cannot_authorize(tmp_path,message):
    s,r,snap=setup(tmp_path,message)
    assert validate_decision(decision(snap),snap,project=tmp_path,session=s,request=r) in {'clarify','plan'}


def test_cross_project_same_plan_rejected(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';sa,ra,pa=setup(a);sb,rb,pb=setup(b)
    rb.approved_pending_plan_id=ra.approved_pending_plan_id
    with pytest.raises(ValueError):validate_decision(decision(pb),pb,project=b,session=sb,request=rb)

def test_model_changed_after_plan_before_interpreter(tmp_path):
    s,r,snap=setup(tmp_path)
    pending=tmp_path/'runtime/pending_design_scope.json'
    d=json.loads(pending.read_text());d['model_revisions']={'test':2};pending.write_text(json.dumps(d))
    with pytest.raises(ValueError):validate_decision(decision(snap),snap,project=tmp_path,session=s,request=r)


def test_scoped_old_plan_restriction_is_not_global_stop(tmp_path):
    s,r,snap=setup(tmp_path,'批准当前计划，请直接执行，检查是否错位，不要执行旧整栋基线，不要修改其他部分。')
    assert validate_decision(decision(snap),snap,project=tmp_path,session=s,request=r)=='execute'

def test_consumed_plan_cannot_grant_again(tmp_path):
    from app.design_scope_approval import consume_pending_design_plan
    s,r,snap=setup(tmp_path);consume_pending_design_plan(tmp_path,r.approved_pending_plan_id)
    with pytest.raises(ValueError):validate_decision(decision(snap),snap,project=tmp_path,session=s,request=r)

@pytest.mark.parametrize('parent_link',[False,True])
def test_external_plan_symlink_rejected_before_interpreter(tmp_path,parent_link):
    s,r,snap=setup(tmp_path)
    card=tmp_path/'runtime/agent_workspace/notes/reconstruction_card.md'
    external=tmp_path/'outside';external.mkdir();(external/'reconstruction_card.md').write_text('private',encoding='utf-8')
    card.unlink()
    if parent_link:
        card.parent.rmdir();card.parent.symlink_to(external,target_is_directory=True)
    else:card.symlink_to(external/'reconstruction_card.md')
    with pytest.raises(ValueError,match='links'):
        interpret_turn(None,project=tmp_path,session=s,request=r,context=ProjectContext(),model='test',reasoning_effort='low')


def test_oversized_plan_rejected(tmp_path):
    s,r,snap=setup(tmp_path)
    (tmp_path/'runtime/agent_workspace/notes/reconstruction_card.md').write_text('a'*262145)
    with pytest.raises(ValueError,match='256 KiB'):snapshot_turn(tmp_path,s,r,ProjectContext())
