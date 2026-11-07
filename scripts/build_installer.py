"""Build an unsigned internal NSIS installer from an audited frozen bundle.

No owner profiles are staged. Public signing/licensing/clean-machine gates remain
separate, and the output receipt never promotes a candidate to public readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from collections import defaultdict
from pathlib import Path, PureWindowsPath

try:
    from scripts.audit_desktop_bundle import audit
except ModuleNotFoundError:
    from audit_desktop_bundle import audit

REPO = Path(__file__).resolve().parents[1]


def nsis_string(value: str) -> str:
    if any(c in value for c in '\r\n\x00'):
        raise ValueError('NSIS input contains a line break or NUL')
    return value.replace('$', '$$').replace('"', '$\\"')


def reparse(path: Path) -> bool:
    info=path.lstat()
    return path.is_symlink() or bool(getattr(info,'st_file_attributes',0) & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def fixed_windows_root(value: str) -> PureWindowsPath:
    """A literal local drive path, never an NSIS/environment expression."""
    if (not isinstance(value,str) or not re.match(r'^[A-Za-z]:[\\/]',value)
            or any(ord(c)<32 for c in value) or any(c in value for c in '$%"<>|?*\'`')):
        raise ValueError('Selected root must be a static drive-qualified Windows absolute path')
    normalized=value.replace('/','\\').rstrip('\\')
    components=normalized[3:].split('\\')
    if (not normalized[3:] or any(not part or part in ('.','..') or ':' in part
            or part.endswith((' ','.')) or PureWindowsPath(part).is_reserved() for part in components)):
        raise ValueError('Selected root cannot be a drive root, traversal or ambiguous Windows path')
    # Root control files and lease paths use ordinary Win32 APIs; payload files
    # separately use extended-length paths. Keep these fixed control paths safe.
    if len(normalized)>200:
        raise ValueError('Selected root exceeds the safe control-path length of 200 characters')
    return PureWindowsPath(normalized)


def selected_roots(install_root: str | None, profile_root: str | None,
                   bundle: Path, output: Path, fixture_root: Path | None):
    if (install_root is None)!=(profile_root is None):
        raise ValueError('Both --install-root and --profile-root are required together')
    if install_root is None:return None
    if fixture_root is not None:
        raise ValueError('Selected production roots cannot be combined with engineering fixture mode')
    roots=[fixed_windows_root(install_root),fixed_windows_root(profile_root)]
    def overlaps(left,right):
        return bool(left.drive and right.drive) and (left.is_relative_to(right) or right.is_relative_to(left))
    protected=[PureWindowsPath(str(p)) for p in (bundle,output)]
    if overlaps(*roots) or any(overlaps(root,path) for root in roots for path in protected):
        raise ValueError('Selected installation/profile roots overlap each other, bundle or build output')
    if os.name=='nt':
        # Resolve existing directory aliases as well as lexical paths. This does
        # not relax the installer's stricter program-directory reparse guard.
        resolved=[PureWindowsPath(str(Path(str(root)).resolve())) for root in roots]
        targets=[PureWindowsPath(str(path.resolve())) for path in (bundle,output)]
        if overlaps(*resolved) or any(overlaps(root,path) for root in resolved for path in targets):
            raise ValueError('Resolved selected roots overlap each other, bundle or build output')
    return roots


def inventory(bundle: Path, fixture: bool=False) -> dict:
    if reparse(bundle):raise ValueError('Linked bundle root is not allowed')
    for item in bundle.rglob('*'):
        if reparse(item):raise ValueError('Linked bundle content is not allowed')
        relative=item.relative_to(bundle)
        if any(part in ('.','..') or any(c in part for c in '\r\n\x00*?') for part in relative.parts):raise ValueError('Unsafe bundle path')
    result=audit(bundle)
    if not result['inventory_pass']:raise ValueError('Bundle inventory rejected private data or linked content')
    if not (bundle/'KStudio.exe').is_file():raise ValueError('Frozen KStudio.exe is required')
    if not fixture:
        required=('KStudioConnector.exe','_internal/harness/node.exe','_internal/harness/node_modules/@deepseek-ai/dsh/lib/bin.js',
                  '_internal/deepseek_harness/__init__.py','_internal/app/static/kstudio.ico','_internal/app/native_deep_fingerprint.rb')
        if any(not (bundle/name).is_file() for name in required):raise ValueError('Incomplete frozen runtime, connector or native guard')
        if not any(p.name in ('THIRD_PARTY_NOTICES.md','third-party-notices.txt') for p in bundle.rglob('*') if p.is_file()):raise ValueError('Missing redistribution notices')
    return result


def payload_include(bundle: Path, files: list[dict], version: str) -> str:
    relative_files=[Path(row['path']) for row in files]
    directories={Path('.')}
    by_directory=defaultdict(list)
    for relative in relative_files:
        directories.update(relative.parents)
        by_directory[relative.parent].append(relative)
    ordered=sorted(directories,key=lambda p:(len(p.parts),p.as_posix()))
    def destination(relative):
        return '$INSTDIR\\versions\\'+version+('\\'+nsis_string(str(relative).replace('/','\\')) if relative!=Path('.') else '')
    lines=['!macro InstallPayload','  SetOverwrite on']
    for directory in ordered:
        target=destination(directory)
        lines.extend([f'  StrCpy $CheckPath "{target}"','  Call CheckPathAncestors',f'  SetOutPath "\\\\?\\{target}"'])
        for file in sorted(by_directory[directory],key=lambda p:p.as_posix()):
            lines.append(f'  File "/oname={nsis_string(file.name)}" "\\\\?\\{nsis_string(str(bundle/file))}"')
    lines+=['!macroend','!macro UninstallPayload']
    # Check all ancestors first; never follow a modified subtree junction while
    # deleting payload files or a changed installer-selected location.
    for directory in ordered:
        lines.extend([f'  StrCpy $CheckPath "{destination(directory)}"','  Call un.CheckPathAncestors'])
    for relative in relative_files:lines.append(f'  Delete "\\\\?\\{destination(relative)}"')
    for directory in reversed(ordered):
        if directory!=Path('.'):lines.append(f'  RMDir "\\\\?\\{destination(directory)}"')
    lines.append('!macroend')
    return '\n'.join(lines)+'\n'


def build(bundle: Path, output: Path, nsis: Path, version: str, sequence: int, source_sha: str,
          fixture_root: Path | None=None, compile_installer: bool=True, *,
          install_root: str | None=None, profile_root: str | None=None) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,79}',version):raise ValueError('Invalid version')
    if type(sequence) is not int or not 1<=sequence<=65535:raise ValueError('Sequence must fit the Windows product version')
    if not re.fullmatch('[0-9a-f]{40}',source_sha):raise ValueError('Source SHA must be a full Git SHA')
    bundle=bundle.absolute();output=output.absolute();nsis=nsis.absolute()
    if output.is_relative_to(bundle):raise ValueError('Build output must be outside bundle')
    if output.exists():raise ValueError('Use a new output directory to preserve previous packages')
    selected=selected_roots(install_root,profile_root,bundle,output,fixture_root)
    data=inventory(bundle,fixture_root is not None)
    product_id='KStudioR3InstallerFixture' if fixture_root is not None else 'KStudioR3'
    product_name='K Studio R3 Installer Fixture' if fixture_root is not None else 'K Studio R3 Beta'
    if fixture_root is not None:
        fixture_root=fixture_root.absolute()
        if not fixture_root.is_relative_to(output.parent) or fixture_root==output.parent or fixture_root.is_relative_to(bundle):raise ValueError('Fixture install root must be a dedicated sibling under this build job')
        install_root=nsis_string(str(fixture_root/'program'))
        profile_root=nsis_string(str(fixture_root/'profile'))
        root_selection='engineering-fixture'
    elif selected is not None:
        install_root,profile_root=(nsis_string(str(path)) for path in selected)
        root_selection='selected-local-fixed-root'
    else:
        install_root='$LOCALAPPDATA\\Programs\\KStudioR3'
        profile_root='$LOCALAPPDATA\\KStudioR3'
        root_selection='per-user-default'
    makensis=nsis/'makensis.exe'
    if not makensis.is_file() or not (nsis/'COPYING').is_file():raise ValueError('Explicit NSIS compiler and license required')
    output.mkdir(parents=True)
    (output/'bundle-inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    include=output/'payload-files.nsh';include.write_text(payload_include(bundle,data['files'],version),encoding='utf-8-sig')
    exe=output/f'KStudio-{version}-win-x64-setup.exe'
    definitions={'PRODUCT_ID':product_id,'PRODUCT_NAME':product_name,'OUTPUT_EXE':str(exe),'VERSION':version,
                 'SEQUENCE':str(sequence),'PAYLOAD_INCLUDE':str(include),'LAUNCHER_FILE':str(REPO/'scripts/launch_installed.ps1'),
                 'NSIS_LICENSE':str(nsis/'COPYING'),'APP_ICON':str(REPO/'app/static/kstudio.ico')}
    script='\n'.join('!define '+name+' "'+nsis_string(value)+'"' for name,value in definitions.items())+'\n'
    script+='!define INSTALL_ROOT "'+install_root+'"\n!define PROFILE_ROOT "'+profile_root+'"\n'
    script+='!include "'+nsis_string(str(REPO/'packaging/kstudio.nsi'))+'"\n'
    entry=output/'installer.nsi';entry.write_text(script,encoding='utf-8-sig')
    receipt={'schema':1,'version':version,'sequence':sequence,'source_sha':source_sha,'file_count':len(data['files']),
             'fixture_only':fixture_root is not None,'candidate_only':True,'production_signed':False,'public_release_ready':False,
             'profile_preserved_on_uninstall':True,'prior_slots_retained':True,'compression':'zlib',
             'running_instance_refused':True,'atomic_current_pointer':True,
             'same_version_repair_crash_atomic':False,
             'same_version_overwrite':'REFUSED_EXIT_6',
             'extended_length_payload_paths':True,
             'root_selection':root_selection,
             'nsis_license':'https://nsis.sourceforge.io/License','compile_status':'NOT_RUN'}
    installer_inputs=['packaging/kstudio.nsi','scripts/build_installer.py','scripts/launch_installed.ps1']
    receipt['installer_source']={
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'dirty':bool(subprocess.check_output(['git','status','--porcelain','--',*installer_inputs],cwd=REPO,text=True).strip()),
        'root_selection':root_selection,
        'sha256':{name:hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in installer_inputs},
        'note':'source_sha identifies frozen application core; installer input hashes identify later packaging fixes'}
    if compile_installer:
        compiler_temp=output/'temp';compiler_temp.mkdir()
        compiler_env=dict(os.environ,TEMP=str(compiler_temp),TMP=str(compiler_temp))
        receipt['compiler_temp_scope']='output/temp; process environment only'
        with (output/'compile.log').open('wb') as log:
            result=subprocess.run([str(makensis),'/V2',str(entry)],stdout=log,stderr=subprocess.STDOUT,timeout=1800,env=compiler_env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        receipt['compile_exit_code']=result.returncode
        receipt['compile_status']='PASS' if result.returncode==0 else 'FAIL'
        if result.returncode==0:
            receipt.update(installer=exe.name,bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if receipt['compile_status']=='FAIL':raise RuntimeError('NSIS compile failed; see output compile.log')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--nsis',required=True,type=Path)
    parser.add_argument('--version',required=True)
    parser.add_argument('--sequence',required=True,type=int)
    parser.add_argument('--source-sha',required=True)
    parser.add_argument('--engineering-fixture-root',type=Path)
    parser.add_argument('--install-root',help='Optional literal fixed Windows program directory; requires --profile-root')
    parser.add_argument('--profile-root',help='Optional literal fixed Windows data directory; requires --install-root')
    args=parser.parse_args()
    print(json.dumps(build(args.bundle,args.output,args.nsis,args.version,args.sequence,args.source_sha,args.engineering_fixture_root,
        install_root=args.install_root,profile_root=args.profile_root),ensure_ascii=False))
