"""Exercise actual frozen updater rejection using a private corrupt archive copy."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('updater','archive','install-root','data-dir','output'):parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    current=a.install_root/'current.json';marker=a.data_dir/'existing-project.txt'
    before={'pointer':sha(current),'data':sha(marker),'versions':sorted(p.name for p in (a.install_root/'versions').iterdir())}
    corrupted=a.output/'failed-corrupt-candidate.zip';shutil.copyfile(a.archive,corrupted)
    with corrupted.open('r+b') as stream:
        stream.seek(100);original=stream.read(1)
        if not original:raise ValueError('Candidate archive too short')
        stream.seek(100);stream.write(bytes([original[0]^1]))
    signed=a.output/'signed-test-failure';operations=[]
    def run(*args):
        result=subprocess.run([str(a.updater),*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        operations.append({'action':args[0],'returncode':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip()})
        return result
    result=run('test-sign','--archive',a.archive,'--output',signed,'--version','r2-corrupt-archive-probe','--sequence','3')
    if result.returncode:raise RuntimeError('Fixture signing failed')
    result=run('install','--manifest',signed/'manifest.json','--archive',corrupted,'--trusted-keys',signed/'trust-test-only.json','--install-root',a.install_root,'--data-dir',a.data_dir)
    after={'pointer':sha(current),'data':sha(marker),'versions':sorted(p.name for p in (a.install_root/'versions').iterdir())}
    receipt={'scope':'real_packaged_updater_corrupt_archive_rejection','original_archive_sha256':sha(a.archive),
             'corrupt_archive_sha256':sha(corrupted),'same_size':a.archive.stat().st_size==corrupted.stat().st_size,
             'corrupt_archive_retained':corrupted.is_file(),'refused':result.returncode==2,
             'before':before,'after':after,'installed_state_and_data_unchanged':before==after,
             'production_trust':False,'operations':operations}
    (a.output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('operations','before','after')}))
    if not receipt['refused'] or before!=after:raise SystemExit(1)


if __name__=='__main__':main()
