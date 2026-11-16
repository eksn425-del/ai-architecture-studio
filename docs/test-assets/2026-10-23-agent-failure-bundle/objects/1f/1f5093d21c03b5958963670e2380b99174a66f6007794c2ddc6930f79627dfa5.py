"""Owner-authorized fixed read-only diagnosis; never calls a writer."""
import json, os, sys
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parent
PROJECT=Path('E:/K AI 产品建模网站/runtime/projects/architecture-project-16c07')
CODE=Path('C:/Users/LOCAL_USER/.codex/worktrees/release-prep-20261019/K AI 产品建模网站')
sys.path.insert(0,str(CODE))
os.environ['ARCH_STUDIO_MCP_CONFIG']='E:/K AI 产品建模网站/outputs/deepseek-provider-test-20261021/sketchup-bridge.local.json'
from app.project_ruby import ProjectRubyExecutor
from app.sketchup_mcp import ConfiguredSketchUpMCP, SketchUpAdapter, MCPCallError
from app.su_relation_audit import audit_su_relations
assert json.load(urlopen('http://127.0.0.1:8803/api/status'))['active_project_id'] is None
session=json.loads((PROJECT/'state/agent_session.json').read_text(encoding='utf8'))
saved=json.loads((PROJECT/'runtime/project_ruby_state.json').read_text(encoding='utf8'))
state=saved['scripts']; assert state['terraced_apartment']['revision']==13
client=ConfiguredSketchUpMCP(); adapter=SketchUpAdapter(client)
identity=adapter.get_active_model_identity()
expected=(PROJECT/session['model_path']).resolve()
assert Path(identity['model_path']).resolve()==expected
# A stale expected token must pass actual native ownership proof to rebind.
executor=ProjectRubyExecutor(PROJECT.parent.parent,PROJECT.name,expected_model_path=expected,
    expected_model_guid='readonly-stale-token-test',mcp=client,adapter=adapter,ruby_state=state)
result={}
try:
    executor.inspect_owned({'script_id':'terraced_apartment','path':['BUILDING','TOWER','FACADE','TOWER_L01','REAR_GLAZING_4']})
except MCPCallError as error:
    result['missing_path_error']=str(error)
    assert 'TOWER_L01' in str(error) and 'REAR_GLAZING_4' in str(error)
else:
    raise AssertionError('Historical missing path unexpectedly exists; inspect without guessing')
executor.expected_model_guid='readonly-stale-token-test-two'
result['relation']=audit_su_relations(executor,'terraced_apartment',[{
    'a':['BUILDING','TOWER','MASSING'],'b':['BUILDING','TOWER','ROOF'],'axis':2,'tolerance':.001}])
assert result['relation']['revision']==13
assert result['relation']['model_identity']['model_guid']==executor.expected_model_guid
assert state['terraced_apartment']['revision']==13
result['native_writes']=0
out=ROOT/'native-readonly-results.json'; assert not out.exists()
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'missing_path_identified':True,'guid_verified_before_audit':True,'revision':13,'native_writes':0,'output':str(out)},ensure_ascii=False))
