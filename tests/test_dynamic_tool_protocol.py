import json
import pytest
from app.native_agent import canonical_dynamic_tools, NativeAgentUnavailable
from app.workspace_files import workspace_file_tools
from app.su_relation_audit import prepare_su_relation_tools
from app.design_scope_approval import capture_pending_design_plan, consume_pending_design_plan, restore_rejected_start_plan
ERROR='Codex thread/start failed: Invalid request: dynamic tools must use either canonical or legacy format consistently'

def test_combined_real_workspace_and_su_audit_specs_use_one_format_without_mutation():
    tools=workspace_file_tools()+prepare_su_relation_tools(object())[0]
    assert {t.get('type') for t in tools}=={None,'function'}
    result=canonical_dynamic_tools(tools)
    assert all(t['type']=='function' for t in result)
    assert [t['name'] for t in result]==[t['name'] for t in tools]
    assert [t['inputSchema'] for t in result]==[t['inputSchema'] for t in tools]
    assert any('type' not in t for t in tools)

def test_bad_tool_rejected_without_widening_handler():
    with pytest.raises(NativeAgentUnavailable):canonical_dynamic_tools([{'type':'namespace','name':'x','tools':[]}])

@pytest.mark.parametrize('change', ['none','thread','tool','error','plan','reference','id'])
def test_only_proven_prestart_rejection_can_restore_new_approval(tmp_path,change):
    (tmp_path/'state').mkdir(); (tmp_path/'state/project_context.json').write_text('{"references":[]}',encoding='utf-8')
    card=tmp_path/'runtime/agent_workspace/notes/reconstruction_card.md';card.parent.mkdir(parents=True);card.write_text('unchanged plan',encoding='utf-8')
    snap=capture_pending_design_plan(tmp_path,'unchanged plan',is_followup=False)
    consume_pending_design_plan(tmp_path,snap['pending_plan_id'])
    if change=='plan':card.write_text('changed',encoding='utf-8')
    if change=='reference':
        image=tmp_path/'inputs/reference/new.png';image.parent.mkdir(parents=True);image.write_bytes(b'new source')
        (tmp_path/'state/project_context.json').write_text('{"references":[{"type":"image","source":"inputs/reference/new.png","evidence_role":"target_building"}]}',encoding='utf-8')
    result=restore_rejected_start_plan(tmp_path,'wrong' if change=='id' else snap['pending_plan_id'],error='timeout' if change=='error' else ERROR,thread_id='started' if change=='thread' else '',tool_call_count=1 if change=='tool' else 0)
    assert result==(change=='none')
    assert json.loads((tmp_path/'runtime/pending_design_scope.json').read_text(encoding='utf-8'))['consumed']==(change!='none')
