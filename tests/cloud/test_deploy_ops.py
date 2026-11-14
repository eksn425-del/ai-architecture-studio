import json
import re
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
    values.update(KSTUDIO_DOMAIN='fixture.test',KSTUDIO_CLOUD_ENV='staging',
        KSTUDIO_CLOUD_PUBLIC_URL='https://fixture.test',KSTUDIO_RELEASE_SHA='a'*40,
        KSTUDIO_IMAGE='kstudio-cloud:'+'a'*40,KSTUDIO_CLOUD_SESSION_SECRET='a'*32,
        KSTUDIO_CLOUD_DATABASE_URL='postgresql+psycopg://kstudio:disposable-password@db:5432/kstudio',
        KSTUDIO_PRICES_CONFIRMED='1',KSTUDIO_PAYMENT_PROVIDER='wechat_native')
    operator={k:'fixture' for k in ('name','support_email','icp','privacy_contact','data_retention','refund_policy')}
    release={k:True for k in ('verified','public_distribution_authorized','signing_verified','clean_windows_verified')}
    release['license_clearance']='CLEARED'
    release['sha256']='b'*64
    values.update(KSTUDIO_OPERATOR=json.dumps(operator),KSTUDIO_CLOUD_RELEASE=json.dumps(release))
    assert ops.check(values,commercial=True)['status']=='READY_FOR_OPERATOR_EXECUTION'
    for unapproved in (True,False,'REVIEW_REQUIRED','cleared',''):
        release['license_clearance']=unapproved;values['KSTUDIO_CLOUD_RELEASE']=json.dumps(release)
        assert 'release_acceptance_missing' in ops.check(values,commercial=True)['errors']
    operator.pop('support_email');values['KSTUDIO_OPERATOR']=json.dumps(operator)
    assert 'operator_identity_contact_or_icp_missing' in ops.check(values,commercial=True)['errors']


def test_preflight_isolates_compose_environments_and_refuses_non_https_or_wrong_database():
    values={'KSTUDIO_DOMAIN':'operator.test','KSTUDIO_CLOUD_ENV':'staging',
        'KSTUDIO_CLOUD_PUBLIC_URL':'https://operator.test','KSTUDIO_RELEASE_SHA':'a'*40,
        'KSTUDIO_CLOUD_DATABASE_URL':'postgresql+psycopg://kstudio:fixture@db:5432/kstudio',
        'KSTUDIO_DATABASE_PASSWORD':'fixture','KSTUDIO_CLOUD_SESSION_SECRET':'a'*32,
        'KSTUDIO_SECRET_DIR':'/private','KSTUDIO_IMAGE':'kstudio-cloud:'+'a'*40}
    assert ops.check(values)['status']=='READY_FOR_OPERATOR_EXECUTION'
    assert ops.selected_private_network('staging')!=ops.selected_private_network('production')
    for url in ('http://operator.test','https://operator.test/path','https://operator.test:444',
                'https://dev@operator.test','https://[broken'):
        assert 'invalid_https_origin' in ops.check({**values,'KSTUDIO_CLOUD_PUBLIC_URL':url})['errors']
    assert 'database_outside_private_compose_contract' in ops.check({
        **values,'KSTUDIO_CLOUD_DATABASE_URL':'postgresql+psycopg://kstudio:fixture@other-db:5432/kstudio'
    })['errors']
    assert 'invalid_deployment_environment' in ops.check({**values,'KSTUDIO_CLOUD_ENV':'test'})['errors']


def test_health_requires_server_release_and_schema(monkeypatch):
    import io
    observed={'status':'ready','environment':'staging','release_sha':'a'*40,'schema_version':3}
    calls=[]
    class Handler:
        def open(self,request,*,timeout):
            calls.append(request.full_url)
            return io.BytesIO(json.dumps(observed).encode())
    monkeypatch.setattr(ops.urllib.request,'build_opener',lambda *handlers:Handler())
    values={'KSTUDIO_CLOUD_PUBLIC_URL':'https://operator.test','KSTUDIO_RELEASE_SHA':'a'*40,
            'KSTUDIO_CLOUD_ENV':'staging'}
    assert ops.check_health(values)['release_sha']=='a'*40
    assert calls==['https://operator.test/health/ready']
    for key,value in [('release_sha','b'*40),('environment','production'),('schema_version',None)]:
        original=observed[key]
        observed[key]=value
        with pytest.raises(ValueError):ops.check_health(values)
        observed[key]=original


