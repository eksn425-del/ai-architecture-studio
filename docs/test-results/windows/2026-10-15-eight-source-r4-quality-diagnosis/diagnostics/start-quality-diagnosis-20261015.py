from pathlib import Path
import hashlib,json,shutil,time
ROOT=Path.cwd();P=ROOT/'runtime/projects/architecture-project-4f0e4';D=ROOT/'runtime/quality-diagnosis-20261015';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((P/'state/agent_session.json').read_text(encoding='utf-8'));model=P/s['model_path']
assert s['ruby_state']['glass_curved_roof']['revision']==4
assert sha(model)=='c337d2bcc36922167da85be070463988bd9622b6c43bb402d2ce8d2151ec63db'
sources=json.loads((ROOT/'runtime/native-recovery-20261014/codex-control-inputs.json').read_text(encoding='utf-8'))['source_images']
source_manifest=[]
for n,row in enumerate(sources,1):
 p=P/'inputs/reference'/Path(row['path']).name
 assert sha(p)==row['sha256'];source_manifest.append({'number':n,'filename':p.name,'sha256':sha(p)})
backup=ROOT/'runtime/backups/20261015-r4-quality-diagnosis'
if not backup.exists():shutil.copytree(P,backup)
safe=P/'outputs/model/blank-disposable-r4-quality-diagnosis-20261015.skp'
if not safe.exists():shutil.copy2(model,safe)
assert sha(safe)==sha(model)
receipt={'project':'architecture-project-4f0e4','revision':4,'root_pid':20606,'original_model':str(model),'safe_copy':str(safe),'original_bytes_sha256':sha(model),'safe_copy_bytes_sha256':sha(safe),'source_images':source_manifest,'backup':str(backup),'geometry_writes':0,'native_identity':'PENDING actual open; bridge initial ECONNREFUSED 127.0.0.1:45678'}
(D/'backup-and-sources.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'backup':'PASS','sources_verified':len(source_manifest),'safe_copy':str(safe),'original_unchanged':True},ensure_ascii=False))
