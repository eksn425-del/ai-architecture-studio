import pytest
from scripts.audit_desktop_bundle import audit
from scripts.prepare_desktop_sdk import prepare


def test_public_certificates_are_kept_private_keys_rejected(tmp_path):
    (tmp_path / 'ca.pem').write_text('-----BEGIN CERTIFICATE-----\nfixture\n-----END CERTIFICATE-----')
    assert audit(tmp_path)['inventory_pass']
    (tmp_path / 'mixed.pem').write_text('-----BEGIN CERTIFICATE-----\nfixture\n-----BEGIN RSA PRIVATE KEY-----')
    assert audit(tmp_path)['rejected_paths'] == ['mixed.pem']
    (tmp_path / 'connections.dpapi').write_bytes(b'encrypted-user-secret')
    assert 'connections.dpapi' in audit(tmp_path)['rejected_paths']


def test_sdk_patch_fails_closed_on_changed_upstream_and_preserves_source(tmp_path):
    package = tmp_path / 'deepseek_harness'
    package.mkdir()
    client = package / 'client.py'
    client.write_text('upstream_changed = True\n')
    original = client.read_bytes()
    with pytest.raises(ValueError, match='changed upstream'):
        prepare(tmp_path)
    assert client.read_bytes() == original


def test_sdk_patch_only_adds_windows_process_flag(tmp_path):
    package = tmp_path / 'deepseek_harness'
    package.mkdir()
    client = package / 'client.py'
    text = 'class Client:\n    def start(self):\n        self._proc = subprocess.Popen(\n            args,\n            stdin=subprocess.PIPE,\n        )\n'
    client.write_text(text)
    prepare(tmp_path)
    assert client.read_text().replace('            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),\n', '') == text
    assert (tmp_path / 'KSTUDIO-SDK-PATCH.json').is_file()
