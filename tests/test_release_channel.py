import base64
import hashlib
import json
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.release_channel import canonical, verify_manifest, stage_archive, activate, rollback,installation_guard


def fixture(tmp_path, name='r2-candidate.1', sequence=1, member='KStudio.exe'):
    archive = tmp_path / (name + '.zip')
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr(member, b'test-only-not-executable')
    payload = dict(schema=1, channel='candidate', platform='windows-x64', version=name,
                   sequence=sequence, expires_at=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat(),
                   sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), bytes=archive.stat().st_size,
                   url='https://downloads.example.invalid/test.zip', data_schema=1,
                   acceptance='internal-only', authenticode='unsigned')
    key = Ed25519PrivateKey.generate()
    keys = {'test-only': base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()}
    envelope = {'payload': payload, 'key_id':'test-only', 'signature':base64.b64encode(key.sign(canonical(payload))).decode()}
    return archive, payload, envelope, keys


def test_signature_tamper_channel_and_expiry(tmp_path):
    _, p, e, keys = fixture(tmp_path)
    assert verify_manifest(e, keys, channel='candidate') == p
    with pytest.raises(ValueError, match='channel'): verify_manifest(e, keys, channel='stable')
    with pytest.raises(ValueError, match='Expired'):
        verify_manifest(e, keys, channel='candidate', now=datetime.now(timezone.utc)+timedelta(days=2))
    e['payload']['url']='https://attacker.example.invalid/malware.zip'
    with pytest.raises(InvalidSignature): verify_manifest(e, keys, channel='candidate')


def test_update_rollback_preserves_data_and_refuses_busy(tmp_path):
    root=tmp_path/'install'; (root/'data').mkdir(parents=True)
    user_file=root/'data'/'project'; user_file.write_bytes(b'original-private-project')
    archive,p,e,keys=fixture(tmp_path)
    verified=verify_manifest(e,keys,channel='candidate')
    with pytest.raises(ValueError, match='active'): stage_archive(archive,root,verified,busy=True)
    stage_archive(archive,root,verified); activate(root,verified)
    archive,p,e,keys=fixture(tmp_path,'r2-candidate.2',2)
    stage_archive(archive,root,verify_manifest(e,keys,channel='candidate')); activate(root,p)
    assert rollback(root)['version']=='r2-candidate.1'
    assert user_file.read_bytes()==b'original-private-project'
    assert (root/'versions'/'r2-candidate.2'/'KStudio.exe').is_file()


def test_tamper_and_path_escape_never_activated(tmp_path):
    archive,p,_,_=fixture(tmp_path,member='../escaped.exe')
    root=tmp_path/'install'
    with pytest.raises(ValueError,match='escapes'): stage_archive(archive,root,p)
    assert not (root/'current.json').exists()
    assert not (root/'escaped.exe').exists()
    archive.write_bytes(b'tampered')
    with pytest.raises(ValueError,match='size'): stage_archive(archive,root,p)

@pytest.mark.parametrize('name',['CON.txt','a./KStudio.exe','data/project','release-manifest.json','C:/KStudio.exe','a/../KStudio.exe'])
def test_windows_archive_paths_are_rejected(tmp_path,name):
    archive,p,_,_=fixture(tmp_path,member=name)
    with pytest.raises(ValueError):stage_archive(archive,tmp_path/'install',p)
    assert not (tmp_path/'install'/'current.json').exists()
    assert not list((tmp_path/'install').glob('staging-*'))

def test_activation_checks_installed_bytes(tmp_path):
    archive,p,_,_=fixture(tmp_path);root=tmp_path/'install';target=stage_archive(archive,root,p)
    (target/'KStudio.exe').write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):activate(root,p)

def test_rollback_does_not_reset_antireplay_sequence(tmp_path):
    root=tmp_path/'install'
    archive,one,_,_=fixture(tmp_path);stage_archive(archive,root,one);activate(root,one)
    archive,two,_,_=fixture(tmp_path,'release-two',2);stage_archive(archive,root,two);activate(root,two)
    rollback(root)
    archive,old,_,_=fixture(tmp_path,'other-release-two',2);stage_archive(archive,root,old)
    with pytest.raises(ValueError,match='Stale'):activate(root,old)

def test_actual_desktop_and_installer_os_locks(tmp_path):
    from app.runtime_safety import LocalRuntimeLease
    root=tmp_path/'install';profile=tmp_path/'profile'
    with LocalRuntimeLease(profile/'desktop-instance'):
        with pytest.raises(ValueError,match='active'):
            with installation_guard(root,profile):pass
    with installation_guard(root,profile):
        with pytest.raises(ValueError,match='active'):
            with installation_guard(root,profile):pass
    assert not (root/'current.json').exists()

def test_download_redirect_policy_rejects_http_and_private(monkeypatch):
    from scripts.release_cli import approved_url
    import socket
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',('127.0.0.1',443))])
    for url in ('http://downloads.example.invalid/a','https://attacker.invalid/a','https://downloads.example.invalid/a'):
        with pytest.raises(ValueError):approved_url(url,['downloads.example.invalid'])

def test_interrupted_download_resumes_and_checks_full_hash(tmp_path,monkeypatch):
    from scripts import release_cli as cli
    import io
    data=b'a'*20+b'b'*30;sha=hashlib.sha256(data).hexdigest();cache=tmp_path/'cache';cache.mkdir();(cache/(sha+'.part')).write_bytes(data[:20])
    monkeypatch.setattr(cli,'approved_url',lambda url,hosts:url)
    class Response(io.BytesIO):
        status=206;url='https://fixture.invalid/a';headers={'Content-Range':'bytes 20-49/50'}
    class Opener:
        def open(self,request,timeout):
            assert request.headers['Range']=='bytes=20-'
            return Response(data[20:])
    monkeypatch.setattr(cli,'build_opener',lambda *args:Opener())
    assert cli.download_resume('https://fixture.invalid/a',cache,['fixture.invalid'],50,sha).read_bytes()==data

def test_minimum_upgrade_baseline_is_enforced(tmp_path):
    archive,p,_,_=fixture(tmp_path);p['min_current_sequence']=5;root=tmp_path/'install'
    stage_archive(archive,root,p)
    with pytest.raises(ValueError,match='baseline'):activate(root,p)
