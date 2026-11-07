import json
import subprocess
from types import SimpleNamespace

import pytest
from sqlalchemy import update

from cloud.db import engine_for,migrate,schema_version
from cloud.auth import create_identity
from cloud.credential_crypto import CredentialCipher
from cloud.provider_connections import ConnectionService
from deploy import ops
from deploy.verify_restore import verify


@pytest.mark.parametrize('target',[None,'kstudio','postgres','kstudio_restore_','kstudio_restore_x;drop','other_db','kstudio_restore_'+'x'*50])
def test_restore_target_refuses_production_and_sql_fragments(target):
    with pytest.raises(ValueError):ops.restore_target(target)


def test_backup_never_overwrites_an_existing_archive(tmp_path):
    f=tmp_path/'archive.age';f.write_bytes(b'previous')
    with pytest.raises(ValueError):ops.encrypted_backup(['docker','compose'],{},f)
    assert f.read_bytes()==b'previous'


def test_failed_age_authentication_does_not_create_or_touch_database(tmp_path,monkeypatch):
    archive=tmp_path/'archive.age';archive.write_bytes(b'tampered')
    key=tmp_path/'private.key';key.write_text('fixture-only-key')
    calls=[]
    def fail(command,**kw):
        calls.append(command)
        raise subprocess.CalledProcessError(1,command)
    monkeypatch.setattr(ops.subprocess,'run',fail)
    with pytest.raises(subprocess.CalledProcessError):
        ops.encrypted_restore(['docker','compose'],{'KSTUDIO_BACKUP_IDENTITY':str(key)},archive,'kstudio_restore_test')
    assert len(calls)==1 and calls[0][0]=='age'
    assert not list(tmp_path.glob('.kstudio-restore-*'))


def test_existing_target_refusal_never_reaches_pg_restore(tmp_path,monkeypatch):
    archive=tmp_path/'archive.age';archive.write_bytes(b'fixture')
    key=tmp_path/'private.key';key.write_text('fixture-only')
    calls=[]
    def run(command,**kw):
        calls.append(command)
        if command[0]=='age':
            from pathlib import Path
            Path(command[command.index('--output')+1]).write_bytes(b'custom-dump')
            return SimpleNamespace(returncode=0)
        assert 'createdb' in command
        raise subprocess.CalledProcessError(1,command)
    monkeypatch.setattr(ops.subprocess,'run',run)
    with pytest.raises(subprocess.CalledProcessError):
        ops.encrypted_restore(['docker','compose'],{'KSTUDIO_BACKUP_IDENTITY':str(key)},archive,'kstudio_restore_existing')
    assert len(calls)==2 and not any('pg_restore' in cmd for cmd in calls)
    assert 'exec' in calls[1] and 'db' in calls[1] and not any('5432' in str(cmd) for cmd in calls)


def test_restored_vault_cannot_pass_without_correct_separate_master_key(tmp_path):
    engine=engine_for('sqlite:///'+str(tmp_path/'restore.sqlite'));migrate(engine)
    user=create_identity(engine,'fixture|restore','Fixture')
    cipher=CredentialCipher({'v1':b'1'*32},'v1')
    ConnectionService(engine,cipher).save(user['id'],{'label':'fixture','provider':'fixture','protocol':'responses',
        'base_url':'https://api.example.invalid/v1','model_id':'model','api_key':'fixture-secret-not-real',
        'cloud_storage_consent':True})
    with pytest.raises(ValueError):verify(engine)
    with pytest.raises(ValueError):verify(engine,CredentialCipher({'v1':b'2'*32},'v1'))
    report=verify(engine,cipher)
    assert report['vault_credentials_decrypted']==1 and report['ledger_consistent']
    assert report['tables']['verified_payment_inbox']['rows']==0
    assert 'fixture-secret' not in json.dumps(report)
    with engine.begin() as c:c.execute(update(schema_version).values(version=999))
    with pytest.raises(ValueError):verify(engine,cipher)
    engine.dispose()


def test_commercial_check_uses_public_operator_contract_and_explicit_license_clearance():
    values={k:'fixture' for k in ('KSTUDIO_DOMAIN','KSTUDIO_DATABASE_PASSWORD','KSTUDIO_CLOUD_DATABASE_URL',
        'KSTUDIO_CLOUD_SESSION_SECRET','KSTUDIO_CLOUD_PUBLIC_URL','KSTUDIO_IMAGE','KSTUDIO_SECRET_DIR',
        'KSTUDIO_OIDC_METADATA_URL','KSTUDIO_OIDC_CLIENT_ID','KSTUDIO_OIDC_CLIENT_SECRET',
        'KSTUDIO_VAULT_ACTIVE_KEY_VERSION','KSTUDIO_VAULT_KEYS_FILE','KSTUDIO_WECHATPAY_MCHID',
        'KSTUDIO_WECHATPAY_APPID','KSTUDIO_WECHATPAY_API_V3_KEY_FILE',
        'KSTUDIO_WECHATPAY_MERCHANT_PRIVATE_KEY_FILE','KSTUDIO_WECHATPAY_MERCHANT_SERIAL',
        'KSTUDIO_WECHATPAY_VERIFY_MATERIAL_FILE','KSTUDIO_BAI_PLATFORM_KEY','KSTUDIO_BACKUP_RECIPIENT')}
    values.update(KSTUDIO_CLOUD_PUBLIC_URL='https://fixture',KSTUDIO_RELEASE_SHA='a'*40,
        KSTUDIO_PRICES_CONFIRMED='1',KSTUDIO_PAYMENT_PROVIDER='wechat_native')
    operator={k:'fixture' for k in ('name','support_email','icp','privacy_contact','data_retention','refund_policy')}
    release={k:True for k in ('verified','public_distribution_authorized','signing_verified','clean_windows_verified')}
    release['license_clearance']='CLEARED'
    values.update(KSTUDIO_OPERATOR=json.dumps(operator),KSTUDIO_CLOUD_RELEASE=json.dumps(release))
    assert ops.check(values,commercial=True)['status']=='READY_FOR_OPERATOR_EXECUTION'
    for unapproved in (True,False,'REVIEW_REQUIRED','cleared',''):
        release['license_clearance']=unapproved;values['KSTUDIO_CLOUD_RELEASE']=json.dumps(release)
        assert 'release_acceptance_missing' in ops.check(values,commercial=True)['errors']
    operator.pop('support_email');values['KSTUDIO_OPERATOR']=json.dumps(operator)
    assert 'operator_identity_contact_or_icp_missing' in ops.check(values,commercial=True)['errors']
