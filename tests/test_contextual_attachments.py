import pytest
from app.contextual_attachments import attachment_snapshot,apply_attachment_intent
from app.models import ProjectContext,Reference


def setup(tmp_path):
    p=tmp_path/'inputs/reference';p.mkdir(parents=True)
    (p/'a.png').write_bytes(b'image-a');(p/'b.png').write_bytes(b'image-b')
    c=ProjectContext(references=[Reference(type='image',source='inputs/reference/'+f,role_origin='awaiting_context',evidence_model_revisions={'blender':3}) for f in ['a.png','b.png']])
    return c


def decisions(snap,roles,quote):return [{'attachment_id':x['attachment_id'],'role':role,'evidence_quote':quote} for x,role in zip(snap,roles)]


def test_mixed_roles_exact_ids(tmp_path):
    c=setup(tmp_path);s=attachment_snapshot(tmp_path,c);msg='第一张是想做的建筑，第二张标了当前模型的问题。'
    assert apply_attachment_intent(tmp_path,c,s,decisions(s,['target_building','defect_location'],msg),msg)
    assert [r.evidence_role for r in c.references]==['target_building','defect_location']


@pytest.mark.parametrize('explicit',[True,False])
def test_no_model_override_of_manual_or_submitted(tmp_path,explicit):
    c=setup(tmp_path);r=c.references[0]
    if explicit:r.role_origin='user'
    else:r.submitted_at='previous-turn'
    s=attachment_snapshot(tmp_path,c)
    with pytest.raises(ValueError):apply_attachment_intent(tmp_path,c,s,decisions(s,['target_building'],'原图'),'原图')


def test_prior_defect_reupload_never_new_target_or_new_revision(tmp_path):
    c=setup(tmp_path);old=c.references[0];old.evidence_role='defect_location';old.submitted_at='old';old.evidence_model_revisions={'blender':2}
    (tmp_path/c.references[1].source).write_bytes(b'image-a')
    s=attachment_snapshot(tmp_path,c);item=s[1:]
    apply_attachment_intent(tmp_path,c,s,decisions(item,['target_building'],'原图'),'原图')
    assert c.references[1].evidence_role=='unknown'
    s=attachment_snapshot(tmp_path,c)
    apply_attachment_intent(tmp_path,c,s,decisions(s[1:],['defect_location'],'问题图'),'问题图')
    assert c.references[1].evidence_model_revisions=={'blender':2}


def test_invented_quote_and_changed_pixels_rejected(tmp_path):
    c=setup(tmp_path);s=attachment_snapshot(tmp_path,c)
    with pytest.raises(ValueError):apply_attachment_intent(tmp_path,c,s,decisions(s,['target_building'],'原图'),'继续')
    (tmp_path/c.references[0].source).write_bytes(b'changed')
    with pytest.raises(ValueError):apply_attachment_intent(tmp_path,c,s,[],'继续')


def test_omitted_roles_preserve_default_and_negative_cannot_promote(tmp_path):
    c=setup(tmp_path);c.references[0].evidence_role='target_building';c.references[0].role_origin='context_default'
    s=attachment_snapshot(tmp_path,c);assert not apply_attachment_intent(tmp_path,c,s,[],'继续')
    assert c.references[0].evidence_role=='target_building'
    apply_attachment_intent(tmp_path,c,s,decisions(s,['target_building'],'不是目标图'),'不是目标图')
    assert c.references[0].evidence_role=='unknown'


def test_same_readonly_turn_interprets_attachment_and_invalidates_plan(tmp_path):
    import json,threading
    from types import SimpleNamespace
    from app.contextual_turn import interpret_turn
    from app.models import AgentSession,ConversationRequest
    c=setup(tmp_path);session=AgentSession(project_id='test',reconstruction_state='planned')
    request=ConversationRequest(message='第一张是我想做的建筑，第二张是当前问题。',agent_action='plan')
    class Runtime:
        _lock=threading.Lock()
        def _prepare_home(self,**kw):pass
        def _run_turn(self,**kw):
            assert kw['read_only'] and not kw['dynamic_tools'] and not kw['mcp_enabled']
            current=json.loads(kw['prompt'])['CURRENT_USER']
            result={'action':'plan','user_message_id':current['user_message_id'],'user_message':current['user_message'],'plan_sha256':current['plan_sha256'],'changes_plan':False,'conditional':False,'reason':'New sources','attachment_roles':decisions(current['attachments'],['target_building','defect_location'],request.message)}
            return SimpleNamespace(reply=json.dumps(result),status='completed')
    action,receipt=interpret_turn(Runtime(),project=tmp_path,session=session,request=request,context=c,model='fixture',reasoning_effort='low')
    assert action=='plan' and receipt['attachment_roles_changed']
    assert session.reconstruction_state=='clarifying'
    pending=json.loads((tmp_path/'runtime/pending_design_scope.json').read_text(encoding='utf-8'))
    assert pending['features']==[] and pending['plan_sha256']


