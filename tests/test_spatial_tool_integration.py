from pathlib import Path
import pytest
from app.agent_tools import AgentToolSurface
from tests.test_su_relation_audit import ContractExecutor,relation

class Connector:
    def list_tools(self):return [{'name':'scene_summary','inputSchema':{'type':'object'}}]


def test_su_audits_host_native_evidence_no_caller_receipt(tmp_path,monkeypatch):
    import app.agent_tools as module
    executor=ContractExecutor()
    monkeypatch.setattr(module,'ProjectRubyExecutor',lambda *a,**kw:executor)
    surface=AgentToolSurface(tmp_path,Connector(),oss_backends={})
    tools=surface.prepare(project_dir=tmp_path/'p',mcp_enabled=True,model_path=Path('/mock/owned.skp'),model_guid='mock-guid',ruby_enabled=True,ruby_state=executor.ruby_state)
    assert {'sketchup_audit_relations','sketchup_audit_clearance'} <= {x['name'] for x in tools.dynamic_tools}
    result=tools.dispatch('sketchup_audit_relations',{'script_id':'main','connections':[relation()]})
    assert result['actual_walkability']=='unverified' and executor.calls
    assert tools.quality_state['sketchup_audit_relations']==result
    with pytest.raises(ValueError):tools.dispatch('sketchup_audit_relations',{'script_id':'main','connections':[relation()],'receipt':{}})


def test_readonly_discussion_does_not_construct_su_executor(tmp_path,monkeypatch):
    import app.agent_tools as module
    monkeypatch.setattr(module,'ProjectRubyExecutor',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('writer constructed')))
    tools=AgentToolSurface(tmp_path,Connector(),oss_backends={}).prepare(project_dir=tmp_path/'p',mcp_enabled=False,model_path=None,model_guid='',ruby_enabled=False,ruby_state={})
    assert not any(x['name'].startswith('sketchup_audit') for x in tools.dynamic_tools)

@pytest.mark.parametrize('audit_failure',[False,True])
def test_su_committed_write_delivers_fresh_audit_or_honest_failure(tmp_path,monkeypatch,audit_failure):
    import json
    import app.agent_tools as module
    executor=ContractExecutor()
    monkeypatch.setattr(module,'ProjectRubyExecutor',lambda *a,**kw:executor)
    review={'needs_fix':True,'issues':[{'priority':1,'problem':'Fixture contact gap'}],'keep':[]}
    monkeypatch.setattr(module,'load_current_independent_visual_review',lambda *a,**kw:review)
    monkeypatch.setattr(module,'record_repair_attempt',lambda *a,**kw:{'status':'fixture_recorded'})
    surface=AgentToolSurface(tmp_path,Connector(),oss_backends={})
    def native_write(name,args,**kw):
        assert name=='sketchup_run_project_ruby' and args['update_mode']=='edit'
        executor.ruby_state['main']['revision']=4
        executor.change=lambda payload:payload.update(revision=4,read_only=not audit_failure)
        return {'success':True,'contentItems':[{'type':'inputText','text':'Native fixture committed revision 4'}]}
    monkeypatch.setattr(surface,'dispatch',native_write)
    tools=surface.prepare(project_dir=tmp_path/'p',mcp_enabled=True,model_path=Path('/mock/owned.skp'),model_guid='mock-guid',ruby_enabled=True,ruby_state=executor.ruby_state,tool_profile='reconstruction_coding')
    tools.dispatch('sketchup_audit_relations',{'script_id':'main','connections':[relation()]})
    output=tools.dispatch('sketchup_run_project_ruby',{'script_id':'main','update_mode':'edit','allowed_mutation_paths':[['LANDING']]})
    audit=output['post_write_spatial_audits']['sketchup_audit_relations']
    assert executor.ruby_state['main']['revision']==4
    assert any('Post-write spatial audit' in x.get('text','') for x in output['contentItems'])
    if audit_failure:assert audit['status']=='unverified' and audit['geometry_already_committed'] is True
    else:assert audit['revision']==4 and audit['actual_walkability']=='unverified'
