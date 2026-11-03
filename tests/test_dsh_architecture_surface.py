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