@pytest.fixture
def commercial_receipts(tmp_path):
    import hashlib
    source='a'*40
    installer='b'*64
    url='https://downloads.operator.test/KStudio.exe'
    gates={'schema_version':1,'audit_base_sha':ops.AUDIT_BASE_SHA,'implementation_sha':source,
        'status':'READY_FOR_OWNER_LAUNCH_APPROVAL','gates':[],
        'release':{'signed_installer_sha256':installer,'download_url':url,'version':'fixture','installer_size_bytes':42,
                   'commercial_policy':{
                       'trial':{'mode':'none'},
                       'rollout':{'mode':'operator_managed','max_users':3,'control_reference':'private cohort evidence reference'}}}}
    for i in range(11):
        gate=f'G{i:02d}'
        evidence=tmp_path/gate/'receipt.json'
        evidence.parent.mkdir()
        evidence.write_text(gate,encoding='utf8')
        gates['gates'].append({'id':gate,'status':'PASS','code_sha':source,'independent_reviewer':'fixture review',
            'blockers':[],'evidence_files':[{'path':str(evidence.relative_to(tmp_path)),
                                             'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}]})
    values={'KSTUDIO_RELEASE_SHA':source,'KSTUDIO_CLOUD_PUBLIC_URL':'https://operator.test','KSTUDIO_CLOUD_ENV':'production',
        'KSTUDIO_CLOUD_RELEASE':json.dumps({'sha256':installer,'url':url,'version':'fixture','size_bytes':42,
            'verified':True,'public_distribution_authorized':True,'signing_verified':True,'clean_windows_verified':True,
            'license_clearance':'CLEARED'}),
        'KSTUDIO_DOWNLOAD_ENABLED':'1','KSTUDIO_PRICES_CONFIRMED':'1','KSTUDIO_PAYMENT_PROVIDER':'wechat_native',
        'KSTUDIO_CLOUD_PRICES':json.dumps({'version':'fixture-pricing','byok_service_enabled':False,'byok_task_units':0,
            'packages':{'intro':{'amount':99,'currency':'CNY','credits':100,'name':'Fixture'}}}),
        'KSTUDIO_CLOUD_MODELS':json.dumps({'deepseek':{'enabled':True,'verified':True,'protocol':'responses',
            'upstream_model':'fixture-model','base_url':'https://model.operator.test/v1','key_env':'KSTUDIO_BAI_PLATFORM_KEY',
            'max_output_tokens':8192,'reservation_units':20,'daily_units':500,'turn_budget_units':80,'max_turn_requests':12,
            'turn_timeout_seconds':3600,'reasoning_effort':'high',
            'price':{'version':'platform-fixture','service_units':1,'input_units_per_million':10,'output_units_per_million':20}}}),
        'KSTUDIO_GLOBAL_MAX_CONCURRENCY':'4','KSTUDIO_OPERATOR':json.dumps({'refund_policy':'fixture verified refund policy'}),
        'KSTUDIO_WECHATPAY_MCHID':'12345678','KSTUDIO_WECHATPAY_APPID':'wx_fixture',
        'KSTUDIO_OIDC_METADATA_URL':'https://id.operator.test/.well-known/openid-configuration',
        'KSTUDIO_OIDC_CLIENT_ID':'fixture-public-client'}
    policy_digest=ops.commercial_policy_sha256(values,gates)
    gates['release']['commercial_policy_sha256']=policy_digest
    approval={'release_sha':source,'signed_installer_sha256':installer,
        'gate_sha256':hashlib.sha256(ops.canonical_json(gates)).hexdigest(),'commercial_policy_sha256':policy_digest,
        'origin':'https://operator.test','approved':True,'owner_reference':'fixture reference',
        'switches':['KSTUDIO_DOWNLOAD_ENABLED']}
    return values,gates,approval


def gate_file_sha(gates):
    import hashlib
    return hashlib.sha256(ops.canonical_json(gates)).hexdigest()


def test_live_switch_requires_independent_gates_exact_sha_and_owner_receipt(tmp_path,commercial_receipts):
    values,gates,approval=commercial_receipts
    def validate(settings=values, commercial=True):
        ops.validate_launch(settings,gates,approval,commercial=commercial,evidence_root=tmp_path)
    def rehash():
        approval['gate_sha256']=gate_file_sha(gates)
    validate()
    with pytest.raises(ValueError):validate(commercial=False)
    with pytest.raises(ValueError):validate({**values,'KSTUDIO_PAYMENT_ENABLED':'1'})
    validate({**values,'KSTUDIO_PAYMENT_ENABLED':'0'})
    gates['audit_base_sha']='c'*40
    rehash()
    with pytest.raises(ValueError):validate()
    gates['audit_base_sha']=ops.AUDIT_BASE_SHA
    row=gates['gates'][4]
    for key,value in [('status','BLOCKED_EXTERNAL'),('code_sha','d'*40),('evidence_files',[])]:
        previous=row[key]
        row[key]=value
        rehash()
        with pytest.raises(ValueError):validate()
        row[key]=previous
    rehash()
    receipt=tmp_path/'G04/receipt.json'
    receipt.write_text('changed after owner approval',encoding='utf8')
    with pytest.raises(ValueError,match='evidence changed'):validate()
    receipt.write_text('G04',encoding='utf8')
    validate()


@pytest.mark.parametrize('key, path, change',[
    ('KSTUDIO_CLOUD_PRICES', ('packages','intro','amount'), 100),
    ('KSTUDIO_CLOUD_PRICES', ('packages','intro','credits'), 101),
    ('KSTUDIO_CLOUD_PRICES', ('version',), 'new-price'),
    ('KSTUDIO_CLOUD_PRICES', ('byok_task_units',), 1),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','daily_units'), 550),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','turn_budget_units'), 81),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','max_turn_requests'), 13),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','turn_timeout_seconds'), 3601),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','max_output_tokens'), 8193),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','reasoning_effort'), 'low'),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','upstream_model'), 'another-model'),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','base_url'), 'https://another.operator.test/v1'),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','price','output_units_per_million'), 21),
    ('KSTUDIO_OPERATOR', ('refund_policy',), 'changed refunds'),
    ('KSTUDIO_GLOBAL_MAX_CONCURRENCY', (), '5'),
    ('KSTUDIO_WECHATPAY_MCHID', (), '23456789'),
    ('KSTUDIO_WECHATPAY_APPID', (), 'another_fixture'),
    ('KSTUDIO_OIDC_METADATA_URL', (), 'https://new-id.operator.test/.well-known/openid-configuration'),
    ('KSTUDIO_OIDC_SCOPE', (), 'openid profile'),
    ('KSTUDIO_CLOUD_MODELS', ('deepseek','timeouts'), {'total': 960}),
])
def test_approved_operating_policy_refuses_environment_drift(tmp_path,commercial_receipts,key,path,change):
    values,gates,approval=commercial_receipts
    if path:
        document=json.loads(values[key])
        target=document
        for part in path[:-1]:target=target[part]
        target[path[-1]]=change
        change=json.dumps(document)
    with pytest.raises(ValueError,match='Effective commercial policy'):
        ops.validate_launch({**values,key:change},gates,approval,commercial=True,evidence_root=tmp_path)


