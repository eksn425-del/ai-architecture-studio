"""Negative controls against the same saved supervised model; do not alter it."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from interactive_seam import context
from app.sketchup_mcp import MCPCallError
root=Path(sys.argv[1]).resolve();ctx=context(root)
def native():return json.loads(ctx.dispatch('blender_inspect',{})['contentItems'][0]['text'])
base=native();sha=base['geometry_sha256'];file=root/'scene'/'scene.blend';bytes_before=hashlib.sha256(file.read_bytes()).hexdigest();checks=[]
cases=[('stale_digest','blender_edit_parts',{'expected_geometry_sha256':'0'*64,'parts':[{'name':'pavilion_roof','dimensions':[7,5,.25],'location':[0,0,3.125]}]}),('host_scope_denies_column','blender_edit_parts',{'expected_geometry_sha256':sha,'parts':[{'name':'column_sw','dimensions':[1,1,1],'location':[0,0,0]}]}),('partial_failed_batch_not_committed','blender_create_assembly',{'expected_geometry_sha256':sha,'parts':[{'name':'TemporaryBeforeFailure','dimensions':[1,1,1],'location':[0,0,0]},{'name':'pavilion_roof','dimensions':[1,1,1],'location':[0,0,0]}]})]
for name,tool,args in cases:
    try:ctx.dispatch(tool,args)
    except MCPCallError as error:checks.append({'name':name,'rejected':True,'detail':str(error)})
    else:raise AssertionError(name+' unexpectedly passed')
    assert hashlib.sha256(file.read_bytes()).hexdigest()==bytes_before
    assert native()['geometry_sha256']==sha
out={'checks':checks,'all_rejected':True,'saved_file_byte_identical':True,'native_reopen_geometry_identical':True};(root/'guard_checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
