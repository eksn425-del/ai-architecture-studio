from pathlib import Path
import json,sys,hashlib
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.audit_native_path_scope import validate_protected_graph
D=R/'runtime/exterior-completion-20261016';B=R/'runtime/customer-readiness-20261015'
files=['scope-interior-completion-before-r14.json','scope-interior-completion-after-r15.json','scope-interior-completion-after-r16.json']
rows=[];snapshots=[]
for f in files:
 d=json.loads((B/f).read_text(encoding='utf8'));s=d['snapshot'];validate_protected_graph(s);snapshots.append(s)
 cleaned={k:v for k,v in s.items() if k!='model_guid'};h=hashlib.sha256(json.dumps(cleaned,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
 rows.append({'file':f,'actual_revision':d['revision'],'collector':d['collector'],'protected_sha256':h,'identity_proof':d.get('identity_proof')})
ok=snapshots[0]['paths']==snapshots[1]['paths']==snapshots[2]['paths'] and len({r['protected_sha256'] for r in rows})==1
out={'status':'PASS' if ok else 'FAIL','root_pid':20606,'scope':'Complete native graph outside actual host-approved25 exact leaves, including ancestor/sibling/loose geometry/identity/presentation; actual14->15->16, not a forged single-step writer receipt','snapshots':rows,'target_count':len(snapshots[0]['paths']),'r16_actual_writer_scope':'Three relocated existing TABLE_Z*_5 frames only; actual committed KEEP/scope receipt preserved in frozen execution state','r15_historical_writer_receipt':'Not separately frozen before r16; actual successful native report, committed source/journal, genuine before/after protection snapshots retained. No fabricated historical receipt.','source_fidelity':'NOT_ASSESSED'}
(D/'r14-r16-native-protected-graph-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');assert ok;print(json.dumps({'status':out['status'],'protected_sha256':rows[0]['protected_sha256'],'revisions':[r['actual_revision'] for r in rows]}))