@pytest.mark.parametrize('part,value,expected',[
    ('trial',{'mode':'credit_grant','credits':25},'trial must match'),
    ('rollout',{'mode':'operator_managed','max_users':4,'control_reference':'private cohort evidence reference'},'Effective commercial policy'),
    ('rollout',{'mode':'operator_managed','max_users':3,'control_reference':''},'rollout scope'),
])
def test_trial_and_rollout_are_explicit_and_hash_bound(tmp_path,commercial_receipts,part,value,expected):
    values,gates,approval=commercial_receipts
    gates['release']['commercial_policy'][part]=value
    approval['gate_sha256']=gate_file_sha(gates)
    with pytest.raises(ValueError,match=expected):
        ops.validate_launch(values,gates,approval,commercial=True,evidence_root=tmp_path)


def test_canonical_approval_ignores_json_format_and_secret_rotation(tmp_path,commercial_receipts):
    values,gates,approval=commercial_receipts
    values={**values,'KSTUDIO_BAI_PLATFORM_KEY':'fixture-rotated',
            'KSTUDIO_OIDC_CLIENT_SECRET':'fixture-rotated','KSTUDIO_CLOUD_SESSION_SECRET':'fixture-rotated',
            'KSTUDIO_WECHATPAY_API_V3_KEY_FILE':'/run/secrets/kstudio/new-fixture.key'}
    for name in ('KSTUDIO_CLOUD_PRICES','KSTUDIO_OPERATOR','KSTUDIO_CLOUD_MODELS'):
        values[name]=json.dumps(json.loads(values[name]),sort_keys=True,indent=2)
    ops.validate_launch(values,gates,approval,commercial=True,evidence_root=tmp_path)


