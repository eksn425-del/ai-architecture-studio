from types import SimpleNamespace
import pytest
from app.dsh_architecture_surface import extend_surface


def test_native_writer_cannot_escape_approved_root_or_edit_scope(monkeypatch,tmp_path):
 calls=[]
 state={'harness_building':{'root_pid':42,'revision':2}}
 class Original:
  def __init__(self,*a):pass
  def prepare(self,**kw):
   return SimpleNamespace(dynamic_tools=[{'name':'sketchup_run_workspace_ruby'}],dispatch=lambda n,a:calls.append((n,a)) or {'success':True})
 monkeypatch.setattr('app.dsh_architecture_surface.AgentToolSurface',Original)
 base=SimpleNamespace(dynamic_tools=[],quality_state={'writes':[]},dispatch=lambda *a:None)
 s=extend_surface(base,runtime_root=tmp_path,mcp=None,project_dir=tmp_path,model_path=tmp_path/'a.skp',model_guid='g',ruby_state=state,allowed_parts={'Stairs'})
 def run(**extra):return s.dispatch('sketchup_run_workspace_ruby',{'script_id':'harness_building','relative_path':'scripts/a.rb',**extra})
 with pytest.raises(ValueError):run(update_mode='replace')
 with pytest.raises(ValueError):run(update_mode='edit',allowed_mutation_paths=[['Roof']])
 with pytest.raises(ValueError):run(update_mode='edit',allowed_mutation_paths=[['Stairs']],allow_full_rebuild=True)
 assert not calls
 assert run(update_mode='edit',allowed_mutation_paths=[['Stairs','Flight02']])['success']
 assert len(calls)==1
 assert base.quality_state['writes'][0]['revision']==2


def test_construction_receipt_requires_new_confirmed_native_revision(monkeypatch,tmp_path):
 state={'harness_building':{'root_pid':42,'revision':2,'durability_status':'saved_unverified_reopen'}}
 calls=[]
 class Original:
  def __init__(self,*a):pass
  def prepare(self,**kw):
   def write(n,a):
    calls.append(a)
    state['harness_building']['revision']+=1
    return {'success':True}
   return SimpleNamespace(dynamic_tools=[{'name':'sketchup_run_workspace_ruby','inputSchema':{'properties':{}}}],dispatch=write)
 monkeypatch.setattr('app.dsh_architecture_surface.AgentToolSurface',Original)
 base=SimpleNamespace(dynamic_tools=[],quality_state={'writes':[]},dispatch=lambda *a:{'success':True})
 s=extend_surface(base,runtime_root=tmp_path,mcp=None,project_dir=tmp_path,model_path=tmp_path/'a.skp',model_guid='g',ruby_state=state,allowed_parts={'Frames'})
 args={'script_id':'harness_building','update_mode':'edit','allowed_mutation_paths':[['Frames']],'construction_stage':'sample'}
 r=s.dispatch('sketchup_run_workspace_ruby',args)
 assert r['construction_step']['revision']==3
 assert r['construction_step']['system_complete'] is False
 assert 'construction_stage' not in calls[0]
 assert s.dispatch('sketchup_model_state',{})['construction_steps'][0]['revision']==3
 state['harness_building']['durability_status']='unconfirmed'
 assert 'construction_step' not in s.dispatch('sketchup_run_workspace_ruby',args)
 assert len((tmp_path/'runtime/construction_steps.jsonl').read_text().splitlines())==1
 with pytest.raises(ValueError):s.dispatch('sketchup_run_workspace_ruby',{**args,'construction_stage':'invented'})
 assert len(calls)==2

 # A failed optional ledger must never make an already committed write retryable.
 state['harness_building']['durability_status']='saved_unverified_reopen'
 ledger=tmp_path/'runtime/construction_steps.jsonl'
 ledger.unlink();ledger.mkdir()
 result=s.dispatch('sketchup_run_workspace_ruby',args)
 assert result['success'] is True
 assert result['construction_step_recording']=='failed_after_commit_do_not_replay'


def test_typed_construction_uses_the_same_committed_progress_ledger(monkeypatch, tmp_path):
    state = {'harness_building': {'root_pid': 42, 'revision': 1, 'durability_status': 'saved_unverified_reopen'}}
    original = SimpleNamespace(dynamic_tools=[])
    monkeypatch.setattr('app.dsh_architecture_surface.AgentToolSurface', lambda *_: SimpleNamespace(prepare=lambda **_: original))

    def dispatch(name, args):
        if name == 'sketchup_apply_parts':
            state['harness_building']['revision'] += 1
        return {'success': True}

    base = SimpleNamespace(dynamic_tools=[], quality_state={'writes': []}, dispatch=dispatch)
    surface = extend_surface(base, runtime_root=tmp_path, mcp=None, project_dir=tmp_path,
                             model_path=tmp_path / 'a.skp', model_guid='g', ruby_state=state, allowed_parts={'FrontWall'})
    result = surface.dispatch('sketchup_apply_parts', {'construction_stage': 'sample', 'parts': []})
    assert result['construction_step']['stage'] == 'sample'
    assert surface.dispatch('sketchup_model_state', {})['construction_steps'][0]['revision'] == 2
