"""Run the packaged updater, not a Python stand-in. Optional real candidate ZIP."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
from app.runtime_safety import LocalRuntimeLease

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--updater',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--archive',type=Path);a=parser.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);profile=a.output/'profile';profile.mkdir();keep=profile/'existing-project.txt';keep.write_text('synthetic existing local model metadata',encoding='utf-8')
    before=hashlib.sha256(keep.read_bytes()).hexdigest();root=a.output/'installed'
    archive=a.archive
    if archive is None:
        archive=a.output/'synthetic-installer-fixture.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('KStudio.exe',b'NOT_A_DESKTOP_EXECUTABLE_INSTALLER_FIXTURE_ONLY')
    operations=[]
    def run(*args,expected=0):
        result=subprocess.run([str(a.updater),*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
        operations.append({'action':args[0],'returncode':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip()})
        if result.returncode!=expected:raise RuntimeError('Packaged updater returned unexpected status: '+result.stderr)
    for sequence in (1,2):
        signed=a.output/('signed-test-'+str(sequence))
        run('test-sign','--archive',archive,'--output',signed,'--version','r2-local-drill-'+str(sequence),'--sequence',str(sequence))
        install=('install','--manifest',signed/'manifest.json','--archive',archive,'--trusted-keys',signed/'trust-test-only.json','--install-root',root,'--data-dir',profile)
        if sequence==1:
            with LocalRuntimeLease(profile/'desktop-instance'):run(*install,expected=2)
        run(*install)
        run(*install) # safe retry of an already activated immutable version
    run('rollback','--install-root',root,'--data-dir',profile)
    current=json.loads((root/'current.json').read_text());after=hashlib.sha256(keep.read_bytes()).hexdigest()
    with archive.open('rb') as stream:archive_sha256=hashlib.file_digest(stream,'sha256').hexdigest()
    with a.updater.open('rb') as stream:updater_sha256=hashlib.file_digest(stream,'sha256').hexdigest()
    receipt={'scope':'packaged_updater_local_candidate_zip' if a.archive else 'packaged_updater_synthetic_archive_not_desktop_acceptance','archive_sha256':archive_sha256,'archive_bytes':archive.stat().st_size,'updater_sha256':updater_sha256,'authenticode':'unsigned','production_trust':False,'two_slots_same_archive':True,'user_data_unchanged':before==after,'rolled_back_to_first':current['sequence']==1,'both_versions_retained':all((root/'versions'/('r2-local-drill-'+str(i))/'KStudio.exe').is_file() for i in (1,2)),'launcher_installed':(root/'launch_installed.ps1').is_file(),'operations':operations}
    (a.output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='operations'}))
    if not all(receipt[x] for x in ('user_data_unchanged','rolled_back_to_first','both_versions_retained','launcher_installed')):raise SystemExit(1)
if __name__=='__main__':main()
