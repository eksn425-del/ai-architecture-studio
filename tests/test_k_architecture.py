import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.k_architecture import ArchitectureContext, validate_graph, specs, catalog
from app.su_harness_tools import SUHarnessTools
from app.deepseek_studio import DeepSeekStudioRuntime

def graph():
    return {'summary':'建筑主体、开放露台、独立屋顶与围护系统',
      'facts':[{'text':'开放露台','basis':'observed','source':'source_1'}],
      'levels':[{'name':'ground','z_mm':0,'role':'ground'},{'name':'terrace','z_mm':3300,'role':'open'}],
      'parts':['Roof','Slabs','Glazing'],'relationships':['露台空间不得填满，玻璃后退'],'edit_parts':['Roof']}

def context(tmp_path, stage='plan', state=None):
    image=tmp_path/'ref.png';image.write_bytes(b'ref')
    return ArchitectureContext(tmp_path,stage,[image],[{'role':'user','content':'只改屋顶'},
        {'role':'assistant','content':'建议修改全楼'}],state)

def bind(c):
    c.save_graph(graph()); c.card.parent.mkdir(parents=True,exist_ok=True)
    c.card.write_text('只改屋顶，其余保持不变。',encoding='utf-8');c.bind_plan()

def test_real_pack_and_read_receipts_no_paths(tmp_path):
    c=context(tmp_path)
    assert len(catalog())==6
    for entry in catalog():assert c.read_skill({'id':entry['id']})['sha256']==entry['sha256']
    assert len((c.base/'skill-usage.jsonl').read_text().splitlines())==6
    with pytest.raises(ValueError):c.read_skill({'id':'../../secret'})

@pytest.mark.parametrize('mutation',['scope','levels','nan','source','duplicate'])
def test_bad_graph_never_reaches_model(mutation):
    g=graph()
    if mutation=='scope':g['edit_parts']=['Everything']
    if mutation=='levels':g['levels'][1]['z_mm']=-1
    if mutation=='nan':g['levels'][1]['z_mm']=float('nan')
    if mutation=='source':g['facts'][0]['source']='imaginary'
    if mutation=='duplicate':g['parts'].append('Roof')
    with pytest.raises(ValueError):validate_graph(g,{'source_1'})


def test_tool_contract_explains_and_rejects_observed_graph_shape_failures():
    from jsonschema import Draft202012Validator
    schema=next(s['inputSchema'] for s in specs('plan') if s['name']=='kstudio_save_design_graph')
    validator=Draft202012Validator(schema)
    valid=graph()
    valid['spatial']={'coordinate_frame':{'units':'mm','x':'right','front':'-Y','up':'+Z','origin':'front left corner'}}
    validator.validate(valid)
    validate_graph(valid,{'source_1'})
    bad=json.loads(json.dumps(valid));bad['spatial']['coordinate_frame']['front']='Y negative'
    assert list(validator.iter_errors(bad))
    bad=json.loads(json.dumps(valid));bad['parts']=[{'name':'Roof'}]
    assert list(validator.iter_errors(bad))
    assert list(validator.iter_errors({'graph':valid}))

@pytest.mark.parametrize('changed',['graph','card','image'])
def test_scope_binding_survives_restart_and_rejects_changes(tmp_path,changed):
    c=context(tmp_path);bind(c)
    resumed=ArchitectureContext(tmp_path,'execute',[tmp_path/'ref.png'],[],{})
    assert resumed.execution_parts()=={'Roof'}
    if changed=='graph':
        g=graph();g['edit_parts']=['Glazing'];c.graph_path.write_text(json.dumps(g))
    if changed=='card':c.card.write_text('changed')
    if changed=='image':
        (tmp_path/'ref.png').write_bytes(b'changed')
        resumed=ArchitectureContext(tmp_path,'execute',[tmp_path/'ref.png'],[],{})
    with pytest.raises(ValueError):resumed.execution_parts()

def test_actual_shared_revision_invalidates_stale_views(tmp_path):
    state={};c=context(tmp_path,'execute',state)
    state['harness_building']={'revision':4}
    q={'views':{v:{'revision':4} for v in ('front','oblique','roof')}}
    assert c.review(q)['evidence_current']
    state['harness_building']['revision']=5
    assert c.review(q)['missing_current_views']==['front','oblique','roof']
    assert c.review(q)['native_reopen']=='NOT_RUN'
    with pytest.raises(ValueError):c.save_graph(graph())


def test_local_repair_reuses_bound_facts_and_only_changes_approved_part_proposal(tmp_path):
    state = {'harness_building': {'root_pid': 19, 'revision': 11}}
    c = context(tmp_path, state=state)
    bind(c)
    scope = c.reusable_edit_graph()['parts']
    assert scope == graph()['parts']
    tool = next(s for s in specs('plan', scope) if s['name'] == 'kstudio_scope_existing_parts')
    assert tool['inputSchema']['properties']['edit_parts']['items']['enum'] == scope
    with pytest.raises(ValueError):
        c.scope_existing_parts({'edit_parts': ['NewPart']})
    saved = c.scope_existing_parts({'edit_parts': ['Slabs']})
    assert saved['approval_granted'] is False
    assert json.loads(c.graph_path.read_text('utf8')) == {**graph(), 'edit_parts': ['Slabs']}
    still_unbound = ArchitectureContext(tmp_path, 'execute', [tmp_path/'ref.png'], [], state)
    with pytest.raises(ValueError):
        still_unbound.execution_parts()
    # An interrupted planning turn can leave a new draft while the last
    # bound graph still supplies the unchanged design facts.
    assert c.reusable_edit_graph() == graph()
    c.scope_existing_parts({'edit_parts': ['Slabs']})
    c.card.write_text('只修楼板原位置的局部接边。', encoding='utf8')
    c.bind_plan()
    assert still_unbound.execution_parts() == {'Slabs'}
    (tmp_path/'ref.png').write_bytes(b'revised evidence')
    changed = ArchitectureContext(tmp_path, 'plan', [tmp_path/'ref.png'], [], state)
    assert changed.reusable_edit_graph() is None

