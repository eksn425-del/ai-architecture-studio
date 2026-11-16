"""Private fixed READ-ONLY native inspection of this three-round case only."""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
PROJECT = Path('E:/K AI 产品建模网站/runtime/projects/architecture-project-16c07')
CODE = Path('C:/Users/LOCAL_USER/.codex/worktrees/release-prep-20261019/K AI 产品建模网站')
sys.path.insert(0, str(CODE))
os.environ['ARCH_STUDIO_MCP_CONFIG'] = 'E:/K AI 产品建模网站/outputs/deepseek-provider-test-20261021/sketchup-bridge.local.json'
from app.sketchup_mcp import SketchUpAdapter

p = argparse.ArgumentParser()
p.add_argument('stage')
p.add_argument('--model', type=Path)
args = p.parse_args()
assert args.stage in {'before-save', 'bound-reopened', 'download-reopened'}, 'Unknown stage'
with urlopen('http://127.0.0.1:8803/api/status', timeout=5) as response:
    assert json.load(response).get('active_project_id') is None, 'Single writer is still active'
session = json.loads((PROJECT/'state/agent_session.json').read_text(encoding='utf8'))
expected = (PROJECT/session['model_path']).resolve() if args.model is None else args.model.resolve()
assert expected.is_relative_to(PROJECT.resolve()) or expected.is_relative_to(ROOT.resolve()), 'Unrelated model refused'
assert expected.suffix.lower() == '.skp' and expected.is_file()
state = json.loads((PROJECT/'runtime/project_ruby_state.json').read_text(encoding='utf8'))
owned = state['scripts']['terraced_apartment']
assert owned['root_pid'] == 19
adapter = SketchUpAdapter()
identity = adapter.get_active_model_identity()
assert Path(identity['model_path']).resolve() == expected, 'Open the correct native file through UI first'
folder = ROOT/'native'
folder.mkdir(exist_ok=True)
out = folder/(args.stage+'.json')
payload = adapter.capture_native_deep_fingerprint(expected_model_path=expected, expected_guid=identity['model_guid'], root_pid=19, output_path=out, representation='definition_graph')
print(json.dumps({'stage':args.stage,'model_path':str(expected),'guid':identity['model_guid'],'root_pid':19,'revision':owned['revision'],'collector':payload['collector'],'definitions':payload.get('definition_count'),'groups':len(payload['groups']),'unique_entities':payload.get('unique_entities_visited'),'geometry_sha':payload['root_geometry_material_sha256'],'output':str(out)},ensure_ascii=False))
