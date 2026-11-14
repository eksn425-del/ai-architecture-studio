"""Repeatable operator entry; never prints dotenv values or deletes database volumes."""
from __future__ import annotations
import argparse, hashlib, ipaddress, json, os, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent
RELEASE_SHA = re.compile(r'[a-f0-9]{40}')
SHA256 = re.compile(r'[a-f0-9]{64}')
IMMUTABLE_IMAGE = re.compile(r'(?:[A-Za-z0-9._/:\-]+@)?sha256:[a-f0-9]{64}')
LAUNCH_SWITCHES = ('KSTUDIO_REGISTRATION_ENABLED', 'KSTUDIO_PLATFORM_ENABLED',
                   'KSTUDIO_DOWNLOAD_ENABLED', 'KSTUDIO_PAYMENT_ENABLED')
NETWORKS = {
    'staging': ('172.31.91.0/24', '172.31.91.3'),
    'production': ('172.31.92.0/24', '172.31.92.3'),
}


def selected_private_network(environment):
    """Keep volumes and trusted front proxy disjoint across deployment environments."""
    subnet, proxy = NETWORKS[environment]
    return {'KSTUDIO_PRIVATE_SUBNET': subnet, 'KSTUDIO_PROXY_IP': proxy}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def check_health(values, *, release_sha=None):
    release_sha = release_sha or values['KSTUDIO_RELEASE_SHA']
    origin = values['KSTUDIO_CLOUD_PUBLIC_URL']
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(origin.rstrip('/') + '/health/ready', headers={'Cache-Control': 'no-cache'})
    with opener.open(request, timeout=20) as response:
        observed = json.loads(response.read(64 * 1024))
    if (observed.get('status') != 'ready' or observed.get('environment') != values['KSTUDIO_CLOUD_ENV']
            or observed.get('release_sha') != release_sha or type(observed.get('schema_version')) is not int):
        raise ValueError('HTTPS endpoint did not prove expected environment, release and schema')
    return {'https_ready': True, 'url': origin, 'release_sha': observed['release_sha'],
            'environment': observed['environment'], 'schema_version': observed['schema_version']}


def _validate_gate_evidence(rows, candidate, evidence_root):
    root = evidence_root.resolve(strict=True)
    for row in rows:
        files = row.get('evidence_files')
        reviewer = row.get('independent_reviewer')
        if (row.get('status') != 'PASS' or row.get('code_sha') != candidate
                or not isinstance(reviewer, str) or not reviewer.strip()
                or row.get('blockers') != [] or not isinstance(files, list) or not files):
            raise ValueError(f"Missing independent acceptance for {row['id']}")
        seen = set()
        for item in files:
            relative = Path(str(item.get('path', ''))) if isinstance(item, dict) else Path()
            expected = item.get('sha256') if isinstance(item, dict) else None
            file = root / relative
            if (relative.is_absolute() or '..' in relative.parts or relative in seen
                    or not SHA256.fullmatch(str(expected)) or file.is_symlink()
                    or not file.resolve().is_relative_to(root) or not file.is_file()):
                raise ValueError(f"Invalid acceptance evidence for {row['id']}")
            with file.open('rb') as stream:
                measured = hashlib.file_digest(stream, 'sha256').hexdigest()
            if measured != expected:
                raise ValueError(f"Acceptance evidence changed for {row['id']}")
            seen.add(relative)


