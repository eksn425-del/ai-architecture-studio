"""Exercise cp936 default file I/O on Linux; actual Windows execution is separate."""
import json
from pathlib import Path
import pytest
from app.design_scope_approval import capture_pending_design_plan,approve_pending_design_plan
from app.reference_roles import load_approved_design_scope,current_model_revisions

def test_utf8_approval_state_under_emulated_cp936_default(tmp_path,monkeypatch):
 state=tmp_path/'state';state.mkdir()
 context=state/'project_context.json'
 context.write_text(json.dumps({'project_name':'中文建筑🌿','references':[]},ensure_ascii=False),encoding='utf-8')
 original_open=Path.open
 original_read=Path.read_text;original_write=Path.write_text
 def cp936_open(self,mode='r',buffering=-1,encoding=None,errors=None,newline=None):
  if 'b' not in mode and encoding is None:encoding='cp936'
  return original_open(self,mode,buffering,encoding,errors,newline)
 monkeypatch.setattr(Path,'open',cp936_open)
 # Python 3.12 may resolve None into 'locale' or UTF-8 before Path.open.
 # Intercept the default entry arguments as well, preserving explicit UTF-8.
 def cp936_read(self,encoding=None,errors=None):
  return original_read(self,encoding=encoding or 'cp936',errors=errors)
 def cp936_write(self,data,encoding=None,errors=None,newline=None):
  return original_write(self,data,encoding=encoding or 'cp936',errors=errors,newline=newline)
 monkeypatch.setattr(Path,'read_text',cp936_read)
 monkeypatch.setattr(Path,'write_text',cp936_write)
 with pytest.raises(UnicodeDecodeError):context.read_text()  # Reproduces the reported implicit-default failure.
 plan='<design_scope>[{"feature_id":"window","requested_state":"中文窗户🌿下沿保持"}]</design_scope>'
 snapshot=capture_pending_design_plan(tmp_path,plan,is_followup=True)
 scope=approve_pending_design_plan(tmp_path,'用户批准🌿',plan,snapshot['plan_sha256'])
 assert load_approved_design_scope(tmp_path)==scope
 assert scope['features'][0]['requested_state']=='中文窗户🌿下沿保持'
 capture_pending_design_plan(tmp_path,'新计划🌿',is_followup=True)
 log=tmp_path/'runtime/design_scope_invalidations.jsonl'
 assert '中文窗户🌿' in log.read_text(encoding='utf-8')
 (state/'modeling_backend.json').write_text('{"backend":"blender","说明":"中文🌿"}',encoding='utf-8')
 scene=tmp_path/'runtime/blender/scene.json';scene.parent.mkdir();scene.write_text('{"revision":3,"说明":"中文🌿"}',encoding='utf-8')
 assert current_model_revisions(tmp_path)=={'blender_scene':3}
