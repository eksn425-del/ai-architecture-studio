import sys,os,json,argparse
from pathlib import Path
from urllib.request import urlopen
sys.path.insert(0,r"C:/Users/LOCAL_USER\.codex\worktrees\release-prep-20261019\K AI 产品建模网站")
os.environ['ARCH_STUDIO_MCP_CONFIG']=r"E:\K AI 产品建模网站\outputs\deepseek-provider-test-20261021\sketchup-bridge.local.json"
from app.sketchup_mcp import SketchUpAdapter
p=Path(r"E:\K AI 产品建模网站\runtime\projects\architecture-project-16c07\outputs\model")
bound=p/'blank-disposable-20261022-173456.skp'
download=p/'blank-disposable-download-check-20261023-r22.skp'
a=argparse.ArgumentParser();a.add_argument('stage',choices=['bound','download','return']);stage=a.parse_args().stage
with urlopen('http://127.0.0.1:8803/api/status',timeout=5) as f: assert json.load(f).get('active_project_id') is None
adapter=SketchUpAdapter()
expected=download if stage=='return' else bound
target=download if stage=='download' else bound
adapter.restore_disposable_model(target,expected)
identity=adapter.get_active_model_identity()
print(json.dumps({'stage':stage,'mechanism':'host_native_lifecycle_not_GUI','identity':identity},ensure_ascii=False))
