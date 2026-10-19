"""Check an explicit method-only allowlist before a Git tree is created."""
from pathlib import Path
import argparse,hashlib,json,re,sys
ALLOWED={'.md','.txt','.json','.py','.tsx','.ts','.yaml','.yml'}
def check(root,paths):
 root=Path(root).resolve();rows=[];errors=[]
 for rel in paths:
  p=(root/rel).resolve()
  if not p.is_relative_to(root) or not p.is_file():errors.append('Outside/missing: '+rel);continue
  if p.suffix.lower() not in ALLOWED or p.stat().st_size>200000:errors.append('Not a small method text file: '+rel);continue
  try:text=p.read_text(encoding='utf8')
  except UnicodeDecodeError:errors.append('Non UTF8: '+rel);continue
  for name,pattern in [('secret',r'(?:sk-[A-Za-z0-9]{24,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})'),('personal Windows path',r'[A-Za-z]:[\\/]Users[\\/][^<>{}\s"\x27]+'),('embedded media',r'data:(?:image|audio|video)/'),('credential field',r'(?i)(?:api_key|access_token|refresh_token|password|cookie)\s*[=:]\s*["\x27][^"\x27]{12,}["\x27]')]:
   if re.search(pattern,text):errors.append(name+': '+rel)
  rows.append({'path':Path(rel).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 return {'ok':not errors,'errors':errors,'files':rows,'media_included':False,'scope':'explicit method-only allowlist'}
def main():
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('allowlist');p.add_argument('--output');a=p.parse_args();paths=json.loads(Path(a.allowlist).read_text(encoding='utf8'));result=check(a.root,paths)
 if a.output:Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'ok':result['ok'],'files':len(result['files']),'errors':result['errors']},ensure_ascii=False));return 0 if result['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
