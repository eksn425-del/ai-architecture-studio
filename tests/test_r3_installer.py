from pathlib import Path
import json
import pytest
import os
from scripts.build_installer import nsis_string, inventory, payload_include, build


def test_inventory_refuses_credentials_and_native_models(tmp_path):
    (tmp_path/'KStudio.exe').write_bytes(b'MZfixture')
    (tmp_path/'owner.skp').write_bytes(b'private')
    with pytest.raises(ValueError,match='private'):inventory(tmp_path,True)


def test_safe_nsis_strings_and_no_broad_uninstall(tmp_path):
    (tmp_path/'KStudio.exe').write_bytes(b'MZfixture')
    (tmp_path/'folder').mkdir();(tmp_path/'folder'/'file $name.txt').write_text('fixture')
    rows=inventory(tmp_path,True)['files']
    output=payload_include(tmp_path,rows,'r3-test')
    assert 'file $$name.txt' in output
    assert 'RMDir /r' not in output and 'Delete "$INSTDIR\\*' not in output
    assert 'Call un.CheckPathAncestors' in output
    assert 'SetOutPath "\\\\?\\$INSTDIR' in output
    assert 'Call CheckPathAncestors\n  ClearErrors\n  SetOutPath ' in output
    assert '  IfErrors install_failed\n' in output
    assert 'Delete "\\\\?\\$INSTDIR' in output
    assert all('versions\\r3-test' in line for line in output.splitlines() if line.strip().startswith('Delete '))
    with pytest.raises(ValueError):nsis_string('invalid\n!system injected')


def test_public_bundle_cannot_be_a_fixture(tmp_path):
    (tmp_path/'KStudio.exe').write_bytes(b'MZfixture')
    with pytest.raises(ValueError,match='Incomplete frozen'):inventory(tmp_path)


def test_build_is_candidate_only_and_does_not_write_inside_bundle(tmp_path):
    bundle=tmp_path/'bundle';bundle.mkdir();(bundle/'KStudio.exe').write_bytes(b'MZfixture')
    nsis=tmp_path/'nsis';nsis.mkdir();(nsis/'makensis.exe').write_bytes(b'MZfixture');(nsis/'COPYING').write_text('fixture')
    with pytest.raises(ValueError,match='outside bundle'):build(bundle,bundle/'out',nsis,'r3-test',1,'a'*40,tmp_path/'installed',False)
    result=build(bundle,tmp_path/'output',nsis,'r3-test',1,'a'*40,tmp_path/'installed',False)
    assert result['candidate_only'] and result['fixture_only'] and not result['public_release_ready']
    entry=(tmp_path/'output/installer.nsi').read_text(encoding='utf-8-sig')
    assert 'KStudioR3InstallerFixture' in entry and 'PROFILE_ROOT' in entry
    with pytest.raises(ValueError,match='new output'):build(bundle,tmp_path/'output',nsis,'r3-test',1,'a'*40,tmp_path/'installed',False)


def test_template_never_recursive_deletes_profiles_or_unknown_folders():
    text=(Path(__file__).resolve().parents[1]/'packaging/kstudio.nsi').read_text(encoding='utf8')
    commands=[line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith(';')]
    assert not any(line.startswith('RMDir /r') for line in commands)
    assert not any('PROFILE_ROOT' in line for line in commands if line.startswith(('Delete ','RMDir ')))
    assert 'RequestExecutionLevel user' in commands
    assert 'SetCompressor /SOLID zlib' in commands
    assert commands.count('!insertmacro MUI_PAGE_DIRECTORY')==2
    assert '!ifdef SELECTABLE_PATHS' in commands


