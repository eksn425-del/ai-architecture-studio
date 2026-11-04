"""Build a PowerShell-only customer acceptance kit; no runtime/profile included."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=True)
    archive=args.output/'KStudio-R2-clean-Windows-check-kit.zip'
    if archive.exists():raise ValueError('Use a new output directory; previous kit is preserved')
    mapping={
        'Test-KStudioCleanWindows.ps1':'scripts/Test-KStudioCleanWindows.ps1',
        'Install-KStudioCandidate.ps1':'scripts/Install-KStudioCandidate.ps1',
        'Verify-KStudioBundle.ps1':'scripts/Verify-KStudioBundle.ps1',
        'README.md':'docs/CLEAN_WINDOWS_QUICKSTART_R2.md',
        'USER_GUIDE_R2.md':'docs/USER_GUIDE_R2.md',
        'CLEAN_WINDOWS_ACCEPTANCE.csv':'docs/CLEAN_WINDOWS_ACCEPTANCE.csv',
    }
    data={name:(root/source).read_bytes() for name,source in mapping.items()}
    manifest={'schema':1,'scope':'CUSTOMER_READONLY_DIAGNOSTIC_AND_OPTIONAL_INSTALL_SCRIPTS',
        'python_or_codex_required_by_customer':False,'automatic_installation':False,
        'clean_machine_acceptance':'NOT_RUN','native_modeling_quality':'NOT_RUN',
        'files':[{'path':name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()} for name,blob in sorted(data.items())]}
    data['MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,blob in sorted(data.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,blob)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for row in manifest['files']:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    receipt={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'all_member_hashes_verified':True,'customer_requires':'Windows PowerShell 5.1 or compatible PowerShell; no Codex/Python',
        'clean_machine_acceptance':'NOT_RUN','source_files':mapping}
    (args.output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'SHA256SUMS').write_text(receipt['sha256']+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
