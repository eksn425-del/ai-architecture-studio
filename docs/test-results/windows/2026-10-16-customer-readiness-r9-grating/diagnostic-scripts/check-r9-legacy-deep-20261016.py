from pathlib import Path
import json,time,sys
R=Path.cwd();sys.path.insert(0,str(R));from app.sketchup_mcp import SketchUpAdapter,ConfiguredSketchUpMCP
D=R/'runtime/customer-readiness-20261015';a=SketchUpAdapter(ConfiguredSketchUpMCP(timeout_seconds=120));i=a.get_active_model_identity();start=time.monotonic()
try:
 d=a.capture_native_deep_fingerprint(expected_model_path=Path(i['model_path']),expected_guid=i['model_guid'],root_pid=20606,output_path=D/'r9-deep-v1-before-save.json');print('V1_DEEP_SUCCESS',d['counts'])
except Exception as e:
 o={'status':'BLOCKED','stage':'r9 whole-document legacy deep collector','geometry_writes':0,'error_type':type(e).__name__,'error':str(e),'elapsed_ms':round((time.monotonic()-start)*1000),'model_path':i['model_path'],'model_guid':i['model_guid'],'root_pid':20606};(D/'r9-deep-v1-limit-failure.json').write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8');print(str(e)[:700])