def validate_launch(values, gates, approval, *, commercial, evidence_root):
    """Bind approval to a trusted release receipt and the exact switches it covers."""
    expected_gates = {f'G{i:02d}' for i in range(11)}
    rows = gates.get('gates', [])
    statuses = {row.get('id'): row for row in rows if isinstance(row, dict)}
    candidate = values['KSTUDIO_RELEASE_SHA']
    release = json.loads(values['KSTUDIO_CLOUD_RELEASE'])
    requested = {name for name in LAUNCH_SWITCHES if values.get(name) == '1'}
    approved_switches = approval.get('switches', [])
    gate_hash = hashlib.sha256(canonical_json(gates)).hexdigest()
    artifact = gates.get('release', {})
    download = urlsplit(str(release.get('url', '')))
    if (not commercial or type(gates.get('schema_version')) is not int or gates['schema_version'] != 1
            or not RELEASE_SHA.fullmatch(str(gates.get('audit_base_sha', '')))
            or gates.get('implementation_sha') != candidate
            or gates.get('status') != 'READY_FOR_OWNER_LAUNCH_APPROVAL'
            or not expected_gates.issubset(statuses) or len(statuses) != len(rows)
            or not set(statuses).issubset(expected_gates | {'G11'})
            or not isinstance(artifact, dict) or not SHA256.fullmatch(str(release.get('sha256', '')))
            or artifact.get('signed_installer_sha256') != release['sha256']
            or artifact.get('version') != release.get('version') or not str(artifact.get('version') or '').strip()
            or type(release.get('size_bytes')) is not int or release['size_bytes'] <= 0
            or artifact.get('installer_size_bytes') != release['size_bytes']
            or artifact.get('download_url') != release.get('url') or download.scheme != 'https'
            or not download.hostname or download.username or download.password or download.fragment
            or approval.get('release_sha') != candidate or approval.get('gate_sha256') != gate_hash
            or approval.get('signed_installer_sha256') != release.get('sha256')
            or approval.get('origin') != values['KSTUDIO_CLOUD_PUBLIC_URL']
            or approval.get('approved') is not True or not approval.get('owner_reference')
            or not isinstance(approved_switches,list) or not set(approved_switches).issubset(LAUNCH_SWITCHES)
            or not requested.issubset(approved_switches)):
        raise ValueError('Independent READY release and matching owner launch approval are required')
    _validate_gate_evidence([statuses[gate] for gate in sorted(expected_gates)], candidate, evidence_root)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def rollback_image(compose, env, previous_image, expected_sha):
    """Probe the exact old image against the current database before changing services."""
    if (not IMMUTABLE_IMAGE.fullmatch(previous_image or '')
            or not RELEASE_SHA.fullmatch(expected_sha or '')):
        raise ValueError('Rollback requires a verified immutable image digest and its exact release SHA')
    image_label = subprocess.check_output(['docker', 'image', 'inspect', '--format',
        '{{index .Config.Labels "org.opencontainers.image.revision"}}', previous_image], text=True).strip()
    if image_label != expected_sha:
        raise ValueError('Rollback image revision does not match verified release')
    rollback_env = {**env, 'KSTUDIO_IMAGE': previous_image}
    # Run the old code with the existing mounted environment and read-only
    # audit before changing a service. No db migration or volume operation.
    probe = subprocess.run([*compose, 'run', '--no-deps', '--rm', '-T', 'app',
        'python', '-m', 'cloud.cli', 'rollback-check'], env=rollback_env, cwd=ROOT, check=True, capture_output=True)
    evidence = json.loads(probe.stdout)
    if (evidence.get('consistent') is not True or evidence.get('rollback_read_only') is not True
            or type(evidence.get('schema_version')) is not int):
        raise ValueError('Rollback image could not audit the current ledger')
    subprocess.run([*compose, 'up', '-d', '--no-build', '--no-deps', 'app', 'maintenance'],
        env=rollback_env, cwd=ROOT, check=True)


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
    required=['KSTUDIO_DOMAIN','KSTUDIO_DATABASE_PASSWORD','KSTUDIO_CLOUD_DATABASE_URL','KSTUDIO_CLOUD_SESSION_SECRET','KSTUDIO_CLOUD_PUBLIC_URL','KSTUDIO_IMAGE','KSTUDIO_RELEASE_SHA','KSTUDIO_SECRET_DIR','KSTUDIO_CLOUD_ENV']
    if commercial:required+=['KSTUDIO_OIDC_METADATA_URL','KSTUDIO_OIDC_CLIENT_ID','KSTUDIO_OIDC_CLIENT_SECRET','KSTUDIO_VAULT_ACTIVE_KEY_VERSION','KSTUDIO_VAULT_KEYS_FILE','KSTUDIO_WECHATPAY_MCHID','KSTUDIO_WECHATPAY_APPID','KSTUDIO_WECHATPAY_API_V3_KEY_FILE','KSTUDIO_WECHATPAY_MERCHANT_PRIVATE_KEY_FILE','KSTUDIO_WECHATPAY_MERCHANT_SERIAL','KSTUDIO_WECHATPAY_VERIFY_MATERIAL_FILE','KSTUDIO_BAI_PLATFORM_KEY','KSTUDIO_BACKUP_RECIPIENT']
    missing=[k for k in required if not values.get(k) or any(x in values[k] for x in ('REPLACE','example.invalid','URL_ENCODED'))]
    errors=[]
    if values.get('KSTUDIO_CLOUD_ENV') not in NETWORKS:errors.append('invalid_deployment_environment')
    try:
        public=urlsplit(values.get('KSTUDIO_CLOUD_PUBLIC_URL',''))
        if public.hostname!=values.get('KSTUDIO_DOMAIN'):errors.append('public_domain_mismatch')
        if (public.scheme!='https' or not public.hostname or '.' not in public.hostname
                or public.username is not None or public.password is not None or public.port not in (None,443)
                or public.path not in ('','/') or public.query or public.fragment):
            errors.append('invalid_https_origin')
        if public.hostname:
            try:ipaddress.ip_address(public.hostname)
            except ValueError:pass
            else:errors.append('public_origin_requires_dns_name')
    except ValueError:errors.append('invalid_https_origin')
    try:
        database=urlsplit(values.get('KSTUDIO_CLOUD_DATABASE_URL',''))
        if (database.scheme!='postgresql+psycopg' or database.netloc is None or database.hostname!='db'
                or database.port!=5432 or database.path!='/kstudio' or database.username!='kstudio'
                or not database.password or database.query or database.fragment):
            errors.append('database_outside_private_compose_contract')
    except ValueError:errors.append('database_outside_private_compose_contract')
    image=values.get('KSTUDIO_IMAGE','')
    sha=values.get('KSTUDIO_RELEASE_SHA','')
    if image and sha and image != 'kstudio-cloud:'+sha and not IMMUTABLE_IMAGE.fullmatch(image):errors.append('image_outside_release_contract')
    if values.get('KSTUDIO_RELEASE_SHA') and not RELEASE_SHA.fullmatch(values['KSTUDIO_RELEASE_SHA']):errors.append('invalid_release_sha')
    if len(values.get('KSTUDIO_CLOUD_SESSION_SECRET',''))<32:errors.append('session_secret_too_short')
    if any(values.get(name,'0') not in ('0','1') for name in LAUNCH_SWITCHES):errors.append('invalid_launch_switch')
    if commercial and values.get('KSTUDIO_PRICES_CONFIRMED')!='1':errors.append('prices_not_confirmed')
    if commercial and values.get('KSTUDIO_PAYMENT_PROVIDER')!='wechat_native':errors.append('wechat_native_not_selected')
    if commercial:
        try:
            operator=json.loads(values.get('KSTUDIO_OPERATOR','{}'))
            if not isinstance(operator,dict) or not all(operator.get(k) for k in ('name','icp','privacy_contact','data_retention','refund_policy')) or not (operator.get('support_email') or operator.get('support_url')):errors.append('operator_identity_contact_or_icp_missing')
            release=json.loads(values.get('KSTUDIO_CLOUD_RELEASE','{}'))
            if (not isinstance(release,dict) or not all(release.get(k) is True for k in ('verified','public_distribution_authorized','signing_verified','clean_windows_verified'))
                    or release.get('license_clearance')!='CLEARED' or not re.fullmatch(r'[a-f0-9]{64}',str(release.get('sha256','')))):
                errors.append('release_acceptance_missing')
        except ValueError:errors.append('invalid_public_metadata_json')
    return {'status':'READY_FOR_OPERATOR_EXECUTION' if not missing and not errors else 'BLOCKED_CONFIGURATION','missing_names':missing,'errors':errors,'production_acceptance':'NOT_PROVEN_BY_PREFLIGHT'}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['check','deploy','health','audit','recover-stale','backup','restore-drill','rollback']);p.add_argument('--env-file',required=True);p.add_argument('--commercial',action='store_true');p.add_argument('--output');p.add_argument('--archive');p.add_argument('--target-db');p.add_argument('--previous-image');p.add_argument('--previous-release-sha');p.add_argument('--permit-closed-production',action='store_true');p.add_argument('--gate-state',type=Path);p.add_argument('--launch-approval',type=Path);a=p.parse_args()
    envfile=Path(a.env_file).resolve();values=load_env(envfile);result=check(values,commercial=a.commercial)
    if a.action=='check':print(json.dumps(result));return 0 if result['status']=='READY_FOR_OPERATOR_EXECUTION' else 2
    if result['status']!='READY_FOR_OPERATOR_EXECUTION':print(json.dumps(result));return 2
    environment=values['KSTUDIO_CLOUD_ENV']
    env={**os.environ,**values,'KSTUDIO_ENV_FILE':str(envfile),**selected_private_network(environment)}
    # Do not let existing shell environment enable a missing config switch.
    env.update({name:values.get(name,'0') for name in LAUNCH_SWITCHES})
    compose=['docker','compose','--project-name','kstudio-cloud-'+environment,
        '--env-file',str(envfile),'-f',str(ROOT/'compose.yml')]
    def docker(*args):subprocess.run([*compose,*args],env=env,cwd=ROOT,check=True)
    if a.action in ('deploy','rollback') and (os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT')):
        raise ValueError('Use the local authorized Docker context on the deployment host')
    if a.action=='deploy':
        if environment=='production':
            if any(env[name]=='1' for name in LAUNCH_SWITCHES):
                if not a.gate_state or not a.launch_approval:
                    raise ValueError('Opening production requires verified release and private owner approval receipts')
                validate_launch(values,json.loads(a.gate_state.read_bytes()),json.loads(a.launch_approval.read_bytes()),
                    commercial=a.commercial,evidence_root=a.gate_state.resolve().parent)
            elif not a.permit_closed_production:
                raise ValueError('Explicit closed production deployment authorization is required')
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
        if actual!=values['KSTUDIO_RELEASE_SHA']:raise ValueError('Deploy checkout differs from pinned release SHA')
        if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT.parent,text=True).strip():raise ValueError('Deploy requires a clean source checkout')
        docker('config','--quiet')
        if IMMUTABLE_IMAGE.fullmatch(values['KSTUDIO_IMAGE']):
            image_label = subprocess.check_output(['docker','image','inspect','--format',
                '{{index .Config.Labels "org.opencontainers.image.revision"}}',values['KSTUDIO_IMAGE']],text=True).strip()
            if image_label!=actual:raise ValueError('Pinned image revision does not match pinned source')
        else:
            docker('build','app')
        docker('up','-d','db')
        docker('--profile','maintenance','run','--rm','migrate')
        docker('up','-d','--no-build','app','proxy','maintenance')
        docker('exec','-T','app','python','-m','cloud.cli','audit')
    elif a.action=='health':
        print(json.dumps(check_health(values)))
    elif a.action in ('audit','recover-stale'):docker('exec','-T','app','python','-m','cloud.cli',a.action)
    elif a.action=='rollback':
        rollback_image(compose,env,a.previous_image,a.previous_release_sha)
        print('Application image changed without migrations or volume operations. Verify HTTPS readiness against the previous release and audit.')
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
