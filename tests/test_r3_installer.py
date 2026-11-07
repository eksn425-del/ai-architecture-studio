from pathlib import Path
import json
import pytest
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
    assert not any('MUI_PAGE_DIRECTORY' in line for line in commands)