def test_discussion_and_plan_expose_no_denied_native_tools(tmp_path):
    surface=SUHarnessTools(tmp_path,None)
    assert surface.prepare(project_dir=tmp_path,mcp_enabled=False,stage_scoped=True).dynamic_tools==[]
    plan=surface.prepare(project_dir=tmp_path,mcp_enabled=False,allow_plan=True,stage_scoped=True)
    assert [s['name'] for s in plan.dynamic_tools]==['sketchup_save_plan']
    assert {s['name'] for s in specs('clarify')}=={'kstudio_read_skill'}

def test_project_memory_does_not_promote_assistant_to_user(tmp_path):
    c=context(tmp_path)
    memory=c.memory()
    assert [m['content'] for m in memory['conversation'] if m['role']=='user']==['只改屋顶']
    assert memory['design_graph_proposal'] is None
    c.conversation.extend([{'role':'user','content':'确认'}, {'role':'assistant','content':'已执行'}])
    assert [m['role'] for m in c.memory()['conversation']]==['user','assistant','user','assistant']

def test_failed_reasoning_usage_and_same_step_retry_are_both_preserved():
    from app.dsh_runtime import reported_usage
    attempt={'type':'assistant/attempt','data':{'turn':1,'step':1,'stream':[
        {'type':'chunk','chunk':{'type':'usage','usage':{'inputTokens':12394,'outputTokens':32768,'totalTokens':45162}}}]}}
    assert reported_usage([attempt])==(12394,32768)
    message={'type':'assistant/message','data':{'turn':1,'step':1,'usage':{'inputTokens':12394,'outputTokens':32768,'totalTokens':45162}}}
    assert reported_usage([attempt,message])==(24788,65536)
    unknown={'type':'assistant/attempt','data':{'turn':1,'step':1,'stream':[]}}
    assert reported_usage([unknown,message])==(None,None)

def test_product_plan_requires_graph_and_records_binding(tmp_path,monkeypatch):
    c=context(tmp_path);(tmp_path/'state').mkdir()
    (tmp_path/'state/project_context.json').write_text(json.dumps({'conversation':c.conversation}))
    monkeypatch.setattr('app.deepseek_studio.discover_project_reference_images',lambda _: [tmp_path/'ref.png'])
    runtime=DeepSeekStudioRuntime(tmp_path,connection={'model':'deepseek-v4.1-flash','api_base':'https://example.invalid/v1',
        'api_key':'fake','mode':'codex-responses'},mcp=None)
    def turn(**kw):
        names={s['name'] for s in kw['specs']}
        assert 'sketchup_apply_parts' not in names
        assert 'kstudio_save_design_graph' in names
        with pytest.raises(ValueError):kw['dispatch']('sketchup_save_plan',{'text':'方案内容'*20})
        kw['dispatch']('kstudio_save_design_graph',graph())
        kw['dispatch']('sketchup_save_plan',{'text':'只修改屋顶，保护其他建筑内容。'*10})
        return SimpleNamespace(reply='计划已准备')
    monkeypatch.setattr(runtime,'_official_turn',turn)
    runtime.respond(project_dir=tmp_path,thread_id=None,prompt='',mcp_enabled=False,agent_action='plan')
    assert c.execution_parts()=={'Roof'}


def test_execution_receives_current_core_skills_even_when_model_skips_read_tool(tmp_path,monkeypatch):
    monkeypatch.delenv('KSTUDIO_DSH_CAPABILITIES',raising=False)
    state={'harness_building':{'revision':1,'root_pid':19}}
    c=context(tmp_path,stage='plan',state=state);bind(c)
    (tmp_path/'state').mkdir();(tmp_path/'state/project_context.json').write_text(json.dumps({'conversation':c.conversation}))
    monkeypatch.setattr('app.deepseek_studio.discover_project_reference_images',lambda _:[tmp_path/'ref.png'])
    runtime=DeepSeekStudioRuntime(tmp_path,connection={'model':'deepseek-v4.1-flash','api_base':'https://example.invalid/v1','api_key':'fixture','mode':'codex-responses'},mcp=None)
    monkeypatch.setattr(runtime.tool_surface,'prepare',lambda **_:
        SimpleNamespace(dynamic_tools=[],quality_state={'views':{}},dispatch=lambda *_:None))
    observed=[]
    def turn(**kwargs):
        observed.append(kwargs['instructions'])
        return SimpleNamespace(reply='Fixture; no provider or native call.')
    monkeypatch.setattr(runtime,'_official_turn',turn)
    runtime.respond(project_dir=tmp_path,thread_id='old-fixture',prompt='继续',mcp_enabled=True,ruby_state=state,agent_action='execute')
    assert len(observed)==1
    for key in ('native','facade','spatial','edit'):
        assert 'HOST-LOADED ARCHITECTURE SKILL '+key+' sha256=' in observed[0]
    assert 'Face.pushpull' in observed[0]
    assert '`window_bay`' in observed[0]
    assert 'commit the simplest receiving part first' in observed[0]
    assert '用俯视核对梯段是否挡住主立面开口' in observed[0]