def test_full_acceptance_build_has_distinct_registration_and_selectable_paths(tmp_path):
    bundle=tmp_path/'bundle'
    for name in ('KStudio.exe','KStudioConnector.exe','_internal/harness/node.exe',
            '_internal/harness/node_modules/@deepseek-ai/dsh/lib/bin.js','_internal/deepseek_harness/__init__.py',
            '_internal/app/static/kstudio.ico','_internal/app/native_deep_fingerprint.rb',
            '_internal/app/window_bay_geometry.rb','_internal/app/vendor/local_mcp_sketchup/LICENSE',
            '_internal/app/vendor/local_mcp_sketchup/NOTICE','THIRD_PARTY_NOTICES.md'):
        path=bundle/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
    compiler=tmp_path/'compiler';compiler.mkdir()
    (compiler/'makensis.exe').write_text('fixture');(compiler/'COPYING').write_text('fixture')
    report=build(bundle,tmp_path/'generic',compiler,'r3-selectable',15,'a'*40,compile_installer=False)
    entry=(tmp_path/'generic/installer.nsi').read_text(encoding='utf-8-sig')
    assert report['root_selection']=='selectable-per-user'
    assert '!define SELECTABLE_PATHS' in entry and 'PRODUCT_ID "KStudioR3"' in entry
    assert (tmp_path/'generic/installer-template.nsi').is_file()
    assert (tmp_path/'generic/launcher-source.ps1').is_file()
    assert report['installer_source']['immutable_compile_inputs']
    report=build(bundle,tmp_path/'isolated',compiler,'r3-selectable',15,'a'*40,
                 compile_installer=False,acceptance_instance='test-r3')
    entry=(tmp_path/'isolated/installer.nsi').read_text(encoding='utf-8-sig')
    assert not report['fixture_only'] and report['acceptance_instance']
    assert '!define SELECTABLE_PATHS' in entry and 'PRODUCT_ID "KStudioR3QA-test-r3"' in entry
    with pytest.raises(ValueError,match='Acceptance instance'):
        build(bundle,tmp_path/'rejected',compiler,'r3-selectable',15,'a'*40,
              compile_installer=False,acceptance_instance='unsafe/instance')


