import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import shutil

import pytest

from scripts.build_installer import build, fixed_windows_root, selected_roots


@pytest.mark.parametrize('value', [
    'E:', 'E:\\', 'relative/path', r'\root-relative', r'\\server\share\app',
    r'\\?\E:\app', r'E:\app\..\other', r'E:\app\.\other',
    r'E:\app::$DATA', r'E:\CON\app', r'E:\app.\child', r'E:\app \child',
    r'E:\$LOCALAPPDATA\app', r'E:\%TEMP%\app', 'E:\\app"\n!system injected',
    'E:\\app\x00bad', r'E:\app\*.exe', r'E:\app\foo?bar',
    "E:\\app'quote", 'E:\\app`quote',
])
def test_selected_roots_reject_nonliteral_or_ambiguous_paths(value):
    with pytest.raises(ValueError): fixed_windows_root(value)


def test_selected_root_accepts_static_chinese_drive_path():
    assert str(fixed_windows_root('e:/建筑工作台/K Studio')) == r'e:\建筑工作台\K Studio'


def test_both_roots_required_and_fixture_mode_is_separate():
    bundle=Path(r'E:\job\bundle');output=Path(r'E:\job\package')
    with pytest.raises(ValueError,match='together'):
        selected_roots(r'E:\apps\KStudio',None,bundle,output,None)
    with pytest.raises(ValueError,match='together'):
        selected_roots(None,r'E:\data\KStudio',bundle,output,None)
    with pytest.raises(ValueError,match='fixture'):
        selected_roots(r'E:\apps\KStudio',r'E:\data\KStudio',bundle,output,Path('fixture'))


@pytest.mark.parametrize('install,profile', [
    (r'E:\job\bundle\installed',r'E:\data'),
    (r'e:\JOB',r'E:\data'),
    (r'E:\apps',r'E:\job\package\profile'),
    (r'E:\apps',r'E:\apps\profile'),
    (r'E:\apps\program',r'E:\apps'),
    (r'E:\same',r'e:\SAME'),
])
def test_rejects_bidirectional_case_insensitive_overlap(install,profile):
    with pytest.raises(ValueError,match='overlap'):
        selected_roots(install,profile,Path(r'E:\job\bundle'),Path(r'E:\job\package'),None)


def test_selected_production_roots_are_fixed_and_receipt_is_sanitized(tmp_path):
    bundle=tmp_path/'bundle';bundle.mkdir()
    required=('KStudio.exe','KStudioConnector.exe','_internal/harness/node.exe',
        '_internal/harness/node_modules/@deepseek-ai/dsh/lib/bin.js','_internal/deepseek_harness/__init__.py',
        '_internal/app/static/kstudio.ico','_internal/app/native_deep_fingerprint.rb','third-party-notices.txt')
    for name in required:
        path=bundle/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('packaging unit fixture')
    nsis=tmp_path/'compiler';nsis.mkdir();(nsis/'makensis.exe').write_bytes(b'MZfixture');(nsis/'COPYING').write_text('fixture')
    program=r'E:\SelectedPrivateProgram\K Studio';profile=r'E:\SelectedPrivateData\profile'
    result=build(bundle,tmp_path/'package',nsis,'r3-root-test',10,'a'*40,compile_installer=False,
        install_root=program,profile_root=profile)
    script=(tmp_path/'package/installer.nsi').read_text(encoding='utf-8-sig')
    assert f'!define INSTALL_ROOT "{program}"' in script
    assert f'!define PROFILE_ROOT "{profile}"' in script
    assert 'KStudioR3InstallerFixture' not in script and result['fixture_only'] is False
    assert result['root_selection']==result['installer_source']['root_selection']=='selected-local-fixed-root'
    assert 'SelectedPrivate' not in json.dumps(result)


@pytest.mark.skipif(os.name!='nt',reason='Real Windows PowerShell launcher contract')
def test_launcher_sets_only_process_temp_and_preserves_root_lease(tmp_path):
    root=tmp_path/'installed';slot=root/'versions/r3-test';slot.mkdir(parents=True)
    (slot/'KStudio.exe').write_bytes(b'fixture; Start-Process is intercepted, not executed')
    (root/'current.json').write_text('{"version":"r3-test","sequence":1}')
    data=tmp_path/'profile with spaces';report=tmp_path/'launch.json'
    runner=tmp_path/'probe.ps1'
    runner.write_text('''param($Launcher,$Root,$Data,$Report)
$ErrorActionPreference='Stop'
function Start-Process {
 param($FilePath,$ArgumentList,$WorkingDirectory,$WindowStyle,[switch]$PassThru)
 $held=$false;$check=$null
 try {
  $check=[IO.File]::Open((Join-Path $Root 'installer-lock/.kstudio-runtime.lock'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::ReadWrite)
  $check.Lock(0,1);$check.Unlock(0,1)
 } catch [IO.IOException] {$held=$true} finally {if($check){$check.Dispose()}}
 [pscustomobject]@{temp=$env:TEMP;tmp=$env:TMP;lease_held=$held;window_style=$WindowStyle;args=$ArgumentList} | ConvertTo-Json | Set-Content -LiteralPath $Report -Encoding utf8
 [pscustomobject]@{HasExited=$true}
}
& $Launcher -InstallRoot $Root -DataDir $Data
''',encoding='utf-8-sig')
    shell=shutil.which('pwsh') or shutil.which('powershell')
    assert shell
    launcher=Path(__file__).resolve().parents[1]/'scripts/launch_installed.ps1'
    before=(os.environ.get('TEMP'),os.environ.get('TMP'))
    run=subprocess.run([shell,'-NoProfile','-File',str(runner),str(launcher),str(root),str(data),str(report)],
        capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stderr
    result=json.loads(report.read_text(encoding='utf-8-sig'))
    assert Path(result['temp'])==Path(result['tmp'])==data/'temp'
    assert (data/'temp').is_dir() and result['lease_held'] is True
    assert result['window_style']=='Hidden' and result['args'][0]=='--data-dir'
    assert (os.environ.get('TEMP'),os.environ.get('TMP'))==before