def test_mixed_clarification_negates_other_role_not_selected_role(tmp_path):
    c=setup(tmp_path);s=attachment_snapshot(tmp_path,c)
    message='第一张不是问题图，是目标建筑；第二张才是当前模型的问题图'
    apply_attachment_intent(tmp_path,c,s,decisions(s,['target_building','defect_location'],message),message)
    assert [x.evidence_role for x in c.references]==['target_building','defect_location']


def test_two_host_turns_sent_unknown_can_be_clarified_without_manual_selector(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.native_agent import AgentTurnResult
    app=create_app(runtime_root=tmp_path);client=TestClient(app)
    pid=client.post('/api/projects',json={'project_name':'Role clarification fixture'}).json()['project_id'];base='/api/projects/'+pid
    project=app.state.store.project_dir(pid)
    refs=project/'inputs/reference';refs.mkdir(exist_ok=True)
    for name in ['a.png','b.png']:(refs/name).write_bytes(name.encode())
    context=app.state.store.load_context(pid)
    context.references=[Reference(type='image',source='inputs/reference/'+n,role_origin='awaiting_context',evidence_model_revisions={'blender_scene':1}) for n in ['a.png','b.png']]
    app.state.store.save(context,project/'state/project_context.json')
    runtime=app.state.model_router.codex_runtime
    # _run_turn/respond are simulated below; CI must not borrow a real login.
    monkeypatch.setattr(type(runtime),'available',property(lambda self:True))
    monkeypatch.setattr(runtime,'_prepare_home',lambda **kw:None)
    calls=[]
    def interpret(**kw):
        assert kw['read_only'] and not kw['dynamic_tools']
        assert kw['reference_images']==[project/'inputs/reference/a.png',project/'inputs/reference/b.png']
        c=json.loads(kw['prompt'])['CURRENT_USER'];calls.append(c)
        clarify=len(calls)==1
        answer={'action':'clarify' if clarify else 'plan','user_message_id':c['user_message_id'],'user_message':c['user_message'],'plan_sha256':c['plan_sha256'],'conditional':False,'changes_plan':False,'reason':'Role intent','attachment_roles':[] if clarify else decisions(c['attachments'],['target_building','defect_location'],c['user_message'])}
        return SimpleNamespace(status='completed',reply=json.dumps(answer))
    monkeypatch.setattr(runtime,'_run_turn',interpret)
    def respond(**kw):
        assert not kw['mcp_enabled']
        if len(calls) > 1:
            card = project/'runtime/agent_workspace/notes/reconstruction_card.md'
            card.parent.mkdir(parents=True, exist_ok=True)
            card.write_text('按用户已解释的两张图整理两层建筑方案。', encoding='utf-8')
        return AgentTurnResult(thread_id='fixture',reply='你想照着哪张图建，哪张是现在模型的问题？' if len(calls)==1 else '已按来源整理计划。')
    monkeypatch.setattr(runtime,'respond',respond)
    first=client.post(base+'/conversation',json={'message':'请先聊一下这些图片','agent_action':'auto'})
    assert first.status_code==200,first.text
    saved=app.state.store.load_context(pid)
    assert all(r.submitted_at and r.role_clarification_pending for r in saved.references)
    second=client.post(base+'/conversation',json={'message':'第一张是目标建筑，第二张是当前模型的问题图。','agent_action':'auto'})
    assert second.status_code==200,second.text
    saved=app.state.store.load_context(pid)
    assert [r.evidence_role for r in saved.references]==['target_building','defect_location']
    assert not any(r.role_clarification_pending for r in saved.references)
    assert second.json()['agent']['geometry_committed'] is False