def test_byok_fee_requires_separate_approval_even_when_other_switches_are_off(tmp_path,commercial_receipts):
    values,gates,approval=commercial_receipts
    price=json.loads(values['KSTUDIO_CLOUD_PRICES'])
    price.update(byok_service_enabled=True,byok_task_units=2)
    values={**values,'KSTUDIO_CLOUD_PRICES':json.dumps(price),**dict.fromkeys(ops.LAUNCH_SWITCHES,'0')}
    assert ops.commercial_open(values)
    policy_digest=ops.commercial_policy_sha256(values,gates)
    gates['release']['commercial_policy_sha256']=policy_digest
    approval.update(gate_sha256=gate_file_sha(gates),commercial_policy_sha256=policy_digest,switches=[])
    with pytest.raises(ValueError,match='matching owner launch approval'):
        ops.validate_launch(values,gates,approval,commercial=True,evidence_root=tmp_path)
    approval['byok_service_approved']=True
    ops.validate_launch(values,gates,approval,commercial=True,evidence_root=tmp_path)
    assert not ops.commercial_open({**values,'KSTUDIO_PRICES_CONFIRMED':'0'})


def test_policy_digest_cli_prints_digest_only(tmp_path,commercial_receipts,monkeypatch,capsys):
    import sys
    values,gates,_=commercial_receipts
    values['KSTUDIO_BAI_PLATFORM_KEY']='fixture-private-secret'
    dotenv=tmp_path/'runtime.env'
    dotenv.write_text('\n'.join(key+'='+value for key,value in values.items()),encoding='utf8')
    state=tmp_path/'release.json'
    state.write_text(json.dumps(gates),encoding='utf8')
    monkeypatch.setattr(sys,'argv',['ops.py','commercial-policy','--env-file',str(dotenv),'--gate-state',str(state)])
    assert ops.main()==0
    output=capsys.readouterr().out
    assert 'fixture-private-secret' not in output
    assert json.loads(output)=={'commercial_policy_sha256':gates['release']['commercial_policy_sha256']}


def test_rollback_refuses_old_image_until_read_only_compatible_audit_passes(monkeypatch):
    calls=[]
    monkeypatch.setattr(ops.subprocess,'check_output',lambda *a,**k:'a'*40)
    def run(command,**kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=b'{"consistent":true,"rollback_read_only":true,"schema_version":3}')
    monkeypatch.setattr(ops.subprocess,'run',run)
    digest='kstudio@sha256:'+'b'*64
    with pytest.raises(ValueError):ops.rollback_image(['docker','compose'],{},'mutable:latest','a'*40)
    with pytest.raises(ValueError):ops.rollback_image(['docker','compose'],{},digest,'f'*40)
    assert calls==[]
    ops.rollback_image(['docker','compose'],{},digest,'a'*40)
    assert len(calls)==2 and calls[0][-1]=='rollback-check'
    assert calls[1][-2:]==['app','maintenance']
    assert '--no-deps' in calls[0] and '--no-deps' in calls[1]


