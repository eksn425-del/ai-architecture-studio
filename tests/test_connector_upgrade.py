import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from app import desktop_bootstrap as bootstrap


@pytest.fixture
def installed(tmp_path, monkeypatch):
    monkeypatch.setattr(os, 'environ', dict(os.environ))
    versions = tmp_path/'installed/versions'
    old = versions/'old'
    current = versions/'new'
    bundle = current/'_internal'
    for name in ('harness/node.exe', 'harness/dsh.cmd', 'harness/node_modules/@deepseek-ai/dsh/lib/bin.js',
                 'app/dsh_host_tools.mjs', 'app/dsh_tool_policy.mjs', 'app/dsh_test_budget.mjs'):
        path = bundle/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture')
    (bundle/'app/architecture_skills').mkdir()
    (current/'KStudioConnector.exe').write_bytes(b'new executable fixture')
    (old/'_internal').mkdir(parents=True)
    (old/'KStudioConnector.exe').write_bytes(b'old executable fixture')
    data = tmp_path/'profile'
    data.mkdir()
    pairing = tmp_path/'paired'
    settings = {'command':str(old/'KStudioConnector.exe'), 'args':[], 'cwd':str(old/'_internal'),
                'env':{'KSTUDIO_PUBLIC_CONNECTOR_ROOT':str(pairing),
                       'ARCHFLOW_GENERATED_SCRIPT_DIR':str(pairing/'generated_scripts')},
                'owner_custom_setting':{'keep':'unchanged'}}
    target = data/'bridge.json'
    original = ('\ufeff' + json.dumps(settings, ensure_ascii=False, indent=4) + '\n').encode('utf-8')
    target.write_bytes(original)
    return bundle, data, settings, original


def test_configure_persists_same_install_upgrade_backups_bytes_and_is_idempotent(installed):
    bundle, data, settings, original = installed
    result = bootstrap.configure(bundle, data)
    assert result['connector_upgrade']['status'] == 'relocated'
    assert Path(result['connector_upgrade']['backup']).read_bytes() == original
    changed = json.loads((data/'bridge.json').read_text(encoding='utf-8'))
    expected = {**settings, 'command':str(bundle.parent/'KStudioConnector.exe'), 'cwd':str(bundle)}
    assert changed == expected
    bytes_after = (data/'bridge.json').read_bytes()
    assert bootstrap.configure(bundle, data)['connector_upgrade']['status'] == 'preserved'
    assert (data/'bridge.json').read_bytes() == bytes_after
    assert len(list((data/'bridge-backups').iterdir())) == 1


@pytest.mark.parametrize('change', ['other_install','custom_location','arguments','other_connector',
                                   'missing_public_env','custom_scripts'])
def test_custom_or_other_install_configuration_is_byte_preserved(installed, change):
    bundle, data, settings, _ = installed
    settings = copy.deepcopy(settings)
    if change == 'other_install':
        settings['command'] = str(data/'other/versions/old/KStudioConnector.exe')
    elif change == 'custom_location':
        settings['command'] = str(data/'custom/KStudioConnector.exe')
    elif change == 'arguments':
        settings['args'] = ['--custom']
    elif change == 'other_connector':
        settings['command'] = str(Path(settings['command']).with_name('OtherConnector.exe'))
    elif change == 'missing_public_env':
        settings['env'] = {}
    else:
        settings['env']['ARCHFLOW_GENERATED_SCRIPT_DIR'] = str(data/'custom-scripts')
    original = json.dumps(settings, indent=4).encode()
    (data/'bridge.json').write_bytes(original)
    assert bootstrap.configure(bundle, data)['connector_upgrade']['status'] == 'preserved'
    assert (data/'bridge.json').read_bytes() == original
    assert not (data/'bridge-backups').exists()


def test_only_matching_old_cwd_relocates_and_retired_binary_can_be_missing(installed):
    bundle, data, settings, _ = installed
    Path(settings['command']).unlink()
    settings['cwd'] = str(data/'custom-working-directory')
    (data/'bridge.json').write_text(json.dumps(settings), encoding='utf-8')
    bootstrap.configure(bundle, data)
    changed = json.loads((data/'bridge.json').read_text())
    assert changed['command'] == str(bundle.parent/'KStudioConnector.exe')
    assert changed['cwd'] == settings['cwd']


@pytest.mark.parametrize('broken', ['not json', '[]', '{"command":null}',
    '{"command":"x","env":[]}', '{"command":"x","args":null}',
    '{"command":"x","command":"y"}'])
def test_corrupt_config_stops_before_environment_or_file_changes(installed, broken):
    bundle, data, _, _ = installed
    (data/'bridge.json').write_bytes(broken.encode())
    before = dict(os.environ)
    with pytest.raises(RuntimeError, match='配置损坏'):
        bootstrap.configure(bundle, data)
    assert (data/'bridge.json').read_bytes() == broken.encode()
    assert dict(os.environ) == before
    assert not (data/'bridge-backups').exists()


def test_missing_new_binary_preserves_old_configuration(installed):
    bundle, data, _, original = installed
    (bundle.parent/'KStudioConnector.exe').unlink()
    with pytest.raises(RuntimeError, match='缺少 K Studio'):
        bootstrap.configure(bundle, data)
    assert (data/'bridge.json').read_bytes() == original
    assert not (data/'bridge-backups').exists()


def test_failed_atomic_replace_keeps_original_and_verified_backup(installed, monkeypatch):
    bundle, data, _, original = installed
    def denied(*_):
        raise PermissionError('fixture locked config')
    monkeypatch.setattr(bootstrap.os, 'replace', denied)
    with pytest.raises(RuntimeError, match='升级未完成'):
        bootstrap.configure(bundle, data)
    assert (data/'bridge.json').read_bytes() == original
    assert next((data/'bridge-backups').iterdir()).read_bytes() == original
    assert not list(data.glob('bridge.*.tmp'))


def test_frozen_runtime_does_not_redirect_custom_same_named_connector(installed, monkeypatch):
    from app import sketchup_mcp
    bundle, data, settings, _ = installed
    custom = data/'custom/KStudioConnector.exe'
    custom.parent.mkdir()
    custom.write_bytes(b'fixture')
    settings['command'] = str(custom)
    (data/'bridge.json').write_text(json.dumps(settings), encoding='utf-8')
    monkeypatch.setenv('ARCH_STUDIO_MCP_CONFIG', str(data/'bridge.json'))
    monkeypatch.setattr(sketchup_mcp.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sketchup_mcp.sys, 'executable', str(bundle.parent/'KStudio.exe'))
    command, env, cwd = sketchup_mcp._resolve_server()
    assert command == [str(custom)]
    assert env == settings['env']
    assert cwd == settings['cwd']


def test_public_package_version_matches_both_runtime_surfaces(tmp_path):
    from app.public_connector import VERSION
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root/'scripts/package_public_connector.py'), str(tmp_path/'package')],
                   check=True, capture_output=True, timeout=15)
    manifest = json.loads((tmp_path/'package/manifest.json').read_text())
    assert manifest['version'] == VERSION == '2026.11.05-r2'
    with zipfile.ZipFile(tmp_path/'package/KStudio-SketchUp-Connector.rbz') as archive:
        assert all(i.date_time[:3] == (2026,11,5) for i in archive.infolist())
        assert VERSION in archive.read('kstudio_connector.rb').decode()
        assert VERSION in archive.read('kstudio_connector/main.rb').decode()
