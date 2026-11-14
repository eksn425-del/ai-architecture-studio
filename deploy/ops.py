"""Repeatable operator entry; never prints dotenv values or deletes database volumes."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent

def restore_target(value):
    if not isinstance(value,str) or not re.fullmatch(r'kstudio_restore_[a-z0-9_]{1,45}',value):
        raise ValueError('Restore requires an explicit new kstudio_restore_* database')
    return value

def encrypted_backup(compose,env,output):
    """pg_dump runs inside the private DB container; no host port is needed."""
    target=Path(output).resolve()
    if target.exists() or target.is_symlink():raise ValueError('Refusing existing backup destination')
    if not target.parent.is_dir():raise ValueError('Create the private backup directory first')
    recipient=env.get('KSTUDIO_BACKUP_RECIPIENT','')
    if not recipient:raise ValueError('Backup public recipient is missing')
    age=env.get('KSTUDIO_AGE_EXECUTABLE','age')
    with tempfile.TemporaryDirectory(prefix='.kstudio-backup-',dir=target.parent) as temporary:
        temporary=Path(temporary);os.chmod(temporary,0o700)
        encrypted=temporary/'database.age'
        with (temporary/'private-errors.log').open('wb') as errors:
            producer=subprocess.Popen([*compose,'exec','-T','db','pg_dump','-U','kstudio','-d','kstudio',
                '--format=custom','--no-owner','--no-acl'],env=env,stdout=subprocess.PIPE,stderr=errors)
            consumer=None
            try:
                consumer=subprocess.Popen([age,'--recipient',recipient,'--output',str(encrypted)],
                    env=env,stdin=producer.stdout,stdout=subprocess.DEVNULL,stderr=errors)
                producer.stdout.close()
                c=consumer.wait(timeout=1800);p=producer.wait(timeout=1800)
                if p or c:raise RuntimeError('Encrypted database backup failed')
            finally:
                for child in (producer,consumer):
                    if child is not None and child.poll() is None:child.kill();child.wait()
        os.chmod(encrypted,0o600)
        # Same-filesystem exclusive publication cannot replace an earlier archive.
        os.link(encrypted,target)
    with target.open('rb') as source:sha=hashlib.file_digest(source,'sha256').hexdigest()
    return {'status':'ENCRYPTED_BACKUP_CREATED','database':'kstudio','bytes':target.stat().st_size,
        'sha256':sha,
        'transport':'docker compose exec private db; no host database port',
        'keys_in_archive':False,'scope':'single-database logical snapshot; not WAL/PITR'}

def encrypted_restore(compose,env,archive,target_database):
    """Authenticate the archive first, create a NEW DB, restore atomically, verify."""
    target_database=restore_target(target_database)
    archive=Path(archive).resolve()
    identity=env.get('KSTUDIO_BACKUP_IDENTITY','')
    if not archive.is_file() or not identity or not Path(identity).is_file():
        raise ValueError('Encrypted archive and separate private backup identity required')
    age=env.get('KSTUDIO_AGE_EXECUTABLE','age')
    with tempfile.TemporaryDirectory(prefix='.kstudio-restore-',dir=archive.parent) as temporary:
        temporary=Path(temporary);os.chmod(temporary,0o700)
        plain=temporary/'database.dump'
        # Decrypt completely before any SQL; authenticated EOF is required.
        subprocess.run([age,'--decrypt','--identity',identity,'--output',str(plain),str(archive)],
            env=env,check=True,capture_output=True,timeout=1800)
        os.chmod(plain,0o600)
        # createdb refuses an existing name. Never DROP or clear an old database.
        subprocess.run([*compose,'exec','-T','db','createdb','-U','kstudio','--',target_database],
            env=env,check=True,capture_output=True,timeout=60)
        with plain.open('rb') as incoming:
            subprocess.run([*compose,'exec','-T','db','pg_restore','-U','kstudio','--dbname',target_database,
                '--exit-on-error','--single-transaction','--no-owner','--no-acl'],
                env=env,stdin=incoming,check=True,capture_output=True,timeout=1800)
    # Read-only verify in the normal application image using its mounted vault keys.
    result=subprocess.run([*compose,'--profile','maintenance','run','--rm','-T','migrate',
        'python','-',target_database],env=env,input=(ROOT/'verify_restore.py').read_bytes(),
        check=True,capture_output=True,timeout=180)
    receipt=json.loads(result.stdout)
    if receipt.get('status')!='PASS':raise RuntimeError('Restored database validation failed')
    return receipt
def load_env(path):
    values={}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        key,sep,value=line.partition('=')
        if not sep or not re.fullmatch(r'[A-Z][A-Z0-9_]*',key):raise ValueError('Invalid private environment file syntax')
        values[key]=value.strip().strip('"') if not value.lstrip().startswith(('{','[')) else value.strip()
    return values

def check(values, *, commercial=False):
    required=['KSTUDIO_DOMAIN','KSTUDIO_DATABASE_PASSWORD','KSTUDIO_CLOUD_DATABASE_URL','KSTUDIO_CLOUD_SESSION_SECRET','KSTUDIO_CLOUD_PUBLIC_URL','KSTUDIO_IMAGE','KSTUDIO_RELEASE_SHA','KSTUDIO_SECRET_DIR']
    if commercial:required+=['KSTUDIO_OIDC_METADATA_URL','KSTUDIO_OIDC_CLIENT_ID','KSTUDIO_OIDC_CLIENT_SECRET','KSTUDIO_VAULT_ACTIVE_KEY_VERSION','KSTUDIO_VAULT_KEYS_FILE','KSTUDIO_WECHATPAY_MCHID','KSTUDIO_WECHATPAY_APPID','KSTUDIO_WECHATPAY_API_V3_KEY_FILE','KSTUDIO_WECHATPAY_MERCHANT_PRIVATE_KEY_FILE','KSTUDIO_WECHATPAY_MERCHANT_SERIAL','KSTUDIO_WECHATPAY_VERIFY_MATERIAL_FILE','KSTUDIO_BAI_PLATFORM_KEY','KSTUDIO_BACKUP_RECIPIENT']
    missing=[k for k in required if not values.get(k) or any(x in values[k] for x in ('REPLACE','example.invalid','URL_ENCODED'))]
    errors=[]
    if values.get('KSTUDIO_CLOUD_PUBLIC_URL') and urlsplit(values['KSTUDIO_CLOUD_PUBLIC_URL']).hostname!=values.get('KSTUDIO_DOMAIN'):errors.append('public_domain_mismatch')
    if values.get('KSTUDIO_RELEASE_SHA') and not re.fullmatch('[a-f0-9]{40}',values['KSTUDIO_RELEASE_SHA']):errors.append('invalid_release_sha')
    if commercial and values.get('KSTUDIO_PRICES_CONFIRMED')!='1':errors.append('prices_not_confirmed')
    if commercial and values.get('KSTUDIO_PAYMENT_PROVIDER')!='wechat_native':errors.append('wechat_native_not_selected')
    if commercial:
        try:
            operator=json.loads(values.get('KSTUDIO_OPERATOR','{}'))
            if not all(operator.get(k) for k in ('name','icp','privacy_contact','data_retention','refund_policy')) or not (operator.get('support_email') or operator.get('support_url')):errors.append('operator_identity_contact_or_icp_missing')
            release=json.loads(values.get('KSTUDIO_CLOUD_RELEASE','{}'))
            if not all(release.get(k) is True for k in ('verified','public_distribution_authorized','signing_verified','clean_windows_verified')) or release.get('license_clearance')!='CLEARED':errors.append('release_acceptance_missing')
        except ValueError:errors.append('invalid_public_metadata_json')
    return {'status':'READY_FOR_OPERATOR_EXECUTION' if not missing and not errors else 'BLOCKED_CONFIGURATION','missing_names':missing,'errors':errors,'production_acceptance':'NOT_PROVEN_BY_PREFLIGHT'}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['check','deploy','health','audit','recover-stale','backup','restore-drill','rollback']);p.add_argument('--env-file',required=True);p.add_argument('--commercial',action='store_true');p.add_argument('--output');p.add_argument('--archive');p.add_argument('--target-db');p.add_argument('--previous-image');a=p.parse_args()
    envfile=Path(a.env_file).resolve();values=load_env(envfile);result=check(values,commercial=a.commercial)
    if a.action=='check':print(json.dumps(result));return 0 if result['status']=='READY_FOR_OPERATOR_EXECUTION' else 2
    if result['status']!='READY_FOR_OPERATOR_EXECUTION':print(json.dumps(result));return 2
    env={**os.environ,**values,'KSTUDIO_ENV_FILE':str(envfile)}
    compose=['docker','compose','--env-file',str(envfile),'-f',str(ROOT/'compose.yml')]
    def docker(*args):subprocess.run([*compose,*args],env=env,cwd=ROOT,check=True)
    if a.action=='deploy':
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
        if actual!=values['KSTUDIO_RELEASE_SHA']:raise ValueError('Deploy checkout differs from pinned release SHA')
        if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT.parent,text=True).strip():raise ValueError('Deploy requires a clean source checkout')
        docker('config','--quiet');docker('build','app','migrate','maintenance');docker('up','-d','db')
        docker('--profile','maintenance','run','--rm','migrate');docker('up','-d','app','proxy','maintenance');docker('exec','-T','app','python','-m','cloud.cli','audit')
    elif a.action=='health':
        with urllib.request.urlopen(values['KSTUDIO_CLOUD_PUBLIC_URL'].rstrip('/')+'/health/ready',timeout=20) as r:status=json.load(r)
        if status.get('status')!='ready':raise ValueError('Public readiness failed')
        print(json.dumps({'https_ready':True,'url':values['KSTUDIO_CLOUD_PUBLIC_URL'],'release_sha':values['KSTUDIO_RELEASE_SHA']}))
    elif a.action in ('audit','recover-stale'):docker('exec','-T','app','python','-m','cloud.cli',a.action)
    elif a.action=='rollback':
        if not a.previous_image or not re.fullmatch(r'[A-Za-z0-9./:_@-]+',a.previous_image):raise ValueError('Exact previous image required')
        env['KSTUDIO_IMAGE']=a.previous_image
        docker('up','-d','--no-build','app','maintenance')
        print('Application image changed; database and all volumes preserved. Verify schema compatibility and health.')
    elif a.action=='backup':
        if not a.output:raise ValueError('New private encrypted backup output required')
        print(json.dumps(encrypted_backup(compose,env,a.output)))
    elif a.action=='restore-drill':
        if not a.archive:raise ValueError('Encrypted archive required')
        print(json.dumps(encrypted_restore(compose,env,a.archive,a.target_db)))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        # Library messages can include URLs/passwords. Report only type at boundary.
        print(json.dumps({'status':'FAILED','error_type':type(exc).__name__,'secrets_printed':False}));sys.exit(1)