def test_rollback_closes_production_admission_and_new_fees_without_breaking_auth_and_refunds(monkeypatch):
    calls=[]
    monkeypatch.setattr(ops.subprocess,'check_output',lambda *a,**k:'a'*40)
    def run(command,**kwargs):
        calls.append((command,kwargs['env']))
        return SimpleNamespace(stdout=b'{"consistent":true,"rollback_read_only":true,"schema_version":3}')
    monkeypatch.setattr(ops.subprocess,'run',run)
    digest='kstudio@sha256:'+'b'*64
    live={**dict.fromkeys(ops.LAUNCH_SWITCHES,'1'),'KSTUDIO_PRICES_CONFIRMED':'1','KSTUDIO_CLOUD_ENV':'production',
          'KSTUDIO_CLOUD_PRICES':'{"byok_service_enabled":true}',
          'KSTUDIO_OIDC_CLIENT_ID':'fixture-oidc','KSTUDIO_PAYMENT_PROVIDER':'wechat_native',
          'KSTUDIO_WECHATPAY_API_V3_KEY_FILE':'/run/secrets/kstudio/wx-fixture.key'}
    ops.rollback_image(['docker','compose'],live,digest,'a'*40)
    for _,env in calls:
        assert all(env[key]=='0' for key in (*ops.LAUNCH_SWITCHES,'KSTUDIO_PRICES_CONFIRMED'))
        assert env['KSTUDIO_IMAGE']==digest and env['KSTUDIO_RELEASE_SHA']=='a'*40
        for key in ('KSTUDIO_OIDC_CLIENT_ID','KSTUDIO_PAYMENT_PROVIDER','KSTUDIO_WECHATPAY_API_V3_KEY_FILE'):
            assert env[key]==live[key]
    assert all(live[key]=='1' for key in ops.LAUNCH_SWITCHES)
    ops.rollback_image(['docker','compose'],{**live,'KSTUDIO_CLOUD_ENV':'staging'},digest,'a'*40)
    assert all(calls[-1][1][key]=='1' for key in ops.LAUNCH_SWITCHES)


def test_compose_forwards_validated_operative_env_to_app_and_maintenance():
    compose=(ops.ROOT/'compose.yml').read_text(encoding='utf8')
    header,services=compose.split('services:\n',1)
    for key in ops.OPERATIVE_ENV_DEFAULTS:
        setting=re.search(rf'^  {key}: "([^"]+)"$',header,re.MULTILINE)
        assert setting
        assert setting[1].startswith('$'+'{'+key) and setting[1].endswith('}')
    for service,next_service in (('app','maintenance'),('maintenance','proxy')):
        body=services.split(f'\n  {service}:\n',1)[1].split(f'\n  {next_service}:\n',1)[0]
        assert '    environment: *operative-env' in body
    assert 'KSTUDIO_BAI_PLATFORM_KEY:' not in header
    assert 'KSTUDIO_OIDC_CLIENT_SECRET:' not in header


def test_maintenance_horizon_is_independent_of_disabled_route_values(monkeypatch):
    from cloud import maintenance
    calls=[]
    class StopAfterOne:
        def __init__(self):
            self.stopped=False
        def is_set(self):
            return self.stopped
        def wait(self,seconds):
            assert seconds==60
            self.stopped=True
    engine=SimpleNamespace(dispose=lambda:calls.append('disposed'))
    settings=SimpleNamespace(database_url='fixture',models={'disabled':{'enabled':False,'timeouts':None}})
    monkeypatch.setattr(maintenance.Settings,'from_env',lambda:settings)
    monkeypatch.setattr(maintenance.threading,'Event',StopAfterOne)
    monkeypatch.setattr(maintenance.signal,'signal',lambda *args:None)
    monkeypatch.setattr(maintenance,'engine_for',lambda _:engine)
    def cycle_default(target):
        assert target is engine
        calls.append('normal recovery horizon')
        return {'status':'ok'}
    monkeypatch.setattr(maintenance,'cycle',cycle_default)
    maintenance.main()
    assert calls==['normal recovery horizon','disposed']
