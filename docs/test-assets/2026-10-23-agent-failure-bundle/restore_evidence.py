"""Read and verify the sanitized, content-addressed evidence bundle."""
from pathlib import Path
import argparse,gzip,hashlib,json

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--list',action='store_true');p.add_argument('--verify',action='store_true')
 p.add_argument('--prefix',default='');p.add_argument('--output',type=Path)
 a=p.parse_args();root=Path(__file__).resolve().parent
 rows=json.loads((root/'manifest.json').read_text(encoding='utf8'))
 rows=[r for r in rows if r['source'].startswith(a.prefix)]
 verified=set()
 for r in rows:
  blob=(root/r['path']).resolve()
  if not blob.is_relative_to((root/'objects').resolve()):raise ValueError('Unsafe object path')
  if a.list:print(r['source'],r['path'],r['encoding'])
  if a.verify or a.output:
   raw=gzip.decompress(blob.read_bytes()) if r['encoding']=='gzip' else blob.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=r['published_sha256']:raise ValueError('Object checksum mismatch: '+r['source'])
   verified.add(r['published_sha256'])
   if a.output:
    dest=(a.output/r['source']).resolve()
    if not dest.is_relative_to(a.output.resolve()):raise ValueError('Unsafe destination path')
    if dest.exists():raise FileExistsError('Refuse to overwrite: '+str(dest))
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 if a.verify:print(json.dumps({'logical_files_verified':len(rows),'unique_objects_verified':len(verified),'status':'PASS'}))
 if not (a.list or a.verify or a.output):p.error('Use --list, --verify or --output DIRECTORY')
if __name__=='__main__':main()
