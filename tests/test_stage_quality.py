import json
import pytest
from app.stage_quality import geometry_stage_limit, continuation_message, ReviewProgress, geometry_diagnostics
from app.blender_backend import BlenderBackend
from app.agent_tools import AgentToolSurface

def test_finite_configurable_stage_limits(monkeypatch):
    assert geometry_stage_limit(False)==('initial_build',3)
    assert geometry_stage_limit(True)==('targeted_repair',2)
    monkeypatch.setenv('KSTUDIO_REPAIR_GEOMETRY_LIMIT','5')
    assert geometry_stage_limit(True)[1]==5
    for raw in ['0','-1','13','unlimited','1.5']:
        monkeypatch.setenv('KSTUDIO_REPAIR_GEOMETRY_LIMIT',raw)
        with pytest.raises(ValueError):geometry_stage_limit(True)

def test_review_progress_distinguishes_repeats_from_distinct_revisions():
    p=ReviewProgress()
    def receipt(rev,problem='seam remains'):
        return {'model_revisions':{'root':rev},'needs_fix':True,'issues':[{'view':'rear','problem':problem}]}
    p.observe(receipt(1));p.observe(receipt(1));p.observe(receipt(1));assert not p.blocked
    p.observe(receipt(2));assert not p.blocked
    p.observe(receipt(3));assert p.advisory_stagnation and not p.blocked
    p.observe(receipt(4,'different issue'));assert not p.blocked
    assert '质量尚未通过' in continuation_message('targeted_repair',2,5,'no_progress')

def box(name,x=0):return {'id':name,'location':[x,0,0],'dimensions':[1,1,1]}

def test_exact_geometry_diagnostics_are_not_fidelity_acceptance():
    qa=geometry_diagnostics({'a':box('a'),'b':box('b')})
    assert any(i['kind']=='duplicate_box_volume' for i in qa['issues'])
    assert qa['quality_status']=='unverified'
    touching=geometry_diagnostics({'a':box('a'),'b':box('b',1)})
    assert any(i['kind']=='coincident_full_face' for i in touching['issues'])
    disjoint=geometry_diagnostics({'a':box('a'),'b':box('b',3)})
    assert disjoint['status']=='no_findings_in_supported_checks'
    assert disjoint['quality_status']=='unverified'
    mesh={'location':[0,0,0],'vertices':[[0,0,0],[1,0,0],[0,1,0]],'faces':[[0,1,2],[2,1,0]]}
    assert geometry_diagnostics({'mesh':mesh})['issues'][0]['kind']=='coincident_full_face'

def test_real_blender_budget_identical_no_progress_and_retained_candidate(tmp_path,monkeypatch):
    (tmp_path/'state').mkdir();(tmp_path/'state/modeling_backend.json').write_text('{"backend":"blender"}')
    monkeypatch.setenv('KSTUDIO_INITIAL_GEOMETRY_LIMIT','1')
    tools=AgentToolSurface(tmp_path,None,oss_backends={}).prepare(project_dir=tmp_path,mcp_enabled=True,model_path=None,model_guid='',ruby_enabled=False,ruby_state={})
    result=tools.dispatch('blender_apply_objects',{'objects':[box('a'),box('b')]})
    assert result['native_reopen']=='PASS' and result['quality_status']=='unverified'
    assert result['geometry_qa']['status']=='review_required'
    assert tools.quality_state['writes']==1
    before=(tmp_path/'runtime/blender/scene.json').read_bytes()
    with pytest.raises(ValueError,match='安全修改上限'):
        tools.dispatch('blender_apply_objects',{'objects':[box('a',2)]})
    assert (tmp_path/'runtime/blender/scene.json').read_bytes()==before
    assert tools.dispatch('blender_inspect_scene',{})['revision']==1
    with pytest.raises(ValueError,match='No geometry progress'):
        BlenderBackend(tmp_path).dispatch('blender_apply_objects',{'objects':[box('a')]})
    assert (tmp_path/'runtime/blender/scene.json').read_bytes()==before
    assert (tmp_path/result['model_path']).is_file()

def test_su_repeated_review_is_advisory_without_host_outcome_preserves_readonly(tmp_path,monkeypatch):
    from app.sketchup_mcp import MCPCallError
    class Executor:
        def __init__(self,*a,**kw):self.ruby_state=kw['ruby_state']
    monkeypatch.setattr('app.agent_tools.ProjectRubyExecutor',Executor)
    monkeypatch.setenv('KSTUDIO_INITIAL_GEOMETRY_LIMIT','7')
    surface=AgentToolSurface(tmp_path,object(),oss_backends={})
    monkeypatch.setattr(surface,'dynamic_tools',lambda **kw:[])
    def run(name,args,**kw):
        if name=='sketchup_run_workspace_ruby':
            state=kw['project_ruby'].ruby_state
            state['villa']={'revision':state.get('villa',{}).get('revision',0)+1}
        return {'success':True}
    monkeypatch.setattr(surface,'dispatch',run)
    monkeypatch.setattr('app.agent_tools.submit_visual_review',lambda project,state,args:{
        'needs_fix':True,'model_revisions':{'villa':state['villa']['revision']},
        'issues':[{'view':'rear','problem':'same unresolved seam'}]})
    context=surface.prepare(project_dir=tmp_path,mcp_enabled=True,model_path=tmp_path/'fixture.skp',model_guid='fixture',ruby_enabled=True,ruby_state={},tool_profile='reconstruction_coding')
    for i in range(3):
        context.dispatch('sketchup_run_workspace_ruby',{'update_mode':'edit','allowed_mutation_paths':[['WALL']]})
        context.dispatch('sketchup_submit_visual_review',{})
    assert context.quality_state['write_limit']==7 and context.quality_state['writes']==3
    assert context.quality_state['advisory_stagnation']
    assert not context.quality_state['no_progress']
    assert context.dispatch('sketchup_get_model_info',{})['success']