@pytest.mark.skipif(os.name != 'nt' or not os.environ.get('KSTUDIO_INSTALLER_FIXTURE'), reason='Explicit compiled engineering fixture only')
def test_real_windows_installer_locks_and_atomic_failure():
    """Uses harmless compiled fixtures, never the real installed application."""
    import ctypes
    import msvcrt
    import subprocess
    import time
    fixture=Path(os.environ['KSTUDIO_INSTALLER_FIXTURE']).resolve()
    assert fixture.name=='installer-fixture' and fixture.drive.upper()=='E:'
    first=fixture/'compile12/KStudio-r3-safe-12-win-x64-setup.exe'
    second=fixture/'compile13/KStudio-r3-safe-13-win-x64-setup.exe'
    third=fixture/'compile14/KStudio-r3-safe-14-win-x64-setup.exe'
    installed=fixture/'locked-junction-fixture/program'
    profile=fixture/'locked-junction-fixture/profile'
    startup=subprocess.STARTUPINFO();startup.dwFlags=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    def run(exe,args=('/S',)):
        return subprocess.run([str(exe),*args],startupinfo=startup,timeout=30).returncode
    profile.parent.mkdir(parents=True,exist_ok=True)
    target=profile.parent/'profile-on-data-drive';target.mkdir(exist_ok=True)
    assert not profile.exists(), 'Use a fresh compiled fixture target'
    subprocess.run(['cmd.exe','/c','mklink','/J',str(profile),str(target)],check=True,capture_output=True)
    assert profile.is_dir() and profile.resolve()==target.resolve()
    assert run(first)==0
    original=(installed/'current.json').read_bytes()
    high=(installed/'highest-sequence.json').read_bytes()
    payload=installed/'versions/r3-safe-12/KStudio.exe'
    old_payload=payload.read_bytes()
    assert run(first)==6
    assert payload.read_bytes()==old_payload and (installed/'current.json').read_bytes()==original
    lease=profile/'desktop-instance/.kstudio-runtime.lock'
    with lease.open('r+b') as handle:
        handle.write(b'\0');handle.flush();handle.seek(0)
        msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        try:
            assert run(second)==5
            # NSIS _?= consumes the unquoted remainder, otherwise it spawns a
            # detached temp uninstaller and the parent stub reports zero.
            command='"'+str(installed/'Uninstall.exe')+'" /S _?='+str(installed)
            assert subprocess.run(command,startupinfo=startup,timeout=30).returncode==5
            assert (installed/'current.json').read_bytes()==original
        finally:
            handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
    # A real first installer waits on its welcome page, holding its OS mutex.
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenMutexW.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_wchar_p];k.OpenMutexW.restype=ctypes.c_void_p
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    process=subprocess.Popen([str(first)],startupinfo=startup)
    try:
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            mutex=k.OpenMutexW(0x100000,False,'Local\\KStudioR3InstallerFixture-Installer')
            if mutex:k.CloseHandle(mutex);break
            time.sleep(.05)
        else:raise AssertionError('First installer did not acquire mutex')
        assert run(second)==5
    finally:
        # Only our dedicated, hidden fixture process; not a user app.
        process.terminate();process.wait(timeout=10)
    # Deny-delete on current lets extraction finish but makes atomic replace fail.
    k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p]
    k.CreateFileW.restype=ctypes.c_void_p
    pointer=k.CreateFileW(str(installed/'current.json'),0x80000000,3,None,3,0x80,None)
    assert pointer not in (None,ctypes.c_void_p(-1).value)
    try:
        assert run(second)==4
        assert (installed/'current.json').read_bytes()==original
        assert (installed/'highest-sequence.json').read_bytes()==high
    finally:k.CloseHandle(pointer)
    # Partial new slots are retained and cannot be destructively retried either.
    partial=(installed/'versions/r3-safe-13/KStudio.exe').read_bytes()
    assert run(second)==6
    assert (installed/'versions/r3-safe-13/KStudio.exe').read_bytes()==partial
    assert (installed/'current.json').read_bytes()==original
    assert run(third)==0
    # Simulate a crash after publishing current but before high-water replacement.
    (installed/'highest-sequence.json').write_bytes(high)
    assert run(first)==3
    assert run(third)==6
    receipt={'running_install_exit':5,'running_uninstall_exit':5,'parallel_install_exit':5,
             'atomic_replace_failure_exit':4,'failure_preserved_current_and_highwater':True,
             'current_sequence_prevents_downgrade':True,'fresh_slot_upgrade':True,
             'same_version_overwrite_refused_exit':6,'original_and_partial_slots_unchanged':True,'profile_junction_real_lock_verified':True,
             'same_version_repair_crash_atomic':False,'fixture_only':True}
    (fixture/'lock-atomic-junction-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


@pytest.mark.skipif(os.name != 'nt' or not os.environ.get('KSTUDIO_INSTALLER_FIXTURE'), reason='Explicit compiled engineering fixture only')
def test_real_deep_path_install_and_uninstall():
    import subprocess
    fixture=Path(os.environ['KSTUDIO_INSTALLER_FIXTURE']).resolve()
    assert fixture.name=='installer-fixture' and fixture.drive.upper()=='E:'
    source=max((p for p in (fixture/'deep-bundle').rglob('*') if p.is_file()),key=lambda p:len(str(p)))
    relative=source.relative_to(fixture/'deep-bundle')
    root=fixture/'installed-deep/program'
    target=root/'versions/r3-deep-16'/relative
    assert len(str(source))>260 and len(str(target))>260
    startup=subprocess.STARTUPINFO();startup.dwFlags=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    exe=fixture/'compile16/KStudio-r3-deep-16-win-x64-setup.exe'
    assert subprocess.run([str(exe),'/S'],startupinfo=startup,timeout=30).returncode==0
    assert target.read_bytes()==source.read_bytes()
    assert subprocess.run('"'+str(root/'Uninstall.exe')+'" /S _?='+str(root),startupinfo=startup,timeout=30).returncode==0
    assert not target.exists() and (root/'unknown.txt').is_file() and (root.parent/'profile/keep.txt').is_file()
